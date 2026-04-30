#!/usr/bin/env python3
"""
MQ Client Optimizer v1

Template-based client readiness and compliance analyzer for IGEL and macOS.
The first version is intentionally safe: it evaluates baselines and writes
reports, but it does not change endpoint configuration.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


APP_NAME = "MQ Client Optimizer"
APP_VERSION = "v1"
BASE_DIR = Path(__file__).resolve().parent
BASELINES_DIR = BASE_DIR / "baselines"


SAMPLES: dict[str, dict[str, Any]] = {
    "igel-os12-citrix": {
        "meta": {
            "agent_version": "2.3.0",
            "baseline_version": "2026.04.30",
            "profile": "igel-os12-citrix",
            "capabilities": [
                "certificates.installed",
                "certificates.details",
                "citrix.installed",
                "citrix.version",
                "network.online",
            ],
        },
        "network": {"online": True, "hostname": "IGEL-CLIENT-01"},
        "certificates": {
            "installed": ["Company Root CA", "DigiCert Global Root CA"],
            "details": [
                {
                    "name": "Company Root CA",
                    "not_after": "2027-12-31T23:59:59Z",
                }
            ],
        },
        "citrix": {"installed": True, "version": "24.2.0"},
    },
    "macos-citrix": {
        "meta": {
            "agent_version": "1.0.0",
            "profile": "macos-citrix",
            "capabilities": ["citrix.installed", "citrix.version", "network.online"],
        },
        "network": {"online": True, "hostname": "MAC-001"},
        "citrix": {"installed": True, "version": "24.2.0"},
    },
    "macos-enterprise-cis-lite": {
        "meta": {
            "agent_version": "1.0.0",
            "profile": "macos-enterprise-cis-lite",
            "hostname": "MacBook-Pro-Enterprise",
        },
        "security": {
            "filevault": {"enabled": True},
            "sip": {"enabled": True},
            "gatekeeper": {"enabled": True},
            "firewall": {"enabled": True, "stealth_mode": False},
            "auto_updates": {
                "automatic_check": True,
                "automatic_install_security": True,
                "critical_updates": True,
            },
        },
        "identity": {
            "ssh_enabled": False,
            "autologin": False,
            "screen_lock": {
                "require_password": True,
                "idle_minutes": 5,
            },
        },
        "mdm": {"enrolled": True, "supervised": True},
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mq-client-optimizer",
        description=f"{APP_NAME} {APP_VERSION}: IGEL and macOS baseline analyzer",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list-baselines", help="List available baselines")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON")

    analyze = sub.add_parser("analyze", help="Analyze client data against a baseline")
    analyze.add_argument("--baseline", required=True, help="Baseline id or JSON file")
    source = analyze.add_mutually_exclusive_group()
    source.add_argument("--input", help="Input JSON file with client data")
    source.add_argument("--agent-url", help="Agent URL returning JSON, for example http://127.0.0.1:38764/status")
    source.add_argument("--sample", action="store_true", help="Use built-in sample data")
    analyze.add_argument("--output-json", help="Write JSON report to this path")
    analyze.add_argument("--output-html", help="Write HTML report to this path")
    analyze.add_argument("--fail-on", choices=["fail", "warn", "unknown", "never"], default="never")

    sample = sub.add_parser("sample-data", help="Print sample input data for a baseline")
    sample.add_argument("--baseline", required=True, help="Baseline id")

    args = parser.parse_args()

    if args.command == "list-baselines":
        baselines = [load_baseline(path) for path in sorted(BASELINES_DIR.glob("*.json"))]
        return print_baselines(baselines, as_json=args.json)

    if args.command == "sample-data":
        data = SAMPLES.get(args.baseline)
        if data is None:
            die(f"No built-in sample exists for baseline: {args.baseline}")
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    baseline = load_baseline(resolve_baseline(args.baseline))
    data = load_data(args, baseline)
    report = analyze_data(baseline, data)
    print_text_report(report)

    if args.output_json:
        write_json_report(report, Path(args.output_json))
    if args.output_html:
        write_html_report(report, Path(args.output_html))

    return exit_code(report, args.fail_on)


def resolve_baseline(name_or_path: str) -> Path:
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate
    bundled = BASELINES_DIR / f"{name_or_path}.json"
    if bundled.exists():
        return bundled
    die(f"Baseline not found: {name_or_path}")


def load_baseline(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            baseline = json.load(f)
    except Exception as exc:
        die(f"Failed to load baseline {path}: {exc}")

    for key in ("id", "name", "platform", "checks"):
        if key not in baseline:
            die(f"Invalid baseline {path}: missing '{key}'")
    return baseline


def load_data(args: argparse.Namespace, baseline: dict[str, Any]) -> dict[str, Any]:
    if args.input:
        return read_json(Path(args.input))
    if args.agent_url:
        return fetch_json(args.agent_url)
    if args.sample:
        sample = SAMPLES.get(baseline["id"])
        if sample is None:
            die(f"No built-in sample exists for baseline: {baseline['id']}")
        return sample
    die("No data source selected. Use --input, --agent-url, or --sample.")


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        die(f"Failed to read input JSON {path}: {exc}")
    if not isinstance(data, dict):
        die("Input JSON must be an object")
    return data


def fetch_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        die(f"Failed to fetch agent data from {url}: {exc}")


def analyze_data(baseline: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    results = [evaluate_check(check, data) for check in baseline.get("checks", [])]
    summary = {
        "total": len(results),
        "pass": count_status(results, "PASS"),
        "warn": count_status(results, "WARN"),
        "fail": count_status(results, "FAIL"),
        "unknown": count_status(results, "UNKNOWN"),
        "unsupported": count_status(results, "UNSUPPORTED"),
    }
    active = [r for r in results if r["status"] not in ("UNKNOWN", "UNSUPPORTED")]
    summary["score"] = round((count_status(active, "PASS") / len(active)) * 100) if active else 0

    return {
        "tool": {"name": APP_NAME, "version": APP_VERSION},
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "baseline": {
            "id": baseline["id"],
            "name": baseline["name"],
            "platform": baseline["platform"],
            "version": baseline.get("version", ""),
            "mode": "analyze",
        },
        "target": target_summary(data),
        "summary": summary,
        "results": results,
    }


def evaluate_check(check: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    required = check.get("required_capability")
    capabilities = get_path(data, "meta.capabilities")
    if required and (not isinstance(capabilities, list) or required not in capabilities):
        return result(check, "UNSUPPORTED", None, f"Missing capability: {required}")

    actual = get_path(data, check.get("source") or check.get("path") or "")
    op = check.get("operator") or check.get("op")

    if actual in (None, "") or actual == -1:
        return result(check, "UNKNOWN", actual, "Value is not available")

    if op in ("eq_true", "eq_false"):
        expected = op == "eq_true"
        ok = actual is expected
        return result(check, "PASS" if ok else "FAIL", actual, f"Expected {expected}, got {actual}")

    if op == "equals":
        expected = check.get("expected")
        ok = str(actual) == str(expected)
        return result(check, "PASS" if ok else "FAIL", actual, f"Expected {expected}, got {actual}")

    if op == "contains":
        actual_values = normalize_list(actual)
        expected_values = normalize_list(check.get("expected"))
        missing = [x for x in expected_values if x not in actual_values]
        status = "PASS" if not missing else "FAIL"
        detail = "All expected values found" if not missing else "Missing: " + ", ".join(map(str, missing))
        return result(check, status, actual_values, detail)

    if op == "min_version":
        expected = str(check.get("expected", ""))
        ok = compare_versions(str(actual), expected) >= 0
        detail = f"Version {actual} satisfies minimum {expected}" if ok else f"Version {actual} is below minimum {expected}"
        return result(check, "PASS" if ok else "FAIL", actual, detail)

    if op == "lte":
        threshold = check.get("threshold")
        ok = isinstance(actual, (int, float)) and actual <= threshold
        return result(check, "PASS" if ok else "FAIL", actual, f"Expected <= {threshold}, got {actual}")

    if op == "cert_name_exists":
        cert = find_cert(actual, check.get("expected", ""))
        detail = f"Found certificate: {cert.get('name')}" if cert else f"Certificate not found: {check.get('expected')}"
        return result(check, "PASS" if cert else "FAIL", cert, detail)

    if op == "cert_expiry_days":
        cert = find_cert(actual, check.get("match", ""))
        if not cert:
            return result(check, "FAIL", None, f"Certificate not found: {check.get('match')}")
        days = days_until(cert.get("not_after") or cert.get("expiry"))
        if days is None:
            return result(check, "FAIL", cert, "Invalid or missing expiry date")
        if days < int(check.get("fail_days", 0)):
            return result(check, "FAIL", days, f"Expired {abs(days)} days ago")
        if days <= int(check.get("warn_days", 30)):
            return result(check, "WARN", days, f"Expires in {days} days")
        return result(check, "PASS", days, f"Valid for {days} days")

    return result(check, "UNKNOWN", actual, f"Unsupported operator: {op}")


def result(check: dict[str, Any], status: str, actual: Any, evidence: str) -> dict[str, Any]:
    return {
        "id": check.get("id", ""),
        "title": check.get("title", ""),
        "category": check.get("category", "general"),
        "severity": check.get("severity", "medium"),
        "status": status,
        "expected": check.get("expected", check.get("match", check.get("threshold"))),
        "actual": actual,
        "evidence": evidence,
        "remediation": check.get("remediation", ""),
    }


def target_summary(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("meta", {})
    network = data.get("network", {})
    return {
        "hostname": meta.get("hostname") or network.get("hostname") or "",
        "profile": meta.get("profile", ""),
        "agent_version": meta.get("agent_version", ""),
        "platform": meta.get("macos_name") or meta.get("platform") or "",
        "os_version": meta.get("macos_version") or meta.get("os_version") or "",
    }


def print_baselines(baselines: list[dict[str, Any]], as_json: bool) -> int:
    if as_json:
        print(json.dumps(baselines, indent=2, sort_keys=True))
        return 0
    print(f"{APP_NAME} {APP_VERSION} baselines")
    for baseline in baselines:
        print(
            f"- {baseline['id']}: {baseline['name']} "
            f"({baseline['platform']}, {len(baseline.get('checks', []))} checks)"
        )
    return 0


def print_text_report(report: dict[str, Any]) -> None:
    baseline = report["baseline"]
    summary = report["summary"]
    target = report["target"]
    print(f"{APP_NAME} {APP_VERSION}")
    print(f"Baseline: {baseline['id']} - {baseline['name']}")
    if target.get("hostname"):
        print(f"Target:   {target['hostname']}")
    print(
        "Summary:  "
        f"score={summary['score']} "
        f"pass={summary['pass']} warn={summary['warn']} "
        f"fail={summary['fail']} unknown={summary['unknown']} "
        f"unsupported={summary['unsupported']}"
    )
    print()
    for row in report["results"]:
        print(f"[{row['status']:<11}] {row['id']:<16} {row['title']}")
        if row["status"] != "PASS":
            print(f"  evidence:    {row['evidence']}")
            if row["remediation"]:
                print(f"  remediation: {row['remediation']}")


def write_json_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)


def write_html_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(r['status'])}</td><td>{esc(r['severity'])}</td>"
        f"<td>{esc(r['id'])}</td><td>{esc(r['title'])}</td>"
        f"<td>{esc(r['evidence'])}</td><td>{esc(r['remediation'])}</td>"
        "</tr>"
        for r in report["results"]
    )
    summary = report["summary"]
    baseline = report["baseline"]
    target = report["target"]
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{esc(APP_NAME)} {esc(APP_VERSION)} Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 32px; color: #17202a; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; font-size: 12px; text-transform: uppercase; }}
    .meta {{ color: #57606a; }}
  </style>
</head>
<body>
  <h1>{esc(APP_NAME)} {esc(APP_VERSION)}</h1>
  <p class="meta">Baseline: {esc(baseline['id'])} - {esc(baseline['name'])}</p>
  <p class="meta">Target: {esc(target.get('hostname') or 'unknown')}</p>
  <h2>Score {summary['score']}</h2>
  <p>Pass: {summary['pass']} · Warn: {summary['warn']} · Fail: {summary['fail']} · Unknown: {summary['unknown']} · Unsupported: {summary['unsupported']}</p>
  <table>
    <thead><tr><th>Status</th><th>Severity</th><th>ID</th><th>Check</th><th>Evidence</th><th>Remediation</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def exit_code(report: dict[str, Any], fail_on: str) -> int:
    summary = report["summary"]
    if fail_on == "never":
        return 0
    if fail_on == "fail" and summary["fail"] > 0:
        return 2
    if fail_on == "warn" and (summary["fail"] > 0 or summary["warn"] > 0):
        return 2
    if fail_on == "unknown" and (summary["fail"] > 0 or summary["warn"] > 0 or summary["unknown"] > 0):
        return 2
    return 0


def get_path(obj: dict[str, Any], path: str) -> Any:
    current: Any = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def compare_versions(actual: str, expected: str) -> int:
    def parts(value: str) -> list[int]:
        out = []
        for part in value.split("."):
            digits = "".join(ch for ch in part if ch.isdigit())
            out.append(int(digits or "0"))
        return out

    a = parts(actual)
    e = parts(expected)
    for i in range(max(len(a), len(e))):
        av = a[i] if i < len(a) else 0
        ev = e[i] if i < len(e) else 0
        if av > ev:
            return 1
        if av < ev:
            return -1
    return 0


def find_cert(certs: Any, wanted: str) -> dict[str, Any] | None:
    wanted_lower = str(wanted).lower()
    for cert in certs if isinstance(certs, list) else []:
        if wanted_lower in str(cert.get("name", "")).lower():
            return cert
    return None


def days_until(value: Any) -> int | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        expiry = dt.datetime.fromisoformat(text)
    except ValueError:
        try:
            expiry = dt.datetime.strptime(str(value), "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        except ValueError:
            return None
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=dt.timezone.utc)
    delta = expiry - dt.datetime.now(dt.timezone.utc)
    return int(delta.total_seconds() // 86400)


def count_status(results: list[dict[str, Any]], status: str) -> int:
    return sum(1 for result_item in results if result_item["status"] == status)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
