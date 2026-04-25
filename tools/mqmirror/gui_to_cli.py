#!/usr/bin/env python3
"""
MQ Mirror v0.3 — GUI actions → terminal command equivalents.

Examples:
  mqmirror list
  mqmirror show settings general
  mqmirror search network
  mqmirror copy settings network 2
  mqmirror run settings general 1 --confirm
  mqmirror show settings network --json
  mqmirror watch
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from typing import Any, Dict, Tuple

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


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def header(title: str) -> None:
    print(f"{BOLD}{CYAN}════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}MQ Mirror v0.3 — {title}{RESET}")
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

    subprocess.run(["pbcopy"], input=cmd, text=True, check=True)
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


def watch_apps() -> int:
    try:
        import objc
        from AppKit import (
            NSWorkspace,
            NSWorkspaceDidActivateApplicationNotification,
            NSWorkspaceDidLaunchApplicationNotification,
            NSWorkspaceDidTerminateApplicationNotification,
        )
        from Foundation import NSObject, NSRunLoop, NSDate
    except ImportError:
        print(f"{RED}Missing dependencies.{RESET}")
        print("Install:")
        print("  pip install pyobjc-framework-Cocoa")
        return 1

    class WorkspaceObserver(NSObject):
        def init(self):
            self = objc.super(WorkspaceObserver, self).init()
            if self is None:
                return None

            nc = NSWorkspace.sharedWorkspace().notificationCenter()
            nc.addObserver_selector_name_object_(
                self, "appActivated:", NSWorkspaceDidActivateApplicationNotification, None
            )
            nc.addObserver_selector_name_object_(
                self, "appLaunched:", NSWorkspaceDidLaunchApplicationNotification, None
            )
            nc.addObserver_selector_name_object_(
                self, "appTerminated:", NSWorkspaceDidTerminateApplicationNotification, None
            )
            self._last_app = None
            return self

        def appActivated_(self, notification):
            app = notification.userInfo().get("NSWorkspaceApplicationKey")
            if app is None:
                return

            name = app.localizedName()
            if name == self._last_app:
                return

            self._last_app = name
            mapped = APP_MAPPINGS.get(name)
            if mapped:
                cmd, desc = mapped
                print(f"\n{DIM}{now()}{RESET} {CYAN}[app activated]{RESET} {BOLD}{name}{RESET}")
                print_command(1, cmd, desc, "safe")

        def appLaunched_(self, notification):
            app = notification.userInfo().get("NSWorkspaceApplicationKey")
            if app is None:
                return

            name = app.localizedName()
            mapped = APP_MAPPINGS.get(name)
            if mapped:
                cmd, desc = mapped
                print(f"\n{DIM}{now()}{RESET} {GREEN}[app launched]{RESET} {BOLD}{name}{RESET}")
                print_command(1, cmd, desc, "safe")

        def appTerminated_(self, notification):
            app = notification.userInfo().get("NSWorkspaceApplicationKey")
            if app is None:
                return

            name = app.localizedName()
            print(f"\n{DIM}{now()}{RESET} {AMBER}[app terminated]{RESET} {BOLD}{name}{RESET}")

    header("watch mode")
    print(f"{MUTED}Watching app launch/switch events. Press Ctrl+C to stop.{RESET}")

    _observer = WorkspaceObserver.alloc().init()

    try:
        loop = NSRunLoop.currentRunLoop()
        while True:
            loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.2))
    except KeyboardInterrupt:
        print(f"\n{GREEN}Stopped.{RESET}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mqmirror",
        description="GUI actions → terminal command equivalents for macOS.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON where supported")
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

    sub.add_parser("watch", help="Watch active app changes and suggest commands")

    args = parser.parse_args()

    if args.command is None:
        list_topics(args.json)
        print()
        print("Examples:")
        print("  mqmirror show settings general")
        print("  mqmirror search network")
        print("  mqmirror copy settings network 2")
        print("  mqmirror run settings general 1 --confirm")
        print("  mqmirror watch")
        return 0

    if args.command == "list":
        list_topics(args.json)
        return 0

    if args.command == "show":
        return show_topic(args.category, args.topic, args.json)

    if args.command == "search":
        return search_library(args.query, args.json)

    if args.command == "copy":
        return copy_command(args.category, args.topic, args.index)

    if args.command == "run":
        return run_command(args.category, args.topic, args.index, args.confirm, args.allow_modifies)

    if args.command == "explain":
        return explain_command(args.raw_command)

    if args.command == "watch":
        return watch_apps()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
