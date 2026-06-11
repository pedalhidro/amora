# Pedal Hidrográfico

Static-PWA web map for an urban cycling collective in São Paulo, plus a
self-hosted backend, Python automation scripts, and an RDF ontology. No cloud
dependency — the project deliberately walked away from GCP and is now
local-first.

## Repo layout

- `web/` — the app. A static PWA: `index.html`, one big `app.js` (single
  file, no build step), `style.css`, `sw.js` (service worker),
  `manifest.json`, icons, `robots.txt`, `sitemap.xml`, `llms.txt` (guia do
  site p/ agentes LLM — aponta pros dumps TTL), `lib/` (vendored deps: `utils.js`,
  `n3.min.js`, `energy-worker.js`, `tom-select.complete.min.js`,
  `tom-select.min.css`, `qrcode.js`, `leaflet/` (js+css+images),
  `locatecontrol/` — Leaflet & friends were vendored off unpkg/jsdelivr;
  only app.js's lazy loads (exifr/heic2any/jszip/geotiff) still hit
  jsdelivr). Leaflet-based map. Also hosts `upload_images.html` (per-photo upload
  form), `upload_tour.html` (per-tour upsert form), `censo.html`
  (aggregated tour metrics + roster, opened as a modal iframe from the
  main app), `upload_videos.html` (permanent redirect stub →
  `upload_images.html`), and the `data/`, `photos/`, `clips/`, and
  `tour_assets/<tour_id>/` directories the app reads from at runtime.
- `backend/pi/` — the self-hosted backend. One Flask service (`main.py`)
  that serves `web/` as static files **and** validates+stores incoming
  photos. No SQLite; state lives in `web/data/uploads.ttl` (per-image
  triples), `web/data/data_graphs.ttl` (manifest pointing at every dump),
  and `web/photos/<phash>/{original,large,thumb}.*` (image variants).
  `phidro.service` (systemd) / `phidro.plist` (launchd),
  `requirements.txt`, `README.md`. Runs on a Raspberry Pi or macOS.
- `research/photos-rdf/` — the RDF research lab. Currently holds
  `build-tours.py` (writes `web/data/tours.ttl` from `data/tours.csv`),
  the seed `data/initial-data.ttl`, `decisions.ttl`, `design.ttl`,
  `conversion-notes.md`, and the legacy `upload-form.html` (kit-download
  form — superseded in production by `web/upload_images.html`). The
  active SHACL `shapes.ttl` and `ontology.ttl` live alongside the data
  in `web/data/`; the Pi reads them from there at startup. The
  former top-level `ontology/` dir (v1.1 `pedalhidrografico.ttl` +
  JSON-LD context) was removed — git history is the only reference.
- `scripts/` — `build-routes.py` (bakes `routes.json` from
  `web/data/tours.ttl` + RideWithGPS), `build-clips.py` (re-encodes raw
  videos in `web/clips/raw/` to 360p/720p mp4 + `.m4a` audio + thumbnail
  and writes the triples directly into `web/data/uploads.ttl` as
  `ph:Video`), `deploy.sh` (legacy GCS static mirror),
  `deploy-cloudrun.sh` (Cloud Run deploy + `--state` flag to sync mutable
  state), `pull-cloudrun.sh` (pull mutable state from the GCS bucket
  back to local), `sync-guard.sh` (anti-clobber guard sourced by the two
  previous scripts — see Conventions), `dev-cloudrun.sh` (run the Cloud
  Run image locally),
  `pi-deploy.sh` (runs on the Pi: git pull + restart + smoke check —
  the `deploy-amora.sh` / `pull-amora.sh` / `push-clips.sh` /
  `gcloud-ssh-rsync.sh` rsync-over-SSH family for the old GCE VM was
  removed; amora is Cloud Run now),
  `remux-clips-audio.py` (one-shot migration: muxes audio back into
  pre-v225 silent `web/clips/*.webm` that were transcoded before audio
  was embedded — see the upload-flow note below; removable once all
  clips are re-encoded), `gen-synthetic-rdf.py`, `exiftool_ph.config`.
  `build-photos.py` and
  `build-routes.mjs` are legacy artefacts pending removal — see "Open
  loose ends".
- `docs/` — design-reference notes not loaded at runtime. `DESIGN.md`
  (RDF substrate / ontology design rationale) and `ICON_DESIGN.md` (PWA
  icon decisions). Excluded from the Cloud Run container.

## Architecture

The app is fully static and works offline (service worker). It reads
pre-baked `routes.json` and resolves Turtle dumps via the manifest at
`web/data/data_graphs.ttl` (which currently lists `tours.ttl` and
`uploads.ttl`). When served by the Pi/Cloud Run backend, uploads hit
`POST /upload-image` or `POST /upload-video` same-origin; on a static-only
host (CDN) the form is offline-friendly but uploads have nowhere to go.

**Photos and videos are described in RDF/Turtle** in a single
`web/data/uploads.ttl` catalog. SHACL shapes live in `web/data/shapes.ttl`:

- `ph:Image` — `phd:image_<phash16>` IRI; `phash` is a 64-bit perceptual
  hash (DCT-based, computed in the browser); near-duplicate uploads share
  an IRI and naturally cluster.
- `ph:Video` — `phd:video_<vhash16>` IRI; `vhash` is computed by sampling
  N=8 evenly-spaced frames, taking each frame's pHash, and majority-voting
  per bit into a single 16-hex fingerprint. Standalone class (NOT a
  subclass of `ph:Image`) so it doesn't inherit bearing/focal warnings
  which don't apply to video. Adds `schema:duration`,
  `ph:availableResolution` (`sh:in` of `audio/360p/480p/720p/1080p`),
  `ph:audio`, optional `ph:video360p` / `ph:video720p`, and
  `schema:thumbnail`.

Key flows:

- **Display.** `web/app.js` fetches `./data/data_graphs.ttl`, follows each
  `void:dataDump` IRI to load the constituent graphs (currently `tours.ttl`
  and `uploads.ttl`), parses them with the bundled N3.js
  (`web/lib/n3.min.js`), and renders one Leaflet marker per `ph:Image`
  AND `ph:Video` (videos use the same `photoDivIcon` markup as photos with
  a red-orange border modifier `.photo-dot-video`; both participate in the
  same density-based clustering via `relaxPhotoMarkers`). GPS from
  `schema:locationCreated`, popup from triples. The **Configurações** modal
  (gear icon in the topbar) lets the user switch between Pi (same-origin),
  CDN, or Local (kit ZIP file picker — stored in memory, image URLs become
  blob URLs). Import/export buttons live there.
- **Upload (unified — images AND videos in one page).**
  `web/upload_images.html` accepts `image/*,video/*` via a single picker;
  each card detects media type from the file MIME and renders the
  appropriate body. Image cards: EXIF auto-fill, anonymize/compress
  toggles, three variants (`original`/`large`/`thumb`) POSTed to
  `/upload-image`. Video cards: trim sliders + steppers, GPS extraction
  from moov ISO 6709 atom, recording-date extraction from
  `com.apple.quicktime.creationdate` (ISO 8601 with TZ regex; falls back
  to mvhd binary uint32 seconds-since-1904), browser-side transcoding to
  webm/(vp9 or vp8)+opus 360p+720p with the **audio embedded in the video
  webm** (so the ghost-video player has sound on iOS Safari, which mutes
  `MediaElementAudioSourceNode` in some configs); a separate `audio.webm`
  (opus) is *also* emitted so the audio loop can play without downloading
  the full video. Thumbnail from frame ~5% in,
  per-card "Apenas áudio" toggle for audio-only clips, POSTed to
  `/upload-video`. Both flows share tour auto-detection (±2h/+12h window)
  and the Tom Select people picker with create-on-the-fly. pHash/vHash
  dedup prevents accidental re-uploads in the same batch AND against
  what's already on the server (catalog includes both hash sets at boot).
  `upload_videos.html` is a permanent redirect stub to
  `upload_images.html` for bookmarked URLs.
- **Validation.** `pyshacl` loads `web/data/shapes.ttl` +
  `web/data/ontology.ttl` once per process. The validator merges the
  incoming TTL with the ontology before checking — `pyshacl`'s `ont_graph`
  parameter does NOT expose ontology-declared instances (like
  `ph:rwgps a schema:Organization`) to `sh:class` checks, so manual
  merging is mandatory. See `docs/DESIGN.md` §2 for the
  full gotcha. `validate_image_ttl` and `validate_video_ttl` are siblings
  that each pin to their target class + IRI prefix.
- **Clips / Animação.** The "Animação" topbar button toggles both the
  marker spotlight pulse AND a ghost-video overlay (translucent `<video>`
  over the map). The app reads `ph:Video` entries from `uploads.ttl` via
  `loadClipsFromUploadsTtl()` — files live under `./clips/`. Plays through
  clips in random order with a 5-state marker handoff (green intro →
  pulsing white → orange outro). Clips with `audioOnly: true` (no
  `ph:video360p`/`ph:video720p`) are skipped by the ghost-video player but
  still participate in the audio loop. An independent "Loop de áudio"
  plays the same clips' audio-only tracks with a longer crossfade for
  ambient use. Both have controls in Ajustes and the layer panel.
- **Deletion.** `POST /delete-image/<phash>` and
  `POST /delete-video/<vhash>` purge the IRI's triples (plus reachable
  bnodes) from `uploads.ttl` AND delete the underlying blobs from the
  store. The frontend popups have a red-orange Excluir button gated by a
  `confirm()` dialog.
- **Tour CRUD & Censo.** `POST /upload-tour` accepts a TTL fragment
  describing exactly one `phd:tour_<id> a ph:Tour` (plus any new
  `phd:pessoa*` / `phd:assoc_*` declarations it references) and upserts
  it into `web/data/tours.ttl`. An optional `announcement` file field
  is saved under `tour_assets/<tour_id>/announcement.<ext>` and wired
  in as `schema:image <URL>` before the triples are persisted.
  `POST /delete-tour/<tour_id>` removes the tour's triples + reachable
  bnodes and purges `tour_assets/<tour_id>/`; it deliberately does NOT
  delete referenced `phd:pessoa*` or series — git history preserves
  those and they may be referenced by other tours.
  On every `/upload-tour` and `/delete-tour`, the backend also **syncs
  `routes.json` incrementally**: if the tour's TTL has a `ph:linkRoute`
  pointing at a RideWithGPS route, it fetches the geometry and upserts that
  tour's entry (keyed by `tourIri`); if the link is absent (new/edited tour
  with no route) or the tour is deleted, it removes the entry. The RWGPS
  fetch runs **outside** the global state lock (only the JSON read-modify-
  write is serialized) and is best-effort — a fetch failure never fails the
  tour save (the entry is kept with `latlngs:null` + `error`, same convention
  as `build-routes.py`). The shared fetch/parse/entry-building logic lives in
  `backend/pi/rwgps.py`, imported by both the backend and
  `scripts/build-routes.py` (single source of truth). The backend reads
  `RWGPS_API_KEY` / `RWGPS_AUTH_TOKEN` from its environment (best-effort
  `.env` load) — required for private/unlisted routes; public routes work
  without. `routes.json` is **mutable state served bucket-first** (like
  `uploads.ttl`) via `GET /routes.json`, with the baked file as seed/fallback.
  `web/upload_tour.html` is the per-tour form (series, sequence, energy
  estimate, intensity, attendee/newcomer counts, announcement art);
  `web/censo.html` shows aggregated metrics + a sortable tour roster
  with "Editar" links pointing at `upload_tour.html?id=<tour_id>`.
  The main app exposes Censo through a modal iframe — opened by the
  "Censo →" sidebar link in the Routes panel — and the iframe is
  re-pointed to `./censo.html` on every open so navigating into the edit
  form internally doesn't strand the user there on re-open.
- **Backend endpoint summary.** Static: `GET /`, `GET /<path:p>`,
  `GET /data/<filename>`, `GET /photos/<path:p>`, `GET /clips/<path:p>`,
  `GET /tour_assets/<path:p>` (in `gcs` mode the last three 302-redirect
  to the bucket's public URL), `GET /feed.xml` (RSS 2.0 dos passeios,
  renderizado de `tours.ttl` e cacheado por hash do catálogo — atualiza
  sozinho a cada tour CRUD). Ops: `GET /health`, `POST /reload` (force
  re-read of the on-disk TTL catalog after an out-of-band edit).
  Mutations: `POST /upload-image`, `POST /upload-video`,
  `POST /upload-tour`, `POST /delete-image/<phash>`,
  `POST /delete-video/<vhash>`, `POST /delete-tour/<tour_id>`.

## Clips workflow

Source videos in `web/clips/raw/` (`.MOV`/`.mp4`/`.m4v`). Run:

```sh
python scripts/build-clips.py
```

Requires `ffmpeg` and `exiftool` in `$PATH` (Homebrew on macOS, `apt` on
Pi). For each source the script:

- Reads GPS via `exiftool` (clips with no GPS are skipped); reads both
  `CreateDate` (mvhd) and Apple `CreationDate` (iOS, with TZ) and prefers
  the Apple value — Apple's is the real recording time; mvhd is the save
  time and is often misleading. Pass `-api QuickTimeUTC=0` so the TZ is
  preserved.
- Transcodes a `<stem>.360p.mp4` (always) and `<stem>.720p.mp4`
  (best-effort, opt-in via `clipsGhost.useHd`) into `web/clips/`.
- Extracts the audio track to `web/clips/audio/<stem>.m4a` (AAC 96k).
- Extracts a thumbnail from the middle of the clip into
  `web/clips/<stem>.thumb.jpg` (~256px short side, JPEG quality 4).
- Reads `web/data/tours.ttl` and associates each clip with the closest
  tour within ±12 h via `ph:capturedDuring` (skipped if no tour matches).
- Writes the triples directly into `web/data/uploads.ttl` as a `ph:Video`
  with deterministic IRI `phd:video_<md5(stem)[:16]>`, with default
  author/provider `phd:pessoaDandan` and CC BY-SA 4.0 license. Idempotent
  upsert — re-running purges + rewrites the same IRI's triples cleanly.

The mtime check on the transcoded files makes re-runs cheap. Adding a new
clip = drop into `raw/` and re-run.

There is **no `clips.json`** — that intermediary was removed; `build-clips.py`
writes RDF directly. App.js reads `ph:Video` from `uploads.ttl` only.

## Conventions — please follow

- **Bump `sw.js` `VERSION`** on *any* change to files in `web/` —
  otherwise the service worker serves stale cached copies and the change
  won't reach users. It's a monotonic `phidro-vN` integer counter; just
  increment. For user-visible changes, also add an entry to the collapsed
  changelog `<details class="help-changelog">` at the top of the Ajuda
  modal in `index.html` (dated, keyed to the new vN).
- **Compression + ETags are load-bearing.** The backend uses
  `flask-compress` (best-effort import; `COMPRESS_STREAMS = True` is
  required or `send_from_directory` responses — app.js, style.css — go out
  raw) and the string-built responses (`/routes.json`, `/data/<ttl>`) get
  `resp.add_etag()` + `make_conditional()` via `_conditional()`. Without
  the ETags, the SW's network-first strategy re-downloads the full 2 MB
  `routes.json` every visit instead of getting a 304. Don't strip either
  when touching those handlers. `index.html` also `<link rel="preload">`s
  `routes.json`, and app.js fetches it *without* `cache: 'no-cache'` so
  the two requests coalesce — keep them matched.
- **No backend auth.** Anyone who can reach the Pi can upload/delete — this
  is an intentional decision (trusted access assumed). Don't reintroduce a
  token; restrict at the edge if needed.
- **The Pi serves its own git clone.** Deploying changes = `git pull` on the
  Pi + restart the service + hard-reload the browser. There is no separate
  build/upload step for the self-hosted path.
- **Ontology:** reuse consolidated vocabularies (schema.org, PROV-O, QUDT,
  GeoSPARQL, Dublin Core); mint `ph:` terms only for what is specific to
  Pedal Hidrográfico.
- **Two deploy targets live now: Pi and Cloud Run.** Pi is the local-first
  default; Cloud Run is hosted at `https://amora.pedalhidrografi.co/` via
  `scripts/deploy-cloudrun.sh`. The backend (`backend/pi/main.py`) is the
  same for both — `storage.py` abstracts state via `STORAGE_BACKEND=local`
  (filesystem) vs `gcs` (bucket). `scripts/deploy.sh` (the old read-only
  static mirror at `tiles.pedalhidrografi.co/rotas_app`) is still around
  but largely superseded.
- **gunicorn runs with `--workers 1` everywhere** (Dockerfile,.service,
  .plist). The mutation lock (`_state_lock`) is per-process; with 2+
  workers, concurrent uploads land in different processes and the second
  read-modify-write of the TTL catalogs silently discards the first (lost
  update). Concurrency comes from threads; Cloud Run scales by instances.
  Don't "tune" the worker count up.
- **Local↔bucket sync is guarded against lost updates.** The four
  dual-writer state files (`uploads.ttl`, `data_graphs.ttl`, `tours.ttl`,
  `routes.json`) are mutated both locally (build scripts, edits) and
  server-side (uploads, Tour CRUD via the bucket). `scripts/sync-guard.sh`
  (sourced by `deploy-cloudrun.sh` and `pull-cloudrun.sh`) stashes the MD5
  of the last successful sync in `.sync-state/` (gitignored, per-machine)
  and refuses any copy whose destination changed since that baseline AND
  differs from the source — exit 3 with reconciliation instructions.
  `--force` overrides (and establishes the baseline on first use on a new
  machine). Don't bypass the guard with raw `gcloud storage cp`; photos/
  and clips/ are content-addressed and additive, so they stay unguarded.
- **GCS read gotcha (Cloud Run).** Always use `bucket.get_blob(key)`
  rather than `bucket.blob(key) + download_as_text()` — the bare-blob form
  produced silently-stale content in Cloud Run despite the bucket having
  one current generation. See `GCSStateStore.read_text` in
  `backend/pi/storage.py` for the fix.
- **Cloud Run container stays magrinho.** `.gcloudignore` /
  `.dockerignore` exclude `web/photos/` and `web/clips/` entirely (not
  just `raw/`). The runtime handlers `/photos/<path>` and `/clips/<path>`
  redirect to the bucket's public URL in `gcs` mode (302 → much faster
  than streaming through Flask). To populate the bucket with local
  `build-clips.py` outputs and Pi-side uploads, run
  `scripts/deploy-cloudrun.sh --state-only`.
- Comments and UI strings are in Portuguese; code identifiers in English.

## Verify before finishing

- JS in `web/`: load it in a browser (or the existing dev server) — the
  browser surfaces syntax errors immediately. No standalone JS tooling here.
- Bump `web/sw.js` `VERSION` if any file under `web/` changed.
- `python -m py_compile backend/pi/main.py`
- Ontology / shapes / data: parse with `rdflib` after editing `*.ttl`.

## Build & deploy

- `python scripts/build-routes.py` — regenerate `web/routes.json` by
  reading `web/data/tours.ttl` (the Tour catalog) and fetching each
  referenced GPX from RideWithGPS. Requires `python-dotenv` plus
  `RWGPS_API_KEY` / `RWGPS_AUTH_TOKEN` in `.env`.
- `python research/photos-rdf/build-tours.py` — regenerate
  `web/data/tours.ttl` from `research/photos-rdf/data/tours.csv`. Run this
  whenever the spreadsheet changes; `build-routes.py` consumes its output.
- `python scripts/build-clips.py` — re-encode anything in `web/clips/raw/`
  to 360p/720p mp4 + `.m4a` audio + thumbnail, and upsert each as a
  `ph:Video` in `web/data/uploads.ttl` (associates with nearest tour
  within ±12 h). See "Clips workflow" above. Requires `ffmpeg` + `exiftool`.
- `bash scripts/deploy-cloudrun.sh` — build + deploy backend to Cloud Run
  (project `pedal-hidrografico`, region `southamerica-east1`, service
  `phidro`, bucket `phidro-state`). Reads `RWGPS_API_KEY`/`RWGPS_AUTH_TOKEN`
  from the local `.env` and injects them as service env vars (the `.env`
  itself never enters the build context — it's in `.gcloudignore`). Flags:
  - `--state` build + deploy + sync mutable state (`uploads.ttl`,
    `data_graphs.ttl`, `routes.json`, `photos/`, `clips/`) to the bucket
  - `--state-only` just sync mutable state, skip rebuild
  - `--mirror` make the bucket an exact mirror of local (deletes objects
    that no longer exist locally; pairs with `--state`/`--state-only`)
  - `--force` override the anti-clobber guard (see Conventions)
  - `--dry-run` preview without executing
- `bash scripts/deploy.sh` (or `bash scripts/deploy.sh --dry-run`) — sync
  `web/` to the legacy GCS static mirror (read-only; needs `gcloud` auth).
- Pi: `pip install -r backend/pi/requirements.txt && python backend/pi/main.py`
  (defaults to port 8000; override with `PORT=…`). See `backend/pi/README.md`.

## Open loose ends

- **Retire legacy build scripts.** `scripts/build-routes.mjs` (the old
  Node port — now orphaned; `package.json`'s `build:routes` already points
  at `build-routes.py`) and `scripts/build-photos.py` (predates the upload
  form) are both superseded. User-deletes when ready:
  `git rm scripts/build-routes.mjs scripts/build-photos.py`. The
  `coletor_*.py` family was already removed.
- **`scripts/gen-synthetic-rdf.py` is stale.** It targets the removed
  top-level `ontology/` dir (`--out-dir ontology/v2`) and emits the old
  `censo/1.0/` namespace with classes absent from the current
  `web/data/ontology.ttl` — its output can't validate against current
  shapes. User-deletes when ready: `git rm scripts/gen-synthetic-rdf.py`
  (or retarget it at `web/data/` if synthetic data is still useful).
- **`research/photos-rdf/upload-form.html`** is the legacy "build a kit ZIP"
  form. Production uploads go through `web/upload_images.html`. Keep the
  research one only if you still use it for batch-export experiments.
- **`web/data/uploads.ttl` and `web/photos/<phash>/`** are runtime artifacts
  of the Pi — gitignore or commit per your deploy strategy. The CDN mirror
  shows no photos until those files exist at the destination.
- **`web/clips/raw/`** holds source videos (large; ~800 MB total).
  Probably want gitignored. The build artifacts (`*.360p.mp4`,
  `*.720p.mp4`, `audio/*.m4a`, `*.thumb.jpg`) are smaller and can be
  committed if you want the static mirror to ship clips, or generated in
  CI. The catalog of triples lives in `web/data/uploads.ttl` (single
  source of truth for both images and videos). For Cloud Run, all of
  `web/clips/` and `web/photos/` is excluded from the container and lives
  in the `phidro-state` bucket — push local outputs with
  `scripts/deploy-cloudrun.sh --state-only`.
- **`web/upload_videos.html`** is a permanent redirect stub pointing at
  `upload_images.html` (which now handles both media types). Safe to
  delete once you're sure no bookmark uses the old URL.

## Notes

- Working files we changed this cycle are likely uncommitted — check
  `git status` and commit with meaningful messages.
- Permanent deletions (files, data) should be left to the user — provide the
  commands rather than running them.
