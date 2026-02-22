# zcrack by zabry0

Cyberpunk hacker-aesthetic PWA — full-screen sci-fi terminal experience optimised for iPhone & desktop.

## Features

- 💀 **Matrix rain** + animated skull canvas terminal with customisable themes & speed
- 🔐 **Animated boot sequence** — cinematic startup with loading video support
- 🌍 **IP Geo Locator** — multi-source lookup with automatic fallback (4 APIs), private-IP detection, interactive 3D wireframe globe
- 📡 **Wi-Fi Sniffer** — live OS-level scan (Windows `netsh` / Linux `nmcli`) with automatic fallback to demo mode; signal bars, encryption badges, channel & band info
- 💻 **Remote Access Terminal** — SSH-flavoured interactive shell (15+ commands: `nmap`, `exploit`, `wget`, `ifconfig`, `netstat`, …) with command history
- 🎙 **Sound Sniffer** — real-time Web Audio API FFT spectrum analyser with waveform overlay, peak frequency & dB readout
- 🎨 **4 colour themes** — green, teal, red, blue — switchable at runtime
- ⚡ **Performance** — CSS GPU-accelerated scanlines, throttled HUD, `requestAnimationFrame` pause on background, service worker offline caching

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML / CSS / JS — zero dependencies, single `index.html` |
| Backend | Python `http.server` — serves static files + `/api/geo` & `/api/wifi` endpoints |
| PWA | `manifest.json` + `sw.js` — installable with offline support |
| Desktop demo | `main.py` — Pygame fullscreen terminal (optional) |

## Quick start

```bash
# clone & run
git clone <repo-url> && cd zcrack-zabry0
python server.py
# open http://localhost:8080
```

## Install as PWA (iPhone)

1. Open the URL in Safari
2. Tap **Share → Add to Home Screen**
3. Launch from home screen for full-screen experience

## Credentials

| Field | Value |
|-------|-------|
| User | `zabry0` |
| Password | `z4bry870` |

## Keyboard shortcuts (desktop)

| Key | Action |
|-----|--------|
| `C` | Clear terminal log |
| `P` | Pause / Resume |
| `T` | Cycle theme |
| `+` | Cycle speed |

## IP Lookup sources (automatic fallback)

| Priority | Source | Free |
|----------|--------|------|
| 1 | [ipwho.is](https://ipwho.is) | ✅ |
| 2 | [freeipapi.com](https://freeipapi.com) | ✅ |
| 3 | [ipapi.co](https://ipapi.co) | ✅ 1 000/day |
| 4 | [ip-api.com](http://ip-api.com) | ✅ (HTTP only) |

Private / reserved ranges (127.x, 10.x, 192.168.x, …) are detected client-side with no API call.

## Project structure

```
index.html      — full PWA app (HTML + CSS + JS in one file)
server.py       — Python local server with geo & wifi API endpoints
main.py         — Pygame desktop demo (optional)
manifest.json   — PWA manifest
sw.js           — service worker (offline caching)
icon.svg        — app icon (cyberpunk skull)
loadingvid.mp4  — boot loading video
```

## License

MIT
