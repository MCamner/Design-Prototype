#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: ./tools/run-demo.sh <demo>

Demos:
  client      Open Client Readiness Dashboard
  fleet       Open Fleet Command Center
  macos       Open macOS Enterprise Dashboard
  certs       Open Certificate Expiry Timeline
  report      Open MQ Fleet Report
  optimizer   Open MQ Client Optimizer
  assets      Open MQ Asset Downloader
  advisor     Open MQ Site Fix Advisor
  mqmirror    Start MQ Mirror live server

Set BROWSER_OPEN=0 to print the path/command without opening it.
EOF
}

open_file() {
  local file="$1"
  if [[ "${BROWSER_OPEN:-1}" == "0" ]]; then
    printf '%s\n' "$file"
    return
  fi
  open "$file"
}

case "${1:-}" in
  client)
    open_file "$ROOT/docs/Client Readiness Dashboard.html"
    ;;
  fleet)
    open_file "$ROOT/docs/Fleet Command Center.html"
    ;;
  macos)
    open_file "$ROOT/docs/macOS Enterprise Dashboard.html"
    ;;
  certs|certificate|certificates)
    open_file "$ROOT/docs/Certificate Expiry Timeline.html"
    ;;
  report)
    open_file "$ROOT/docs/MQ Fleet Report.html"
    ;;
  optimizer|mq-client-optimizer)
    open_file "$ROOT/docs/MQ Client Optimizer.html"
    ;;
  assets|asset-downloader)
    open_file "$ROOT/docs/MQ Asset Downloader.html"
    ;;
  advisor|site-fix)
    open_file "$ROOT/docs/MQ Site Fix Advisor.html"
    ;;
  mqmirror|mirror)
    exec "$ROOT/tools/mqmirror/start.sh"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    echo "Unknown demo: $1" >&2
    echo >&2
    usage >&2
    exit 2
    ;;
esac
