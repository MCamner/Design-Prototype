# Design Prototype

Interactive web prototypes for enterprise client platforms.

Author: Mattias Camner

## Overview

This repository contains browser-based prototypes for exploring endpoint
readiness, macOS compliance, fleet visibility, certificate expiry risk, and
lightweight asset recovery workflows.

The prototypes are intentionally lightweight:

- Single-file HTML apps in `docs/`
- No build step
- Demo/sample data when no local helper is available
- Optional Python helper agents for live local or fleet data
- Browser-only utility flows where possible

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

### MQ Asset Downloader

File: `docs/MQ Asset Downloader.html`

Scans a public page URL for image assets, shows selectable previews in a
Photoshop-inspired workspace, and downloads selected images as a zip archive
with a manifest.

Supports a broad "all websites / other builders" mode plus a narrower
Squarespace asset filter. It can discover common image sources such as `img`,
`srcset`, lazy-load data attributes, metadata images, links, and CSS background
images when present in the fetched or pasted HTML.

### MQ Site Fix Advisor v1.1.0

File: `docs/MQ Site Fix Advisor.html`

Audits a public page URL or pasted HTML for common SEO, image, link, and CSS
issues. Results are shown in an older vSphere-inspired console layout with
severity, location, practical fix guidance, platform notes, and exportable JSON.

Checks include missing titles/descriptions, H1 problems, Open Graph gaps,
missing image alt text, insecure HTTP resources, placeholder links, fixed-width
CSS, removed focus outlines, extreme z-index values, and small font sizes.

**Generate fix** — after a scan, generates a corrected `<head>` block (or full
HTML) with all automatically fixable issues applied, ready to copy and paste.

**Guide** — in-tool step-by-step guide accessible via the `?` button in the
top bar.

Open the landing page:

```text
docs/index.html
```

Or open any prototype HTML file directly in a browser.

## Quick Start

Demo Mode

All dashboards can be opened directly from docs/ and will fall back to
embedded demo/sample data when live data is unavailable.

docs/Client Readiness Dashboard.html
docs/Fleet Command Center.html
docs/macOS Enterprise Dashboard.html
docs/Certificate Expiry Timeline.html
docs/MQ Asset Downloader.html
docs/MQ Site Fix Advisor.html

Client Readiness Live Data

Use this agent for:

docs/Client Readiness Dashboard.html

Start the Client Readiness Agent from the project root:

python3 helper/client_readiness_agent.py

It exposes live readiness data on:

http://127.0.0.1:38765/status

Test it:

curl -s http://127.0.0.1:38765/status | python3 -m json.tool

If the dashboard shows IGEL-CLIENT-01, it is using demo/sample data.
That usually means the Client Readiness Agent is not running, the browser cannot
reach it, or the dashboard has fallen back to embedded sample data.

macOS Live Data

Use this agent for:

docs/macOS Enterprise Dashboard.html
docs/Certificate Expiry Timeline.html

Start the macOS Enterprise Agent from the project root:

python3 helper/macos_agent.py

It exposes live macOS data on:

http://127.0.0.1:38764/status

For fuller MDM/profile/user data:

sudo python3 helper/macos_agent.py

Test it:

curl -s http://127.0.0.1:38764/status | python3 -m json.tool

Fleet Live Data

Use this collector for:

docs/Fleet Command Center.html

Edit:

helper/fleet_clients.json

Start the collector:

python3 helper/fleet_collector.py

Open:

http://localhost:38766

Live fleet data requires each configured client to expose a Client Readiness
Agent on port 38765. The included helper/client_readiness_agent.py provides
that endpoint for local testing and supported macOS/Linux clients.

Safe Sharing

Agent output may include hostname, serial number, local IP addresses, user names,
certificate subjects, or other local machine details.

Before sharing status output publicly, redact it:

curl -s http://127.0.0.1:38764/status | python3 tools/redact-macos-agent-status.py

Do not paste raw agent output into public GitHub issues, README files,
screenshots, or discussions.

Ports

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
│   ├── MQ Asset Downloader.html
│   ├── MQ Site Fix Advisor.html
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

The MQ Asset Downloader and MQ Site Fix Advisor are documented inline in their
tool UIs and run as standalone browser pages.

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

### MQ Client Optimizer v1

`tools/mq-client-optimizer/` contains a safe, template-based optimizer analyzer
for IGEL and macOS clients. It evaluates bundled baselines for IGEL OS 12 +
Citrix, macOS + Citrix, and macOS enterprise CIS-style compliance, then writes
console, JSON, or HTML reports. A browser app is available at
`docs/MQ Client Optimizer.html`.

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py list-baselines
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze --baseline macos-enterprise-cis-lite --sample
python3 tools/mq-client-optimizer/mq_client_optimizer.py serve
```

## Notes

This is a design and architecture exploration, not a finished product. Some
live modes depend on helper agents that may be local-only, external, or future
work.

The Client Readiness Agent is intentionally lightweight; IGEL UMS integration
and managed remediation flows are future work.

## License

MIT License
