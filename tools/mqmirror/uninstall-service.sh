#!/usr/bin/env bash
set -e

PLIST_NAME="com.mqmirror.agent"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

if [ ! -f "$PLIST_DEST" ]; then
  echo "Tjänsten är inte installerad."
  exit 0
fi

launchctl unload "$PLIST_DEST" 2>/dev/null || true
rm -f "$PLIST_DEST"
echo "✔ MQ Mirror-tjänsten avinstallerad"
