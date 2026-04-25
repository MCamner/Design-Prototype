# MQ Mirror

GUI actions → terminal command equivalents.

A macOS command-line prototype that helps translate common GUI actions into matching terminal commands.

---

## Concept

MQ Mirror answers a simple question:

> If I do this in the GUI, what is the equivalent terminal command?

It combines:

- a GUI-to-CLI command library
- safe copy/run helpers
- frontmost app/window inspection
- compact watch mode for context changes
- runtime checks for local dependencies

---

## Run

Use the wrapper from the repository root:

```bash
tools/mqmirror/mqmirror list
```

Or run the Python file directly:

```bash
python3 tools/mqmirror/gui_to_cli.py list
```

If the launcher is on your `PATH`, use:

```bash
mqmirror list
mqmirror inspect
mqmirror watch --compact --ignore-terminal
```

---

## Quick shortcuts

```bash
tools/mqmirror/mqmirror network
tools/mqmirror/mqmirror battery
tools/mqmirror/mqmirror finder
tools/mqmirror/mqmirror privacy
tools/mqmirror/mqmirror keyboard
tools/mqmirror/mqmirror trackpad
```

These shortcut commands map to the underlying command library.

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

```bash
tools/mqmirror/mqmirror copy settings network 2
tools/mqmirror/mqmirror run settings general 1
tools/mqmirror/mqmirror run settings general 1 --confirm
```

Commands marked as `modifies` are blocked by default unless explicitly allowed.

---

## Context inspection

```bash
tools/mqmirror/mqmirror inspect
tools/mqmirror/mqmirror inspect --json
tools/mqmirror/mqmirror watch --interval 1
tools/mqmirror/mqmirror watch --interval 1 --compact
tools/mqmirror/mqmirror watch --compact --ignore-terminal
```

Stop watch mode with `Ctrl+C`.

Use `--ignore-terminal` when running watch mode from Terminal, iTerm, VS Code,
Warp, or Ghostty. It suppresses updates caused by the terminal itself becoming
the frontmost app.

---

## Runtime checks

```bash
tools/mqmirror/mqmirror version
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

On Swedish macOS, check:

- `Systeminställningar → Integritet och säkerhet → Hjälpmedel`
- `Systeminställningar → Integritet och säkerhet → Automatisering`

Allow the app that actually runs the command. If you run from the built-in
Terminal, allow `Terminal`. If you run from an integrated terminal, allow
`Visual Studio Code`, `Code`, or the relevant terminal app.

If `inspect` shows error `-10827`, quit and reopen the terminal app after
changing permissions, then test again:

```bash
mqmirror inspect
```

For a clean live view while clicking around in other apps:

```bash
mqmirror watch --compact --ignore-terminal
```

When browser context is available, MQ Mirror can suggest commands such as:

```bash
open 'https://example.com'
curl -I 'https://example.com'
```

---

## Direction

MQ Mirror is a prototype for learning and documenting how common macOS GUI actions map to terminal commands.

The long-term direction is:

- GUI action → CLI equivalent
- context-aware command suggestions
- safer command execution
- structured command libraries for macOS administration
