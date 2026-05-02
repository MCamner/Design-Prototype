#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HANDOFF="$REPO_ROOT/docs/handoff.html"

echo "◈ GUI → CLI Companion"
echo "  → Live-server: http://127.0.0.1:7070"
echo "  → Handoff:     $HANDOFF"
echo "  (Ctrl+C för att stoppa)"
echo ""

# Starta Python i bakgrunden, fånga PID
python3 "$SCRIPT_DIR/gui_to_cli.py" &
PY_PID=$!

# Vänta tills servern svarar (max 5 sek)
for i in $(seq 1 10); do
  sleep 0.5
  if curl -sf http://127.0.0.1:7070/api/commands >/dev/null 2>&1; then
    break
  fi
done

# Öppna handoff.html i standardwebbläsaren
open "$HANDOFF"

# Håll scriptet vid liv tills Ctrl+C
wait $PY_PID
