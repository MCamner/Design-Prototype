# Design Prototype

![Version](https://img.shields.io/badge/version-0.1.4-blue)
![Status](https://img.shields.io/badge/status-active%20prototype-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-blueviolet)

Browser-based enterprise validation lab for turning rough endpoint, compliance,
readiness, and fleet-management ideas into visible, testable, and shareable
prototypes.

Not one single app — a collection of practical tools for testing enterprise
client workflows before they become production systems.

---

## Quick Start

All dashboards open in the browser with no setup. They fall back to embedded
demo data when no live helper is running.

```bash
./tools/run-demo.sh client     # Client Readiness Dashboard
./tools/run-demo.sh macos      # macOS Enterprise Dashboard
./tools/run-demo.sh fleet      # Fleet Command Center
./tools/run-demo.sh optimizer  # MQ Client Optimizer
./tools/run-demo.sh mqmirror   # MQ Mirror
```

Or open directly:

```bash
open "docs/Client Readiness Dashboard.html"
open "docs/macOS Enterprise Dashboard.html"
open "docs/Fleet Command Center.html"
```

If you see `IGEL-CLIENT-01` in a dashboard, it is using demo data — that is expected.

Live demo: [mcamner.github.io/Design-Prototype](https://mcamner.github.io/Design-Prototype/)

---

## What's in here

| Component | Status | Live helper | Demo fallback |
| --- | --- | --- | --- |
| Client Readiness Dashboard | Active | Yes | Yes |
| Fleet Command Center | Active | Yes | Yes |
| macOS Enterprise Dashboard | Active | Yes | Yes |
| Certificate Expiry Timeline | Active | Partial | Yes |
| MQ Mirror | Active tool | Yes | No |
| MQ Client Optimizer | Active tool | Yes | Yes |
| MQ Site Fix Advisor | Prototype | No | Yes |
| MQ Asset Downloader | Prototype | No | Yes |

---

## Live data setup

### macOS Enterprise Dashboard

```bash
python3 helper/macos_agent.py          # basic
sudo python3 helper/macos_agent.py     # MDM / profile / user data
# → http://127.0.0.1:38764/status
```

### Client Readiness Dashboard

```bash
python3 helper/client_readiness_agent.py
# → http://127.0.0.1:38765/status
```

### Fleet Command Center

Edit `helper/fleet_clients.json`, then:

```bash
python3 helper/fleet_collector.py
# → http://localhost:38766
```

Each configured client must expose a Client Readiness Agent on port `38765`.

### Ports

| Port    | Component              |
| ------- | ---------------------- |
| `7070`  | MQ Mirror live server  |
| `38764` | macOS Enterprise Agent |
| `38765` | Client Readiness Agent |
| `38766` | Fleet Collector        |

---

## Tools

### MQ Mirror — GUI→CLI Companion

Watches your macOS GUI context and streams equivalent terminal commands in
real-time to a local web page.

```bash
./tools/mqmirror/start.sh
# → opens docs/handoff.html at http://127.0.0.1:7070
```

CLI commands:

```bash
python3 tools/mqmirror/gui_to_cli.py list
python3 tools/mqmirror/gui_to_cli.py watch --compact --ignore-terminal
```

### MQ Client Optimizer

Evaluates bundled baselines for IGEL OS 12 + Citrix, macOS + Citrix, and
macOS enterprise CIS-style compliance.

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py list-baselines
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
    --baseline macos-enterprise-cis-lite --sample
```

### Draw.io Generator

Local Flask server that generates Draw.io diagrams from natural language
descriptions via an LLM backend.

```bash
cd tools/drawio-generator
./start.sh
# → http://127.0.0.1:5001
```

Requires a `.env` file — copy `.env.example` and fill in your API key.

---

## Repository structure

```text
Design-Prototype/
├── docs/
│   ├── index.html
│   ├── ARCHITECTURE.md
│   ├── SAFE-SHARING.md
│   ├── handoff.html                      ← MQ Mirror live UI
│   ├── Client Readiness Dashboard.html
│   ├── Fleet Command Center.html
│   ├── macOS Enterprise Dashboard.html
│   ├── Certificate Expiry Timeline.html
│   ├── MQ Fleet Report.html
│   ├── MQ Asset Downloader.html
│   ├── MQ Site Fix Advisor.html
│   └── MQ Client Optimizer.html
├── helper/
│   ├── client_readiness_agent.py
│   ├── fleet_collector.py
│   ├── fleet_clients.json
│   └── macos_agent.py
└── tools/
    ├── redact-macos-agent-status.py
    ├── drawio-generator/
    ├── mq-client-optimizer/
    └── mqmirror/
```

---

## Safe sharing

Agent output may include hostname, serial, IP addresses, usernames, and
certificate subjects. Redact before sharing:

```bash
curl -s http://127.0.0.1:38764/status | python3 tools/redact-macos-agent-status.py
```

See [docs/SAFE-SHARING.md](docs/SAFE-SHARING.md) for the full redaction guide.

---

## Project docs

| Doc | Purpose |
| --- | --- |
| [GitHub Pages](https://mcamner.github.io/Design-Prototype/) | Product-style front door |
| [Demo Gallery](docs/DEMO-GALLERY.md) | Visual overview of the prototypes |
| [Architecture](docs/ARCHITECTURE.md) | Helper agents, ports, and data flow |
| [Safe Sharing](docs/SAFE-SHARING.md) | What to redact before sharing output |
| [Project Map](docs/PROJECT-MAP.md) | How the repo is structured |
| [Project Status](docs/PROJECT-STATUS.md) | Active, rough, and next-step areas |
| [Roadmap](docs/ROADMAP.md) | Planned hardening and next milestones |

---

## Notes

This is a design and architecture exploration, not a finished product. Some
live modes depend on helper agents that may be local-only, external, or future
work.

---

## Author

Mattias Camner — Infrastructure / Platform Architect

---

## License

MIT
