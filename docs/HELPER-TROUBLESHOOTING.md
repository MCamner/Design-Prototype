# Helper Agent Troubleshooting

The browser prototypes work in demo mode without helpers. Use this guide when a
dashboard should show live data but still appears to be using bundled samples.

## Quick checks

| Helper | Command | Health URL |
| --- | --- | --- |
| macOS Enterprise Agent | `python3 helper/macos_agent.py` | `http://127.0.0.1:38764/status` |
| Client Readiness Agent | `python3 helper/client_readiness_agent.py` | `http://127.0.0.1:38765/status` |
| Fleet Collector | `python3 helper/fleet_collector.py` | `http://127.0.0.1:38766/status` |
| MQ Mirror | `./tools/mqmirror/start.sh` | `http://127.0.0.1:7070` |
| MQ Client Optimizer | `python3 tools/mq-client-optimizer/mq_client_optimizer.py serve` | `http://127.0.0.1:38865/healthz` |

## Common symptoms

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Dashboard shows `IGEL-CLIENT-01` | Demo fallback is active | Start the relevant helper and refresh |
| Browser cannot fetch helper data | Helper is not running or port differs | Open the health URL directly |
| macOS posture fields are incomplete | Basic mode lacks privileged data | Run `sudo python3 helper/macos_agent.py` only if you need MDM/profile/user data |
| Fleet rows are offline | `helper/fleet_clients.json` points at unreachable clients | Confirm each client has readiness agent port `38765` open locally or on the expected host |
| MQ Mirror sees no GUI context | macOS permissions are missing | Grant Accessibility or Automation permission to the terminal app running MQ Mirror |

## Validation commands

```bash
python3 tools/check-public-docs.py
bash tools/check-frontdoor.sh
bash tools/smoke-check.sh
```

## Safe debugging

Do not paste raw live `/status` output into public issues. Use the redaction
helper for macOS agent output and prefer reproducing issues with bundled sample
data.
