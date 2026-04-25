#!/usr/bin/env python3
"""
gui_to_cli.py — GUI-to-CLI Companion (Python proof-of-concept)

Lyssnar på macOS-händelser via NSWorkspace och Accessibility API
och skriver ut terminal-ekvivalenter i realtid.

Installation:
    pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices watchdog

Krav:
    Ge terminalen Accessibility-behörighet:
    Systeminställningar → Integritet & Säkerhet → Tillgänglighet → lägg till Terminal

Kör:
    python3 gui_to_cli.py
"""

import sys
import os
import subprocess
from datetime import datetime

# ── Dependency check ──────────────────────────────────────────────────────────
import ctypes
import ctypes.util

try:
    import objc
    from AppKit import (
        NSWorkspace, NSWorkspaceDidActivateApplicationNotification,
        NSWorkspaceDidLaunchApplicationNotification,
        NSWorkspaceDidTerminateApplicationNotification,
        NSWorkspaceDidMountNotification,
        NSRunningApplication,
    )
    from Foundation import NSObject, NSNotificationCenter, NSRunLoop, NSDate
    import ApplicationServices as AS
    import Quartz
except ImportError:
    print("❌  Saknade beroenden. Kör:")
    print("    pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices")
    sys.exit(1)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("⚠️  watchdog saknas — filsystemshändelser inaktiverade.")
    print("   Kör: pip install watchdog\n")


# ── Terminal output helpers ───────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[38;5;82m"
BLUE   = "\033[38;5;75m"
AMBER  = "\033[38;5;220m"
PURPLE = "\033[38;5;141m"
CYAN   = "\033[38;5;87m"
MUTED  = "\033[38;5;244m"
RED    = "\033[38;5;203m"

CATEGORY_COLORS = {
    "Finder":   GREEN,
    "System":   BLUE,
    "Nätverk":  AMBER,
    "Git":      PURPLE,
    "Homebrew": CYAN,
    "App":      CYAN,
}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def print_command(category, gui_action, cmd, explanation=""):
    color = CATEGORY_COLORS.get(category, MUTED)
    print(f"\n{DIM}{ts()}{RESET}  {color}{BOLD}[{category}]{RESET}")
    print(f"  {BOLD}{gui_action}{RESET}")
    print(f"  {MUTED}↓{RESET}")
    print(f"  {GREEN}❯{RESET} {BOLD}{cmd}{RESET}")
    if explanation:
        print(f"  {MUTED}{explanation}{RESET}")

def print_separator():
    print(f"\n{MUTED}{'─' * 60}{RESET}")

def print_header():
    print(f"""
{BOLD}{GREEN}┌─────────────────────────────────────────┐
│      GUI → CLI Companion  v0.1          │
│      Tryck Ctrl+C för att avsluta       │
└─────────────────────────────────────────┘{RESET}

{MUTED}Lyssnar på macOS-händelser...{RESET}
{MUTED}(Se till att Terminal har Accessibility-behörighet){RESET}
""")


# ── App-name → CLI mappings ───────────────────────────────────────────────────
APP_LAUNCH_CMDS = {
    "Finder":              ("open -a Finder",               "Öppnar Finder-appen"),
    "Safari":              ("open -a Safari",               "Öppnar Safari"),
    "Terminal":            ("open -a Terminal",             "Öppnar Terminal"),
    "Xcode":               ("open -a Xcode",                "Öppnar Xcode"),
    "Visual Studio Code":  ("code .",                       "Öppnar VS Code i aktuell katalog"),
    "TextEdit":            ("open -e fil.txt",              "Öppnar fil i TextEdit"),
    "Activity Monitor":    ("top",                          "Visar processer i realtid"),
    "Disk Utility":        ("diskutil list",                "Listar alla diskenheter"),
    "System Preferences":  ("open /System/Applications/System\\ Preferences.app", ""),
    "System Settings":     ("open /System/Applications/System\\ Settings.app",    ""),
    "App Store":           ("brew search <namn>",           "Sök paket via Homebrew istället"),
    "Simulator":           ("xcrun simctl list",            "Listar tillgängliga simulatorer"),
    "Instruments":         ("instruments -s devices",       "Listar enheter för profilering"),
}

APP_QUIT_CMDS = {
    "Finder":   ("osascript -e 'tell application \"Finder\" to quit'", ""),
    "Safari":   ("osascript -e 'tell application \"Safari\" to quit'", ""),
}


# ── NSWorkspace observer ──────────────────────────────────────────────────────
class WorkspaceObserver(NSObject):

    def init(self):
        self = objc.super(WorkspaceObserver, self).init()
        if self is None:
            return None
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(
            self, "appActivated:", NSWorkspaceDidActivateApplicationNotification, None)
        nc.addObserver_selector_name_object_(
            self, "appLaunched:", NSWorkspaceDidLaunchApplicationNotification, None)
        nc.addObserver_selector_name_object_(
            self, "appTerminated:", NSWorkspaceDidTerminateApplicationNotification, None)
        nc.addObserver_selector_name_object_(
            self, "volumeMounted:", NSWorkspaceDidMountNotification, None)
        self._last_app = None
        return self

    def appActivated_(self, notification):
        info = notification.userInfo()
        app = info.get("NSWorkspaceApplicationKey")
        if app is None:
            return
        name = app.localizedName()
        if name == self._last_app:
            return
        self._last_app = name
        cmd, note = APP_LAUNCH_CMDS.get(name, (None, None))
        if cmd:
            print_command("App", f"Byter till {name}", cmd, note)

    def appLaunched_(self, notification):
        info = notification.userInfo()
        app = info.get("NSWorkspaceApplicationKey")
        if app is None:
            return
        name = app.localizedName()
        cmd, note = APP_LAUNCH_CMDS.get(name, (None, None))
        if cmd:
            print_command("App", f"Öppnar {name}", cmd, note)

    def appTerminated_(self, notification):
        info = notification.userInfo()
        app = info.get("NSWorkspaceApplicationKey")
        if app is None:
            return
        name = app.localizedName()
        cmd, note = APP_QUIT_CMDS.get(name, (None, None))
        if cmd:
            print_command("App", f"Stänger {name}", cmd, note)

    def volumeMounted_(self, notification):
        info = notification.userInfo()
        path = info.get("NSWorkspaceVolumeLocalizedNameKey", "volym")
        print_command("System",
            f"Monterar disk: {path}",
            f"diskutil mount /Volumes/{path}",
            "eller: hdiutil attach disk.dmg")


# ── Accessibility observer (AXObserver) ──────────────────────────────────────
def check_accessibility():
    """Kontrollera om Accessibility är beviljat."""
    trusted = AS.AXIsProcessTrusted()
    if not trusted:
        print(f"\n{RED}{BOLD}⚠️  Accessibility-behörighet saknas!{RESET}")
        print(f"{MUTED}Gå till:{RESET}")
        print(f"  Systeminställningar → Integritet & Säkerhet →")
        print(f"  Tillgänglighet → lägg till Terminal (eller iTerm2)\n")
        # Öppna pref-panelen automatiskt
        subprocess.Popen([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        ])
    return trusted

AX_ELEMENT_CMDS = {
    # Knappnamn → (kommando, förklaring)
    "Empty Trash":       ("rm -rf ~/.Trash/*",               "Tömmer papperskorgen"),
    "Eject":             ("diskutil eject /Volumes/<enhet>", "Matar ut disk"),
    "Connect":           ("ssh användarnamn@server",         "Ansluter via SSH"),
    "New Folder":        ("mkdir ny-mapp",                   "Skapar ny mapp"),
    "Get Info":          ("stat fil",                        "Visar filinfo"),
    "Duplicate":         ("cp -r fil fil-kopia",             "Kopierar fil"),
    "Move to Trash":     ("trash fil  # brew install trash", ""),
    "Show Original":     ("readlink -f länk",                "Följer symbolisk länk"),
    "Compress":          ("zip -r arkiv.zip mapp/",          "Komprimerar till zip"),
    "Burn to Disc":      ("hdiutil burn fil.iso",            "Bränner ISO till skiva"),
}

def setup_ax_observer():
    """AXObserver via Python/pyobjc är instabilt — hoppas över i denna version.
    Implementeras i Swift-appen med native AXObserverCreate."""
    return None


# ── FSEvents via watchdog ─────────────────────────────────────────────────────
class FinderEventHandler(FileSystemEventHandler):

    def on_created(self, event):
        path = event.src_path
        if event.is_directory:
            print_command("Finder", f"Ny mapp skapades: {os.path.basename(path)}",
                f"mkdir -p \"{path}\"")
        else:
            print_command("Finder", f"Ny fil skapades: {os.path.basename(path)}",
                f"touch \"{path}\"")

    def on_deleted(self, event):
        path = event.src_path
        flag = "-r " if event.is_directory else ""
        print_command("Finder", f"Raderar: {os.path.basename(path)}",
            f"rm {flag}\"{path}\"",
            "⚠️  rm är permanent — överväg: trash (brew install trash)")

    def on_moved(self, event):
        src  = event.src_path
        dest = event.dest_path
        src_dir  = os.path.dirname(src)
        dest_dir = os.path.dirname(dest)
        src_name  = os.path.basename(src)
        dest_name = os.path.basename(dest)

        if src_dir == dest_dir:
            # Byte namn
            print_command("Finder", f"Byter namn: {src_name} → {dest_name}",
                f"mv \"{src}\" \"{dest}\"")
        else:
            # Flytt
            print_command("Finder", f"Flyttar: {src_name}",
                f"mv \"{src}\" \"{dest}\"")

    def on_modified(self, event):
        # Ignorera katalogmodifieringar (för mycket brus)
        if event.is_directory:
            return
        path = event.src_path
        # Filtrera bort system-noise
        if any(skip in path for skip in [".DS_Store", "__pycache__", ".localized"]):
            return
        print_command("Finder", f"Fil ändrad: {os.path.basename(path)}",
            f"# Redigera med: nano \"{path}\"  eller  code \"{path}\"")


def start_fs_watcher():
    if not HAS_WATCHDOG:
        return None, None

    watch_paths = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
    ]

    handler  = FinderEventHandler()
    observer = Observer()
    for p in watch_paths:
        if os.path.exists(p):
            observer.schedule(handler, p, recursive=True)
            print(f"{MUTED}  📂 Bevakar: {p}{RESET}")

    observer.start()
    return observer, handler


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print_header()

    # Workspace-observer
    workspace_observer = WorkspaceObserver.alloc().init()
    print(f"{GREEN}✓{RESET} NSWorkspace-observer aktiv (app-switchar, monterade volymer)")

    # AX-observer
    ax_obs = setup_ax_observer()
    if ax_obs:
        print(f"{GREEN}✓{RESET} Accessibility-observer aktiv (knappar, UI-element)")
    else:
        print(f"{MUTED}–{RESET}  Accessibility-observer: hoppas över (implementeras i Swift-appen)")

    # FS-watcher
    print(f"\n{MUTED}Filsystem-bevakning:{RESET}")
    fs_observer, _ = start_fs_watcher()
    if fs_observer:
        print(f"{GREEN}✓{RESET} watchdog aktiv (Desktop, Documents, Downloads)")

    print_separator()
    print(f"\n{BOLD}Redo. Gör saker i macOS GUI...{RESET}\n")

    try:
        # Kör NSRunLoop (krävs för Cocoa-notiser)
        loop = NSRunLoop.currentRunLoop()
        while True:
            loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
    except KeyboardInterrupt:
        print(f"\n\n{MUTED}Avslutar...{RESET}")
        if fs_observer:
            fs_observer.stop()
            fs_observer.join()
        print(f"{GREEN}Hej då!{RESET}\n")

if __name__ == "__main__":
    main()
