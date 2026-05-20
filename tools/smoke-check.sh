#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

fail=0

check_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    echo "[OK] $file"
  else
    echo "[FAIL] Missing: $file" >&2
    fail=1
  fi
}

check_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    echo "[OK] $dir/"
  else
    echo "[FAIL] Missing directory: $dir" >&2
    fail=1
  fi
}

echo "== Required files =="
check_file README.md
check_file VERSION
check_file CHANGELOG.md
check_file LICENSE
check_file docs/index.html
check_file docs/ARCHITECTURE.md
check_file docs/SAFE-SHARING.md
check_file tools/run-demo.sh
check_file tools/check-public-docs.py

echo
echo "== Required directories =="
check_dir docs
check_dir helper
check_dir tools
check_dir docs/screenshots

echo
echo "== Expected dashboard files =="
check_file "docs/Client Readiness Dashboard.html"
check_file "docs/Fleet Command Center.html"
check_file "docs/macOS Enterprise Dashboard.html"
check_file "docs/Certificate Expiry Timeline.html"
check_file "docs/MQ Fleet Report.html"
check_file "docs/MQ Asset Downloader.html"
check_file "docs/MQ Site Fix Advisor.html"
check_file "docs/MQ Client Optimizer.html"

echo
echo "== Expected screenshot files =="
check_file "docs/screenshots/client-readiness-dashboard.png"
check_file "docs/screenshots/fleet-command-center.png"
check_file "docs/screenshots/macos-enterprise-dashboard.png"
check_file "docs/screenshots/certificate-expiry-timeline.png"
check_file "docs/screenshots/mq-site-fix-advisor.png"
check_file "docs/screenshots/mq-asset-downloader.png"
check_file "docs/screenshots/mq-client-optimizer.png"

echo
echo "== Public docs check =="
python3 tools/check-public-docs.py

echo
echo "== Python compile check =="
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/design-prototype-pycache}"
python3 -m compileall -q helper tools
echo "[OK] Python files compile"

echo
echo "== Shell syntax check =="
while IFS= read -r -d '' script; do
  bash -n "$script"
  echo "[OK] $script"
done < <(find . -name "*.sh" -type f -not -path "./.git/*" -print0)

echo
echo "== Demo runner check =="
BROWSER_OPEN=0 ./tools/run-demo.sh client >/dev/null
BROWSER_OPEN=0 ./tools/run-demo.sh macos >/dev/null
BROWSER_OPEN=0 ./tools/run-demo.sh fleet >/dev/null
BROWSER_OPEN=0 ./tools/run-demo.sh optimizer >/dev/null
BROWSER_OPEN=0 ./tools/run-demo.sh assets >/dev/null
BROWSER_OPEN=0 ./tools/run-demo.sh site-fix >/dev/null
./tools/run-demo.sh list >/dev/null
echo "[OK] Demo runner commands resolve"

echo
echo "== README link sanity =="
for target in \
  "docs/DEMO-GALLERY.md" \
  "docs/PROJECT-MAP.md" \
  "docs/PROJECT-STATUS.md" \
  "docs/ROADMAP.md" \
  "docs/ARCHITECTURE.md" \
  "docs/SAFE-SHARING.md"
do
  if grep -q "$target" README.md; then
    echo "[OK] README references $target"
  else
    echo "[WARN] README does not reference $target"
  fi
done

echo
if [[ "$fail" -eq 0 ]]; then
  echo "SMOKE CHECK PASSED"
else
  echo "SMOKE CHECK FAILED" >&2
  exit 1
fi
