#!/usr/bin/env python3

"""
redact-macos-agent-status.py

Reads macOS Enterprise Agent JSON from stdin and masks sensitive fields before
sharing output publicly.

Usage:
  curl -s http://127.0.0.1:38764/status | python3 tools/redact-macos-agent-status.py
"""

import json
import sys


def mask_ip(value):
    if not isinstance(value, str):
        return value

    parts = value.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        return f"{parts[0]}.{parts[1]}.x.x"

    return "REDACTED"


def redact(data):
    meta = data.get("meta", {})
    meta["serial"] = "REDACTED"
    meta["hostname"] = "REDACTED"

    identity = data.get("identity", {})
    for user in identity.get("users", []):
        if "fullname" in user:
            user["fullname"] = "REDACTED"
        if "name" in user:
            user["name"] = "REDACTED"

    network = data.get("network", {})
    for interface in network.get("interfaces", []):
        if "ip" in interface:
            interface["ip"] = mask_ip(interface["ip"])

    # Optional: certificates can sometimes contain hostnames, usernames,
    # subjects, or organization details.
    certificates = data.get("certificates", {})
    for cert_group in certificates.values():
        if isinstance(cert_group, list):
            for cert in cert_group:
                if isinstance(cert, dict):
                    for key in ("subject", "issuer", "common_name", "serial"):
                        if key in cert:
                            cert[key] = "REDACTED"

    return data


def main():
    raw = sys.stdin.read().strip()

    if not raw:
        print("ERROR: No JSON input received.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    redacted = redact(data)
    print(json.dumps(redacted, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
