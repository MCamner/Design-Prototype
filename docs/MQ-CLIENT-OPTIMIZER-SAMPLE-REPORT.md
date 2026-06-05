# MQ Client Optimizer Sample Report

This is the expected shape of the console report generated from bundled sample
data:

```bash
python3 tools/mq-client-optimizer/mq_client_optimizer.py analyze \
  --baseline macos-enterprise-cis-lite \
  --sample
```

```text
MQ Client Optimizer v1
Baseline: macos-enterprise-cis-lite - macOS enterprise CIS-lite compliance
Target:   MacBook-Pro-Enterprise
Summary:  score=95 pass=19 warn=0 fail=1 unknown=0 unsupported=0

[PASS       ] SEC-001          FileVault disk encryption
[PASS       ] SEC-002          System Integrity Protection
[PASS       ] SEC-003          Gatekeeper enabled
[PASS       ] SEC-004          Application Firewall enabled
[FAIL       ] SEC-005          Firewall stealth mode
  evidence:    Expected True, got False
  remediation: Run: sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on.
[PASS       ] SEC-006          Automatic security updates
[PASS       ] SEC-007          Critical updates auto-install
[PASS       ] SEC-008          Automatic update check
[PASS       ] ID-001           Remote Login SSH disabled
[PASS       ] ID-002           Auto-login disabled
[PASS       ] ID-003           Screen lock with password
[PASS       ] ID-004           Screen lock delay max 5 minutes
[PASS       ] ID-005           Guest account disabled
[PASS       ] ID-006           Login window shows name and password fields
[PASS       ] SHR-001          File Sharing disabled
[PASS       ] SHR-002          Screen Sharing disabled
[PASS       ] SHR-003          Remote Management disabled
[PASS       ] SHR-004          AirDrop disabled
[PASS       ] MDM-001          MDM enrolled
[PASS       ] MDM-002          Device supervised
```

The sample intentionally includes one failed check so reviewers can see
remediation text and report severity behavior.
