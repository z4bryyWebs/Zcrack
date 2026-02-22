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


# ─── HTTP handler ─────────────────────────────────────────────────────────────

class ZcrackHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static files from BASE and handles /api/geo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/geo":
            params = urllib.parse.parse_qs(parsed.query)
            ip = (params.get("ip") or [""])[0].strip()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            try:
                if not ip:
                    raise ValueError("No IP address provided")
                payload = {"ok": True,  "data": geo_lookup(ip)}
            except Exception as exc:
                payload = {"ok": False, "error": str(exc)}

            self.wfile.write(json.dumps(payload).encode("utf-8"))
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
