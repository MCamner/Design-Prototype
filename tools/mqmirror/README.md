# MQ Mirror

GUI actions → terminal command equivalents.

A macOS prototype that helps translate common GUI actions into matching terminal commands.

## Run

```bash
python3 tools/mqmirror/gui_to_cli.py list
```

## Examples

```bash
python3 tools/mqmirror/gui_to_cli.py show settings general
python3 tools/mqmirror/gui_to_cli.py show settings network
python3 tools/mqmirror/gui_to_cli.py search wifi
python3 tools/mqmirror/gui_to_cli.py copy settings network 2
python3 tools/mqmirror/gui_to_cli.py run settings general 1
python3 tools/mqmirror/gui_to_cli.py run settings general 1 --confirm
python3 tools/mqmirror/gui_to_cli.py show settings network --json
python3 tools/mqmirror/gui_to_cli.py watch
```

## Modes

- `list` — show available GUI areas
- `show` — show terminal equivalents for a GUI area
- `search` — search the command library
- `copy` — copy a command to clipboard
- `run` — run a selected command safely
- `watch` — watch app launch/switch events
- `--json` — output machine-readable data where supported

## Direction

MQ Mirror is a prototype for learning and documenting how common macOS GUI actions map to terminal commands.
