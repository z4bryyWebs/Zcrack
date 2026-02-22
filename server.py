#!/usr/bin/env python3
"""
zcrack local server — zabry0
Serves the app as static files AND provides a /api/geo?ip=X endpoint
that performs IP geolocation server-side.

No CORS issues: the browser talks to localhost, the server talks to APIs.

Run:   python server.py
Open:  http://localhost:8080
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import re
import subprocess
import platform

PORT = 8080
BASE = os.path.dirname(os.path.abspath(__file__))


# ─── parsers ──────────────────────────────────────────────────────────────────

def _parse_ipwho(d):
    if d.get("success") is False:
        raise ValueError(d.get("message", "fail"))
    conn = d.get("connection") or {}
    tz   = d.get("timezone")
    return {
        "ip":      d.get("ip", "?"),
        "city":    d.get("city", "?"),
        "region":  d.get("region", "?"),
        "country": d.get("country", "?"),
        "cc":      d.get("country_code", "?"),
        "isp":     conn.get("isp") or conn.get("org") or d.get("org", "?"),
        "lat":     d.get("latitude", 0),
        "lon":     d.get("longitude", 0),
        "tz":      tz.get("id", "?") if isinstance(tz, dict) else (tz or "?"),
    }


def _parse_freeipapi(d):
    if not d.get("latitude") and not d.get("longitude"):
        raise ValueError("no geo data")
    return {
        "ip":      d.get("ipAddress", "?"),
        "city":    d.get("cityName", "?"),
        "region":  d.get("regionName", "?"),
        "country": d.get("countryName", "?"),
        "cc":      d.get("countryCode", "?"),
        "isp":     d.get("asn") or d.get("isp", "?"),
        "lat":     d.get("latitude", 0),
        "lon":     d.get("longitude", 0),
        "tz":      d.get("timeZone", "?"),
    }


def _parse_ipapico(d):
    if d.get("error"):
        raise ValueError(d.get("reason", "fail"))
    return {
        "ip":      d.get("ip", "?"),
        "city":    d.get("city", "?"),
        "region":  d.get("region", "?"),
        "country": d.get("country_name", "?"),
        "cc":      d.get("country_code", "?"),
        "isp":     d.get("org", "?"),
        "lat":     d.get("latitude", 0),
        "lon":     d.get("longitude", 0),
        "tz":      d.get("timezone", "?"),
    }


def _parse_ipwhoami(d):
    """ip-api.com free endpoint (HTTP only, handled server-side fine)."""
    if d.get("status") == "fail":
        raise ValueError(d.get("message", "fail"))
    return {
        "ip":      d.get("query", "?"),
        "city":    d.get("city", "?"),
        "region":  d.get("regionName", "?"),
        "country": d.get("country", "?"),
        "cc":      d.get("countryCode", "?"),
        "isp":     d.get("isp") or d.get("org", "?"),
        "lat":     d.get("lat", 0),
        "lon":     d.get("lon", 0),
        "tz":      d.get("timezone", "?"),
    }


# ─── sources ──────────────────────────────────────────────────────────────────

GEO_SOURCES = [
    (
        "ipwho.is",
        lambda ip: f"https://ipwho.is/{urllib.parse.quote(ip)}",
        _parse_ipwho,
    ),
    (
        "freeipapi.com",
        lambda ip: f"https://freeipapi.com/api/json/{urllib.parse.quote(ip)}",
        _parse_freeipapi,
    ),
    (
        "ipapi.co",
        lambda ip: f"https://ipapi.co/{urllib.parse.quote(ip)}/json/",
        _parse_ipapico,
    ),
    (
        "ip-api.com",
        lambda ip: f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,query",
        _parse_ipwhoami,
    ),
]


def geo_lookup(ip: str) -> dict:
    """Try each source in order, return on first success."""
    errors = []
    for name, url_fn, parser in GEO_SOURCES:
        try:
            url = url_fn(ip)
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "zcrack/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            result = parser(data)
            result["_src"] = name
            return result
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise RuntimeError("All sources failed — " + " | ".join(errors))


# ─── Wi-Fi scan ───────────────────────────────────────────────────────────────

def _auth_to_enc(auth: str) -> str:
    a = auth.upper()
    if 'WPA3' in a: return 'WPA3'
    if 'WPA2' in a: return 'WPA2'
    if 'WPA'  in a: return 'WPA'
    if 'WEP'  in a: return 'WEP'
    if 'OPEN' in a or 'NONE' in a or not a.strip(): return 'OPEN'
    return 'WPA2'

def _ch_to_band(ch: int) -> str:
    if ch <= 13:  return '2.4 GHz'
    if ch <= 177: return '5 GHz'
    return '6 GHz'

def _wifi_windows() -> list:
    r = subprocess.run(
        ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
        capture_output=True, timeout=12)
    try:
        text = r.stdout.decode('utf-8')
    except UnicodeDecodeError:
        text = r.stdout.decode('cp850', errors='replace')

    nets = []
    ssid = ''; auth = 'WPA2'
    bssid = None; sig = 50; radio = ''; ch = 6

    def flush():
        nonlocal bssid
        if bssid and ssid:
            nets.append({'ssid': ssid, 'mac': bssid, 'sig': sig,
                         'enc': _auth_to_enc(auth), 'ch': ch,
                         'band': _ch_to_band(ch)})
        bssid = None

    for line in text.splitlines():
        # SSID line (not BSSID)
        m = re.match(r'^\s*SSID\s+\d+\s*:\s*(.*)$', line, re.IGNORECASE)
        if m and 'BSSID' not in line.upper():
            flush()
            ssid = m.group(1).strip(); auth = 'WPA2'; ch = 6; radio = ''
            continue
        # Authentication / Ověřování
        m = re.match(r'^\s*(?:Authentication|Ov[eě][rř]ov[aá]n[ií])\s*:\s*(.+)$', line, re.IGNORECASE)
        if m: auth = m.group(1).strip(); continue
        # BSSID
        m = re.match(r'^\s*BSSID\s+\d+\s*:\s*([\da-fA-F:]+)', line, re.IGNORECASE)
        if m: flush(); bssid = m.group(1).strip(); sig = 50; radio = ''; ch = 6; continue
        # Signal / Signál
        m = re.match(r'^\s*(?:Signal|Sign[aá]l)\s*:\s*(\d+)%', line, re.IGNORECASE)
        if m: sig = int(m.group(1)); continue
        # Radio type / Typ rádia
        m = re.match(r'^\s*(?:Radio\s+type|Typ\s+r[aá]dia)\s*:\s*(.+)$', line, re.IGNORECASE)
        if m: radio = m.group(1).strip(); continue
        # Channel / Kanál
        m = re.match(r'^\s*(?:Channel|Kan[aá]l)\s*:\s*(\d+)', line, re.IGNORECASE)
        if m: ch = int(m.group(1)); continue
    flush()
    nets.sort(key=lambda n: -n['sig'])
    return nets

def _wifi_linux() -> list:
    r = subprocess.run(
        ['nmcli', '-t', '-f', 'SSID,BSSID,SIGNAL,SECURITY,CHAN,FREQ', 'dev', 'wifi', 'list'],
        capture_output=True, timeout=12)
    text = r.stdout.decode('utf-8', errors='replace')
    nets = []
    for line in text.splitlines():
        # nmcli -t escapes colons in values as \: — split on unescaped colons
        parts = re.split(r'(?<!\\):', line)
        if len(parts) < 6: continue
        ssid = parts[0].replace('\\:', ':') or '<Hidden>'
        mac  = ':'.join(parts[1:7]) if len(parts) >= 8 else parts[1].replace('\\:', ':')
        try:    sig = int(parts[7] if len(parts) >= 9 else parts[2])
        except: sig = 50
        sec  = (parts[8] if len(parts) >= 10 else parts[3]).upper()
        try:    ch  = int(parts[9] if len(parts) >= 11 else parts[4])
        except: ch  = 6
        freq = parts[10] if len(parts) >= 12 else parts[5]
        band = '5 GHz' if '5' in freq else ('6 GHz' if '6' in freq else '2.4 GHz')
        enc  = ('WPA3' if 'WPA3' in sec else 'WPA2' if 'WPA2' in sec else
                'WPA'  if 'WPA'  in sec else 'WEP'  if 'WEP'  in sec else 'OPEN')
        nets.append({'ssid': ssid, 'mac': mac, 'sig': sig, 'enc': enc, 'ch': ch, 'band': band})
    nets.sort(key=lambda n: -n['sig'])
    return nets

def wifi_scan() -> list:
    if platform.system() == 'Windows':
        return _wifi_windows()
    return _wifi_linux()


# ─── HTTP handler ─────────────────────────────────────────────────────────────

class ZcrackHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static files from BASE and handles /api/geo and /api/wifi."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def _json(self, payload: dict):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/api/wifi':
            try:
                nets = wifi_scan()
                self._json({'ok': True, 'data': nets})
            except Exception as exc:
                self._json({'ok': False, 'error': str(exc)})
            print(f'[wifi] scanned → {len(nets) if "nets" in dir() else 0} networks')
            return

        if parsed.path == "/api/geo":
            params = urllib.parse.parse_qs(parsed.query)
            ip = (params.get("ip") or [""])[0].strip()

            try:
                if not ip:
                    raise ValueError('No IP address provided')
                self._json({'ok': True,  'data': geo_lookup(ip)})
            except Exception as exc:
                self._json({'ok': False, 'error': str(exc)})
            return

        # Fall through to built-in static file serving
        super().do_GET()

    def log_message(self, fmt, *args):
        # Only log API calls, suppress noisy static-file lines
        if "/api/" in (args[0] if args else ""):
            print(f"[geo] {args[0].split()[1] if args else ''} → {args[1]}")


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.chdir(BASE)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ZcrackHandler) as httpd:
        print(f"[zcrack] Serving at  http://localhost:{PORT}")
        print(f"[zcrack] Geo API at  http://localhost:{PORT}/api/geo?ip=8.8.8.8")
        print( "[zcrack] Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[zcrack] Stopped.")
