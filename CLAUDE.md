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
  form), `upload_tour.html` (per-tour upsert form),
  `backfill_tours.html` (mass-backfill applet for missing tour fields),
  `censo.html` (aggregated tour metrics + roster, opened as a modal
  iframe from the main app), `upload_videos.html` (permanent redirect
  stub → `upload_images.html`), and the `data/`, `photos/`, `clips/`,
  and `tour_assets/<tour_id>/` directories the app reads from at runtime.
- `backend/` — the self-hosted backend. One Flask service (`main.py`)
  that serves `web/` as static files **and** validates+stores incoming
  photos. No SQLite; state lives in `web/data/uploads.ttl` (per-image
  triples), `web/data/tours.ttl` (tour catalog), and
  `web/photos/<phash>/{original,large,thumb}.*` (image variants).
  `web/data/data_graphs.ttl` is a VoID manifest the frontend still follows,
  but the backend no longer mutates it — the dump list is fixed
  (`CATALOG_DUMPS = tours.ttl + uploads.ttl`) and `/data/data_graphs.ttl`
  is served from a static shim (`DATA_GRAPHS_SHIM`).
  `phidro.plist` (launchd), `requirements.txt`, `README.md`. Runs locally
  (macOS/Linux) or on Cloud Run. (Was `backend/pi/` — the Raspberry Pi
  deploy was retired; the systemd unit + `pi-deploy.sh` were removed.)
- `research/photos-rdf/` — the RDF research lab. Currently holds
  the seed `data/initial-data.ttl`, `data/tours.csv` (historical
  spreadsheet dump — `build-tours.py`, which regenerated `tours.ttl`
  from it, was removed: `tours.ttl` is now maintained solely via
  `upload_tour.html` / the Tour CRUD endpoints, and a CSV rebuild would
  wipe the backfilled narratives and announcement images),
  `decisions.ttl`, `design.ttl`,
  `conversion-notes.md`, and the legacy `upload-form.html` (kit-download
  form — superseded in production by `web/upload_images.html`). The
  active SHACL `shapes.ttl` and `ontology.ttl` live alongside the data
  in `web/data/`; the backend reads them from there at startup. The
  former top-level `ontology/` dir (v1.1 `pedalhidrografico.ttl` +
  JSON-LD context) was removed — git history is the only reference.
- `scripts/` — `build-routes.py` (**full rebuild** of `routes.json` from
  `web/data/tours.ttl` + RideWithGPS — NOT the normal path: the backend keeps
  `routes.json` incrementally on every Tour CRUD; this is for bake/recovery
  only, then push via `deploy-cloudrun.sh --state`), `build-clips.py`
  (re-encodes raw videos in `web/clips/raw/` to 360p/720p mp4 + `.m4a` audio +
  thumbnail and writes the triples directly into `web/data/uploads.ttl` as
  `ph:Video` — local **batch** tool; the one remaining local catalog-writer,
  push via `deploy-cloudrun.sh --state-only`), `deploy.sh` (legacy GCS static
  mirror), `deploy-cloudrun.sh` (Cloud Run deploy + `--state` flag to sync
  mutable state; also enables bucket Object Versioning + a lifecycle rule
  idempotently — see Conventions), `pull-cloudrun.sh` (pull mutable state from
  the GCS bucket back to local), `state-history.sh` (list/diff/restore prior
  GCS object generations of a state file — the recovery UX on top of Object
  Versioning), `sync-guard.sh` (anti-clobber guard sourced by
  deploy/pull-cloudrun — see Conventions), `dev-cloudrun.sh` (run the Cloud
  Run image locally — the `deploy-amora.sh` / `pull-amora.sh` /
  `push-clips.sh` / `gcloud-ssh-rsync.sh` / `pi-deploy.sh` family for the
  old GCE VM and Raspberry Pi deploys was removed; amora is Cloud Run now),
  `remux-clips-audio.py` (one-shot migration: muxes audio back into
  pre-v225 silent `web/clips/*.webm` that were transcoded before audio
  was embedded — see the upload-flow note below; removable once all
  clips are re-encoded), `migrate-bnodes-to-iris.py` (one-shot migration:
  converted the historical blank nodes in `tours.ttl`/`uploads.ttl` into the
  derived-IRI convention — idempotent, removable once it's clearly not needed
  again), `gen-synthetic-rdf.py`, `mock_location.sh` (empurra posições de
  teste da localização ao vivo pro backend — random walk, 1 ponto/3 s; bate no
  remoto amora por padrão, `--local` p/ 127.0.0.1:8080; curl não precisa de
  CORS), `exiftool_ph.config`.
  `build-photos.py` and
  `build-routes.mjs` are legacy artefacts pending removal — see "Open
  loose ends".
- `docs/` — design-reference notes not loaded at runtime. `DESIGN.md`
  (RDF substrate / ontology design rationale) and `ICON_DESIGN.md` (PWA
  icon decisions). Excluded from the Cloud Run container.
- `capacitor/` — native iOS/Android shell (Capacitor) that wraps the SAME
  web app. `capacitor.config.json` points `server.url` at
  `https://amora.pedalhidrografi.co` (loads the published site —
  `location.origin` stays amora, so no CORS), with the
  `@capacitor-community/background-geolocation` plugin. The one thing it buys
  over the PWA: **Localização ao vivo keeps transmitting with the screen off /
  app backgrounded** (the background bridge lives in `web/app.js` —
  `window.phidroLivePush`). `run-ios.sh` / `run-android.sh` build+deploy to a
  physical device via `npx cap run` without opening Xcode/Android Studio;
  `npm run icons` regenerates app icon + splash from `assets/` via
  `@capacitor/assets`. `README.md`, plus gitignored `android/`, `ios/`,
  `www/`, `node_modules/`. Edits to `web/` alone need NO native rebuild — the
  app loads the remote site (so iterate by deploying `web/`, not rebuilding).

## Architecture

The app is fully static and works offline (service worker). It reads
pre-baked `routes.json` and resolves Turtle dumps via the manifest at
`web/data/data_graphs.ttl` (which currently lists `tours.ttl` and
`uploads.ttl`). When served by the backend (local or Cloud Run), uploads hit
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

**Nested nodes are minted IRIs, not blank nodes.** The `schema:GeoCoordinates`
(`schema:locationCreated`), `nfo:FileHash` (`nfo:hasHash`), `qudt:QuantityValue`
(`ph:energyEstimate` / `ph:measuredEnergy`), and `ph:RouteReference`
(`ph:linkRoute`) sub-objects use deterministic IRIs derived from the parent —
`<parent>_geo`, `_hash`, `_energy`, `_measured`, `_route` (e.g.
`phd:tour_1_energy`, `phd:image_<phash>_geo`). The trailing `_` keeps siblings
distinct (`phd:tour_1` never prefix-matches `phd:tour_10`). This is what makes
deletion/merge trivial: purging a subject = removing `(subject, *, *)` plus the
`<subject>_*` derived IRIs (`_derived_subjects` / `_purge_subject` in
`backend/main.py`), with no blank-node-reachability walk. Both the TTL emitters
(`upload_images.html`, `upload_tour.html`, `backfill_tours.html`,
`scripts/build-clips.py`) and the validator's re-upload `exclude` set rely on
this prefix convention. (`scripts/migrate-bnodes-to-iris.py` converted the
historical bnode data — git history holds the pre-IRI form.)

Key flows:

- **Display.** `web/app.js` fetches `./data/data_graphs.ttl`, follows each
  `void:dataDump` IRI to load the constituent graphs (currently `tours.ttl`
  and `uploads.ttl`), parses them with the bundled N3.js
  (`web/lib/n3.min.js`), and renders one Leaflet marker per `ph:Image`
  AND `ph:Video` (videos use the same `photoDivIcon` markup as photos with
  a red-orange border modifier `.photo-dot-video`; both participate in the
  same density-based clustering via `relaxPhotoMarkers`). GPS from
  `schema:locationCreated`, popup from triples. The **layer panel** gained
  per-row action icons (fixed column: ▲/▼ to stack inline — the old ordering
  modal was removed — plus an action icon: ☰ Rotas / 📍 Compartilhar / ✨
  Animação / ⬆ Enviar / ✎ or ⚙ config / 🗑) and persists per-layer
  visibility + opacity across sessions. The **Destacar rota ★** button in a
  route's modal draws a ~1.5×-thicker copy and materializes the **Rota
  destacada** layer (hidden until a highlight exists; its 🗑 clears it —
  `addRouteHighlight` / `clearRouteHighlight` / `setRouteHighlightRow`). In the
  trace-edit toolbar the old **Editar** is now **📂 Carregar** (`#trace-load`,
  opens the load-route modal). The **Configurações** modal
  (gear icon in the topbar) lets the user switch between Servidor
  (same-origin; persisted source value `'server'`, legacy `'pi'` is migrated
  on load), CDN, or Local (kit ZIP file picker — stored in memory, image
  URLs become blob URLs). Import/export buttons live there.
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
  `POST /delete-video/<vhash>` purge the IRI's triples (plus its `<iri>_*`
  derived IRIs) from `uploads.ttl` AND delete the underlying blobs from the
  store. The frontend popups have a red-orange Excluir button gated by a
  `confirm()` dialog.
- **Localização ao vivo.** A camada "Pessoas ao vivo" (painel de camadas;
  ligada por default só p/ VER — nunca arranca transmitindo, por privacidade)
  faz polling de `GET /live-locations` e desenha cada pessoa: marcador
  `divIcon` com anel colorido + inicial + (opcional) seta de rumo, esmaecendo
  via `.is-stale` quando o fix envelhece. O rastro é uma linha ligando os
  fixes + pontos cujo tamanho reflete a `accuracy` de cada um (o slider da
  camada controla a opacidade dos pontos, `_liveBandOpacity`). Clicar numa
  pessoa abre um popup p/ ajustar cor/opacidade/esconder o histórico dela
  (persistido em `phidro:livePersonOverrides`). O ícone 📍 da linha abre um
  modal (apelido + retenção hh/mm do rastro, default 3 h) e liga/desliga a
  transmissão da própria posição (token = `crypto.randomUUID()` por
  dispositivo, POST `/live-location`; no browser via `watchPosition`, no shell
  nativo via background-geolocation com a tela apagada). Ver e transmitir são
  flags independentes (`_liveViewing` / `_liveSharing`), reconciliados por
  `applyLiveLocation` a cada mudança de Ajustes / `visibilitychange` /
  `pageshow`.
- **Tour CRUD & Censo.** `POST /upload-tour` accepts a TTL fragment
  describing exactly one `phd:tour_<id> a ph:Tour` (plus any new
  `phd:pessoa*` / `phd:assoc_*` declarations it references) and upserts
  it into `web/data/tours.ttl`. Two modes via the `mode` form field:
  `replace` (default — the TTL is the tour's complete new state,
  purge-and-replace; right for creation) and `patch` (predicate-level
  merge-patch — only predicates asserted in the TTL, plus those listed
  in the comma-separated `remove` form field as CURIEs/IRIs, replace
  the existing ones; everything else survives, so clients don't have
  to round-trip predicates they don't know about). Patch is synthesized
  server-side into the equivalent full document inside the state lock
  (`synthesize_tour_patch`), so SHACL validates the FINAL state and the
  rest of the pipeline (announcement injection, route sync) is shared.
  Both forms use patch for edits; creation stays on replace. An optional
  `announcement` file field is saved under
  `tour_assets/<tour_id>/announcement.<ext>` and wired in as
  `schema:image <URL>` before the triples are persisted (under `patch`,
  a new file also replaces the current `schema:image`).
  `POST /delete-tour/<tour_id>` removes the tour's triples + its `<iri>_*`
  derived IRIs and purges `tour_assets/<tour_id>/`; it deliberately does NOT
  delete referenced `phd:pessoa*` or series — git history preserves
  those and they may be referenced by other tours.
  On every `/upload-tour` and `/delete-tour`, the backend also **syncs
  `routes.json` incrementally**: if the tour (read from the PERSISTED
  `tours.ttl`, not the posted fragment — the entry's series numbering
  resolves `phd:assoc_*` subjects that live outside the fragment) has a
  `ph:linkRoute` pointing at a RideWithGPS route, it fetches the geometry
  and upserts that tour's entry (keyed by `tourIri`); if the link is
  absent (new/edited tour with no route) or the tour is deleted, it
  removes the entry. The RWGPS
  fetch runs **outside** the global state lock (only the JSON read-modify-
  write is serialized) and is best-effort — a fetch failure never fails the
  tour save (the entry is kept with `latlngs:null` + `error`, same convention
  as `build-routes.py`). The shared fetch/parse/entry-building logic lives in
  `backend/rwgps.py`, imported by both the backend and
  `scripts/build-routes.py` (single source of truth). The backend reads
  `RWGPS_API_KEY` / `RWGPS_AUTH_TOKEN` from its environment (best-effort
  `.env` load) — required for private/unlisted routes; public routes work
  without. `routes.json` is **mutable state served bucket-first** (like
  `uploads.ttl`) via `GET /routes.json`, with the baked file as seed/fallback.
  `web/upload_tour.html` is the per-tour form (series, sequence, energy
  estimate, intensity, attendee/newcomer counts, announcement art; edit
  mode via `?id=` submits `mode=patch` + a `remove` list of the form-
  managed predicates left empty); `web/backfill_tours.html` is the
  mass-backfill applet (one card per tour, only the seven backfill
  fields — description, departed/arrived, moving duration, energies,
  announcement image — sends a per-tour patch of just the changed
  fields); `web/censo.html` shows aggregated metrics + a sortable tour
  roster with "Editar" links pointing at `upload_tour.html?id=<tour_id>`.
  The main app exposes Censo through a modal iframe — opened by the
  "Censo →" sidebar link in the Routes panel — and the iframe is
  re-pointed to `./censo.html` on every open so navigating into the edit
  form internally doesn't strand the user there on re-open.
- **Backend endpoint summary.** Static: `GET /` (com SSR mínimo por
  passeio quando há `?tour=<id>`: troca title/description/canonical/OG,
  injeta JSON-LD NewsArticle + um `<article>` renderizado de `tours.ttl`
  pra crawlers/no-JS — o app remove o nó ao abrir o modal do deep link;
  render é best-effort e degrada pro index estático), `GET /<path:p>`,
  `GET /data/<filename>`, `GET /photos/<path:p>`, `GET /clips/<path:p>`,
  `GET /tour_assets/<path:p>` (in `gcs` mode the last three 302-redirect
  to the bucket's public URL), `GET /feed.xml` (RSS 2.0 dos passeios,
  renderizado de `tours.ttl` e cacheado por hash do catálogo — atualiza
  sozinho a cada tour CRUD), `GET /sitemap.xml` (dinâmico, sobrepõe o
  estático: home + `/?tour=<id>` por passeio — deep link que o app abre
  no modal da rota — com bloco Google News pros passeios das últimas
  48 h; cache por hash + TTL de 1 h). Ops: `GET /health`, `POST /reload`
  (force re-read of the on-disk TTL catalog after an out-of-band edit).
  Mutations: `POST /upload-image`, `POST /upload-video`,
  `POST /upload-tour` (`mode=replace|patch` + `remove` — see Tour CRUD),
  `POST /delete-image/<phash>`, `POST /delete-video/<vhash>`,
  `POST /delete-tour/<tour_id>`. Localização ao vivo (efêmera, EM MEMÓRIA —
  NÃO toca os catálogos): `POST /live-location` (upsert da posição + rastro de
  um token pseudônimo; body JSON `{id, name?, lat, lng, accuracy?, heading?,
  ttl?}`; rastro thinned por tempo/distância, teto 500 pts/pessoa e 500
  pessoas), `GET /live-locations` (posições não-expiradas + rastro de cada
  uma; `Cache-Control: no-store`, sem ETag), `POST /live-location/stop` (apaga
  o próprio token na hora — NÃO chamado automaticamente; fica p/ um "apagar
  meu rastro" explícito). Estado em `_live_positions` (dict por token sob
  `_live_positions_lock`), retenção por token (`ttl` em s, default 3 h, teto
  24 h, podada em `_prune_live`). CORS é aberto SÓ nestes endpoints
  (`_LIVE_CORS_ORIGINS` = `capacitor://` / `ionic://` / `http(s)://localhost`,
  via `@app.after_request _live_cors`) pro shell nativo Capacitor — uploads/
  CRUD seguem same-origin. Estado por-processo: no Cloud Run **exige a
  instância fixa em 1** (min=max=1), senão POST e GET caem em processos
  diferentes e o app não vê (mesma razão do `--workers 1`).

## Clips workflow

Source videos in `web/clips/raw/` (`.MOV`/`.mp4`/`.m4v`). Run:

```sh
python scripts/build-clips.py
```

Requires `ffmpeg` and `exiftool` in `$PATH` (Homebrew on macOS, `apt` on
Linux). For each source the script:

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
- **No backend auth.** Anyone who can reach the server can upload/delete —
  this is an intentional decision (trusted access assumed). Don't reintroduce
  a token; restrict at the edge if needed.
- **Ontology:** reuse consolidated vocabularies (schema.org, PROV-O, QUDT,
  GeoSPARQL, Dublin Core); mint `ph:` terms only for what is specific to
  Pedal Hidrográfico.
- **Cloud Run is the hosted deploy target** at
  `https://amora.pedalhidrografi.co/` via `scripts/deploy-cloudrun.sh`;
  the same backend (`backend/main.py`) also runs locally for dev or
  self-hosting — `storage.py` abstracts state via `STORAGE_BACKEND=local`
  (filesystem) vs `gcs` (bucket). The old Raspberry Pi deploy was retired.
  `scripts/deploy.sh` (the old read-only static mirror at
  `tiles.pedalhidrografi.co/rotas_app`) is still around but largely
  superseded.
- **gunicorn runs with `--workers 1` everywhere** (Dockerfile, .plist).
  The mutation lock (`_state_lock`) is per-process; with 2+
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
- **The server is the sole writer of the catalogs in normal ops.** Photo/
  video uploads, Tour CRUD, and deletes all go through the backend
  (`upload_*.html` forms → POST); `routes.json` is server-owned (incremental
  sync on Tour CRUD). The only local catalog-writers left are the **batch/
  recovery** scripts: `build-clips.py` (writes `uploads.ttl`) and
  `build-routes.py` (full `routes.json` rebuild). Treat them as round-trip:
  `pull-cloudrun.sh` → run → `deploy-cloudrun.sh --state[-only]` (sync-guarded).
  Don't hand-edit `tours.ttl`/`uploads.ttl` — edit tours via
  `upload_tour.html?id=` (`mode=patch`) or `backfill_tours.html`; if you must
  hand-edit, pull first and push immediately through the guarded scripts.
- **The bucket has Object Versioning + a lifecycle rule** (enabled idempotently
  on every `deploy-cloudrun.sh`, mirroring the CORS block). Every server write
  to a state file keeps the prior generation; noncurrent versions expire after
  90 days (`daysSinceNoncurrentTime` — never `age`, which would delete live
  objects). This is the recovery net for a clobber / bad purge / lost update.
  Browse + recover with `scripts/state-history.sh list|diff|restore <file>`;
  `restore` is non-destructive (writes a new current generation) — follow it
  with `POST /reload` so the backend re-reads. Local (`STORAGE_BACKEND=local`)
  has no equivalent; history there is just git for the tracked TTLs.
- **GCS read gotcha (Cloud Run).** Always use `bucket.get_blob(key)`
  rather than `bucket.blob(key) + download_as_text()` — the bare-blob form
  produced silently-stale content in Cloud Run despite the bucket having
  one current generation. See `GCSStateStore.read_text` in
  `backend/storage.py` for the fix.
- **Cloud Run container stays magrinho.** `.gcloudignore` /
  `.dockerignore` exclude `web/photos/` and `web/clips/` entirely (not
  just `raw/`). The runtime handlers `/photos/<path>` and `/clips/<path>`
  redirect to the bucket's public URL in `gcs` mode (302 → much faster
  than streaming through Flask). To populate the bucket with local
  `build-clips.py` outputs and locally-collected uploads, run
  `scripts/deploy-cloudrun.sh --state-only`.
- Comments and UI strings are in Portuguese; code identifiers in English.

## Verify before finishing

- JS in `web/`: load it in a browser (or the existing dev server) — the
  browser surfaces syntax errors immediately. No standalone JS tooling here.
- Bump `web/sw.js` `VERSION` if any file under `web/` changed.
- `python -m py_compile backend/main.py`
- Ontology / shapes / data: parse with `rdflib` after editing `*.ttl`.

## Build & deploy

- `python scripts/build-routes.py` — **full rebuild** of `web/routes.json` by
  reading `web/data/tours.ttl` (the Tour catalog) and fetching each
  referenced GPX from RideWithGPS. Requires `python-dotenv` plus
  `RWGPS_API_KEY` / `RWGPS_AUTH_TOKEN` in `.env`. **Not the normal path** —
  the backend keeps `routes.json` incrementally on every Tour CRUD; use this
  only for bake/recovery, then push via `deploy-cloudrun.sh --state`.
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
    `data_graphs.ttl`, `routes.json`, `photos/`, `clips/`, `tour_assets/`)
    to the bucket
  - `--state-only` just sync mutable state, skip rebuild
  - `--mirror` make the bucket an exact mirror of local (deletes objects
    that no longer exist locally; pairs with `--state`/`--state-only`)
  - `--force` override the anti-clobber guard (see Conventions)
  - `--dry-run` preview without executing
- `bash scripts/deploy.sh` (or `bash scripts/deploy.sh --dry-run`) — sync
  `web/` to the legacy GCS static mirror (read-only; needs `gcloud` auth).
- Local backend: `pip install -r backend/requirements.txt && python backend/main.py`
  (defaults to port 8000; override with `PORT=…`). See `backend/README.md`.

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
  of the backend — gitignore or commit per your deploy strategy. The CDN
  mirror shows no photos until those files exist at the destination.
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
