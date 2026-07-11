---
name: verify
description: Drive the amora web app (web/) in a headless browser to verify frontend changes end-to-end.
---

# Verifying web/ changes in a headless session

The app is a static PWA — no build step, no JS test tooling. Verification =
serve `web/`, drive it with Playwright + the pre-installed Chromium, screenshot.

## Recipe that works

```sh
# 1. Serve web/ (backend not needed for frontend-only changes)
python3 -m http.server 8123 --directory web &

# 2. Playwright: npm install playwright in the scratchpad (2 packages, ~3 s;
#    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 is already set — do NOT playwright install)
# 3. Launch with the bundled browser:
#    chromium.launch({ executablePath: '/opt/pw-browsers/chromium', headless: true })
```

Wait ~2.5 s after `goto` (waitUntil: 'domcontentloaded') for app boot
(routes.json + TTL catalogs).

## Gotchas

- **Chromium cannot CONNECT through the remote session's egress proxy** (curl
  can; the browser gets ERR_CONNECTION_RESET on every external host — tiles,
  OSRM, Photon, jsdelivr). Playwright's `proxy:` option doesn't help. For
  external APIs the change depends on: capture real responses with curl first,
  then fulfill in-page via `page.route('**host**', r => r.fulfill({...}))` —
  transport stubbed, payload + app real. Tiles just fail (gray map); harmless.
- The trace editor's global keydown treats **Esc as "cancel drawing"** and
  Cmd+Z as undo when focus is on `body` — focus an input (or click a specific
  control) before sending keys, or you'll tear down the state you're checking.
- Leaflet popups opened during a `flyTo` get closed when the zoom animation
  starts — assert after `moveend`/a settle timeout.
- Elevation/energy figures show "↑ carregando"/0 offline — expected, don't
  assert on them.

## Flows worth driving

- Trace editor: `#trace-btn` → map clicks / `#geo-search-btn` picks add
  trackpoints; assert `.trackpoint-marker` count, `.tp-label` texts,
  `#trace-metrics` text, undo via `#trace-undo`.
- Geo search: `#geo-search-btn` → `#geo-search-input` (350 ms debounce, min
  3 chars) → `#geo-search-results li`; status messages in `#geo-search-status`.
- Mobile: `setViewportSize({width: 390,…})` — panels reposition on open, so
  close/reopen after resizing.

Remember the repo conventions: bump `web/sw.js` VERSION + changelog entry in
`index.html` for any `web/` change.
