# Client Readiness Dashboard

Single-client readiness dashboard for Citrix, thin-client, kiosk, and macOS access scenarios.

The dashboard evaluates a client against embedded readiness profiles and shows pass/fail/warn/unsupported checks with supporting evidence.

---

## Quick start

Open directly in a browser:

```text
docs/Client Readiness Dashboard.html
```

If no helper agent is running, the dashboard uses sample data.

---

## Live helper mode

The dashboard tries to read live data from:

```text
http://127.0.0.1:38765/status
```

Start the included helper agent:

```bash
python3 helper/client_readiness_agent.py
```

For a one-shot JSON payload:

```bash
python3 helper/client_readiness_agent.py --once
```

---

## Supported profiles

Profiles are embedded in the HTML file.

Common profile IDs used by the related fleet dashboard:

| Profile ID | Description |
|------------|-------------|
| `igel-os12-citrix` | IGEL OS 12 + Citrix readiness |
| `elux7-citrix` | eLux 7 + Citrix readiness |
| `macos-citrix` | macOS + Citrix readiness |
| `kiosk` | Kiosk readiness |

---

## Dashboard features

| Feature | Description |
|---------|-------------|
| Readiness scorecards | Total/pass/fail/warn/unsupported summary |
| Profile selector | Switches between embedded readiness profiles |
| Evidence view | Shows check-level details and remediation context |
| Capability warning | Highlights unsupported checks when helper capabilities are missing |
| Export | Generates readiness report output |
| Sample mode | Works without a helper agent |

---

## Related files

```text
docs/Client Readiness Dashboard.html
docs/Fleet Command Center.html
helper/client_readiness_agent.py
helper/fleet_collector.py
```
