# Sample Data

Design-Prototype keeps public demos usable without live infrastructure by
bundling small sample data sets directly in the HTML prototypes or helper tools.

## Public sample identity

The main demo identity is:

```text
IGEL-CLIENT-01
```

If a dashboard shows `IGEL-CLIENT-01`, it is using demo data. That is expected
for GitHub Pages and safe screenshots.

## Where sample data lives

| Area | Sample source | Notes |
| --- | --- | --- |
| Client Readiness Dashboard | Embedded in `docs/Client Readiness Dashboard.html` | Thin-client and Citrix-style readiness checks |
| Fleet Command Center | Embedded in `docs/Fleet Command Center.html` plus `helper/fleet_clients.json` | Fleet rows can be replaced with local helper endpoints |
| macOS Enterprise Dashboard | Embedded in `docs/macOS Enterprise Dashboard.html` | Uses representative macOS posture values |
| Certificate Expiry Timeline | Embedded dashboard examples | Useful for renewal-risk screenshots |
| MQ Client Optimizer | `--sample` mode and bundled baselines | Produces console, JSON, or HTML reports |
| MQ Site Fix Advisor | Example and pasted HTML flows | No live helper required |
| MQ Asset Downloader | URL or pasted HTML fallback | No live helper required |

## Generate sample optimizer output

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
  --baseline macos-enterprise-cis-lite \
  --sample
```

## Sharing rule

Use bundled sample data for public issues and screenshots. If you need to share
live helper data, redact it first:

```bash
curl -s http://127.0.0.1:38764/status \
  | python3 tools/redact-macos-agent-status.py \
  | python3 -m json.tool
```
