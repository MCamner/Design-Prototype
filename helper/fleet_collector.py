#!/usr/bin/env python3
"""
Fleet Collector
===============
Pollar alla klienters readiness-agent (port 38765) och exponerar
aggregerad data på http://0.0.0.0:38766/fleet

Användning:
  python3 helper/fleet_collector.py

Konfigurera klienter i:
  helper/fleet_clients.json

Öppna dashboarden i webbläsaren:
  http://localhost:38766
"""

import json
import os
import sys
import time
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen, Request
from urllib.error import URLError
import datetime

# ── Konfiguration ─────────────────────────────────────────────────────────────
PORT          = 38766
AGENT_PORT    = 38765
POLL_INTERVAL = 30      # sekunder mellan polls
CLIENT_TIMEOUT = 3      # timeout per klient (sekunder)
MAX_WORKERS   = 32      # max parallella anslutningar

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE    = os.path.join(BASE_DIR, 'fleet_clients.json')
DASHBOARD_FILE = os.path.join(BASE_DIR, '..', 'docs', 'Fleet Command Center.html')

# ── Delat tillstånd ──────────────────────────────────────────────────────────
_lock        = threading.Lock()
_fleet       = {}       # ip → client dict
_last_polled = None
_poll_count  = 0

# ── Klientpollning ────────────────────────────────────────────────────────────
def load_config():
    if not os.path.exists(CONFIG_FILE):
        example = [
            {"ip": "10.10.4.87", "hostname": "IGEL-001", "site": "Stockholm HQ"},
            {"ip": "10.10.4.88", "hostname": "IGEL-002", "site": "Stockholm HQ"},
        ]
        with open(CONFIG_FILE, 'w') as f:
            json.dump(example, f, indent=2)
        print(f"  Skapade exempelkonfig: {CONFIG_FILE}")
        print("  Redigera filen och lägg till dina klient-IP:er, starta sedan om.\n")
    with open(CONFIG_FILE) as f:
        return json.load(f)


def poll_client(cfg):
    ip       = cfg['ip']
    hostname = cfg.get('hostname', ip)
    site     = cfg.get('site', '')
    url      = f"http://{ip}:{AGENT_PORT}/status"

    try:
        req = Request(url, headers={'User-Agent': 'FleetCollector/1.0'})
        with urlopen(req, timeout=CLIENT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())

        # Hostname från agenten har företräde om den rapporterar ett
        resolved_hostname = (
            data.get('meta', {}).get('hostname') or hostname
        )

        return {
            'ip':            ip,
            'hostname':      resolved_hostname,
            'site':          site,
            'profile':       data.get('meta', {}).get('profile', ''),
            'agent_version': data.get('meta', {}).get('agent_version', ''),
            'status':        'online',
            'last_seen':     _utcnow(),
            'data':          data,
            'error':         None,
        }

    except Exception as exc:
        # Behåll last_seen från föregående lyckade poll
        prev      = _fleet.get(ip, {})
        last_seen = prev.get('last_seen')

        return {
            'ip':            ip,
            'hostname':      hostname,
            'site':          site,
            'profile':       cfg.get('profile', ''),
            'agent_version': None,
            'status':        'offline',
            'last_seen':     last_seen,
            'data':          None,
            'error':         str(exc),
        }


def poll_all(clients):
    results = {}
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(clients) or 1)) as ex:
        futures = {ex.submit(poll_client, c): c for c in clients}
        for fut in as_completed(futures):
            r = fut.result()
            results[r['ip']] = r
    return results


def poll_loop():
    global _last_polled, _poll_count
    while True:
        clients = load_config()
        t0      = time.time()
        results = poll_all(clients)

        with _lock:
            _fleet.clear()
            _fleet.update(results)
            _last_polled = _utcnow()
            _poll_count += 1

        online  = sum(1 for r in results.values() if r['status'] == 'online')
        offline = len(results) - online
        elapsed = time.time() - t0
        _log(f"Poll #{_poll_count}: {online} online, {offline} offline ({elapsed:.1f}s)")

        time.sleep(POLL_INTERVAL)


def poll_once_async():
    """Trigger en omedelbar poll utan att störa poll_loop."""
    def _run():
        clients = load_config()
        results = poll_all(clients)
        with _lock:
            _fleet.update(results)
    threading.Thread(target=_run, daemon=True).start()

# ── HTTP-server ───────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')

        if path in ('', '/index.html'):
            self._serve_dashboard()
        elif path == '/fleet':
            self._serve_fleet()
        elif path == '/fleet/reload':
            self._serve_reload()
        elif path == '/fleet/clients':
            self._serve_clients_config()
        else:
            self._send_json(404, {'error': 'not found'})

    # -- Endpoints ------------------------------------------------------------

    def _serve_fleet(self):
        with _lock:
            payload = {
                'collected_at': _last_polled or _utcnow(),
                'poll_count':   _poll_count,
                'clients':      list(_fleet.values()),
            }
        self._send_json(200, payload)

    def _serve_reload(self):
        poll_once_async()
        self._send_json(202, {'status': 'reloading'})

    def _serve_clients_config(self):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            self._send_json(200, data)
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _serve_dashboard(self):
        try:
            with open(DASHBOARD_FILE, 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._send_json(404, {'error': 'Dashboard-filen hittades inte'})

    # -- Helpers --------------------------------------------------------------

    def _send_json(self, code, obj):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Logga bara fel, inte varje GET
        if args and str(args[1]) not in ('200', '202'):
            _log(f"HTTP {args[1]} {args[0]}")

# ── Hjälpfunktioner ───────────────────────────────────────────────────────────
def _utcnow():
    return datetime.datetime.utcnow().isoformat() + 'Z'

def _log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print()
    print("  Fleet Collector")
    print("  ───────────────────────────────────────────")
    print(f"  Dashboard:  http://localhost:{PORT}")
    print(f"  API:        http://localhost:{PORT}/fleet")
    print(f"  Konfig:     {CONFIG_FILE}")
    print(f"  Pollintervall: {POLL_INTERVAL}s  |  Timeout: {CLIENT_TIMEOUT}s/klient")
    print()

    # Starta pollloop i bakgrunden
    threading.Thread(target=poll_loop, daemon=True).start()

    # Starta HTTP-server
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(('', PORT), Handler) as srv:
            _log(f"Lyssnar på port {PORT}…")
            srv.serve_forever()
    except OSError as e:
        print(f"\nFel: {e}")
        print(f"Är port {PORT} redan upptagen? Avsluta eventuell befintlig instans först.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAvslutar.")
