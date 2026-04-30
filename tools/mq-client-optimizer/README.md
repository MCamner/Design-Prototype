# MQ Client Optimizer v1

Template-based optimizer and readiness analyzer for IGEL and macOS clients.

This first version is intentionally safe. It supports `analyze`, JSON/HTML
reports, bundled baselines, sample data, local JSON input, and agent URLs. It
does not yet apply endpoint changes.

## Baselines

| Baseline | Platform | Purpose |
| --- | --- | --- |
| `igel-os12-citrix` | IGEL OS 12 | Citrix readiness and certificate checks |
| `macos-citrix` | macOS | Citrix Workspace readiness |
| `macos-enterprise-cis-lite` | macOS | CIS-style enterprise compliance |

## Usage

List baselines:

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py list-baselines
```

Analyze with built-in sample data:

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
  --baseline macos-enterprise-cis-lite \
  --sample
```

Analyze live macOS data from the existing macOS agent:

```bash
python3 helper/macos_agent.py
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
  --baseline macos-enterprise-cis-lite \
  --agent-url http://127.0.0.1:38764/status \
  --output-json reports/macos-optimizer-report.json \
  --output-html reports/macos-optimizer-report.html
```

Analyze an IGEL/readiness JSON export:

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
  --baseline igel-os12-citrix \
  --input client.json \
  --output-json reports/igel-optimizer-report.json
```

Print sample input shape for a baseline:

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py sample-data \
  --baseline igel-os12-citrix
```

## Report Statuses

| Status | Meaning |
| --- | --- |
| `PASS` | The check matches the baseline |
| `WARN` | The check passes but needs attention soon, such as certificate expiry |
| `FAIL` | The check does not match the baseline |
| `UNKNOWN` | The value was missing or unavailable |
| `UNSUPPORTED` | The input agent does not expose the required capability |

## v1 Scope

Included:

- Baseline-driven evaluator
- IGEL OS 12 + Citrix readiness baseline
- macOS + Citrix readiness baseline
- macOS enterprise CIS-lite baseline
- JSON input, sample input, and HTTP agent input
- Console, JSON, and HTML reports

Not included yet:

- IGEL UMS API integration
- macOS remediation execution
- Rollback history
- Per-client readiness agent implementation

