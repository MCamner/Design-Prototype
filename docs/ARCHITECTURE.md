# Architecture

Design-Prototype is a browser-first enterprise validation lab. It turns rough endpoint, compliance, readiness, and fleet-management ideas into visible, testable, and shareable prototypes.

## Purpose

The repo exists to make enterprise client workflows easier to evaluate before they become production systems. Most prototypes are intentionally lightweight: a static browser UI, demo fallback data, and optional local helper agents for live signals.

## Browser-first prototype model

The main demos live as single-file HTML apps under `docs/`. They can be opened directly from GitHub Pages or from the filesystem.

This keeps demos easy to share:

- no build step for the dashboard prototypes
- no account or cloud service required for demo mode
- no helper process required for fallback data
- clear handoff between visual design and future production implementation

## Local helper agents

Some dashboards can read live local data when helper agents are running:

| Helper | Path | Port | Purpose |
|---|---|---:|---|
| macOS Enterprise Agent | `helper/macos_agent.py` | `38764` | Local macOS posture, users, MDM, updates, network, certificates |
| Client Readiness Agent | `helper/client_readiness_agent.py` | `38765` | Endpoint readiness status for client validation demos |
| Fleet Collector | `helper/fleet_collector.py` | `38766` | Aggregates configured client readiness agents |
| MQ Mirror | `tools/mqmirror/start.sh` | `7070` | Streams GUI-to-CLI command handoff cards |
| MQ Client Optimizer | `tools/mq-client-optimizer/mq_client_optimizer.py serve` | `38865` | Baseline readiness API and local browser tool |
| Draw.io Generator | `tools/drawio-generator/start.sh` | `5001` | Local diagram generation service |

## Data flow

Typical live flow:

```text
local endpoint or sample input
-> helper agent or static demo data
-> browser dashboard
-> operator reads status, risk, and next actions
```

Fleet flow:

```text
client readiness agents
-> fleet_collector.py
-> Fleet Command Center / Certificate Expiry Timeline / MQ Fleet Report
```

Tool flow:

```text
baseline/sample/pasted JSON
-> MQ Client Optimizer
-> console, JSON, or HTML report
```

## Ports

| Port | Component |
|---:|---|
| `7070` | MQ Mirror live server |
| `38764` | macOS Enterprise Agent |
| `38765` | Client Readiness Agent |
| `38766` | Fleet Collector |
| `38865` | MQ Client Optimizer local API |
| `5001` | Draw.io Generator |

## Demo mode vs live mode

Demo mode uses embedded or bundled sample data. It is safe for public screenshots and GitHub Pages.

Live mode reads local machine or fleet information from helper agents. Live mode can expose hostnames, serial numbers, IP addresses, usernames, and certificate subjects. Redact before sharing outputs.

## Safe sharing model

Public docs, screenshots, and GitHub issues should use demo data or redacted live data.

Use:

```bash
curl -s http://127.0.0.1:38764/status \
  | python3 tools/redact-macos-agent-status.py
```

See [SAFE-SHARING.md](SAFE-SHARING.md) for what is safe to paste into issues.

## Future production hardening

Before turning any prototype into production software:

- replace demo assumptions with explicit schemas
- add authentication for live helper endpoints
- define data retention and log policies
- package helper agents with launchd/service management
- add browser and Python test coverage
- document threat model and deployment boundaries
- separate local-only tools from shareable public demos
