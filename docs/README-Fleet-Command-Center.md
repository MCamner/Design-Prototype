# Fleet Command Center

Real-time readiness dashboard for thin-client fleets (IGEL OS, eLux, macOS, Kiosk).  
Companion to **Client Readiness Dashboard** — shows the whole fleet on one screen instead of one client at a time.

---

## Overview

```
┌─────────────────────────────────────────────────────┐
│  Fleet Command Center                               │
│  ○ Fleet Score  ○ Stats  ○ By Site                  │
│─────────────────────────────────────────────────────│
│  [IGEL-001 READY] [IGEL-002 WARN] [ELUX-001 FAIL]  │  ← client grid
│  [MAC-001 READY]  [KIOSK-001 OFFLINE] …             │
│─────────────────────────────────────────────────────│
│  Detail panel / Activity feed          (right side) │
└─────────────────────────────────────────────────────┘
```

**Without a collector** — opens in demo mode with 48 simulated clients and live animation.  
**With a collector** — shows real clients, evaluates checks using the same rules as Client Readiness Dashboard, auto-refreshes every 30 s.

---

## Quick start (demo mode)

Open directly in a browser — no server needed:

```
docs/Fleet Command Center.html
```

The dashboard detects that no collector is running and switches to demo mode (amber indicator).

---

## Quick start (live mode)

### Requirements

- Python 3.8+ (no external packages)
- Client Readiness Agent running on each client (`helper/client_readiness_agent.py`, port 38765)

### 1. Configure clients

Edit `helper/fleet_clients.json`:

```json
[
  { "ip": "10.10.4.87", "hostname": "IGEL-001", "site": "Stockholm HQ" },
  { "ip": "10.10.4.88", "hostname": "IGEL-002", "site": "Stockholm HQ" },
  { "ip": "10.10.4.89", "hostname": "ELUX-001", "site": "Göteborg Office" },
  { "ip": "10.10.4.90", "hostname": "MAC-001",  "site": "Remote" }
]
```

| Field      | Required | Description                        |
|------------|----------|------------------------------------|
| `ip`       | Yes      | Client IP address                  |
| `hostname` | Yes      | Display name (overridden by agent) |
| `site`     | No       | Office / location label            |

### 2. Start the collector

Run on any machine in the same network as the clients:

```bash
python3 helper/fleet_collector.py
```

```
Fleet Collector
───────────────────────────────────────────
Dashboard:  http://localhost:38766
API:        http://localhost:38766/fleet
Konfig:     helper/fleet_clients.json
Pollintervall: 30s  |  Timeout: 3s/klient
```

### 3. Open the dashboard

From the collector machine:
```
http://localhost:38766
```

From any other machine in the network:
```
http://<collector-ip>:38766
```

The header switches from **amber "Demo mode"** to **green "Live · collector"** once the collector is reachable.

---

## Architecture

```
┌──────────┐  :38765/status   ┌──────────────────┐  :38766/fleet   ┌──────────────────────┐
│  Client  │ ◄─────────────── │ fleet_collector   │ ◄────────────── │ Fleet Command Center │
│  Agent   │                  │ .py               │                 │ (browser)            │
└──────────┘  (poll every 30s)└──────────────────┘  (fetch every   └──────────────────────┘
                                                      30s)
```

- The collector polls all clients concurrently (up to 32 threads, 3 s timeout each)
- The dashboard tries `/fleet` first (relative — works when served by collector), then `http://127.0.0.1:38766/fleet` (direct — works when opened as a file on the same machine as the collector)
- Check evaluation happens in the browser using the same Eval engine as Client Readiness Dashboard

---

## Collector API

| Endpoint         | Method | Description                              |
|------------------|--------|------------------------------------------|
| `/`              | GET    | Serves Fleet Command Center HTML         |
| `/fleet`         | GET    | JSON with all client statuses            |
| `/fleet/reload`  | GET    | Triggers an immediate re-poll            |
| `/fleet/clients` | GET    | Returns current `fleet_clients.json`     |

### `/fleet` response format

```json
{
  "collected_at": "2026-04-22T10:00:00Z",
  "poll_count": 42,
  "clients": [
    {
      "ip": "10.10.4.87",
      "hostname": "IGEL-001",
      "site": "Stockholm HQ",
      "profile": "igel-os12-citrix",
      "agent_version": "2.3.0",
      "status": "online",
      "last_seen": "2026-04-22T09:59:55Z",
      "data": { ... }
    }
  ]
}
```

---

## Supported profiles

| Profile ID          | Label               | Source agent required |
|---------------------|---------------------|-----------------------|
| `igel-os12-citrix`  | IGEL OS 12 + Citrix | Yes                   |
| `elux7-citrix`      | eLux 7 + Citrix     | Yes                   |
| `macos-citrix`      | macOS + Citrix      | Yes                   |
| `kiosk`             | Kiosk               | Yes                   |

The profile is read from the agent's `meta.profile` field. The collector config can also specify a `profile` field per client as fallback.

---

## Dashboard features

| Feature              | Description                                             |
|----------------------|---------------------------------------------------------|
| Fleet Score          | % of active (non-offline) clients with READY status     |
| Status badges        | READY / WARN / FAIL / CRITICAL / OFFLINE                |
| Critical alert banner| Appears when any client is FAIL or CRITICAL             |
| Grid / List view     | Toggle between card grid and table                      |
| Filters              | By status, profile, site, or hostname search            |
| By Site breakdown    | Per-office readiness progress bars                      |
| Client detail panel  | Click any client → full check results with evidence     |
| Activity feed        | Real-time log of status changes                         |
| Manual refresh       | Refresh button in footer (live mode only)               |

---

## File structure

```
design-prototyp/
├── docs/
│   ├── Fleet Command Center.html      ← dashboard (single file, no build step)
│   └── Client Readiness Dashboard.html
├── helper/
│   ├── fleet_collector.py             ← central collector server
│   └── fleet_clients.json             ← client IP / hostname config
```

---

## Ports

| Port  | Component              |
|-------|------------------------|
| 38765 | Client Readiness Agent (per client) |
| 38766 | Fleet Collector (central machine)   |

---

*Author: Mattias Camner*
