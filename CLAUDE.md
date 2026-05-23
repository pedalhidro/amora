# Pedal Hidrográfico

Static-PWA web map for an urban cycling collective in São Paulo, plus a
self-hosted backend, Python automation scripts, and an RDF ontology. No cloud
dependency — the project deliberately walked away from GCP and is now
local-first.

## Repo layout

- `public/` — the app. A static PWA: `index.html`, one big `app.js`
  (~3500 lines, single file, no build step), `style.css`, `sw.js` (service
  worker), `manifest.json`, icons, `lib/utils.js`. Leaflet-based map.
- `backend/pi/` — the self-hosted backend. One Flask service (`main.py`)
  that serves the app *and* the photo archive; SQLite index + files on disk.
  `phidro.service` (systemd) / `phidro.plist` (launchd), `requirements.txt`,
  `README.md`. Runs on a Raspberry Pi (64-bit OS) or macOS.
- `ontology/` — the RDF vocabulary (`pedalhidrografico.ttl`, v1.1) + the
  JSON-LD context + generated instance data + a standalone graph explorer.
- `scripts/` — `build-routes.mjs` (bakes `routes.json` from RideWithGPS),
  `build-photos.py` (EXIF → `public/photos.json` + thumbnails),
  `coletor_*.py` (photo collectors), `deploy.sh` (GCS static deploy).

## Architecture

The app is fully static and works offline (service worker). It reads
pre-baked `routes.json` and a photo manifest. When served by the Pi backend,
uploads/edits hit same-origin API routes; on a static-only host those routes
404 and the app degrades to read-only.

**Photos are a "voiced manifest."** `photos.jsonld` is
`{@context, generatedAt, voices:[{id,label,kind,signed,verified,pubkey,photos:[...]}]}`.
Each voice is a named graph / perspective. The app folds the voices into one
view (`foldVoices` in `app.js`).

Key concepts (all implemented — "Part B steps 1–5"):

- **Voices** — perspectives on the photo archive. `kind` is `person`
  (animate) or `model` (inanimate; the `voice/censo` voice is the model).
- **Precedence stack** — for the photo layer, voices are ordered; the top
  voice wins per photo. State in `localStorage` (`phidro:voiceOrder`,
  `phidro:voiceOff`, `phidro:activeVoice`). Managed in the "Vozes" modal.
- **Clusters** — uploads are perceptual-hashed (dHash) on the Pi; near-
  identical photos share a `cluster` id so the same photo across voices is
  recognised. `foldVoices` keys on `cluster || id`.
- **Divergence** — when voices disagree about a clustered photo's metadata,
  it is surfaced (popup section, ghost markers, review panel) — but only
  when a `model` voice is involved; person-vs-person stays silent precedence.
- **Signing** — exporting a voice `.zip` signs `voice.json` with a browser-
  held ECDSA P-256 key (`localStorage` `phidro:idKey`); import verifies
  integrity only (no key pinning). Bad signature flags, doesn't reject.

## Conventions — please follow

- **Bump `sw.js` `VERSION`** (currently `phidro-v31`) on *any* change to
  files in `public/` — otherwise the service worker serves stale cached
  copies and the change won't reach users. It's a monotonic `phidro-vN`.
- **No backend auth.** Anyone who can reach the Pi can upload/delete — this
  is an intentional decision (trusted access assumed). Don't reintroduce a
  token; restrict at the edge if needed.
- **The Pi serves its own git clone.** Deploying changes = `git pull` on the
  Pi + restart the service + hard-reload the browser. There is no separate
  build/upload step for the self-hosted path.
- **Ontology:** reuse consolidated vocabularies (schema.org, PROV-O, QUDT,
  GeoSPARQL, Dublin Core); mint `ph:` terms only for what is specific to
  Pedal Hidrográfico.
- **No GCP.** The `scripts/deploy.sh` GCS path still exists for a read-only
  static mirror at `tiles.pedalhidrografi.co/rotas_app`, but the live system
  is the Pi. Don't add cloud dependencies.
- Comments and UI strings are in Portuguese; code identifiers in English.

## Verify before finishing

- `node --check public/app.js && node --check public/sw.js`
- `python3 -m py_compile backend/pi/main.py`
- Ontology: parse with `rdflib` after editing `*.ttl`.

## Build & deploy

- `npm run build:routes` — regenerate `public/routes.json`.
- `python3 scripts/build-photos.py [--photos-root DIR]` — regenerate
  `public/photos.json` + thumbnails.
- `npm run deploy:dry` / `npm run deploy` — sync `public/` to the GCS static
  mirror (read-only; needs `gcloud` auth).
- Pi: see `backend/pi/README.md`.

## Open loose ends

- Local cleanup the user runs: `rm -rf backend/delete-photo` (stray empty
  dir) and `git rm --cached public/.DS_Store` (tracked despite `.gitignore`).
- `public/photos.json` is not committed — it's a build artifact. The static
  GCS mirror shows no photos until `build-photos.py` is run locally first.
- `backend/pi/data/` is the live local archive (gitignored) — don't delete.

## Notes

- Working files we changed this cycle are likely uncommitted — check
  `git status` and commit with meaningful messages.
- Permanent deletions (files, data) should be left to the user — provide the
  commands rather than running them.
