#!/usr/bin/env python3
"""
MQ Mirror — menyradskompanjon.
Kopplar mot den körande gui_to_cli.py-servern och visar status i macOS-menyraden.

Krav:  pip install rumps
Start: python3 tools/mqmirror/menubar.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

try:
    import rumps
except ImportError:
    sys.exit("rumps saknas — kör: pip install rumps")

BASE       = "http://127.0.0.1:7070"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
HANDOFF    = os.path.join(REPO_ROOT, "docs", "handoff.html")


class MQApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("◌", quit_button=None)
        self._status = rumps.MenuItem("Ansluter…")
        self._status.set_callback(None)
        self.menu = [
            rumps.MenuItem("Öppna Handoff →", callback=self._open_handoff),
            None,
            self._status,
            None,
            rumps.MenuItem("Avsluta", callback=lambda _: rumps.quit_application()),
        ]
        rumps.Timer(self._poll, 3).start()

    def _poll(self, _: object) -> None:
        try:
            with urllib.request.urlopen(BASE + "/api/commands", timeout=2) as r:
                count = len(json.loads(r.read()))
            self.title = "◈"
            self._status.title = f"{count} kommandon fångade"
        except Exception:
            self.title = "◌"
            self._status.title = "Ej ansluten — starta med start.sh"

    def _open_handoff(self, _: object) -> None:
        subprocess.Popen(["open", HANDOFF])


if __name__ == "__main__":
    MQApp().run()
