# Pedal Hidrográfico

Static-PWA web map for an urban cycling collective in São Paulo, plus a
self-hosted backend, Python automation scripts, and an RDF ontology. No cloud
dependency — the project deliberately walked away from GCP and is now
local-first.

## Repo layout

- `web/` — the app. A static PWA: `index.html`, one big `app.js` (single
  file, no build step), `style.css`, `sw.js` (service worker),
  `manifest.json`, icons, `lib/{utils.js,n3.min.js}` (N3.js vendored).
  Leaflet-based map. Also hosts `upload_images.html` (per-photo upload form)
  and the `data/` + `photos/` directories the app reads from.
- `backend/pi/` — the self-hosted backend. One Flask service (`main.py`)
  that serves `web/` as static files **and** validates+stores incoming
  photos. No SQLite; state lives in `web/data/photos.ttl` (catalog) +
  `web/photos/<phash>/{original,large,thumb}.*` (image variants).
  `phidro.service` (systemd) / `phidro.plist` (launchd),
  `requirements.txt`, `README.md`. Runs on a Raspberry Pi or macOS.
- `research/photos-rdf/` — the RDF substrate. `ontology.ttl` +
  `shapes.ttl` (SHACL — what the Pi validates against), `data/tours.ttl`
  (catalog of historical rides, generated from a TSV by `build-tours.py`),
  `data/initial-data.ttl` (person declarations + demo image),
  `upload-form.html` (batch download-kit form), `DESIGN.md`.
- `ontology/` — the older RDF vocabulary (`pedalhidrografico.ttl`, v1.1)
  with a JSON-LD context. Superseded by `research/photos-rdf/`; kept for now.
- `scripts/` — `build-routes.py` (bakes `routes.json` from RideWithGPS),
  `coletor_*.py` (legacy photo collectors), `deploy.sh` (GCS static deploy).

## Architecture

The app is fully static and works offline (service worker). It reads
pre-baked `routes.json` and a Turtle catalog at `web/data/photos.ttl`.
When served by the Pi backend, uploads hit `POST /upload-image` same-origin;
on a static-only host (CDN) the form is offline-friendly but uploads have
nowhere to go.

**Photos are described in RDF/Turtle** per the SHACL shapes in
`research/photos-rdf/shapes.ttl` (notably `ph:ImageShape`). One photo =
one `phd:image_<phash16>` IRI. `phash` is a 64-bit perceptual hash (pHash,
DCT-based, computed in the browser); near-duplicate uploads share an IRI
and naturally cluster.

Key flows:

- **Display.** `web/app.js` fetches `./data/photos.ttl`, parses it with the
  bundled N3.js (`web/lib/n3.min.js`), and renders one Leaflet marker per
  `ph:Image` (GPS from `schema:locationCreated`, popup from triples).
  The **Source** modal (`🗂 Fonte…` in the topbar) lets the user switch
  between Pi (same-origin), CDN, or Local (kit ZIP file picker — stored in
  memory, image URLs become blob URLs). Import/export buttons live there.
- **Upload.** `web/upload_images.html` is the operational form. Each card =
  one photo with EXIF auto-fill, tour auto-detect, multi-select people
  (Tom Select w/ create-on-the-fly), license + anonymize/compress toggles.
  Each card POSTs `multipart/form-data` to `/upload-image` with a
  self-contained single-image TTL block + `original`/`large`/`thumb`
  variants. The Pi validates with pyshacl, writes files into
  `web/photos/<phash>/`, and merges the triples into `web/data/photos.ttl`
  (deduping by IRI). pHash dedup prevents accidental re-uploads in the
  same batch.
- **Validation.** `pyshacl` loads `research/photos-rdf/{shapes,ontology}.ttl`
  once per process. The validator merges the incoming TTL with the
  ontology before checking — `pyshacl`'s `ont_graph` parameter does NOT
  expose ontology-declared instances (like `ph:rwgps a schema:Organization`)
  to `sh:class` checks, so manual merging is mandatory. See
  `research/photos-rdf/DESIGN.md` §2 for the full gotcha.

## Conventions — please follow

- **Bump `sw.js` `VERSION`** (currently `phidro-v51`) on *any* change to
  files in `web/` — otherwise the service worker serves stale cached
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

- JS in `web/`: load it in a browser (or the existing dev server) — the
  browser surfaces syntax errors immediately. No standalone JS tooling here.
- `python -m py_compile backend/pi/main.py`
- Ontology: parse with `rdflib` after editing `*.ttl`.

## Build & deploy

- `python scripts/build-routes.py` — regenerate `web/routes.json`
  (requires `pip install python-dotenv` and credentials in `.env`).
- `python research/photos-rdf/build-tours.py` — regenerate
  `research/photos-rdf/data/tours.ttl` from the TSV in the same dir.
  `web/data/tours.ttl` is a symlink to this file.
- `bash scripts/deploy.sh` (or `bash scripts/deploy.sh --dry-run`) — sync
  `web/` to the GCS static mirror (read-only; needs `gcloud` auth).
- Pi: `pip install -r backend/pi/requirements.txt && python backend/pi/main.py`
  (defaults to port 8000; override with `PORT=…`). See `backend/pi/README.md`.

## Open loose ends

- **Retire** `scripts/build-photos.py` — its photos.json artifact is gone;
  uploads now flow through `web/upload_images.html` → Pi → `web/data/photos.ttl`.
  Pillow/HEIF dropped from `backend/pi/requirements.txt`. User-deletes:
  `git rm scripts/build-photos.py`.
- **Legacy data dirs** under `backend/pi/data/` (`fotos/`, `originals/`,
  `photos.db`, voice ZIPs) are orphaned — the new backend stores nothing
  there. Inspect and `rm -rf` at your own pace.
- Local cleanup the user runs: `git rm --cached web/.DS_Store` (tracked
  despite `.gitignore`).
- `web/data/photos.ttl` and `web/photos/<phash>/` are runtime artifacts of
  the Pi — gitignore or commit per your deploy strategy. The CDN mirror
  shows no photos until that catalog exists at the destination.

## Notes

- Working files we changed this cycle are likely uncommitted — check
  `git status` and commit with meaningful messages.
- Permanent deletions (files, data) should be left to the user — provide the
  commands rather than running them.
