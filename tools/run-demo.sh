#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Design-Prototype demo runner

Usage:
  ./tools/run-demo.sh list
  ./tools/run-demo.sh client
  ./tools/run-demo.sh fleet
  ./tools/run-demo.sh macos
  ./tools/run-demo.sh certs
  ./tools/run-demo.sh report
  ./tools/run-demo.sh optimizer
  ./tools/run-demo.sh site-fix
  ./tools/run-demo.sh assets
  ./tools/run-demo.sh mqmirror
  ./tools/run-demo.sh macos-agent
  ./tools/run-demo.sh client-agent
  ./tools/run-demo.sh fleet-agent

Demos:
  client      Open Client Readiness Dashboard
  fleet       Open Fleet Command Center
  macos       Open macOS Enterprise Dashboard
  certs       Open Certificate Expiry Timeline
  report      Open MQ Fleet Report
  optimizer   Open MQ Client Optimizer
  assets      Open MQ Asset Downloader
  advisor     Open MQ Site Fix Advisor
  site-fix    Open MQ Site Fix Advisor
  mqmirror    Start MQ Mirror live server
  macos-agent Start macOS Enterprise Agent
  client-agent Start Client Readiness Agent
  fleet-agent Start Fleet Collector

Set BROWSER_OPEN=0 to print the path/command without opening it.
EOF
}

open_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Missing file: $file" >&2
    exit 1
  fi

  if [[ "${BROWSER_OPEN:-1}" == "0" ]]; then
    printf '%s\n' "$file"
    return
  fi

  if command -v open >/dev/null 2>&1; then
    open "$file"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$file"
  else
    echo "Open manually: $file"
  fi
}

case "${1:-}" in
  list)
    usage
    ;;
  client)
    open_file "docs/Client Readiness Dashboard.html"
    ;;
  fleet)
    open_file "docs/Fleet Command Center.html"
    ;;
  macos)
    open_file "docs/macOS Enterprise Dashboard.html"
    ;;
  certs|certificate|certificates)
    open_file "docs/Certificate Expiry Timeline.html"
    ;;
  report)
    open_file "docs/MQ Fleet Report.html"
    ;;
  optimizer|mq-client-optimizer)
    open_file "docs/MQ Client Optimizer.html"
    ;;
  assets|asset-downloader)
    open_file "docs/MQ Asset Downloader.html"
    ;;
  advisor|site-fix)
    open_file "docs/MQ Site Fix Advisor.html"
    ;;
  mqmirror|mirror)
    exec ./tools/mqmirror/start.sh
    ;;
  macos-agent)
    exec python3 helper/macos_agent.py
    ;;
  client-agent)
    exec python3 helper/client_readiness_agent.py
    ;;
  fleet-agent)
    exec python3 helper/fleet_collector.py
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
