#!/usr/bin/env python3
"""
MQ Mirror v0.5 — GUI actions → terminal command equivalents.

Examples:
  mqmirror list
  mqmirror show settings general
  mqmirror search network
  mqmirror copy settings network 2
  mqmirror run settings general 1 --confirm
  mqmirror show settings network --json
  mqmirror inspect
  mqmirror watch
"""

from __future__ import annotations

import argparse
import json
import platform
import shlex
import shutil
import sys
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

VERSION = "0.5"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[38;5;82m"
CYAN = "\033[38;5;87m"
AMBER = "\033[38;5;220m"
RED = "\033[38;5;203m"
MUTED = "\033[38;5;244m"

Command = Tuple[str, str, str]

COMMAND_LIBRARY: Dict[str, Dict[str, Any]] = {
    "settings.general": {
        "gui": "System Settings → General",
        "commands": [
            ("open -a 'System Settings'", "Open System Settings", "safe"),
            ("sw_vers", "Show macOS version", "safe"),
            ("system_profiler SPSoftwareDataType", "Show software overview", "safe"),
            ("scutil --get ComputerName", "Show computer name", "safe"),
            ("scutil --get LocalHostName", "Show local host name", "safe"),
            ("hostname", "Show hostname", "safe"),
        ],
    },
    "settings.network": {
        "gui": "System Settings → Network",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Network-Settings.extension"', "Open Network settings", "safe"),
            ("networksetup -listallhardwareports", "List network interfaces", "safe"),
            ("ipconfig getifaddr en0", "Show Wi-Fi IP address", "safe"),
            ("route -n get default", "Show default gateway", "safe"),
            ("scutil --dns", "Show DNS configuration", "safe"),
            ("networksetup -getdnsservers Wi-Fi", "Show Wi-Fi DNS servers", "safe"),
        ],
    },
    "settings.displays": {
        "gui": "System Settings → Displays",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Displays-Settings.extension"', "Open Displays settings", "safe"),
            ("system_profiler SPDisplaysDataType", "Show display/GPU information", "safe"),
        ],
    },
    "settings.privacy": {
        "gui": "System Settings → Privacy & Security",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension"', "Open Privacy & Security", "safe"),
            ("spctl --status", "Show Gatekeeper status", "safe"),
            ("fdesetup status", "Show FileVault status", "safe"),
            ("csrutil status", "Show SIP status", "safe"),
        ],
    },
    "settings.keyboard": {
        "gui": "System Settings → Keyboard",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Keyboard-Settings.extension"', "Open Keyboard settings", "safe"),
            ("defaults read NSGlobalDomain ApplePressAndHoldEnabled", "Show press-and-hold setting", "safe"),
            ("defaults read NSGlobalDomain InitialKeyRepeat", "Show initial key repeat", "safe"),
            ("defaults read NSGlobalDomain KeyRepeat", "Show key repeat", "safe"),
        ],
    },
    "settings.trackpad": {
        "gui": "System Settings → Trackpad",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Trackpad-Settings.extension"', "Open Trackpad settings", "safe"),
            ("defaults read com.apple.AppleMultitouchTrackpad", "Show trackpad preferences", "safe"),
        ],
    },
    "settings.battery": {
        "gui": "System Settings → Battery",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Battery-Settings.extension"', "Open Battery settings", "safe"),
            ("pmset -g batt", "Show battery status", "safe"),
            ("pmset -g", "Show power management settings", "safe"),
        ],
    },
    "settings.bluetooth": {
        "gui": "System Settings → Bluetooth",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.BluetoothSettings"', "Open Bluetooth settings", "safe"),
            ("system_profiler SPBluetoothDataType", "Show Bluetooth information", "safe"),
        ],
    },
    "settings.sound": {
        "gui": "System Settings → Sound",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Sound-Settings.extension"', "Open Sound settings", "safe"),
            ("system_profiler SPAudioDataType", "Show audio devices", "safe"),
        ],
    },
    "settings.users": {
        "gui": "System Settings → Users & Groups",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Users-Groups-Settings.extension"', "Open Users & Groups", "safe"),
            ("whoami", "Show current user", "safe"),
            ("id", "Show current user identity/groups", "safe"),
            ("dscl . list /Users", "List local users", "safe"),
        ],
    },
    "settings.sharing": {
        "gui": "System Settings → General → Sharing",
        "commands": [
            ('open "x-apple.systempreferences:com.apple.Sharing-Settings.extension"', "Open Sharing settings", "safe"),
            ("scutil --get ComputerName", "Show computer name", "safe"),
            ("scutil --get LocalHostName", "Show local hostname", "safe"),
            ("launchctl print system/com.openssh.sshd 2>/dev/null | head", "Inspect SSH daemon state", "safe"),
        ],
    },
    "finder.files": {
        "gui": "Finder → file operations",
        "commands": [
            ("open .", "Open current folder in Finder", "safe"),
            ("pwd", "Show current directory", "safe"),
            ("ls -la", "List files with details", "safe"),
            ("mkdir new-folder", "Create folder", "modifies"),
            ("touch file.txt", "Create file", "modifies"),
            ("mv old.txt new.txt", "Rename or move file", "modifies"),
            ("trash file.txt  # brew install trash", "Move file to Trash safely", "modifies"),
        ],
    },
    "apps.common": {
        "gui": "Open common apps",
        "commands": [
            ("open -a Finder", "Open Finder", "safe"),
            ("open -a Safari", "Open Safari", "safe"),
            ("open -a Terminal", "Open Terminal", "safe"),
            ("open -a 'System Settings'", "Open System Settings", "safe"),
            ("open -a 'Activity Monitor'", "Open Activity Monitor", "safe"),
            ("open -a 'Visual Studio Code'", "Open VS Code", "safe"),
        ],
    },
    "developer.xcode": {
        "gui": "Xcode / developer tools",
        "commands": [
            ("xcode-select -p", "Show active developer directory", "safe"),
            ("xcodebuild -version", "Show Xcode version", "safe"),
            ("xcrun simctl list", "List simulators", "safe"),
            ("xcrun xctrace list devices", "List devices for profiling", "safe"),
        ],
    },
}

APP_MAPPINGS = {
    "Finder": ("open -a Finder", "Open Finder"),
    "Safari": ("open -a Safari", "Open Safari"),
    "Terminal": ("open -a Terminal", "Open Terminal"),
    "System Settings": ("open -a 'System Settings'", "Open System Settings"),
    "Activity Monitor": ("open -a 'Activity Monitor'", "Open Activity Monitor"),
    "Visual Studio Code": ("open -a 'Visual Studio Code'", "Open VS Code"),
    "Xcode": ("open -a Xcode", "Open Xcode"),
    "Disk Utility": ("diskutil list", "List disks"),
    "Simulator": ("xcrun simctl list", "List simulators"),
}

SETTINGS_HINTS = {
    "general": "settings.general",
    "network": "settings.network",
    "wi-fi": "settings.network",
    "wifi": "settings.network",
    "displays": "settings.displays",
    "display": "settings.displays",
    "privacy": "settings.privacy",
    "security": "settings.privacy",
    "keyboard": "settings.keyboard",
    "trackpad": "settings.trackpad",
    "battery": "settings.battery",
    "bluetooth": "settings.bluetooth",
    "sound": "settings.sound",
    "users": "settings.users",
    "groups": "settings.users",
    "sharing": "settings.sharing",
}


TOPIC_ALIASES = {
    "general": ("settings", "general"),
    "network": ("settings", "network"),
    "wifi": ("settings", "network"),
    "wi-fi": ("settings", "network"),
    "display": ("settings", "displays"),
    "displays": ("settings", "displays"),
    "privacy": ("settings", "privacy"),
    "security": ("settings", "privacy"),
    "keyboard": ("settings", "keyboard"),
    "trackpad": ("settings", "trackpad"),
    "battery": ("settings", "battery"),
    "bluetooth": ("settings", "bluetooth"),
    "sound": ("settings", "sound"),
    "users": ("settings", "users"),
    "sharing": ("settings", "sharing"),
    "finder": ("finder", "files"),
    "files": ("finder", "files"),
    "apps": ("apps", "common"),
    "xcode": ("developer", "xcode"),
}


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def header(title: str) -> None:
    print(f"{BOLD}{CYAN}════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}MQ Mirror v0.5 — {title}{RESET}")
    print(f"{BOLD}{CYAN}════════════════════════════════════════════════════{RESET}")


def safety_badge(level: str) -> str:
    if level == "safe":
        return f"{GREEN}safe{RESET}"
    if level == "modifies":
        return f"{AMBER}modifies{RESET}"
    if level == "dangerous":
        return f"{RED}dangerous{RESET}"
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
    print(f"  {GREEN}{index:>2}.{RESET} {BOLD}{command}{RESET}")
    print(f"      {MUTED}{description} · {safety_badge(safety)}{RESET}")


def quote(value: str) -> str:
    return shlex.quote(value)


def run_capture(cmd: List[str], timeout: float = 3.0) -> str:
    result = run_process(cmd, timeout=timeout)
    return str(result.get("stdout", "")).strip()


def run_process(cmd: List[str], timeout: float = 3.0) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return {"stdout": "", "stderr": "", "returncode": 1}
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def osascript(script: str, timeout: float = 3.0) -> str:
    return run_capture(["osascript", "-e", script], timeout=timeout)


def osascript_result(script: str, timeout: float = 3.0) -> Dict[str, Any]:
    return run_process(["osascript", "-e", script], timeout=timeout)


def frontmost_app_context_appkit(error: str = "") -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "app": "",
        "bundle_id": "",
        "window_title": "",
    }

    try:
        from AppKit import NSWorkspace

        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app:
            context["app"] = app.localizedName() or ""
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
    lines = str(result.get("stdout", "")).splitlines()
    while len(lines) < 3:
        lines.append("")

    if not lines[0] and result.get("returncode") != 0:
        return frontmost_app_context_appkit(
            str(result.get("stderr") or "Could not read frontmost app via System Events.")
        )

    context = {
        "app": lines[0],
        "bundle_id": lines[1],
        "window_title": lines[2],
    }
    return context


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
  return currentPath & linefeed & (selectedPaths as text)
end tell
'''
    lines = osascript(script).splitlines()
    current_path = lines[0] if lines else ""
    selected_paths: List[str] = []
    if len(lines) > 1 and lines[1]:
        selected_paths = [p for p in lines[1].split(", ") if p]
    return {
        "current_path": current_path,
        "selected_paths": selected_paths,
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
    return {
        "tab_title": lines[0],
        "url": lines[1],
    }


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


def command_from_topic(topic: str) -> List[Command]:
    item = COMMAND_LIBRARY.get(topic)
    if not item:
        return []
    return list(item["commands"])


def suggest_for_context(context: Dict[str, Any]) -> List[Command]:
    suggestions: List[Command] = []
    app = context.get("app", "")
    title = context.get("window_title", "")
    title_l = title.lower()

    mapped = APP_MAPPINGS.get(app)
    if mapped:
        suggestions.append((mapped[0], mapped[1], "safe"))

    if app == "Finder":
        finder = context.get("finder", {})
        path = finder.get("current_path") or ""
        selected = finder.get("selected_paths") or []
        if path:
            suggestions.extend([
                (f"cd {quote(path)}", "Use Finder folder in the shell", "safe"),
                (f"ls -la {quote(path)}", "List Finder folder contents", "safe"),
            ])
        if selected:
            first = selected[0]
            suggestions.extend([
                (f"file {quote(first)}", "Identify selected Finder item", "safe"),
                (f"mdls {quote(first)}", "Show Spotlight metadata for selected item", "safe"),
            ])

    browser = context.get("browser", {})
    url = browser.get("url") or ""
    if url:
        suggestions.extend([
            (f"open {quote(url)}", "Open current browser URL", "safe"),
            (f"curl -I {quote(url)}", "Fetch HTTP headers for current URL", "safe"),
        ])

    if app == "System Settings":
        for hint, topic in SETTINGS_HINTS.items():
            if hint in title_l:
                suggestions.extend(command_from_topic(topic))
                break
        if not any(hint in title_l for hint in SETTINGS_HINTS):
            suggestions.extend(command_from_topic("settings.general"))

    if app == "Activity Monitor":
        suggestions.extend([
            ("ps aux", "List running processes", "safe"),
            ("top -o cpu", "Inspect CPU-heavy processes", "safe"),
            ("vm_stat", "Show virtual memory statistics", "safe"),
        ])

    if app == "Disk Utility":
        suggestions.extend([
            ("diskutil list", "List disks and volumes", "safe"),
            ("df -h", "Show mounted filesystem usage", "safe"),
        ])

    if app == "Terminal":
        suggestions.extend([
            ("pwd", "Show current shell directory", "safe"),
            ("history | tail -20", "Show recent shell commands", "safe"),
        ])

    if app == "Visual Studio Code":
        suggestions.extend([
            ("pwd", "Show current workspace directory", "safe"),
            ("git status --short", "Show repository changes", "safe"),
        ])

    seen = set()
    unique = []
    for cmd in suggestions:
        if cmd[0] in seen:
            continue
        seen.add(cmd[0])
        unique.append(cmd)
    return unique[:8]


def print_context(context: Dict[str, Any]) -> None:
    header("inspect")
    print(f"{GREEN}App:{RESET} {context.get('app') or 'unknown'}")
    has_context_errors = bool(context.get("errors"))
    if context.get("bundle_id"):
        print(f"{MUTED}Bundle:{RESET} {context['bundle_id']}")
    if context.get("window_title"):
        print(f"{MUTED}Window:{RESET} {context['window_title']}")
    if context.get("context_source"):
        print(f"{MUTED}Context source:{RESET} {context['context_source']}")
    if has_context_errors:
        for error in context["errors"]:
            print(f"{AMBER}Context warning:{RESET} {error}")
        print(f"{MUTED}macOS may require Accessibility/Automation permission for Terminal or your shell app.{RESET}")

    finder = context.get("finder") or {}
    if finder.get("current_path"):
        print(f"{MUTED}Finder path:{RESET} {finder['current_path']}")
    if finder.get("selected_paths"):
        print(f"{MUTED}Selection:{RESET} {', '.join(finder['selected_paths'])}")

    browser = context.get("browser") or {}
    if browser.get("tab_title"):
        print(f"{MUTED}Tab:{RESET} {browser['tab_title']}")
    if browser.get("url"):
        print(f"{MUTED}URL:{RESET} {browser['url']}")

    print()
    suggestions = context.get("suggestions", [])
    if not suggestions:
        if has_context_errors and not context.get("app"):
            print(f"{AMBER}No command suggestions because MQ Mirror could not read the active GUI context.{RESET}")
            print("Allow your terminal app in System Settings → Privacy & Security → Accessibility and Automation, then run mqmirror inspect again.")
            return

        print(f"{AMBER}No command suggestions for this context yet.{RESET}")
        print("Tip: add a mapping to APP_MAPPINGS, SETTINGS_HINTS, or suggest_for_context().")
        return

    print(f"{CYAN}Terminal equivalents:{RESET}")
    for i, (command, description, safety) in enumerate(suggestions, start=1):
        print_command(i, command, description, safety)


def inspect_command(as_json: bool = False) -> int:
    context = inspect_frontmost()
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
        print(f"{GREEN}❯{RESET} {key}")
        print(f"  {MUTED}{value['gui']}{RESET}")


def show_topic(category: str, topic: str, as_json: bool = False) -> int:
    key = topic_key(category, topic)
    item = COMMAND_LIBRARY.get(key)

    if not item:
        print(f"{RED}No mapping found for: {key}{RESET}")
        print("Run: mqmirror list")
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
    return (
        value.lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
        .replace(".", "")
        .replace("/", "")
        .replace("&", "and")
    )


def search_library(query: str, as_json: bool = False) -> int:
    query_l = normalize_search_text(query)
    matches = {}

    for key, item in COMMAND_LIBRARY.items():
        haystack = f"{key} {item['gui']} " + " ".join(
            f"{cmd} {desc}" for cmd, desc, _ in item["commands"]
        )
        if query_l in normalize_search_text(haystack):
            matches[key] = item

    if as_json:
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return 0 if matches else 1

    header(f"search: {query}")

    if not matches:
        print(f"{AMBER}No matches.{RESET}")
        return 1

    for key, item in matches.items():
        print()
        print(f"{GREEN}❯ {key}{RESET}")
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
        print(f"{RED}pbcopy not found. Copy manually:{RESET}")
        print(cmd)
        return 1

    try:
        subprocess.run(["pbcopy"], input=cmd, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"{RED}Could not copy with pbcopy:{RESET} {error}")
        print(f"{MUTED}Copy manually:{RESET}")
        print(cmd)
        return 1

    print(f"{GREEN}Copied:{RESET} {cmd}")
    print(f"{MUTED}{description} · {safety_badge(safety)}{RESET}")
    return 0


def run_command(category: str, topic: str, index: int, confirm: bool, allow_modifies: bool) -> int:
    command = get_command(category, topic, index)
    if not command:
        print(f"{RED}No command found for {category}.{topic} index {index}{RESET}")
        return 1

    cmd, description, safety = command

    if safety != "safe" and not allow_modifies:
        print(f"{AMBER}Blocked:{RESET} command safety is {safety_badge(safety)}")
        print("Use --allow-modifies if you really want to run it.")
        print(cmd)
        return 1

    if not confirm:
        print(f"{AMBER}Dry run only.{RESET}")
        print("Use --confirm to execute.")
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
    print(f"{MUTED}Command:{RESET} {raw_command}")
    print("Tip: add this command to COMMAND_LIBRARY if it belongs in MQ Mirror.")
    return 1


def watch_apps(
    interval: float = 1.0,
    as_json: bool = False,
    compact: bool = False,
    ignore_terminal: bool = False,
) -> int:
    header("watch mode")
    print(f"{MUTED}Watching frontmost app/window context. Press Ctrl+C to stop.{RESET}")
    if ignore_terminal:
        print(f"{MUTED}Ignoring Terminal/iTerm/VS Code terminal contexts.{RESET}")

    last_key = None
    try:
        while True:
            context = inspect_frontmost()
            if ignore_terminal and is_terminal_context(context):
                time.sleep(interval)
                continue

            key = (
                context.get("app"),
                context.get("window_title"),
                (context.get("browser") or {}).get("url"),
                (context.get("finder") or {}).get("current_path"),
            )
            if key != last_key:
                last_key = key
                if as_json:
                    print(json.dumps(context, ensure_ascii=False))
                else:
                    print()
                    if compact:
                        print_context_compact(context)
                    else:
                        print(f"{DIM}{now()}{RESET}")
                        print_context(context)
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{GREEN}Stopped.{RESET}")
        return 0


def watch_app_events() -> int:
    print(f"{AMBER}watch-events now uses built-in AppleScript polling.{RESET}")
    return watch_apps(interval=0.5, as_json=False)


def is_terminal_context(context: Dict[str, Any]) -> bool:
    app = str(context.get("app") or "")
    bundle_id = str(context.get("bundle_id") or "")
    terminal_apps = {
        "Terminal",
        "iTerm2",
        "Warp",
        "Ghostty",
        "Visual Studio Code",
        "Code",
    }
    terminal_bundle_prefixes = (
        "com.apple.Terminal",
        "com.googlecode.iterm2",
        "dev.warp.Warp",
        "com.mitchellh.ghostty",
        "com.microsoft.VSCode",
    )

    return app in terminal_apps or bundle_id.startswith(terminal_bundle_prefixes)



def doctor() -> int:
    header("doctor")

    checks = [
        ("platform", platform.system(), "ok" if platform.system() == "Darwin" else "not macOS"),
        ("python", sys.version.split()[0], "ok"),
        ("osascript", shutil.which("osascript") or "-", "ok" if shutil.which("osascript") else "missing"),
        ("open", shutil.which("open") or "-", "ok" if shutil.which("open") else "missing"),
        ("pbcopy", shutil.which("pbcopy") or "-", "ok" if shutil.which("pbcopy") else "missing"),
    ]

    try:
        import AppKit  # noqa: F401
        pyobjc = "ok"
    except ImportError:
        pyobjc = "missing"

    checks.append(("pyobjc", pyobjc, "optional for watch-events"))

    failed = False

    for name, value, status in checks:
        if status in {"ok", "Darwin"}:
            color = GREEN
        elif status == "optional for watch-events":
            color = AMBER
        else:
            color = RED
            failed = True

        print(f"{BOLD}{name:<12}{RESET} {value}  {color}{status}{RESET}")

    print()
    print(f"{MUTED}Context check:{RESET}")
    ctx = frontmost_app_context()
    app = ctx.get("app") or "-"
    window = ctx.get("window_title") or "-"
    print(f"  app:    {app}")
    print(f"  window: {window}")

    if ctx.get("errors"):
        print()
        print(f"{AMBER}macOS may require Accessibility or Automation permission.{RESET}")
        print("Check: System Settings → Privacy & Security → Accessibility / Automation")

    if pyobjc == "missing":
        print()
        print("Optional watch-events dependency:")
        print("  pip install pyobjc-framework-Cocoa")

    return 1 if failed else 0


def print_context_compact(context: Dict[str, Any]) -> None:
    app = context.get("app") or "unknown"
    window = context.get("window_title") or ""
    suggestions = context.get("suggestions", [])

    print(f"{DIM}{now()}{RESET} {CYAN}{app}{RESET}")
    if window:
        print(f"  {MUTED}{window}{RESET}")

    if not suggestions:
        print(f"  {AMBER}No suggestions yet.{RESET}")
        return

    for i, (command, description, safety) in enumerate(suggestions[:4], start=1):
        print(f"  {GREEN}{i}.{RESET} {BOLD}{command}{RESET}")
        print(f"     {MUTED}{description} · {safety_badge(safety)}{RESET}")


def rewrite_shortcut_args(argv: List[str]) -> List[str]:
    if len(argv) == 2 and argv[1] in TOPIC_ALIASES:
        category, topic = TOPIC_ALIASES[argv[1]]
        return [argv[0], "show", category, topic]

    return argv


def main() -> int:
    sys.argv = rewrite_shortcut_args(sys.argv)

    parser = argparse.ArgumentParser(
        prog="mqmirror",
        description="GUI actions → terminal command equivalents for macOS.",
    )
    parser.add_argument("--json", dest="global_json", action="store_true", help="Output JSON where supported")
    sub = parser.add_subparsers(dest="command")

    list_parser = sub.add_parser("list", help="List available GUI-to-CLI topics")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")

    show = sub.add_parser("show", help="Show commands for a GUI area")
    show.add_argument("category")
    show.add_argument("topic")
    show.add_argument("--json", action="store_true", help="Output JSON")

    search = sub.add_parser("search", help="Search command library")
    search.add_argument("query")
    search.add_argument("--json", action="store_true", help="Output JSON")

    copy = sub.add_parser("copy", help="Copy command by topic/index")
    copy.add_argument("category")
    copy.add_argument("topic")
    copy.add_argument("index", type=int)

    run = sub.add_parser("run", help="Run command by topic/index")
    run.add_argument("category")
    run.add_argument("topic")
    run.add_argument("index", type=int)
    run.add_argument("--confirm", action="store_true", help="Actually execute command")
    run.add_argument("--allow-modifies", action="store_true", help="Allow modifies commands")

    explain = sub.add_parser("explain", help="Explain a command if it exists in the library")
    explain.add_argument("raw_command")

    inspect_parser = sub.add_parser("inspect", help="Inspect frontmost app/window and suggest commands")
    inspect_parser.add_argument("--json", action="store_true", help="Output JSON")

    watch = sub.add_parser("watch", help="Watch frontmost app/window context and suggest commands")
    watch.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    watch.add_argument("--json", action="store_true", help="Output JSON lines")
    watch.add_argument("--compact", action="store_true", help="Use compact watch output")
    watch.add_argument("--ignore-terminal", action="store_true", help="Skip terminal app contexts while watching")

    sub.add_parser("watch-events", help="Watch app/window changes using AppleScript polling")
    sub.add_parser("doctor", help="Check local MQ Mirror runtime dependencies")
    sub.add_parser("version", help="Print MQ Mirror version")

    args = parser.parse_args()
    as_json = bool(getattr(args, "global_json", False) or getattr(args, "json", False))

    if args.command is None:
        list_topics(as_json)
        if as_json:
            return 0
        print()
        print("Examples:")
        print("  mqmirror network")
        print("  mqmirror show settings general")
        print("  mqmirror search network")
        print("  mqmirror copy settings network 2")
        print("  mqmirror run settings general 1 --confirm")
        print("  mqmirror inspect")
        print("  mqmirror watch")
        return 0

    if args.command == "list":
        list_topics(as_json)
        return 0

    if args.command == "show":
        return show_topic(args.category, args.topic, as_json)

    if args.command == "search":
        return search_library(args.query, as_json)

    if args.command == "copy":
        return copy_command(args.category, args.topic, args.index)

    if args.command == "run":
        return run_command(args.category, args.topic, args.index, args.confirm, args.allow_modifies)

    if args.command == "explain":
        return explain_command(args.raw_command)

    if args.command == "inspect":
        return inspect_command(as_json)

    if args.command == "watch":
        return watch_apps(args.interval, as_json, args.compact, args.ignore_terminal)

    if args.command == "watch-events":
        return watch_app_events()

    if args.command == "doctor":
        return doctor()

    if args.command == "version":
        print(f"mqmirror {VERSION}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
