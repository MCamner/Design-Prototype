#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.mqmirror.agent"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_DIR="$HOME/.mq"
PYTHON="$(command -v python3 || true)"

if [ -z "$PYTHON" ]; then
  echo "✖ python3 hittades inte i PATH"
  exit 1
fi

mkdir -p "$LOG_DIR"

echo "◈ MQ Mirror — Installerar bakgrundstjänst"
echo "  Python: $PYTHON"
echo "  Skript: $SCRIPT_DIR/gui_to_cli.py"
echo "  Plist:  $PLIST_DEST"
echo "  Loggar: $LOG_DIR/mqmirror.log"
echo

cat > "$PLIST_DEST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/gui_to_cli.py</string>
        <string>watch</string>
        <string>--compact</string>
        <string>--ignore-terminal</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/mqmirror.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/mqmirror-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

# Ladda om om redan aktiv
if launchctl list 2>/dev/null | grep -q "$PLIST_NAME"; then
  launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi
launchctl load "$PLIST_DEST"

echo "✔ Tjänsten är installerad och startad"
echo "  MQ Mirror startar automatiskt vid nästa login."
echo
echo "  Menyradikon (valfritt):"
echo "    pip install rumps"
echo "    python3 $SCRIPT_DIR/menubar.py"
echo
echo "  Status:"
echo "    launchctl list | grep mqmirror"
echo "    tail -f $LOG_DIR/mqmirror.log"
echo
echo "  Avinstallera:"
echo "    $SCRIPT_DIR/uninstall-service.sh"
