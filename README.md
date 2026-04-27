# Design Prototype

Interactive web prototypes for enterprise client platforms.

Author: Mattias Camner

## Overview

This repository contains browser-based prototypes for exploring endpoint
readiness, macOS compliance, fleet visibility, and certificate expiry risk.

The prototypes are intentionally lightweight:

- Single-file HTML apps in `docs/`
- No build step
- Demo/sample data when no local helper is available
- Optional Python helper agents for live local or fleet data

## Prototypes

### Client Readiness Dashboard

File: `docs/Client Readiness Dashboard.html`

Validates a single client against readiness profiles for Citrix and thin-client
scenarios.

Live data: expects a Client Readiness Agent on port `38765`. That agent is
referenced by the UI but is not currently included in this repo.

### Fleet Command Center

File: `docs/Fleet Command Center.html`

Aggregates many client readiness states into a fleet view with filters, site
breakdown, detail panel, and activity feed.

Live data: uses `helper/fleet_collector.py` on port `38766`, which polls client
agents on port `38765`.

### macOS Enterprise Dashboard

File: `docs/macOS Enterprise Dashboard.html`

Shows macOS security and compliance posture with CIS-style checks, local users,
MDM, network, software updates, and certificates.

Live data: uses `helper/macos_agent.py` on port `38764`.

### Certificate Expiry Timeline

File: `docs/Certificate Expiry Timeline.html`

Visualizes certificate expiry risk across local macOS data or fleet data.

Live data: reads from the Fleet Collector (`38766`) and/or macOS Agent (`38764`)
when available.

### Squarespace Asset Downloader

File: `docs/Squarespace Asset Downloader.html`

Scans a public Squarespace page URL for image assets, shows selectable previews,
and downloads selected images as a zip archive with a manifest.

Open the landing page:

```text
docs/index.html
```

Or open any prototype HTML file directly in a browser.

## Quick Start

### Demo Mode

All dashboards can be opened directly from `docs/` and will fall back to
embedded demo/sample data when live data is unavailable.

```text
docs/Client Readiness Dashboard.html
docs/Fleet Command Center.html
docs/macOS Enterprise Dashboard.html
docs/Certificate Expiry Timeline.html
docs/Squarespace Asset Downloader.html
```

### macOS Live Data

Run the local macOS agent from the project root:

```bash
python3 helper/macos_agent.py
```

For fuller MDM/profile/user data:

```bash
sudo python3 helper/macos_agent.py
```

Then open:

```text
docs/macOS Enterprise Dashboard.html
docs/Certificate Expiry Timeline.html
```

### Fleet Live Data

Edit:

```text
helper/fleet_clients.json
```

Start the collector:

```bash
python3 helper/fleet_collector.py
```

Open:

```text
http://localhost:38766
```

Live fleet data requires each configured client to expose a Client Readiness
Agent on port `38765`. The collector is included in this repo; the per-client
readiness agent is currently not included.

## Ports

| Port | Component |
| --- | --- |
| `38764` | macOS Enterprise Agent |
| `38765` | Client Readiness Agent expected by readiness/fleet prototypes |
| `38766` | Fleet Collector |

## Repository Structure

```text
design-prototyp/
├── docs/
│   ├── index.html
│   ├── Client Readiness Dashboard.html
│   ├── Fleet Command Center.html
│   ├── macOS Enterprise Dashboard.html
│   ├── Certificate Expiry Timeline.html
│   ├── Squarespace Asset Downloader.html
│   ├── README-Client-Readiness-Dashboard.md
│   ├── README-Fleet-Command-Center.md
│   ├── README-macOS-Enterprise-Dashboard.md
│   └── README-Certificate-Expiry-Timeline.md
├── helper/
│   ├── fleet_collector.py
│   ├── fleet_clients.json
│   └── macos_agent.py
└── tools/
    └── mqmirror/
        ├── README.md
        ├── gui_to_cli.py
        └── mqmirror
```

## Documentation

- `docs/README-Client-Readiness-Dashboard.md`
- `docs/README-Fleet-Command-Center.md`
- `docs/README-macOS-Enterprise-Dashboard.md`
- `docs/README-Certificate-Expiry-Timeline.md`
- `tools/mqmirror/README.md`

## Tools

### MQ Mirror

`tools/mqmirror/` contains a small macOS CLI prototype that maps common GUI
actions to equivalent terminal commands.

Run from the repo:

```bash
python3 tools/mqmirror/gui_to_cli.py list
```

If the launcher has been added to your `PATH`, run:

```bash
mqmirror list
mqmirror inspect
mqmirror watch --compact --ignore-terminal --limit 4
```

More details:

- `tools/mqmirror/README.md`
- `tools/mqmirror/gui_to_cli.py`
- `tools/mqmirror/mqmirror`

## Notes

This is a design and architecture exploration, not a finished product. Some
live modes depend on helper agents that may be local-only, external, or future
work.

Known gap: `helper/client_readiness_agent.py` is referenced by the Client
Readiness and Fleet prototypes but is not currently present in this repository.

## License

MIT License
