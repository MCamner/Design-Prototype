#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

fail=0

ok() {
  echo "[OK] $*"
}

bad() {
  echo "[FAIL] $*" >&2
  fail=1
}

check_file() {
  local file="$1"
  [[ -f "$file" ]] && ok "$file" || bad "Missing file: $file"
}

echo "== Front door files =="
check_file docs/index.html
check_file docs/DEMO-GALLERY.md
check_file docs/screenshots/README.md
check_file docs/ARCHITECTURE.md
check_file docs/SAFE-SHARING.md

echo
echo "== Key landing-page content =="
for term in \
  "Enterprise validation lab" \
  "Client Readiness Dashboard" \
  "Fleet Command Center" \
  "macOS Enterprise Dashboard" \
  "Certificate Expiry Timeline" \
  "MQ Mirror" \
  "Safe sharing"
do
  if grep -qi "$term" docs/index.html; then
    ok "docs/index.html contains: $term"
  else
    bad "docs/index.html missing: $term"
  fi
done

echo
echo "== Local href and image target check =="
python3 <<'PY'
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

root = Path(".").resolve()
html_file = Path("docs/index.html")
failures = []


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.targets.append(attrs["href"])
        if tag == "img" and attrs.get("src"):
            self.targets.append(attrs["src"])


parser = LinkParser()
parser.feed(html_file.read_text(encoding="utf-8"))

for raw in parser.targets:
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https", "mailto"}:
        continue
    if raw.startswith("#"):
        continue

    path_part = unquote(parsed.path)
    if not path_part:
        continue

    target = (html_file.parent / path_part).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        failures.append((raw, "escapes repo root"))
        continue

    if not target.exists():
        failures.append((raw, f"missing target: {target.relative_to(root)}"))

if failures:
    for raw, reason in failures:
        print(f"[FAIL] {raw} -> {reason}")
    raise SystemExit(1)

print("[OK] All local front-door links and images point to existing files")
PY

echo
echo "== Demo gallery sanity =="
for term in \
  "https://mcamner.github.io/Design-Prototype/" \
  "docs/screenshots/" \
  "tools/run-demo.sh" \
  "docs/SAFE-SHARING.md"
do
  if grep -q "$term" docs/DEMO-GALLERY.md; then
    ok "docs/DEMO-GALLERY.md contains: $term"
  else
    bad "docs/DEMO-GALLERY.md missing: $term"
  fi
done

echo
if [[ "$fail" -eq 0 ]]; then
  echo "FRONT DOOR CHECK PASSED"
else
  echo "FRONT DOOR CHECK FAILED" >&2
  exit 1
fi
