# macOS Enterprise Dashboard

Security and compliance dashboard for enterprise-managed Macs.  
Evaluates controls against the **CIS macOS Benchmark Level 1** and displays results in a single-page report — live from the machine or from sample data.

---

## What it checks

| ID       | Control                         | Severity | CIS Reference |
|----------|---------------------------------|----------|---------------|
| SEC-001  | FileVault disk encryption       | Critical | CIS 2.6.1     |
| SEC-002  | System Integrity Protection     | Critical | CIS 5.1.1     |
| SEC-003  | Gatekeeper                      | High     | CIS 2.5.2     |
| SEC-004  | Application Firewall            | High     | CIS 2.6.2     |
| SEC-005  | Firewall stealth mode           | Medium   | CIS 2.6.3     |
| SEC-006  | Automatic security updates      | High     | CIS 1.1.3     |
| SEC-007  | Critical updates auto-install   | High     | CIS 1.1.4     |
| SEC-008  | Automatic update check          | Medium   | CIS 1.1.1     |
| ID-001   | SSH remote login disabled       | High     | CIS 2.3.3     |
| ID-002   | Auto-login disabled             | Critical | CIS 2.3.1     |
| ID-003   | Screen lock with password       | High     | CIS 2.4.3     |
| ID-004   | Screen lock delay ≤ 5 min       | Medium   | CIS 2.4.4     |
| MDM-001  | MDM enrolled                    | High     | Enterprise    |
| MDM-002  | Device supervised               | Medium   | Enterprise    |

Each failed check shows an expandable **remediation step** directly in the UI.

---

## Quick start

### Option A — Sample data (no agent needed)

Open the dashboard directly in a browser:

```
docs/macOS Enterprise Dashboard.html
```

The page loads with realistic sample data and an amber **"Sample data"** indicator. All sections and checks are fully functional.

---

### Option B — Live data from your Mac

#### 1. Start the agent

Open a terminal in the project root and run:

```bash
python3 helper/macos_agent.py
```

For full data (MDM profiles, FileVault status, user accounts):

```bash
sudo python3 helper/macos_agent.py
```

You should see:

```
macOS Enterprise Agent
───────────────────────────────────────────
API:      http://127.0.0.1:38764/status
Refresh:  http://127.0.0.1:38764/refresh
Interval: 300s
```

The agent collects data immediately on start, then re-collects every 5 minutes.

#### 2. Open the dashboard

```
docs/macOS Enterprise Dashboard.html
```

The header switches to a green **"Live · agent"** indicator. The dashboard shows your machine's real hostname, model, macOS version, and actual check results.

#### 3. Verify the agent is running

```bash
curl http://127.0.0.1:38764/status
```

---

## Dashboard sections

### Compliance Score
Circular gauge (0–100) showing the percentage of active checks that pass. Color coded: green ≥ 80, amber ≥ 55, red < 55.

### Compliance Checks
All 14 CIS checks grouped by severity. Click any failed check to expand its remediation instruction.

### Security Controls
Detailed view of each security setting — FileVault, SIP, Gatekeeper, Firewall, XProtect version, and auto-update policy.

### Identity & Access
SSH status, auto-login, screen lock settings, and a table of all local user accounts with admin/standard role.

### Device Management
MDM enrollment and supervision status, MDM server, and a list of all installed configuration profiles.

### Network
All network interfaces with IP addresses and connection status, active SSID, DNS servers.

### Software Updates
Pending macOS/app updates and date of last installed update.

### Certificates
System keychain certificates with days-remaining countdown. Color coded: green > 60 days, amber ≤ 60 days, red = expired.

---

## Agent reference

### Data sources

| Data                  | macOS command                          | Requires sudo |
|-----------------------|----------------------------------------|---------------|
| FileVault status      | `fdesetup status`                      | No            |
| SIP status            | `csrutil status`                       | No            |
| Gatekeeper            | `spctl --status`                       | No            |
| Firewall              | `socketfilterfw --getglobalstate`      | No            |
| macOS version         | `sw_vers`                              | No            |
| Hardware info         | `system_profiler SPHardwareDataType`   | No            |
| Local users           | `dscl . list /Users`                   | Recommended   |
| Admin group members   | `dscl . read /Groups/admin`            | Recommended   |
| SSH status            | `systemsetup -getremotelogin`          | Yes           |
| Screen lock settings  | `defaults read com.apple.screensaver`  | No            |
| MDM enrollment        | `profiles status -type enrollment`     | Yes           |
| Installed profiles    | `profiles list -all`                   | Yes           |
| Software updates      | `softwareupdate --list`                | No            |
| Network interfaces    | `networksetup -listallhardwareports`   | No            |
| System certificates   | `security find-certificate`            | No            |

### API endpoints

| Endpoint   | Description                          |
|------------|--------------------------------------|
| `/status`  | Full JSON payload                    |
| `/refresh` | Triggers an immediate re-collection  |

### Ports

| Port  | Component      |
|-------|----------------|
| 38764 | macOS Agent    |
| 38765 | Client Readiness Agent (other tool) |
| 38766 | Fleet Collector (other tool)        |

---

## Troubleshooting

**Dashboard shows "Sample data" even though the agent is running**  
Check that the agent is listening on port 38764:
```bash
curl http://127.0.0.1:38764/status
```
If the browser blocks `localhost` requests from a local file, serve the `docs/` folder with any static file server and open the dashboard from that local server. For example:
```bash
cd docs
python3 -m http.server 8000
```
Then open `http://localhost:8000/macOS%20Enterprise%20Dashboard.html`.

**MDM / profiles show no data**  
Run the agent with `sudo`. The `profiles` command requires elevated privileges.

**`csrutil` / SIP shows unknown**  
SIP status can only be read from the OS itself, not from a virtual machine. This is expected on VMs.

**SSH status shows unknown**  
`systemsetup -getremotelogin` requires sudo on some macOS versions.

---

## File structure

```
design-prototyp/
├── docs/
│   └── macOS Enterprise Dashboard.html   ← dashboard (no build step)
├── helper/
│   └── macos_agent.py                    ← data collector agent
```

---

## Related prototypes

- `docs/Certificate Expiry Timeline.html` can read certificate data from the macOS agent on port `38764`.
- `docs/Fleet Command Center.html` is the fleet-level view for readiness data from multiple clients.
- `docs/Client Readiness Dashboard.html` is the single-client readiness view for Citrix/thin-client scenarios.

---

*Author: Mattias Camner*
