# Fleet Command Center

Real-time readiness dashboard for thin-client fleets: IGEL OS, eLux, macOS, and
kiosk clients.

It is the fleet companion to `docs/Client Readiness Dashboard.html`: one screen
for many clients instead of one screen for one client.

## Overview

Without a collector, the dashboard opens in demo mode with simulated clients.

With a collector, it shows real clients, evaluates checks using the same rules
as Client Readiness Dashboard, and auto-refreshes every 30 seconds.

## Quick Start: Demo Mode

Open directly in a browser:

```text
docs/Fleet Command Center.html
```

The dashboard detects that no collector is running and switches to demo mode.

## Quick Start: Live Mode

### Requirements

- Python 3.8 or newer
- No external Python packages
- Client Readiness Agent on each client at `http://<client-ip>:38765/status`

The fleet collector is included in this repo. The per-client
`helper/client_readiness_agent.py` is referenced by the dashboard but is not
currently present. Use demo mode, provide a compatible external agent, or add
that helper before expecting live client data.

### Configure Clients

Edit `helper/fleet_clients.json`:

```json
[
  { "ip": "10.10.4.87", "hostname": "IGEL-001", "site": "Stockholm HQ" },
  { "ip": "10.10.4.88", "hostname": "IGEL-002", "site": "Stockholm HQ" },
  { "ip": "10.10.4.89", "hostname": "ELUX-001", "site": "Goteborg Office" },
  { "ip": "10.10.4.90", "hostname": "MAC-001", "site": "Remote" }
]
```

| Field | Required | Description |
| --- | --- | --- |
| `ip` | Yes | Client IP address |
| `hostname` | Yes | Display name, overridden by agent when available |
| `site` | No | Office or location label |

### Start the Collector

Run on a machine in the same network as the clients:

```bash
python3 helper/fleet_collector.py
```

Expected output:

```text
Fleet Collector
Dashboard:  http://localhost:38766
API:        http://localhost:38766/fleet
Konfig:     helper/fleet_clients.json
Pollintervall: 30s  |  Timeout: 3s/klient
```

### Open the Dashboard

From the collector machine:

```text
http://localhost:38766
```

From another machine in the network:

```text
http://<collector-ip>:38766
```

The header switches from demo mode to live collector mode once the collector is
reachable.

## Architecture

```text
Client Agent (:38765/status)
  -> fleet_collector.py (:38766/fleet)
  -> Fleet Command Center (browser)
```

- The collector polls all clients concurrently.
- Polling uses up to 32 worker threads and a 3 second timeout per client.
- The dashboard tries `/fleet` first when served by the collector.
- When opened as a local file, it also tries `http://127.0.0.1:38766/fleet`.
- Check evaluation happens in the browser.

## Collector API

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Serves Fleet Command Center HTML |
| `/fleet` | GET | JSON with all client statuses |
| `/fleet/reload` | GET | Triggers an immediate re-poll |
| `/fleet/clients` | GET | Returns current `fleet_clients.json` |

### `/fleet` Response Format

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
      "data": {}
    }
  ]
}
```

## Supported Profiles

| Profile ID | Label | Source agent required |
| --- | --- | --- |
| `igel-os12-citrix` | IGEL OS 12 + Citrix | Yes |
| `elux7-citrix` | eLux 7 + Citrix | Yes |
| `macos-citrix` | macOS + Citrix | Yes |
| `kiosk` | Kiosk | Yes |

The profile is read from the agent's `meta.profile` field. The collector config
can also specify a `profile` field per client as fallback.

### Expected Client Agent Payload

The collector passes each client's `data` object through to the dashboard. For
best results, the client agent should return JSON shaped like the Client
Readiness Dashboard sample data:

```json
{
  "meta": {
    "hostname": "IGEL-001",
    "profile": "igel-os12-citrix",
    "agent_version": "1.0.0",
    "capabilities": ["network", "processes", "certificates"]
  },
  "network": {},
  "processes": {},
  "certificates": {}
}
```

## Dashboard Features

| Feature | Description |
| --- | --- |
| Fleet Score | Percent of active clients with READY status |
| Status badges | READY, WARN, FAIL, CRITICAL, and OFFLINE |
| Critical alert banner | Appears when any client is FAIL or CRITICAL |
| Grid/List view | Toggle between card grid and table |
| Filters | Filter by status, profile, site, or hostname |
| By Site breakdown | Per-office readiness progress bars |
| Client detail panel | Full check results with evidence |
| Activity feed | Real-time log of status changes |
| Manual refresh | Refresh button in footer for live mode |

## File Structure

```text
design-prototyp/
docs/
  Fleet Command Center.html
  Client Readiness Dashboard.html
helper/
  fleet_collector.py
  fleet_clients.json
```

Missing from the current repo: `helper/client_readiness_agent.py`.

## Ports

| Port | Component |
| --- | --- |
| `38765` | Client Readiness Agent per client |
| `38766` | Fleet Collector on central machine |

Author: Mattias Camner
