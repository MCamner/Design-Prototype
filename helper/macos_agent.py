#!/usr/bin/env python3
"""
macOS Enterprise Agent
======================
Samlar säkerhets- och compliance-data från macOS och exponerar det
på http://127.0.0.1:38764/status

Användning:
  sudo python3 helper/macos_agent.py

Obs: Vissa kontroller (MDM-profiler, FileVault) kräver sudo.
     Kör utan sudo för en delmängd av data.
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import datetime
import http.server
import socketserver
import platform

PORT    = 38764
REFRESH = 300   # sekunder mellan automatisk datainsamling

_lock  = threading.Lock()
_cache = {}

# ── Hjälpfunktioner ──────────────────────────────────────────────────────────

def run(cmd, timeout=8):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
        )
        return result.stdout.strip()
    except Exception:
        return ''

def run_json(cmd, timeout=10):
    try:
        out = run(cmd, timeout=timeout)
        return json.loads(out)
    except Exception:
        return None

def read_default(domain, key):
    return run(f'defaults read "{domain}" "{key}" 2>/dev/null')

# ── Datainsamlare ─────────────────────────────────────────────────────────────

def collect_meta():
    sw = {}
    for line in run(['sw_vers']).splitlines():
        k, _, v = line.partition(':')
        sw[k.strip()] = v.strip()

    hw_json = run_json(['system_profiler', 'SPHardwareDataType', '-json'])
    hw = (hw_json or {}).get('SPHardwareDataType', [{}])[0]

    hostname = run(['hostname', '-s']) or run(['hostname'])

    return {
        'agent_version':  '1.0.0',
        'collected_at':   _utcnow(),
        'hostname':       hostname,
        'serial':         hw.get('serial_number', ''),
        'model':          hw.get('machine_model', '') or hw.get('_name', ''),
        'chip':           hw.get('chip_type', '') or hw.get('cpu_type', ''),
        'memory_gb':      _parse_memory(hw.get('physical_memory', '')),
        'macos_version':  sw.get('ProductVersion', ''),
        'macos_build':    sw.get('BuildVersion', ''),
        'macos_name':     sw.get('ProductName', ''),
    }


def collect_security():
    # FileVault
    fv_out     = run(['fdesetup', 'status'])
    fv_enabled = 'On' in fv_out

    # SIP
    sip_out     = run(['csrutil', 'status'])
    sip_enabled = 'enabled' in sip_out.lower() and 'disabled' not in sip_out.lower()

    # Gatekeeper
    gk_out     = run(['spctl', '--status'])
    gk_enabled = 'enabled' in gk_out.lower()

    # Firewall
    fw_path = '/usr/libexec/ApplicationFirewall/socketfilterfw'
    fw_out  = run([fw_path, '--getglobalstate'])
    fw_enabled = 'enabled' in fw_out.lower() or 'state = 1' in fw_out.lower()
    stealth_out  = run([fw_path, '--getstealthmode'])
    stealth_mode = 'enabled' in stealth_out.lower()
    block_all_out  = run([fw_path, '--getblockall'])
    block_all = 'enabled' in block_all_out.lower()

    # Secure boot / chip
    chip_out    = run('system_profiler SPHardwareDataType 2>/dev/null | grep "Chip"')
    apple_chip  = 'apple' in chip_out.lower()
    secure_boot = 'Full Security' if apple_chip else _get_secure_boot_intel()

    # XProtect version
    xp_version = run(
        'defaults read /Library/Apple/System/Library/CoreServices/XProtect.bundle'
        '/Contents/Resources/XProtect.meta Version 2>/dev/null'
    ) or run(
        'defaults read /System/Library/CoreServices/XProtect.bundle'
        '/Contents/Resources/XProtect.meta Version 2>/dev/null'
    )
    xp_date = _xprotect_date()

    # Automatic Updates
    au_domain = 'com.apple.SoftwareUpdate'
    auto_check    = read_default(au_domain, 'AutomaticCheckEnabled')   != '0'
    auto_download = read_default(au_domain, 'AutomaticDownload')        != '0'
    auto_macos    = read_default(au_domain, 'AutomaticallyInstallMacOSUpdates') == '1'
    auto_app      = read_default(au_domain, 'AutomaticallyInstallAppUpdates')  != '0'
    auto_security = read_default(au_domain, 'ConfigDataInstall')        != '0'
    critical_updates = read_default(au_domain, 'CriticalUpdateInstall') != '0'

    return {
        'filevault':   { 'enabled': fv_enabled,  'status': fv_out[:120] },
        'sip':         { 'enabled': sip_enabled,  'status': sip_out[:120] },
        'gatekeeper':  { 'enabled': gk_enabled,   'status': gk_out[:80] },
        'firewall': {
            'enabled':     fw_enabled,
            'stealth_mode': stealth_mode,
            'block_all':   block_all,
            'status':      fw_out[:80],
        },
        'secure_boot': { 'level': secure_boot, 'apple_chip': apple_chip },
        'xprotect':    { 'version': xp_version, 'last_update': xp_date },
        'auto_updates': {
            'automatic_check':             auto_check,
            'automatic_download':          auto_download,
            'automatic_install_macos':     auto_macos,
            'automatic_install_app':       auto_app,
            'automatic_install_security':  auto_security,
            'critical_updates':            critical_updates,
        },
    }


def collect_identity():
    # Local users (exclude system accounts)
    users_raw   = run("dscl . list /Users | grep -v '^_'").splitlines()
    system_accs = {'root','daemon','nobody','Guest'}
    users       = []

    admin_group = run("dscl . read /Groups/admin GroupMembership 2>/dev/null")
    admin_members = set(admin_group.replace('GroupMembership:', '').split())

    for u in users_raw:
        u = u.strip()
        if not u or u in system_accs:
            continue
        uid_raw = run(f'dscl . read /Users/{u} UniqueID 2>/dev/null')
        uid_match = re.search(r'\d+', uid_raw)
        uid = int(uid_match.group()) if uid_match else 0
        if uid < 500:
            continue
        realname = run(f'dscl . read /Users/{u} RealName 2>/dev/null').replace('RealName:\n', '').replace('RealName: ', '').strip()
        users.append({
            'name':     u,
            'fullname': realname or u,
            'admin':    u in admin_members,
            'uid':      uid,
        })

    # SSH
    ssh_out = run(['systemsetup', '-getremotelogin'])
    ssh_enabled = 'On' in ssh_out

    # Autologin
    autologin_user = run('defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser 2>/dev/null')
    autologin = bool(autologin_user)

    # Screen lock
    ask_pw       = run('defaults read com.apple.screensaver askForPassword 2>/dev/null')
    pw_delay_raw = run('defaults read com.apple.screensaver askForPasswordDelay 2>/dev/null')
    screen_lock  = ask_pw.strip() == '1'
    try:
        pw_delay = int(float(pw_delay_raw.strip()))
    except Exception:
        pw_delay = -1

    # Screen saver timeout (display sleep)
    idle_raw = run('pmset -g | grep displaysleep')
    idle_match = re.search(r'displaysleep\s+(\d+)', idle_raw)
    idle_minutes = int(idle_match.group(1)) if idle_match else -1

    return {
        'users':       users,
        'ssh_enabled': ssh_enabled,
        'autologin':   autologin,
        'screen_lock': {
            'enabled':           screen_lock,
            'delay_seconds':     pw_delay,
            'idle_minutes':      idle_minutes,
            'require_password':  screen_lock,
        },
    }


def collect_mdm():
    enrolled   = False
    supervised = False
    server     = ''
    dep        = False
    profiles   = []

    try:
        enroll_out = run(['profiles', 'status', '-type', 'enrollment'])
        enrolled   = 'Yes' in enroll_out or 'Enrolled via DEP' in enroll_out
        supervised = 'supervised' in enroll_out.lower()
        dep        = 'DEP' in enroll_out

        server_match = re.search(r'MDM server\s*:\s*(.+)', enroll_out)
        if server_match:
            server = server_match.group(1).strip()

        # Installed profiles
        prof_out = run(['profiles', 'list', '-all'])
        for line in prof_out.splitlines():
            line = line.strip()
            if not line or line.startswith('There are'):
                continue
            profiles.append({'name': line[:120]})
    except Exception:
        pass

    return {
        'enrolled':   enrolled,
        'supervised': supervised,
        'dep':        dep,
        'server':     server,
        'profiles':   profiles,
    }


def collect_software():
    # Pending updates
    updates_raw = run(['softwareupdate', '--list'], timeout=30)
    pending = []
    name_match = None
    for line in updates_raw.splitlines():
        line = line.strip()
        nm = re.match(r'\*\s+Label:\s+(.+)', line)
        if nm:
            name_match = nm.group(1).strip()
        size_m = re.search(r'Size:\s+([\d.]+\s*\w+)', line)
        if name_match and size_m:
            pending.append({'name': name_match, 'size': size_m.group(1)})
            name_match = None

    # Last software update
    last_update = run('defaults read /Library/Receipts/InstallHistory.plist 2>/dev/null | head -20')
    last_date = ''
    dm = re.search(r'(\d{4}-\d{2}-\d{2})', last_update)
    if dm:
        last_date = dm.group(1)

    return {
        'pending_updates': pending,
        'last_update':     last_date,
    }


def collect_network():
    interfaces = []

    # networksetup -listallhardwareports
    hw_ports = run(['networksetup', '-listallhardwareports'])
    port_blocks = re.split(r'\n\n+', hw_ports)

    for block in port_blocks:
        name_m  = re.search(r'Hardware Port:\s+(.+)', block)
        dev_m   = re.search(r'Device:\s+(\w+)', block)
        if not name_m or not dev_m:
            continue
        name   = name_m.group(1).strip()
        dev    = dev_m.group(1).strip()
        ip     = _get_interface_ip(dev)
        status = 'active' if ip else 'inactive'

        iface = {'name': name, 'device': dev, 'status': status}
        if ip:
            iface['ip'] = ip

        # SSID for Wi-Fi
        if 'wi-fi' in name.lower() or 'airport' in name.lower():
            ssid = run('/System/Library/PrivateFrameworks/Apple80211.framework'
                       '/Versions/Current/Resources/airport -I 2>/dev/null | grep " SSID"')
            ssid_m = re.search(r'SSID:\s+(.+)', ssid)
            if ssid_m:
                iface['ssid'] = ssid_m.group(1).strip()

        interfaces.append(iface)

    # VPN connections (from scutil)
    vpn_out = run('scutil --nc list 2>/dev/null')
    for line in vpn_out.splitlines():
        if 'Connected' in line:
            vpn_name_m = re.search(r'"([^"]+)"', line)
            name = vpn_name_m.group(1) if vpn_name_m else 'VPN'
            interfaces.append({'name': name, 'device': 'vpn', 'status': 'connected'})

    # DNS
    dns_raw = run('scutil --dns | grep "nameserver\[" | head -8')
    dns = list(dict.fromkeys(re.findall(r'[\d.]+', dns_raw)))

    # Proxy
    proxy_raw = run(['networksetup', '-getwebproxy', 'Wi-Fi'])
    proxy_on  = 'Yes' in proxy_raw

    return {
        'interfaces': interfaces[:10],
        'dns':        dns[:4],
        'proxy':      { 'enabled': proxy_on },
    }


def collect_certificates():
    certs = []
    raw = run('security find-certificate -a -p /Library/Keychains/System.keychain 2>/dev/null | '
              'openssl x509 -noout -subject -issuer -dates 2>/dev/null')
    # Parse blocks
    for block in raw.split('notBefore='):
        after_m = re.search(r'notAfter=(.+)', block)
        subj_m  = re.search(r'subject=(.+)', block)
        if not after_m:
            continue
        name = ''
        if subj_m:
            cn_m = re.search(r'CN\s*=\s*([^,\n]+)', subj_m.group(1))
            if cn_m:
                name = cn_m.group(1).strip()
        try:
            expiry_dt = datetime.datetime.strptime(after_m.group(1).strip(), '%b %d %H:%M:%S %Y %Z')
            expiry = expiry_dt.strftime('%Y-%m-%d')
        except Exception:
            expiry = ''
        if name:
            certs.append({'name': name, 'expiry': expiry})

    # Deduplicate
    seen = set()
    unique = []
    for c in certs:
        if c['name'] not in seen:
            seen.add(c['name'])
            unique.append(c)

    return {'system': unique[:20]}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow():
    return datetime.datetime.utcnow().isoformat() + 'Z'

def _parse_memory(s):
    m = re.search(r'(\d+)', str(s))
    if not m:
        return 0
    val = int(m.group(1))
    if 'GB' in s or 'gb' in s:
        return val
    if 'MB' in s or 'mb' in s:
        return round(val / 1024)
    return val

def _get_interface_ip(dev):
    raw = run(f'ipconfig getifaddr {dev} 2>/dev/null')
    return raw if raw else ''

def _get_secure_boot_intel():
    out = run('system_profiler SPiBridgeDataType 2>/dev/null | grep -i "secure boot"')
    if 'Full' in out:
        return 'Full Security'
    if 'Medium' in out:
        return 'Medium Security'
    if 'No' in out or 'Disabled' in out:
        return 'No Security'
    return 'Unknown'

def _xprotect_date():
    raw = run('ls -la /Library/Apple/System/Library/CoreServices/XProtect.bundle 2>/dev/null || '
              'ls -la /System/Library/CoreServices/XProtect.bundle 2>/dev/null')
    dm = re.search(r'(\w{3}\s+\d+\s+\d+:\d+|\w{3}\s+\d+\s+\d{4})', raw)
    return dm.group(1) if dm else ''


# ── Collect all ───────────────────────────────────────────────────────────────

def collect_all():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Collecting system data…", flush=True)
    try:
        data = {
            'meta':        collect_meta(),
            'security':    collect_security(),
            'identity':    collect_identity(),
            'mdm':         collect_mdm(),
            'software':    collect_software(),
            'network':     collect_network(),
            'certificates': collect_certificates(),
        }
        with _lock:
            _cache.clear()
            _cache.update(data)
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Done.", flush=True)
    except Exception as e:
        print(f"Error collecting data: {e}", flush=True)


def refresh_loop():
    collect_all()
    while True:
        time.sleep(REFRESH)
        collect_all()


# ── HTTP server ───────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/', '/status'):
            with _lock:
                payload = dict(_cache)
            body = json.dumps(payload, default=str).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        elif path == '/refresh':
            threading.Thread(target=collect_all, daemon=True).start()
            body = b'{"status":"refreshing"}'
            self.send_response(202)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    if platform.system() != 'Darwin':
        print("This agent only runs on macOS.")
        sys.exit(1)

    print()
    print("  macOS Enterprise Agent")
    print("  ───────────────────────────────────────────")
    print(f"  API:      http://127.0.0.1:{PORT}/status")
    print(f"  Refresh:  http://127.0.0.1:{PORT}/refresh")
    print(f"  Interval: {REFRESH}s")
    if os.geteuid() != 0:
        print("  Obs: Kör med sudo för full MDM/FileVault-data")
    print()

    threading.Thread(target=refresh_loop, daemon=True).start()

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as srv:
            srv.serve_forever()
    except OSError as e:
        print(f"Fel: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAvslutar.")
