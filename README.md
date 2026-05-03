# Design Prototype

Interactive web prototypes and macOS developer tools.

Author: Mattias Camner

## Overview

Browser-based prototypes for endpoint readiness, macOS compliance, fleet
visibility, certificate expiry risk, and asset workflows — plus local macOS
developer tooling.

The prototypes are intentionally lightweight:

- Single-file HTML apps in `docs/`
- No build step
- Demo/sample data when no local helper is available
- Optional Python helper agents for live local or fleet data

---

## Prototypes

### Client Readiness Dashboard

File: `docs/Client Readiness Dashboard.html`

Validates a single client against readiness profiles for Citrix and thin-client
scenarios.

Live data: uses `helper/client_readiness_agent.py` on port `38765`.

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

### MQ Fleet Report

File: `docs/MQ Fleet Report.html`

Fleet-wide report view. Standalone browser page, no helper required.

### MQ Asset Downloader

File: `docs/MQ Asset Downloader.html`

Scans a public page URL for image assets, shows selectable previews in a
Photoshop-inspired workspace, and downloads selected images as a zip archive
with a manifest.

Supports a broad "all websites / other builders" mode plus a narrower
Squarespace asset filter.

### MQ Site Fix Advisor

File: `docs/MQ Site Fix Advisor.html`

Audits a public page URL or pasted HTML for common SEO, image, link, and CSS
issues. Results shown in a console layout with severity, location, fix guidance,
platform notes, and exportable JSON.

**Generate fix** — after a scan, generates a corrected `<head>` block with all
automatically fixable issues applied.

---

## Quick Start

### Demo mode

All dashboards open directly from `docs/` and fall back to embedded demo data
when no live helper is running.

```text
docs/Client Readiness Dashboard.html
docs/Fleet Command Center.html
docs/macOS Enterprise Dashboard.html
docs/Certificate Expiry Timeline.html
docs/MQ Asset Downloader.html
docs/MQ Site Fix Advisor.html
```

### Client Readiness live data

```bash
python3 helper/client_readiness_agent.py
# → http://127.0.0.1:38765/status
curl -s http://127.0.0.1:38765/status | python3 -m json.tool
```

If the dashboard shows `IGEL-CLIENT-01`, it is using demo data.

### macOS live data

```bash
python3 helper/macos_agent.py          # basic
sudo python3 helper/macos_agent.py     # MDM / profile / user data
# → http://127.0.0.1:38764/status
curl -s http://127.0.0.1:38764/status | python3 -m json.tool
```

### Fleet live data

Edit `helper/fleet_clients.json`, then:

```bash
python3 helper/fleet_collector.py
# → http://localhost:38766
```

Each configured client must expose a Client Readiness Agent on port `38765`.

### Safe sharing

Agent output may include hostname, serial, IP addresses, usernames, and
certificate subjects. Redact before sharing:

```bash
curl -s http://127.0.0.1:38764/status | python3 tools/redact-macos-agent-status.py
```

### Ports

| Port    | Component                  |
|---------|----------------------------|
| `7070`  | MQ Mirror live server      |
| `38764` | macOS Enterprise Agent     |
| `38765` | Client Readiness Agent     |
| `38766` | Fleet Collector            |

---

## Tools

### MQ Mirror — GUI→CLI Companion

`tools/mqmirror/` watches your macOS GUI context and streams the equivalent
terminal commands in real-time to a local web page.

**Start (recommended):**

```bash
./tools/mqmirror/start.sh
```

Opens `docs/handoff.html` automatically and starts the live server on
`http://127.0.0.1:7070`.

**Manual:**

```bash
python3 tools/mqmirror/gui_to_cli.py watch --compact --ignore-terminal
```

**Handoff UI** (`docs/handoff.html`):

- Live command cards streamed via SSE from the Python server
- Search, category filter chips, pin commands, export session as `.sh`
- ▶ Run — executes command in the selected terminal (Terminal.app, iTerm2, Warp, Ghostty)
- ■ Stop — gracefully shuts down the server
- Command history persists across restarts (`tools/mqmirror/mq-history.json`)
- Tab title flashes `(●)` when new commands arrive while the tab is in the background

**CLI commands:**

```bash
python3 tools/mqmirror/gui_to_cli.py list
python3 tools/mqmirror/gui_to_cli.py inspect
python3 tools/mqmirror/gui_to_cli.py search network
python3 tools/mqmirror/gui_to_cli.py show settings network
python3 tools/mqmirror/gui_to_cli.py watch --compact --no-serve
```

### MQ Client Optimizer

`tools/mq-client-optimizer/` evaluates bundled baselines for IGEL OS 12 +
Citrix, macOS + Citrix, and macOS enterprise CIS-style compliance. Outputs
console, JSON, or HTML reports. Browser app: `docs/MQ Client Optimizer.html`.

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py list-baselines
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
    --baseline macos-enterprise-cis-lite --sample
python3 tools/mq-client-optimizer/mq_client_optimizer.py serve
```

### Draw.io Generator

`tools/drawio-generator/` is a local Flask server that generates Draw.io
diagrams from natural language descriptions via an LLM backend.

```bash
cd tools/drawio-generator
./start.sh
# → http://127.0.0.1:5001
```

Requires a `.env` file — copy `.env.example` and fill in your API key.

---

## Repository Structure

```text
design-prototyp/
├── docs/
│   ├── index.html
│   ├── handoff.html                      ← MQ Mirror live UI
│   ├── handoff-standalone.html
│   ├── Client Readiness Dashboard.html
│   ├── Fleet Command Center.html
│   ├── macOS Enterprise Dashboard.html
│   ├── Certificate Expiry Timeline.html
│   ├── MQ Fleet Report.html
│   ├── MQ Asset Downloader.html
│   ├── MQ Site Fix Advisor.html
│   ├── MQ Client Optimizer.html
│   ├── README-Client-Readiness-Dashboard.md
│   ├── README-Fleet-Command-Center.md
│   ├── README-macOS-Enterprise-Dashboard.md
│   └── README-Certificate-Expiry-Timeline.md
├── helper/
│   ├── client_readiness_agent.py
│   ├── fleet_collector.py
│   ├── fleet_clients.json
│   └── macos_agent.py
└── tools/
    ├── redact-macos-agent-status.py
    ├── drawio-generator/
    │   ├── server.py
    │   ├── start.sh
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── templates/index.html
    ├── mq-client-optimizer/
    │   ├── mq_client_optimizer.py
    │   ├── README.md
    │   └── baselines/
    └── mqmirror/
        ├── gui_to_cli.py
        ├── gui_to_cli_orginal.py
        ├── start.sh
        ├── mqmirror
        └── README.md
```

## Notes

This is a design and architecture exploration, not a finished product. Some
live modes depend on helper agents that may be local-only, external, or future
work.

The Client Readiness Agent is intentionally lightweight; IGEL UMS integration
and managed remediation flows are future work.

## License

MIT License