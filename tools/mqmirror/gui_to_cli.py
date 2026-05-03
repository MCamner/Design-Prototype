#!/usr/bin/env python3
"""
MQ Mirror v0.6 — GUI actions → terminal command equivalents.
Merged: context-aware watch mode (v0.5) + live HTTP/SSE server for handoff.html.

Examples:
  python3 gui_to_cli.py                          # watch + live server (default)
  python3 gui_to_cli.py watch --compact
  python3 gui_to_cli.py watch --no-serve
  python3 gui_to_cli.py inspect
  python3 gui_to_cli.py list
  python3 gui_to_cli.py search network
  python3 gui_to_cli.py show settings network
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import sys
import subprocess
import threading
import time
import queue as _queue
from collections import deque
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

VERSION  = "0.6"
LIVE_PORT = 7070

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
GREEN = "\033[38;5;82m"
CYAN  = "\033[38;5;87m"
AMBER = "\033[38;5;220m"
RED   = "\033[38;5;203m"
MUTED = "\033[38;5;244m"

Command  = Tuple[str, str, str]
BOX_WIDTH = 72
DEFAULT_SUGGESTION_LIMIT = 12

COMMAND_LIBRARY: Dict[str, Dict[str, Any]] = {
    "settings.general": {
        "gui": "System Settings → General",
        "commands": [
            ("open -a 'System Settings'",                        "Open System Settings",       "safe"),
            ("sw_vers",                                           "Show macOS version",          "safe"),
            ("system_profiler SPSoftwareDataType",                "Show software overview",      "safe"),
            ("scutil --get ComputerName",                         "Show computer name",          "safe"),
            ("scutil --get LocalHostName",                        "Show local host name",        "safe"),
            ("hostname",                                          "Show hostname",               "safe"),
        ],
    },
    "settings.network": {
        "gui": "System Settings → Network",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Network-Settings.extension"', "Open Network settings", "safe"),
            ("networksetup -listallhardwareports",                "List network interfaces",     "safe"),
            ("ipconfig getifaddr en0",                            "Show Wi-Fi IP address",       "safe"),
            ("route -n get default",                              "Show default gateway",        "safe"),
            ("scutil --dns",                                      "Show DNS configuration",      "safe"),
            ("networksetup -getdnsservers Wi-Fi",                 "Show Wi-Fi DNS servers",      "safe"),
        ],
    },
    "settings.displays": {
        "gui": "System Settings → Displays",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Displays-Settings.extension"', "Open Displays settings", "safe"),
            ("system_profiler SPDisplaysDataType",                "Show display/GPU information","safe"),
        ],
    },
    "settings.privacy": {
        "gui": "System Settings → Privacy & Security",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension"', "Open Privacy & Security", "safe"),
            ("spctl --status",                                    "Show Gatekeeper status",      "safe"),
            ("fdesetup status",                                   "Show FileVault status",       "safe"),
            ("csrutil status",                                    "Show SIP status",             "safe"),
        ],
    },
    "settings.keyboard": {
        "gui": "System Settings → Keyboard",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Keyboard-Settings.extension"', "Open Keyboard settings", "safe"),
            ("defaults read NSGlobalDomain ApplePressAndHoldEnabled", "Show press-and-hold setting", "safe"),
            ("defaults read NSGlobalDomain InitialKeyRepeat",     "Show initial key repeat",    "safe"),
            ("defaults read NSGlobalDomain KeyRepeat",            "Show key repeat",             "safe"),
        ],
    },
    "settings.trackpad": {
        "gui": "System Settings → Trackpad",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Trackpad-Settings.extension"', "Open Trackpad settings", "safe"),
            ("defaults read com.apple.AppleMultitouchTrackpad",   "Show trackpad preferences",  "safe"),
        ],
    },
    "settings.battery": {
        "gui": "System Settings → Battery",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Battery-Settings.extension"', "Open Battery settings", "safe"),
            ("pmset -g batt",                                     "Show battery status",         "safe"),
            ("pmset -g",                                          "Show power management",       "safe"),
        ],
    },
    "settings.bluetooth": {
        "gui": "System Settings → Bluetooth",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.BluetoothSettings"', "Open Bluetooth settings", "safe"),
            ("system_profiler SPBluetoothDataType",               "Show Bluetooth information",  "safe"),
        ],
    },
    "settings.sound": {
        "gui": "System Settings → Sound",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Sound-Settings.extension"', "Open Sound settings", "safe"),
            ("system_profiler SPAudioDataType",                   "Show audio devices",          "safe"),
        ],
    },
    "settings.users": {
        "gui": "System Settings → Users & Groups",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Users-Groups-Settings.extension"', "Open Users & Groups", "safe"),
            ("whoami",                                            "Show current user",           "safe"),
            ("id",                                                "Show current user identity",  "safe"),
            ("dscl . list /Users",                                "List local users",            "safe"),
        ],
    },
    "settings.sharing": {
        "gui": "System Settings → General → Sharing",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Sharing-Settings.extension"', "Open Sharing settings", "safe"),
            ("scutil --get ComputerName",                         "Show computer name",          "safe"),
            ("scutil --get LocalHostName",                        "Show local hostname",         "safe"),
            ("launchctl print system/com.openssh.sshd 2>/dev/null | head", "Inspect SSH daemon", "safe"),
        ],
    },
    "finder.files": {
        "gui": "Finder → file operations",
        "commands": [
            ("open .",                                            "Open current folder in Finder","safe"),
            ("pwd",                                               "Show current directory",      "safe"),
            ("ls -la",                                            "List files with details",     "safe"),
            ("mkdir new-folder",                                  "Create folder",               "modifies"),
            ("touch file.txt",                                    "Create file",                 "modifies"),
            ("mv old.txt new.txt",                                "Rename or move file",         "modifies"),
            ("trash file.txt  # brew install trash",              "Move file to Trash safely",   "modifies"),
        ],
    },
    "apps.common": {
        "gui": "Open common apps",
        "commands": [
            ("open -a Finder",                                    "Open Finder",                 "safe"),
            ("open -a Safari",                                    "Open Safari",                 "safe"),
            ("open -a Terminal",                                  "Open Terminal",               "safe"),
            ("open -a 'System Settings'",                         "Open System Settings",        "safe"),
            ("open -a 'Activity Monitor'",                        "Open Activity Monitor",       "safe"),
            ("open -a 'Visual Studio Code'",                      "Open VS Code",                "safe"),
        ],
    },
    "developer.xcode": {
        "gui": "Xcode / developer tools",
        "commands": [
            ("xcode-select -p",                                   "Show active developer directory", "safe"),
            ("xcodebuild -version",                               "Show Xcode version",          "safe"),
            ("xcrun simctl list",                                 "List simulators",             "safe"),
            ("xcrun xctrace list devices",                        "List devices for profiling",  "safe"),
        ],
    },
    "apps.console": {
        "gui": "Console / unified logging",
        "commands": [
            ("log stream --style compact",                        "Stream unified logs",         "safe"),
            ("log show --last 1h --style compact",                "Show logs last hour",         "safe"),
            ("log show --predicate 'eventMessage CONTAINS[c] \"error\"' --last 1h", "Show error logs", "safe"),
        ],
    },
    "apps.keychain": {
        "gui": "Keychain Access / certificates",
        "commands": [
            ("security list-keychains",                           "List keychains",              "safe"),
            ("security find-certificate -a -p",                   "Export certificates (PEM)",   "safe"),
            ("security find-identity -v -p codesigning",          "List code signing identities","safe"),
        ],
    },
}

APP_MAPPINGS = {
    "Finder":             ("open -a Finder",              "Open Finder"),
    "Safari":             ("open -a Safari",              "Open Safari"),
    "Google Chrome":      ("open -a 'Google Chrome'",     "Open Chrome"),
    "Firefox":            ("open -a Firefox",             "Open Firefox"),
    "Arc":                ("open -a Arc",                 "Open Arc"),
    "Brave Browser":      ("open -a 'Brave Browser'",     "Open Brave"),
    "Terminal":           ("open -a Terminal",            "Open Terminal"),
    "iTerm2":             ("open -a iTerm",               "Open iTerm2"),
    "System Settings":    ("open -a 'System Settings'",   "Open System Settings"),
    "Activity Monitor":   ("open -a 'Activity Monitor'",  "Open Activity Monitor"),
    "Visual Studio Code": ("open -a 'Visual Studio Code'","Open VS Code"),
    "Cursor":             ("open -a Cursor",              "Open Cursor"),
    "Xcode":              ("open -a Xcode",               "Open Xcode"),
    "Console":            ("open -a Console",             "Open Console"),
    "Keychain Access":    ("open -a 'Keychain Access'",   "Open Keychain Access"),
    "Disk Utility":       ("diskutil list",               "List disks"),
    "Simulator":          ("xcrun simctl list",           "List simulators"),
    "Slack":              ("open -a Slack",               "Open Slack"),
    "Figma":              ("open -a Figma",               "Open Figma"),
}

SETTINGS_HINTS = {
    "general":   "settings.general",
    "network":   "settings.network",
    "wi-fi":     "settings.network",
    "wifi":      "settings.network",
    "displays":  "settings.displays",
    "display":   "settings.displays",
    "privacy":   "settings.privacy",
    "security":  "settings.privacy",
    "keyboard":  "settings.keyboard",
    "trackpad":  "settings.trackpad",
    "battery":   "settings.battery",
    "bluetooth": "settings.bluetooth",
    "sound":     "settings.sound",
    "users":     "settings.users",
    "groups":    "settings.users",
    "sharing":   "settings.sharing",
}

TOPIC_ALIASES = {
    "general":   ("settings", "general"),
    "network":   ("settings", "network"),
    "wifi":      ("settings", "network"),
    "wi-fi":     ("settings", "network"),
    "display":   ("settings", "displays"),
    "displays":  ("settings", "displays"),
    "privacy":   ("settings", "privacy"),
    "security":  ("settings", "privacy"),
    "keyboard":  ("settings", "keyboard"),
    "trackpad":  ("settings", "trackpad"),
    "battery":   ("settings", "battery"),
    "bluetooth": ("settings", "bluetooth"),
    "sound":     ("settings", "sound"),
    "users":     ("settings", "users"),
    "sharing":   ("settings", "sharing"),
    "finder":    ("finder",    "files"),
    "files":     ("finder",    "files"),
    "apps":      ("apps",      "common"),
    "xcode":     ("developer", "xcode"),
    "console":   ("apps",      "console"),
    "keychain":  ("apps",      "keychain"),
}

APP_CATEGORY = {
    "Finder":             "Finder",
    "System Settings":    "System",
    "System Preferences": "System",
    "Activity Monitor":   "System",
    "Disk Utility":       "System",
    "Console":            "System",
    "Keychain Access":    "System",
    "Safari":             "Browser",
    "Google Chrome":      "Browser",
    "Firefox":            "Browser",
    "Arc":                "Browser",
    "Brave Browser":      "Browser",
    "Microsoft Edge":     "Browser",
    "Terminal":           "Terminal",
    "iTerm2":             "Terminal",
    "Warp":               "Terminal",
    "Ghostty":            "Terminal",
    "Xcode":              "Developer",
    "Visual Studio Code": "Developer",
    "Cursor":             "Developer",
    "Instruments":        "Developer",
    "Simulator":          "Developer",
}


# ── Live HTTP / SSE server ────────────────────────────────────────────────────

_cmd_id    = 0
_cmd_lock  = threading.Lock()
_cmd_history: deque = deque(maxlen=100)
_sse_queues: list   = []
_sse_lock  = threading.Lock()


def _emit(category: str, gui_action: str, cmd: str, explanation: str = "") -> None:
    global _cmd_id
    with _cmd_lock:
        _cmd_id += 1
        entry = {
            "id":         _cmd_id,
            "ts":         datetime.now().strftime("%H:%M:%S"),
            "category":   category,
            "gui_action": gui_action,
            "command":    cmd,
            "explanation": explanation,
        }
        _cmd_history.append(entry)
    payload = json.dumps(entry)
    with _sse_lock:
        dead = []
        for q in _sse_queues:
            try:
                q.put_nowait(payload)
            except _queue.Full:
                dead.append(q)
        for q in dead:
            _sse_queues.remove(q)


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class _LiveHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/commands":
            with _cmd_lock:
                body = json.dumps(list(_cmd_history)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q: _queue.Queue = _queue.Queue(maxsize=50)
            with _sse_lock:
                _sse_queues.append(q)
            try:
                while True:
                    try:
                        data = q.get(timeout=15)
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                    except _queue.Empty:
                        self.wfile.write(b": ka\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with _sse_lock:
                    if q in _sse_queues:
                        _sse_queues.remove(q)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_: Any) -> None:
        pass


def _start_live_server() -> None:
    server = _ThreadedHTTPServer(("127.0.0.1", LIVE_PORT), _LiveHandler)
    server.serve_forever()


# ── Helpers ───────────────────────────────────────────────────────────────────

def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def configure_output(plain: bool = False) -> None:
    if not plain and "NO_COLOR" not in os.environ:
        return
    for name in ("RESET", "BOLD", "DIM", "GREEN", "CYAN", "AMBER", "RED", "MUTED"):
        globals()[name] = ""


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return parsed


def strip_ansi(value: str) -> str:
    plain, in_escape = "", False
    for char in value:
        if char == "\033":
            in_escape = True
            continue
        if in_escape and char == "m":
            in_escape = False
            continue
        if not in_escape:
            plain += char
    return plain


def visible_len(value: str) -> int:
    return len(strip_ansi(value))


def ascii_line(char: str = "=") -> str:
    return "+" + (char * (BOX_WIDTH - 2)) + "+"


def ascii_row(value: str = "") -> str:
    padding = max(0, BOX_WIDTH - visible_len(value) - 4)
    return f"| {value}{' ' * padding} |"


def header(title: str) -> None:
    logo = [
        " __  __  ___    __  __ _                     ",
        "|  \\/  |/ _ \\  |  \\/  (_)_ __ _ __ ___  _ __ ",
        "| |\\/| | | | | | |\\/| | | __| __/ _ \\| __|",
        "| |  | | |_| | | |  | | | |  | | (_) | |   ",
        "|_|  |_|\\__\\_\\ |_|  |_|_|_|  |_|\\___/|_|   ",
    ]
    print(f"{BOLD}{CYAN}{ascii_line('=')}{RESET}")
    for line in logo:
        print(f"{BOLD}{CYAN}{ascii_row(line)}{RESET}")
    print(f"{BOLD}{CYAN}{ascii_line('-')}{RESET}")
    print(f"{BOLD}{CYAN}{ascii_row(f'v{VERSION} :: {title}')}{RESET}")
    print(f"{BOLD}{CYAN}{ascii_line('=')}{RESET}")


def safety_badge(level: str) -> str:
    if level == "safe":      return f"{GREEN}safe{RESET}"
    if level == "modifies":  return f"{AMBER}modifies{RESET}"
    if level == "dangerous": return f"{RED}dangerous{RESET}"
    return f"{MUTED}{level}{RESET}"


def topic_key(category: str, topic: str) -> str:
    return f"{category}.{topic}"


def get_topic(category: str, topic: str) -> Dict[str, Any] | None:
    return COMMAND_LIBRARY.get(topic_key(category, topic))


def get_command(category: str, topic: str, index: int) -> Command | None:
    item = get_topic(category, topic)
    if not item:
        return None
    commands = item["commands"]
    if index < 1 or index > len(commands):
        return None
    return commands[index - 1]


def print_command(index: int, command: str, description: str, safety: str = "safe") -> None:
    print(f"  {GREEN}[{index:02}]{RESET} {BOLD}$ {command}{RESET}")
    print(f"       {MUTED}-> {description} :: {safety_badge(safety)}{RESET}")


def quote(value: str) -> str:
    return shlex.quote(value)


def run_capture(cmd: List[str], timeout: float = 3.0) -> str:
    return str(run_process(cmd, timeout=timeout).get("stdout", "")).strip()


def run_process(cmd: List[str], timeout: float = 3.0) -> Dict[str, Any]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, check=False)
    except Exception:
        return {"stdout": "", "stderr": "", "returncode": 1}
    return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(),
            "returncode": result.returncode}


def osascript(script: str, timeout: float = 3.0) -> str:
    return run_capture(["osascript", "-e", script], timeout=timeout)


def osascript_result(script: str, timeout: float = 3.0) -> Dict[str, Any]:
    return run_process(["osascript", "-e", script], timeout=timeout)


# ── Context inspection ────────────────────────────────────────────────────────

def frontmost_app_context_appkit(error: str = "") -> Dict[str, Any]:
    context: Dict[str, Any] = {"app": "", "bundle_id": "", "window_title": ""}
    try:
        from AppKit import NSWorkspace  # type: ignore[import-untyped]
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app:
            context["app"]       = app.localizedName() or ""
            context["bundle_id"] = app.bundleIdentifier() or ""
            context["context_source"] = "AppKit"
    except Exception as appkit_error:
        if not error:
            error = str(appkit_error)
    if error:
        context["errors"] = [error]
    return context


def frontmost_app_context() -> Dict[str, Any]:
    script = r'''
tell application "System Events"
  set frontProc to first application process whose frontmost is true
  set appName to name of frontProc
  set bundleId to ""
  try
    set bundleId to bundle identifier of frontProc
  end try
  set windowTitle to ""
  try
    if exists window 1 of frontProc then set windowTitle to name of window 1 of frontProc
  end try
  return appName & linefeed & bundleId & linefeed & windowTitle
end tell
'''
    result = osascript_result(script)
    lines  = str(result.get("stdout", "")).splitlines()
    while len(lines) < 3:
        lines.append("")
    if not lines[0] and result.get("returncode") != 0:
        return frontmost_app_context_appkit(
            str(result.get("stderr") or "Could not read frontmost app via System Events.")
        )
    return {"app": lines[0], "bundle_id": lines[1], "window_title": lines[2]}


def finder_context() -> Dict[str, Any]:
    script = r'''
tell application "Finder"
  set currentPath to ""
  try
    set currentPath to POSIX path of (insertion location as alias)
  end try
  set selectedPaths to {}
  try
    repeat with itemRef in selection
      set end of selectedPaths to POSIX path of (itemRef as alias)
    end repeat
  end try
  set oldDelimiters to AppleScript's text item delimiters
  set AppleScript's text item delimiters to linefeed
  set selectedText to selectedPaths as text
  set AppleScript's text item delimiters to oldDelimiters
  return currentPath & linefeed & selectedText
end tell
'''
    lines = osascript(script).splitlines()
    return {
        "current_path":  lines[0] if lines else "",
        "selected_paths": [p for p in lines[1:] if p],
    }


def browser_context(app_name: str) -> Dict[str, Any]:
    if app_name not in {"Safari", "Google Chrome", "Microsoft Edge", "Arc"}:
        return {}
    if app_name == "Safari":
        script = r'''
tell application "Safari"
  if not (exists front window) then return linefeed
  set tabTitle to name of current tab of front window
  set tabUrl to URL of current tab of front window
  return tabTitle & linefeed & tabUrl
end tell
'''
    else:
        script = f'''
tell application "{app_name}"
  if not (exists front window) then return linefeed
  set tabTitle to title of active tab of front window
  set tabUrl to URL of active tab of front window
  return tabTitle & linefeed & tabUrl
end tell
'''
    lines = osascript(script).splitlines()
    while len(lines) < 2:
        lines.append("")
    return {"tab_title": lines[0], "url": lines[1]}


def inspect_frontmost() -> Dict[str, Any]:
    context = frontmost_app_context()
    app = context.get("app", "")
    if app == "Finder":
        context["finder"] = finder_context()
    browser = browser_context(app)
    if browser:
        context["browser"] = browser
    context["suggestions"] = suggest_for_context(context)
    return context


# ── Suggestion engine ─────────────────────────────────────────────────────────

def command_from_topic(topic: str) -> List[Command]:
    item = COMMAND_LIBRARY.get(topic)
    return list(item["commands"]) if item else []


def host_from_url(url: str) -> str:
    return (urlparse(url).hostname or "").strip("[]")


def browser_diagnostics(url: str) -> List[Command]:
    host = host_from_url(url)
    if not host:
        return []
    h = quote(host)
    return [
        (f"dig {h}",                                                          "Inspect DNS records",         "safe"),
        (f"whois {h}",                                                        "Look up domain registration", "safe"),
        (f"openssl s_client -connect {h}:443 -servername {h}",               "Inspect TLS handshake",       "safe"),
        (f"echo | openssl s_client -connect {h}:443 -servername {h} 2>/dev/null | openssl x509 -noout -dates -subject -issuer",
         "Show certificate expiry",                                                                          "safe"),
    ]


def file_type_suggestions(path: str) -> List[Command]:
    ext = os.path.splitext(path)[1].lower()
    p   = quote(path)
    if ext == ".py":
        return [(f"python3 {p}",                    "Run Python script",          "safe"),
                (f"python3 -m py_compile {p}",      "Check syntax",               "safe")]
    if ext == ".sh":
        return [(f"bash {p}",                       "Run shell script",           "safe"),
                (f"chmod +x {p}",                   "Make executable",            "modifies")]
    if ext == ".zip":
        return [(f"unzip -l {p}",                   "List zip contents",          "safe"),
                (f"unzip {p}",                      "Extract zip here",           "modifies")]
    if ext in {".tar", ".gz", ".tgz"}:
        return [(f"tar -tzf {p}",                   "List archive contents",      "safe"),
                (f"tar -xzf {p}",                   "Extract archive",            "modifies")]
    if ext == ".json":
        return [(f"cat {p} | python3 -m json.tool", "Pretty-print JSON",          "safe"),
                (f"jq '.' {p}",                     "Pretty-print JSON (jq)",     "safe")]
    if ext == ".plist":
        return [(f"plutil -p {p}",                  "Print plist as JSON",        "safe"),
                (f"defaults read {p}",              "Read with defaults",         "safe")]
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}:
        return [(f"sips -g all {p}",                "Show image metadata",        "safe"),
                (f"sips -s format jpeg -o /tmp/converted.jpg {p}", "Convert to JPEG", "modifies")]
    if ext == ".pdf":
        return [(f"mdls {p} | grep kMDItem",        "Show PDF metadata",          "safe"),
                (f"qlmanage -p {p}",                "Quick Look preview",         "safe")]
    if ext in {".mp3", ".m4a", ".flac", ".wav", ".aac"}:
        return [(f"mdls {p} | grep -E 'Duration|Artist|Album|Title'", "Show audio metadata", "safe"),
                (f"afplay {p}",                     "Play audio file",            "safe")]
    if ext in {".mp4", ".mov", ".mkv", ".avi"}:
        return [(f"mdls {p} | grep -E 'Duration|PixelHeight|PixelWidth'", "Show video info", "safe"),
                (f"qlmanage -p {p}",                "Quick Look preview",         "safe")]
    return []


def selected_file_diagnostics(path: str) -> List[Command]:
    p = quote(path)
    cmds: List[Command] = [
        (f"du -sh {p}",                      "Show item size",                "safe"),
        (f"stat -f '%N %z bytes %Sm' {p}",   "Show file stats",               "safe"),
        (f"xattr -l {p}",                    "Show extended attributes",      "safe"),
        (f"qlmanage -p {p}",                 "Preview with Quick Look",       "safe"),
    ]
    if path.endswith(".app"):
        cmds.extend([
            (f"codesign -dv --verbose=4 {p}", "Inspect code signature",       "safe"),
            (f"spctl --assess -vv {p}",        "Assess with Gatekeeper",       "safe"),
        ])
    return cmds


def system_settings_diagnostics(title: str) -> List[Command]:
    tl = title.lower()
    cmds: List[Command] = []
    if any(w in tl for w in ("privacy", "security", "integritet", "säkerhet")):
        cmds.extend([
            ("spctl --status",                                  "Show Gatekeeper status",   "safe"),
            ("fdesetup status",                                 "Show FileVault status",    "safe"),
            ("profiles status -type enrollment",                "Show MDM enrollment",      "safe"),
            ("profiles list",                                   "List config profiles",     "safe"),
            ("tccutil reset All",                               "Reset privacy permissions","dangerous"),
        ])
    if any(w in tl for w in ("network", "wi-fi", "wifi", "nätverk")):
        cmds.extend([
            ("ifconfig",                                        "Show network interfaces",  "safe"),
            ("networksetup -listallnetworkservices",            "List network services",    "safe"),
            ("scutil --dns",                                    "Show DNS config",          "safe"),
            ("netstat -rn",                                     "Show routing table",       "safe"),
        ])
    if any(w in tl for w in ("sharing", "delning")):
        cmds.extend([
            ("launchctl print system/com.openssh.sshd",        "Inspect SSH daemon",       "safe"),
            ("systemsetup -getremotelogin",                     "Show Remote Login status", "safe"),
            ("scutil --get ComputerName",                       "Show computer name",       "safe"),
        ])
    if any(w in tl for w in ("login", "inlogg", "background", "bakgrund")):
        cmds.extend([
            ("sfltool dumpbtm",                                 "Dump login item metadata", "safe"),
            ("launchctl print gui/$(id -u)",                    "Inspect user launch services","safe"),
        ])
    return cmds


def suggest_for_context(context: Dict[str, Any]) -> List[Command]:
    suggestions: List[Command] = []
    app   = context.get("app",          "")
    title = context.get("window_title", "")
    tl    = title.lower()

    mapped = APP_MAPPINGS.get(app)
    if mapped:
        suggestions.append((mapped[0], mapped[1], "safe"))

    if app == "Finder":
        finder   = context.get("finder", {})
        path     = finder.get("current_path") or ""
        selected = finder.get("selected_paths") or []
        if path:
            suggestions += [
                (f"cd {quote(path)}",           "cd to current Finder folder",   "safe"),
                (f"ls -la {quote(path)}",       "List folder contents",          "safe"),
                (f"du -sh {quote(path)}/*",     "Show subfolder sizes",          "safe"),
                (f"open {quote(path)}",         "Open folder in Finder",         "safe"),
            ]
        if selected:
            first = selected[0]
            suggestions += [
                (f"file {quote(first)}",        "Identify file type",            "safe"),
                (f"mdls {quote(first)}",        "Show Spotlight metadata",       "safe"),
                (f"open {quote(first)}",        "Open selected file",            "safe"),
            ]
            suggestions.extend(selected_file_diagnostics(first))
            suggestions.extend(file_type_suggestions(first))
            if len(selected) > 1:
                quoted_all = " ".join(quote(p) for p in selected[:5])
                suggestions += [
                    (f"ls -la {quoted_all}", f"List {len(selected)} selected items", "safe"),
                    (f"du -sh {quoted_all}", f"Show sizes for {len(selected)} items", "safe"),
                ]

    browser = context.get("browser", {})
    url = browser.get("url") or ""
    if url:
        suggestions += [
            (f"open {quote(url)}",    "Open current browser URL",       "safe"),
            (f"curl -I {quote(url)}", "Fetch HTTP headers for URL",     "safe"),
        ]
        suggestions.extend(browser_diagnostics(url))

    if app == "System Settings":
        for hint, topic in SETTINGS_HINTS.items():
            if hint in tl:
                suggestions.extend(command_from_topic(topic))
                break
        if not any(hint in tl for hint in SETTINGS_HINTS):
            suggestions.extend(command_from_topic("settings.general"))
        suggestions.extend(system_settings_diagnostics(title))

    if app == "Activity Monitor":
        suggestions += [
            ("ps aux",         "List running processes",     "safe"),
            ("top -o cpu",     "Inspect CPU-heavy processes","safe"),
            ("top -o mem",     "Inspect memory-heavy processes","safe"),
            ("lsof -i",        "List open network sockets",  "safe"),
            ("vm_stat",        "Show virtual memory stats",  "safe"),
            ("kill -TERM PID", "Terminate process by PID",   "dangerous"),
        ]

    if app == "Disk Utility":
        suggestions += [
            ("diskutil list",                     "List disks and volumes",       "safe"),
            ("diskutil info /",                   "Show startup volume info",     "safe"),
            ("df -h",                             "Show mounted filesystem usage","safe"),
            ("mount",                             "Show mounted filesystems",     "safe"),
            ("tmutil listlocalsnapshots /",        "List Time Machine snapshots",  "safe"),
        ]

    if app in {"Terminal", "iTerm2", "Warp", "Ghostty"}:
        suggestions += [
            ("pwd",                     "Show current shell directory", "safe"),
            ("history | tail -20",      "Show recent shell commands",   "safe"),
        ]

    if app == "Visual Studio Code":
        suggestions += [
            ("pwd",                     "Show workspace directory",     "safe"),
            ("git status --short",      "Show repository changes",      "safe"),
        ]

    if app == "Xcode":       suggestions.extend(command_from_topic("developer.xcode"))
    if app == "Console":     suggestions.extend(command_from_topic("apps.console"))
    if app == "Keychain Access": suggestions.extend(command_from_topic("apps.keychain"))

    seen: set = set()
    unique: List[Command] = []
    for cmd in suggestions:
        if cmd[0] not in seen:
            seen.add(cmd[0])
            unique.append(cmd)
    return unique[:DEFAULT_SUGGESTION_LIMIT]


# ── Output / display ──────────────────────────────────────────────────────────

def limited_context(context: Dict[str, Any], limit: int | None) -> Dict[str, Any]:
    if limit is None:
        return context
    limited = dict(context)
    limited["suggestions"] = list(context.get("suggestions", []))[:limit]
    return limited


def print_context(context: Dict[str, Any], limit: int | None = None) -> None:
    context = limited_context(context, limit)
    header("inspect")
    has_errors = bool(context.get("errors"))
    meta = [("App", context.get("app") or "unknown")]
    if context.get("bundle_id"):    meta.append(("Bundle", context["bundle_id"]))
    if context.get("window_title"): meta.append(("Window", context["window_title"]))

    print(f"{MUTED}{ascii_line('-')}{RESET}")
    for label, value in meta:
        print(f"{MUTED}|{RESET} {GREEN}{label:<14}{RESET} {value}")
    print(f"{MUTED}{ascii_line('-')}{RESET}")

    if has_errors:
        for err in context["errors"]:
            print(f"{AMBER}Context warning:{RESET} {err}")

    finder = context.get("finder") or {}
    if finder.get("current_path"):   print(f"{MUTED}| Finder path    {RESET} {finder['current_path']}")
    if finder.get("selected_paths"): print(f"{MUTED}| Selection      {RESET} {', '.join(finder['selected_paths'])}")

    browser = context.get("browser") or {}
    if browser.get("tab_title"): print(f"{MUTED}| Tab            {RESET} {browser['tab_title']}")
    if browser.get("url"):       print(f"{MUTED}| URL            {RESET} {browser['url']}")

    print()
    suggestions = context.get("suggestions", [])
    if not suggestions:
        print(f"{AMBER}No command suggestions for this context yet.{RESET}")
        return
    print(f"{CYAN}:: Terminal equivalents{RESET}")
    for i, (command, description, safety) in enumerate(suggestions, start=1):
        print_command(i, command, description, safety)


def print_context_compact(context: Dict[str, Any], limit: int | None = None) -> None:
    context = limited_context(context, limit)
    app         = context.get("app") or "unknown"
    window      = context.get("window_title") or ""
    suggestions = context.get("suggestions", [])
    print(f"{DIM}{now()}{RESET} {CYAN}{app}{RESET}")
    if window:
        print(f"  {MUTED}{window}{RESET}")
    if not suggestions:
        print(f"  {AMBER}No suggestions yet.{RESET}")
        return
    cap = limit if limit is not None else 4
    for i, (command, description, safety) in enumerate(suggestions[:cap], start=1):
        print(f"  {GREEN}{i}.{RESET} {BOLD}{command}{RESET}")
        print(f"     {MUTED}{description} · {safety_badge(safety)}{RESET}")


# ── CLI commands ──────────────────────────────────────────────────────────────

def inspect_command(as_json: bool = False, limit: int | None = None) -> int:
    context = inspect_frontmost()
    context = limited_context(context, limit)
    if as_json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        print_context(context)
    return 0


def list_topics(as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(COMMAND_LIBRARY, indent=2, ensure_ascii=False))
        return
    header("command library")
    for key, value in sorted(COMMAND_LIBRARY.items()):
        print(f"{GREEN}>{RESET} {key}")
        print(f"  {MUTED}{value['gui']}{RESET}")


def show_topic(category: str, topic: str, as_json: bool = False) -> int:
    key  = topic_key(category, topic)
    item = COMMAND_LIBRARY.get(key)
    if not item:
        print(f"{RED}No mapping found for: {key}{RESET}")
        return 1
    if as_json:
        print(json.dumps({key: item}, indent=2, ensure_ascii=False))
        return 0
    header(str(item["gui"]))
    print()
    for i, (command, description, safety) in enumerate(item["commands"], start=1):
        print_command(i, command, description, safety)
    return 0


def normalize_search_text(value: str) -> str:
    return (value.lower()
            .replace("-", "").replace("_", "").replace(" ", "")
            .replace(".", "").replace("/", "").replace("&", "and"))


def search_library(query: str, as_json: bool = False) -> int:
    ql = normalize_search_text(query)
    matches = {
        key: item for key, item in COMMAND_LIBRARY.items()
        if ql in normalize_search_text(
            f"{key} {item['gui']} " + " ".join(f"{c} {d}" for c, d, _ in item["commands"])
        )
    }
    if as_json:
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return 0 if matches else 1
    header(f"search: {query}")
    if not matches:
        print(f"{AMBER}No matches.{RESET}")
        return 1
    for key, item in matches.items():
        print(f"\n{GREEN}> {key}{RESET}")
        print(f"  {MUTED}{item['gui']}{RESET}")
        for i, (command, description, safety) in enumerate(item["commands"], start=1):
            print_command(i, command, description, safety)
    return 0


def copy_command(category: str, topic: str, index: int) -> int:
    command = get_command(category, topic, index)
    if not command:
        print(f"{RED}No command found for {category}.{topic} index {index}{RESET}")
        return 1
    cmd, description, safety = command
    if not shutil.which("pbcopy"):
        print(f"{RED}pbcopy not found:{RESET}")
        print(cmd)
        return 1
    try:
        subprocess.run(["pbcopy"], input=cmd, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"{RED}pbcopy failed:{RESET} {error}\n{cmd}")
        return 1
    print(f"{GREEN}Copied:{RESET} {cmd}")
    print(f"{MUTED}{description} · {safety_badge(safety)}{RESET}")
    return 0


def run_command(category: str, topic: str, index: int,
                confirm: bool, allow_modifies: bool) -> int:
    command = get_command(category, topic, index)
    if not command:
        print(f"{RED}No command found for {category}.{topic} index {index}{RESET}")
        return 1
    cmd, description, safety = command
    if safety != "safe" and not allow_modifies:
        print(f"{AMBER}Blocked:{RESET} safety is {safety_badge(safety)}")
        print("Use --allow-modifies to run it.")
        return 1
    if not confirm:
        print(f"{AMBER}Dry run.{RESET} Use --confirm to execute.")
        print()
        print_command(index, cmd, description, safety)
        return 0
    print(f"{GREEN}Running:{RESET} {cmd}")
    return subprocess.call(cmd, shell=True)


def explain_command(raw_command: str) -> int:
    header("explain")
    for key, item in COMMAND_LIBRARY.items():
        for i, (cmd, description, safety) in enumerate(item["commands"], start=1):
            if raw_command == cmd or raw_command in cmd:
                print(f"{GREEN}Match:{RESET} {key} #{i}")
                print_command(i, cmd, description, safety)
                return 0
    print(f"{AMBER}No exact library match.{RESET}")
    return 1


def is_terminal_context(context: Dict[str, Any]) -> bool:
    app = str(context.get("app") or "")
    bid = str(context.get("bundle_id") or "")
    return app in {"Terminal", "iTerm2", "Warp", "Ghostty", "Visual Studio Code", "Code"} or \
           bid.startswith(("com.apple.Terminal", "com.googlecode.iterm2",
                           "dev.warp.Warp", "com.mitchellh.ghostty", "com.microsoft.VSCode"))


def doctor() -> int:
    header("doctor")
    checks = [
        ("platform",  platform.system(),       "ok" if platform.system() == "Darwin" else "not macOS"),
        ("python",    sys.version.split()[0],  "ok"),
        ("osascript", shutil.which("osascript") or "-", "ok" if shutil.which("osascript") else "missing"),
        ("open",      shutil.which("open") or "-",      "ok" if shutil.which("open")      else "missing"),
        ("pbcopy",    shutil.which("pbcopy") or "-",    "ok" if shutil.which("pbcopy")    else "missing"),
    ]
    try:
        import AppKit  # type: ignore[import-untyped]  # noqa: F401
        checks.append(("pyobjc", "ok", "optional AppKit fallback"))
    except ImportError:
        checks.append(("pyobjc", "missing", "optional — install: pip install pyobjc-framework-Cocoa"))

    failed = False
    for name, value, status in checks:
        color = GREEN if status == "ok" else (AMBER if "optional" in status else RED)
        if status not in {"ok"} and "optional" not in status:
            failed = True
        print(f"{BOLD}{name:<12}{RESET} {value}  {color}{status}{RESET}")

    print(f"\n{MUTED}Context check:{RESET}")
    ctx = frontmost_app_context()
    print(f"  app:    {ctx.get('app') or '-'}")
    print(f"  window: {ctx.get('window_title') or '-'}")
    if ctx.get("errors"):
        print(f"\n{AMBER}Needs Accessibility permission:{RESET}")
        print("  System Settings → Privacy & Security → Accessibility → add Terminal")
    return 1 if failed else 0


# ── Watch mode (core loop) ────────────────────────────────────────────────────

def watch_apps(
    interval: float = 1.0,
    as_json: bool = False,
    compact: bool = False,
    ignore_terminal: bool = False,
    limit: int | None = None,
    serve: bool = True,
) -> int:
    header("watch mode")

    if serve:
        t = threading.Thread(target=_start_live_server, daemon=True)
        t.start()
        print(f"{GREEN}✓{RESET} Live-server: {CYAN}http://127.0.0.1:{LIVE_PORT}{RESET}")
        print(f"  → Öppna {BOLD}docs/handoff.html{RESET} för att se kommandon i realtid")

    print(f"{MUTED}Watching frontmost app/window. Ctrl+C to stop.{RESET}")
    if ignore_terminal:
        print(f"{MUTED}Ignoring terminal app contexts.{RESET}")
    print()

    last_key = None
    try:
        while True:
            context = inspect_frontmost()
            if ignore_terminal and is_terminal_context(context):
                time.sleep(interval)
                continue

            app    = context.get("app", "")
            window = context.get("window_title", "")
            url    = (context.get("browser") or {}).get("url")
            path   = (context.get("finder")  or {}).get("current_path")
            key    = (app, window, url, path)

            if key != last_key:
                last_key = key
                context  = limited_context(context, limit)

                # Emit each suggestion to the live server
                if serve:
                    category  = APP_CATEGORY.get(app, "App")
                    gui_label = app + (" → " + window if window else "")
                    for cmd, description, _ in context.get("suggestions", []):
                        _emit(category, gui_label, cmd, description)

                if as_json:
                    print(json.dumps(context, ensure_ascii=False))
                elif compact:
                    print_context_compact(context, limit)
                else:
                    print(f"\n{DIM}{now()}{RESET}")
                    print_context(context, limit)

            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{GREEN}Stopped.{RESET}")
        return 0


# ── Entry point ───────────────────────────────────────────────────────────────

def rewrite_shortcut_args(argv: List[str]) -> List[str]:
    args = argv[1:]
    alias_args = [a for a in args if a in TOPIC_ALIASES]
    if len(alias_args) == 1:
        alias     = alias_args[0]
        remaining = [a for a in args if a != alias]
        if all(a.startswith("-") for a in remaining):
            cat, topic = TOPIC_ALIASES[alias]
            return [argv[0], *remaining, "show", cat, topic]
    return argv


def main() -> int:
    sys.argv = rewrite_shortcut_args(sys.argv)

    parser = argparse.ArgumentParser(
        prog="mqmirror",
        description="GUI actions → terminal command equivalents for macOS.",
    )
    parser.add_argument("--json",  dest="global_json",  action="store_true")
    parser.add_argument("--plain", dest="global_plain", action="store_true")
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list",    help="List available GUI-to-CLI topics")
    list_p.add_argument("--json", action="store_true")

    show_p = sub.add_parser("show",    help="Show commands for a GUI area")
    show_p.add_argument("category")
    show_p.add_argument("topic")
    show_p.add_argument("--json", action="store_true")

    srch_p = sub.add_parser("search",  help="Search command library")
    srch_p.add_argument("query")
    srch_p.add_argument("--json", action="store_true")

    copy_p = sub.add_parser("copy",    help="Copy command by topic/index")
    copy_p.add_argument("category")
    copy_p.add_argument("topic")
    copy_p.add_argument("index", type=int)

    run_p  = sub.add_parser("run",     help="Run command by topic/index")
    run_p.add_argument("category")
    run_p.add_argument("topic")
    run_p.add_argument("index", type=int)
    run_p.add_argument("--confirm",       action="store_true")
    run_p.add_argument("--allow-modifies",action="store_true")

    expl_p = sub.add_parser("explain", help="Explain a command")
    expl_p.add_argument("raw_command")

    insp_p = sub.add_parser("inspect", help="Inspect frontmost app and suggest commands")
    insp_p.add_argument("--json",  action="store_true")
    insp_p.add_argument("--limit", type=positive_int)
    insp_p.add_argument("--plain", action="store_true")

    wtch_p = sub.add_parser("watch",   help="Watch context and suggest commands (default mode)")
    wtch_p.add_argument("--interval",       type=float, default=1.0)
    wtch_p.add_argument("--json",           action="store_true")
    wtch_p.add_argument("--compact",        action="store_true")
    wtch_p.add_argument("--ignore-terminal",action="store_true")
    wtch_p.add_argument("--limit",          type=positive_int)
    wtch_p.add_argument("--plain",          action="store_true")
    wtch_p.add_argument("--no-serve",       action="store_true",
                        help=f"Don't start the live HTTP server on port {LIVE_PORT}")

    sub.add_parser("doctor",  help="Check runtime dependencies")
    sub.add_parser("version", help="Print version")

    args    = parser.parse_args()
    as_json = bool(getattr(args, "global_json", False) or getattr(args, "json", False))
    configure_output(bool(getattr(args, "global_plain", False) or getattr(args, "plain", False)))

    # Default: no subcommand → watch mode
    if args.command is None:
        return watch_apps(serve=True, compact=True, ignore_terminal=True)

    if args.command == "list":    list_topics(as_json); return 0
    if args.command == "show":    return show_topic(args.category, args.topic, as_json)
    if args.command == "search":  return search_library(args.query, as_json)
    if args.command == "copy":    return copy_command(args.category, args.topic, args.index)
    if args.command == "run":     return run_command(args.category, args.topic, args.index,
                                                     args.confirm, args.allow_modifies)
    if args.command == "explain": return explain_command(args.raw_command)
    if args.command == "inspect": return inspect_command(as_json, args.limit)
    if args.command == "watch":
        return watch_apps(args.interval, as_json, args.compact,
                          args.ignore_terminal, args.limit,
                          serve=not args.no_serve)
    if args.command == "doctor":  return doctor()
    if args.command == "version": print(f"mqmirror {VERSION}"); return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
