# macOS Enterprise Dashboard

Security and compliance dashboard for enterprise-managed Macs.

It evaluates controls against a CIS macOS Benchmark Level 1 style baseline and
displays results in a single-page report, either live from the Mac or from
sample data.

## What It Checks

| ID | Control | Severity | Reference |
| --- | --- | --- | --- |
| `SEC-001` | FileVault disk encryption | Critical | CIS 2.6.1 |
| `SEC-002` | System Integrity Protection | Critical | CIS 5.1.1 |
| `SEC-003` | Gatekeeper | High | CIS 2.5.2 |
| `SEC-004` | Application Firewall | High | CIS 2.6.2 |
| `SEC-005` | Firewall stealth mode | Medium | CIS 2.6.3 |
| `SEC-006` | Automatic security updates | High | CIS 1.1.3 |
| `SEC-007` | Critical updates auto-install | High | CIS 1.1.4 |
| `SEC-008` | Automatic update check | Medium | CIS 1.1.1 |
| `ID-001` | SSH remote login disabled | High | CIS 2.3.3 |
| `ID-002` | Auto-login disabled | Critical | CIS 2.3.1 |
| `ID-003` | Screen lock with password | High | CIS 2.4.3 |
| `ID-004` | Screen lock delay max 5 min | Medium | CIS 2.4.4 |
| `MDM-001` | MDM enrolled | High | Enterprise |
| `MDM-002` | Device supervised | Medium | Enterprise |

Each failed check shows an expandable remediation step directly in the UI.

## Quick Start

### Option A: Sample Data

Open the dashboard directly in a browser:

```text
docs/macOS Enterprise Dashboard.html
```

The page loads with sample data and an amber sample data indicator.

### Option B: Live Data From Your Mac

Start the agent from the project root:

```bash
python3 helper/macos_agent.py
```

For full data, including MDM profiles, FileVault status, and user accounts:

```bash
sudo python3 helper/macos_agent.py
```

Expected output:

```text
macOS Enterprise Agent
API:      http://127.0.0.1:38764/status
Refresh:  http://127.0.0.1:38764/refresh
Interval: 300s
```

The agent collects data immediately on start, then re-collects every 5 minutes.

Open the dashboard:

```text
docs/macOS Enterprise Dashboard.html
```

The header switches to live agent mode when the agent is reachable.

Verify the agent:

```bash
curl http://127.0.0.1:38764/status
```

## Dashboard Sections

### Compliance Score

Circular gauge from 0 to 100 showing the percentage of active checks that pass.
Color coding: green at 80 or higher, amber at 55 or higher, red below 55.

### Compliance Checks

All 14 checks grouped by severity. Failed checks can be expanded to show
remediation guidance.

### Security Controls

Detailed view of FileVault, SIP, Gatekeeper, Firewall, XProtect version, and
auto-update policy.

### Identity And Access

SSH status, auto-login, screen lock settings, and local user accounts with
admin or standard role.

### Device Management

MDM enrollment and supervision status, MDM server, and installed configuration
profiles.

### Network

Network interfaces, IP addresses, connection status, active SSID, and DNS
servers.

### Software Updates

Pending macOS/app updates and date of last installed update.

### Certificates

System keychain certificates with days-remaining countdown. Color coding:
green above 60 days, amber at 60 days or less, red for expired certificates.

## Agent Reference

### Data Sources

| Data | macOS command | Requires sudo |
| --- | --- | --- |
| FileVault status | `fdesetup status` | No |
| SIP status | `csrutil status` | No |
| Gatekeeper | `spctl --status` | No |
| Firewall | `socketfilterfw --getglobalstate` | No |
| macOS version | `sw_vers` | No |
| Hardware info | `system_profiler SPHardwareDataType` | No |
| Local users | `dscl . list /Users` | Recommended |
| Admin group members | `dscl . read /Groups/admin` | Recommended |
| SSH status | `systemsetup -getremotelogin` | Yes |
| Screen lock settings | `defaults read com.apple.screensaver` | No |
| MDM enrollment | `profiles status -type enrollment` | Yes |
| Installed profiles | `profiles list -all` | Yes |
| Software updates | `softwareupdate --list` | No |
| Network interfaces | `networksetup -listallhardwareports` | No |
| System certificates | `security find-certificate` | No |

### API Endpoints

| Endpoint | Description |
| --- | --- |
| `/status` | Full JSON payload |
| `/refresh` | Triggers an immediate re-collection |

### Ports

| Port | Component |
| --- | --- |
| `38764` | macOS Agent |
| `38765` | Client Readiness Agent used by other prototypes |
| `38766` | Fleet Collector used by other prototypes |

## Troubleshooting

### Dashboard Shows Sample Data

Check that the agent is listening on port `38764`:

```bash
curl http://127.0.0.1:38764/status
```

If the browser blocks `localhost` requests from a local file, serve the `docs/`
folder with any static file server:

```bash
cd docs
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/macOS%20Enterprise%20Dashboard.html
```

### MDM Or Profiles Show No Data

Run the agent with `sudo`. The `profiles` command requires elevated
privileges.

### SIP Shows Unknown

SIP status can only be read from the OS itself, not from a virtual machine.

### SSH Status Shows Unknown

`systemsetup -getremotelogin` requires sudo on some macOS versions.

## File Structure

```text
design-prototyp/
docs/
  macOS Enterprise Dashboard.html
helper/
  macos_agent.py
```

## Related Prototypes

- `docs/Certificate Expiry Timeline.html`
- `docs/Fleet Command Center.html`
- `docs/Client Readiness Dashboard.html`

Author: Mattias Camner
