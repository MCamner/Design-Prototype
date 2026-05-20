# Safe Sharing

Design-Prototype is safe to browse in demo mode, but live helper agents can expose local machine and fleet details. Treat live output as private unless it has been reviewed or redacted.

## Sensitive fields

Live helper output may include:

- hostname
- serial number
- IP addresses
- usernames
- local paths
- certificate subjects and issuers
- installed software names
- MDM/profile identifiers
- site or fleet names

## Redact macOS agent output

Use the redaction helper before pasting macOS Enterprise Agent output into issues, docs, or chat:

```bash
curl -s http://127.0.0.1:38764/status \
  | python3 tools/redact-macos-agent-status.py
```

Save a redacted snapshot:

```bash
curl -s http://127.0.0.1:38764/status \
  | python3 tools/redact-macos-agent-status.py \
  > redacted-macos-status.json
```

## Safe to share

Usually safe:

- GitHub Pages links
- screenshots using bundled demo data
- redacted JSON from helper agents
- command output from `--sample` modes
- browser console errors without host/user identifiers
- baseline names from bundled sample files

## Do not share publicly

Do not paste these into GitHub issues:

- raw `/status` output from live agents
- real serial numbers
- real usernames
- internal IP addresses
- client names or site names
- certificate subjects from production environments
- screenshots showing real endpoint identifiers

## Issue checklist

Before opening an issue:

1. Reproduce with demo data when possible.
2. Remove or redact hostnames, serials, usernames, and IP addresses.
3. Include the prototype name and browser.
4. Include the helper command only if it does not expose private data.
5. Attach redacted output, not raw live output.
