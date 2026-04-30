#!/usr/bin/env python3
"""
Client Readiness Agent
======================
Lightweight local agent for MQ Client Optimizer, Client Readiness Dashboard,
and Fleet Command Center.

It exposes readiness data at http://127.0.0.1:38765/status and can also print
a single JSON payload with --once.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import http.server
import json
import platform
import plistlib
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


PORT = 38765
REFRESH = 300
AGENT_VERSION = "1.0.0"

_lock = threading.Lock()
_cache: dict[str, Any] = {}


def main() -> int:
    parser = argparse.ArgumentParser(description="MQ Client Readiness Agent")
    parser.add_argument("--once", action="store_true", help="Print one JSON payload and exit")
    parser.add_argument("--profile", help="Override reported profile id")
    parser.add_argument("--port", type=int, default=PORT, help=f"HTTP port, default {PORT}")
    parser.add_argument("--refresh", type=int, default=REFRESH, help=f"Refresh interval, default {REFRESH}s")
    args = parser.parse_args()

    if args.once:
        print(json.dumps(collect_all(args.profile), indent=2, sort_keys=True))
        return 0

    print()
    print("  MQ Client Readiness Agent")
    print("  -------------------------------------------")
    print(f"  API:      http://127.0.0.1:{args.port}/status")
    print(f"  Refresh:  http://127.0.0.1:{args.port}/refresh")
    print(f"  Interval: {args.refresh}s")
    print()

    threading.Thread(target=refresh_loop, args=(args.profile, args.refresh), daemon=True).start()
    Handler.profile_override = args.profile
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as srv:
            srv.serve_forever()
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopping.")
        return 0


def refresh_loop(profile_override: str | None, interval: int) -> None:
    collect_into_cache(profile_override)
    while True:
        time.sleep(interval)
        collect_into_cache(profile_override)


def collect_into_cache(profile_override: str | None) -> None:
    data = collect_all(profile_override)
    with _lock:
        _cache.clear()
        _cache.update(data)


def collect_all(profile_override: str | None = None) -> dict[str, Any]:
    system = platform.system()
    if system == "Darwin":
        data = collect_macos(profile_override)
    elif system == "Linux":
        data = collect_linux(profile_override)
    else:
        data = collect_generic(profile_override)

    data["meta"]["collected_at"] = utcnow()
    data["meta"]["agent_version"] = AGENT_VERSION
    data["meta"]["capabilities"] = sorted(discover_capabilities(data))
    return data


def collect_macos(profile_override: str | None) -> dict[str, Any]:
    hostname = run(["hostname", "-s"]) or socket.gethostname()
    sw = parse_sw_vers()
    certs = collect_macos_certificates()
    citrix = detect_macos_citrix()

    return {
        "meta": {
            "profile": profile_override or "macos-citrix",
            "platform": "macOS",
            "platform_release": sw.get("ProductVersion", platform.release()),
            "platform_build": sw.get("BuildVersion", ""),
            "machine": platform.machine(),
            "hostname": hostname,
            "baseline_version": "2026.04.30",
        },
        "network": {"online": network_online(), "hostname": hostname, "local_ips": local_ips()},
        "certificates": certs,
        "citrix": citrix,
        "processes": {"running": running_processes(["wfica", "AuthManager", "ServiceRecords", "Citrix"]), "missing": []},
    }


def collect_linux(profile_override: str | None) -> dict[str, Any]:
    os_release = parse_os_release()
    hostname = run(["hostname", "-s"]) or socket.gethostname()
    certs = collect_linux_certificates()
    citrix = detect_linux_citrix()

    return {
        "meta": {
            "profile": profile_override or infer_linux_profile(os_release),
            "platform": os_release.get("PRETTY_NAME") or "Linux",
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "hostname": hostname,
            "baseline_version": "2026.04.30",
        },
        "network": {"online": network_online(), "hostname": hostname, "local_ips": local_ips()},
        "certificates": certs,
        "citrix": citrix,
        "processes": {"running": running_processes(["wfica", "selfservice", "storebrowse", "pcscd"]), "missing": []},
    }


def collect_generic(profile_override: str | None) -> dict[str, Any]:
    hostname = socket.gethostname()
    return {
        "meta": {
            "profile": profile_override or "kiosk",
            "platform": platform.system() or "unknown",
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "hostname": hostname,
            "baseline_version": "2026.04.30",
        },
        "network": {"online": network_online(), "hostname": hostname, "local_ips": local_ips()},
        "certificates": {"installed": [], "details": []},
        "citrix": {"installed": False, "version": "", "path": ""},
        "processes": {"running": [], "missing": []},
    }


def parse_sw_vers() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in run(["sw_vers"]).splitlines():
        key, _, value = line.partition(":")
        if key:
            values[key.strip()] = value.strip()
    return values


def parse_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" not in line or line.strip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    except Exception:
        return {}
    return values


def infer_linux_profile(os_release: dict[str, str]) -> str:
    text = " ".join(os_release.values()).lower()
    if "elux" in text:
        return "elux7-citrix"
    return "igel-os12-citrix"


def detect_macos_citrix() -> dict[str, Any]:
    candidates = [
        Path("/Applications/Citrix Workspace.app/Contents/Info.plist"),
        Path("/Applications/Citrix Viewer.app/Contents/Info.plist"),
    ]
    for info_plist in candidates:
        if info_plist.exists():
            return {"installed": True, "version": plist_version(info_plist), "path": str(info_plist.parent.parent)}

    receipts = glob.glob("/Library/Receipts/*Citrix*.plist") + glob.glob("/var/db/receipts/com.citrix*.plist")
    if receipts:
        return {"installed": True, "version": "", "path": receipts[0]}
    return {"installed": False, "version": "", "path": ""}


def detect_linux_citrix() -> dict[str, Any]:
    for binary in ("wfica", "selfservice", "storebrowse"):
        path = shutil.which(binary)
        if path:
            return {"installed": True, "version": citrix_binary_version(path), "path": path}

    package_version = linux_package_version(["icaclient", "ctxusb", "citrix-workspace"])
    if package_version:
        return {"installed": True, "version": package_version, "path": ""}
    return {"installed": False, "version": "", "path": ""}


def plist_version(path: Path) -> str:
    try:
        with path.open("rb") as f:
            data = plistlib.load(f)
        return str(data.get("CFBundleShortVersionString") or data.get("CFBundleVersion") or "")
    except Exception:
        return ""


def citrix_binary_version(path: str) -> str:
    for command in ([path, "-version"], [path, "--version"], [path, "-v"]):
        out = run(command, timeout=3)
        match = re.search(r"(\d+\.\d+(?:\.\d+)*)", out)
        if match:
            return match.group(1)
    return ""


def linux_package_version(names: list[str]) -> str:
    if shutil.which("dpkg-query"):
        for name in names:
            out = run(["dpkg-query", "-W", "-f=${Version}", name], timeout=3)
            if out and "no packages found" not in out.lower():
                return out.strip()
    if shutil.which("rpm"):
        for name in names:
            out = run(["rpm", "-q", "--qf", "%{VERSION}", name], timeout=3)
            if out and "not installed" not in out.lower():
                return out.strip()
    return ""


def collect_macos_certificates() -> dict[str, Any]:
    raw = run(
        "security find-certificate -a -p /Library/Keychains/System.keychain 2>/dev/null | "
        "openssl x509 -noout -subject -issuer -dates -fingerprint -sha1 2>/dev/null",
        timeout=20,
    )
    details = parse_pem_certificates(raw, store="system")
    return {"installed": sorted({cert["name"] for cert in details if cert.get("name")}), "details": details}


def collect_linux_certificates() -> dict[str, Any]:
    candidates = []
    for pattern in ("/etc/ssl/certs/*.pem", "/etc/ssl/certs/*.crt", "/usr/local/share/ca-certificates/*.crt", "/wfs/ca-certs/*.crt"):
        candidates.extend(glob.glob(pattern))

    details = []
    for path in candidates[:300]:
        out = run(["openssl", "x509", "-in", path, "-noout", "-subject", "-issuer", "-dates", "-fingerprint", "-sha1"], timeout=3)
        if out:
            parsed = parse_certificate_block(out, store=str(Path(path).parent))
            if parsed:
                parsed["path"] = path
                details.append(parsed)

    deduped = dedupe_certs(details)
    return {"installed": sorted({cert["name"] for cert in deduped if cert.get("name")}), "details": deduped}


def parse_pem_certificates(raw: str, store: str) -> list[dict[str, Any]]:
    certs = []
    for block in re.split(r"(?=subject=)", raw):
        parsed = parse_certificate_block(block, store)
        if parsed:
            certs.append(parsed)
    return dedupe_certs(certs)


def parse_certificate_block(block: str, store: str) -> dict[str, Any] | None:
    if "subject=" not in block and "notAfter=" not in block:
        return None
    subject = match_line(block, r"subject=(.+)")
    issuer = match_line(block, r"issuer=(.+)")
    not_after_raw = match_line(block, r"notAfter=(.+)")
    fingerprint = match_line(block, r"SHA1 Fingerprint=(.+)") or match_line(block, r"sha1 Fingerprint=(.+)")
    name = common_name(subject) or subject[:120]
    return {
        "thumbprint": (fingerprint or "").replace(":", ""),
        "store": store,
        "name": name,
        "subject": subject,
        "issuer": issuer,
        "not_after": normalize_cert_date(not_after_raw),
    }


def match_line(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def common_name(subject: str) -> str:
    for pattern in (r"CN\s*=\s*([^,\n/]+)", r"/CN=([^/\n]+)"):
        match = re.search(pattern, subject)
        if match:
            return match.group(1).strip()
    return ""


def normalize_cert_date(value: str) -> str:
    if not value:
        return ""
    for fmt in ("%b %d %H:%M:%S %Y %Z", "%b  %d %H:%M:%S %Y %Z"):
        try:
            parsed = dt.datetime.strptime(value, fmt).replace(tzinfo=dt.timezone.utc)
            return parsed.isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    return value


def dedupe_certs(certs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for cert in certs:
        key = cert.get("thumbprint") or (cert.get("name"), cert.get("not_after"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(cert)
    return unique


def discover_capabilities(data: dict[str, Any]) -> set[str]:
    caps = {"meta.profile", "meta.baseline_version", "network.hostname", "network.online"}
    if data.get("network", {}).get("local_ips") is not None:
        caps.add("network.local_ips")
    if data.get("certificates", {}).get("installed"):
        caps.add("certificates.installed")
    if data.get("certificates", {}).get("details"):
        caps.add("certificates.details")
    if data.get("citrix", {}).get("installed") is not None:
        caps.add("citrix.installed")
    if data.get("citrix", {}).get("version") is not None:
        caps.add("citrix.version")
    if data.get("processes", {}).get("running") is not None:
        caps.add("processes.running")
    return caps


def network_online() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=2):
            return True
    except OSError:
        return False


def local_ips() -> list[str]:
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if not ip.startswith("127.") and ip != "::1":
                ips.add(ip)
    except OSError:
        pass

    if platform.system() == "Darwin":
        for line in run(["ifconfig"]).splitlines():
            match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)", line)
            if match and not match.group(1).startswith("127."):
                ips.add(match.group(1))
    elif platform.system() == "Linux":
        for ip in run(["hostname", "-I"]).split():
            if not ip.startswith("127."):
                ips.add(ip)
    return sorted(ips)


def running_processes(names: list[str]) -> list[str]:
    ps = run(["ps", "-axo", "comm="], timeout=5)
    found = []
    for name in names:
        if re.search(rf"(^|/){re.escape(name)}(\s|$)", ps, re.IGNORECASE | re.MULTILINE):
            found.append(name)
    return sorted(set(found))


def run(cmd: list[str] | str, timeout: int = 8) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
        return (result.stdout or "").strip()
    except Exception:
        return ""


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    profile_override: str | None = None

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/status"):
            with _lock:
                payload = dict(_cache)
            self.send_json(200, payload)
        elif path == "/refresh":
            threading.Thread(target=collect_into_cache, args=(self.profile_override,), daemon=True).start()
            self.send_json(202, {"status": "refreshing"})
        else:
            self.send_json(404, {"error": "not found"})

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
