# Certificate Expiry Timeline

Certificate expiry risk dashboard for local macOS data, fleet data, or embedded sample data.

The timeline helps spot expired, critical, warning, notice, and healthy certificates across machines and sites.

---

## Quick start

Open directly in a browser:

```text
docs/Certificate Expiry Timeline.html
```

If no live source is available, the dashboard uses sample data.

---

## Live data sources

The dashboard tries these sources automatically:

| Source | URL | Provider |
|--------|-----|----------|
| Fleet Collector | `http://127.0.0.1:38766/fleet` | `helper/fleet_collector.py` |
| macOS Agent | `http://127.0.0.1:38764/status` | `helper/macos_agent.py` |

Start the macOS agent:

```bash
python3 helper/macos_agent.py
```

Start the fleet collector:

```bash
python3 helper/fleet_collector.py
```

---

## Dashboard features

| Feature | Description |
|---------|-------------|
| Expiry status | Groups certificates by expired, critical, warning, notice, OK, and unknown |
| Timeline view | Shows upcoming certificate expirations over time |
| Source/site context | Displays which machine or site a certificate belongs to |
| Filtering/sorting | Helps isolate urgent certificate work |
| Sample fallback | Works without live agents |

---

## Related files

```text
docs/Certificate Expiry Timeline.html
docs/macOS Enterprise Dashboard.html
docs/Fleet Command Center.html
helper/macos_agent.py
helper/fleet_collector.py
```
