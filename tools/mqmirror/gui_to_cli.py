#!/usr/bin/env python3
"""
MQ Mirror — GUI actions → terminal command equivalents.

Modes:
  python3 tools/mqmirror/gui_to_cli.py list
  python3 tools/mqmirror/gui_to_cli.py show settings general
  python3 tools/mqmirror/gui_to_cli.py search network
  python3 tools/mqmirror/gui_to_cli.py watch
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[38;5;82m"
CYAN = "\033[38;5;87m"
AMBER = "\033[38;5;220m"
RED = "\033[38;5;203m"
MUTED = "\033[38;5;244m"


Command = Tuple[str, str, str]  # command, description, safety


COMMAND_LIBRARY: Dict[str, Dict[str, object]] = {
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
    print(f"{BOLD}{CYAN}MQ Mirror — {title}{RESET}")
    print(f"{BOLD}{CYAN}════════════════════════════════════════════════════{RESET}")


def safety_badge(level: str) -> str:
    if level == "safe":
        return f"{GREEN}safe{RESET}"
    if level == "modifies":
        return f"{AMBER}modifies{RESET}"
    if level == "dangerous":
        return f"{RED}dangerous{RESET}"
    return f"{MUTED}{level}{RESET}"


def print_command(command: str, description: str, safety: str = "safe") -> None:
    print(f"  {GREEN}❯{RESET} {BOLD}{command}{RESET}")
    print(f"    {MUTED}{description} · {safety_badge(safety)}{RESET}")


def list_topics() -> None:
    header("command library")
    for key, value in sorted(COMMAND_LIBRARY.items()):
        print(f"{GREEN}❯{RESET} {key}")
        print(f"  {MUTED}{value['gui']}{RESET}")


def show_topic(category: str, topic: str) -> int:
    key = f"{category}.{topic}"
    item = COMMAND_LIBRARY.get(key)

    if not item:
        print(f"{RED}No mapping found for: {key}{RESET}")
        print()
        print("Try:")
        list_topics()
        return 1

    header(str(item["gui"]))
    print()
    for command, description, safety in item["commands"]:  # type: ignore[index]
        print_command(command, description, safety)
    return 0


def search_library(query: str) -> int:
    query_l = query.lower()
    matches = []

    for key, item in COMMAND_LIBRARY.items():
        haystack = f"{key} {item['gui']} " + " ".join(
            f"{cmd} {desc}" for cmd, desc, _ in item["commands"]  # type: ignore[index]
        )
        if query_l in haystack.lower():
            matches.append((key, item))

    header(f"search: {query}")

    if not matches:
        print(f"{AMBER}No matches.{RESET}")
        return 1

    for key, item in matches:
        print()
        print(f"{GREEN}❯ {key}{RESET}")
        print(f"  {MUTED}{item['gui']}{RESET}")
        for command, description, safety in item["commands"]:  # type: ignore[index]
            print_command(command, description, safety)

    return 0


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
                print_command(cmd, desc)

        def appLaunched_(self, notification):
            app = notification.userInfo().get("NSWorkspaceApplicationKey")
            if app is None:
                return

            name = app.localizedName()
            mapped = APP_MAPPINGS.get(name)
            if mapped:
                cmd, desc = mapped
                print(f"\n{DIM}{now()}{RESET} {GREEN}[app launched]{RESET} {BOLD}{name}{RESET}")
                print_command(cmd, desc)

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
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List available GUI-to-CLI topics")

    show = sub.add_parser("show", help="Show commands for a GUI area")
    show.add_argument("category", help="Example: settings, finder, apps, developer")
    show.add_argument("topic", help="Example: general, network, files, common")

    search = sub.add_parser("search", help="Search command library")
    search.add_argument("query")

    sub.add_parser("watch", help="Watch active app changes and suggest commands")

    args = parser.parse_args()

    if args.command is None:
        list_topics()
        print()
        print("Examples:")
        print("  python3 tools/mqmirror/gui_to_cli.py show settings general")
        print("  python3 tools/mqmirror/gui_to_cli.py search network")
        print("  python3 tools/mqmirror/gui_to_cli.py watch")
        return 0

    if args.command == "list":
        list_topics()
        return 0

    if args.command == "show":
        return show_topic(args.category, args.topic)

    if args.command == "search":
        return search_library(args.query)

    if args.command == "watch":
        return watch_apps()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
