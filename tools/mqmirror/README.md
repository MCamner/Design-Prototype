# MQ Mirror

GUI actions → terminal command equivalents.

A macOS prototype that helps translate common GUI actions into matching terminal commands.

---

## Concept

MQ Mirror is a small command-line companion for macOS.

It helps answer:

> “If I do this in the GUI, what is the equivalent terminal command?”

It combines:

- a GUI-to-CLI command library
- safe copy/run helpers
- frontmost app/window inspection
- watch mode for app/window context changes

---

## Run

```bash
tools/mqmirror/mqmirror list
```

Or run the Python file directly:

```bash
python3 tools/mqmirror/gui_to_cli.py list
```

---

## Quick examples

```bash
tools/mqmirror/mqmirror network
tools/mqmirror/mqmirror battery
tools/mqmirror/mqmirror finder
tools/mqmirror/mqmirror privacy
```

---

## Command library

```bash
tools/mqmirror/mqmirror list
tools/mqmirror/mqmirror show settings general
tools/mqmirror/mqmirror show settings network
tools/mqmirror/mqmirror search wifi
tools/mqmirror/mqmirror show settings network --json
```

---

## Copy and run

Copy a command to clipboard:

```bash
tools/mqmirror/mqmirror copy settings network 2
```

Dry-run a command:

```bash
tools/mqmirror/mqmirror run settings general 1
```

Run a safe command:

```bash
tools/mqmirror/mqmirror run settings general 1 --confirm
```

Commands marked as `modifies` are blocked by default unless explicitly allowed.

---

## Context inspection

Inspect the current frontmost app/window:

```bash
tools/mqmirror/mqmirror inspect
```

JSON output:

```bash
tools/mqmirror/mqmirror inspect --json
```

Watch context changes:

```bash
tools/mqmirror/mqmirror watch --interval 1
```

Compact watch mode:

```bash
tools/mqmirror/mqmirror watch --interval 1 --compact
```

Stop watch mode with `Ctrl+C`.

---

## Runtime checks

Show version:

```bash
tools/mqmirror/mqmirror version
```

Check local runtime dependencies:

```bash
tools/mqmirror/mqmirror doctor
```

---

## Modes

- `list` — show available GUI areas
- `show` — show terminal equivalents for a GUI area
- `search` — search the command library
- `copy` — copy a command to clipboard
- `run` — run a selected command safely
- `inspect` — inspect the frontmost app/window and suggest terminal equivalents
- `watch` — watch frontmost app/window context and suggest commands when it changes
- `watch-events` — app launch/switch event watcher using PyObjC
- `doctor` — check runtime dependencies
- `version` — show current MQ Mirror version

---

## App context inspection

`inspect` and `watch` use macOS AppleScript/System Events to read:

- frontmost app
- active window title
- Finder path/selection
- browser tab URL where available

macOS may ask for Accessibility or Automation permission the first time this runs.

---

## Direction

MQ Mirror is a prototype for learning and documenting how common macOS GUI actions map to terminal commands.

The long-term direction is:

- GUI action → CLI equivalent
- context-aware command suggestions
- safer command execution
- structured command libraries for macOS administration
