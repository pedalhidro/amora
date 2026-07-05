# Plan: upload form at batch scale (~90 HEIC + ~10 MOV per batch)

**Handoff plan — self-contained.** Execute Phase A first, verify, then Phase B.
Written 2026-07-04 against `web/upload_images.html` @ 2092 lines (sw `phidro-v300`).

> ⚠️ **Line numbers drift.** All anchors below were verified against v300, but this
> file gets edited. Re-locate every anchor **by symbol name** before editing; treat
> line numbers as hints only.
>
> ⚠️ **Read `CLAUDE.md` (repo root) first.** Load-bearing conventions used below:
> Portuguese comments/UI strings, English identifiers; bump `web/sw.js` `VERSION`
> on any `web/` change; changelog entry in the Ajuda modal; no backend auth; the
> backend runs `--workers 1` with a global `_state_lock`; commits are the user's
> call — stop and ask before committing.
>
> ⚠️ **Unrelated dirty files.** `capacitor/assets/*.png` (modified), `.vscode/`,
> `REVIEW_HANDOFF.md` are other workstreams — do not touch, stage, or clean them.

---

## 1. Problem

Selecting ~68 mixed photos/videos in a smartphone browser loads ~15 cards then
the tab crashes (OOM). Target batch profile: **~90 HEIC images + ~10 MOV videos
(10–30 s); hard ceiling 2× that (180 + 20).**

### Root cause (verified)

Per accepted image card, retained for the card's whole lifetime:

1. **`card.bitmap`** — the full-res decoded `ImageBitmap`, stored in the card
   object in `createImageCard` and only consumed at upload time by
   `buildVariants`. 12 MP ≈ 46 MB RGBA each. **This is the OOM.**
2. **Full-res thumbnail decode** — `buildCardElem` sets
   `$('.card-thumb', elem).src = URL.createObjectURL(file)`, so the browser
   decodes the entire photo a second time to paint a 56 px `<img>`.
3. **2 eager Tom Select instances per card** (`initPersonSelect` ×
   author/provider) — 360 instances at the 180-card ceiling.
4. For HEIC inputs, `card.file` is the **in-memory** heic2any-converted JPEG
   (not a disk-backed File).

Videos: every accepted card immediately mounts `<video preload="metadata">`
with a full-file object URL (assigned in `createVideoCard`, NOT in
`buildVideoCardElem`); no cap, no lazy loading. iOS Safari also caps live
media elements, so 10–20 mounted `<video>`s degrade independently of memory.

The picker loop (`$('#files')` change handler) is strictly sequential
(required: dedup must see just-accepted cards) but never yields to the event
loop and only updates `#filesStatus` **after** the whole batch.

---

## 2. Phase A — crash fixes (client-only, `web/upload_images.html`)

### A1. Do not retain `card.bitmap`; re-decode at upload

- In `createImageCard`: after `phash = computePHash(bitmap)` **and** after A2's
  thumb generation, call `bitmap.close()`. Do **not** store `bitmap` on the
  card object (remove it from the card literal).
- In `buildVariants`: decode fresh at the top —
  `const bitmap = await createImageBitmap(card.file, { imageOrientation: 'from-image' })`
  — use it for `compressToTarget` / `anonymizeJpeg` / `makeThumbnail`, and
  `close()` it in a `finally`.
  - **MANDATORY: keep `{ imageOrientation: 'from-image' }`.** Without it,
    browsers hand back unrotated pixels and every portrait iPhone photo
    uploads sideways in `large`/`original`. The existing decode in
    `createImageCard` has a comment explaining this — read it.
- In `uploadImageCard`: the readiness guard is
  `if (!card.phash || !card.bitmap)` — change to `if (!card.phash)`, or every
  upload fails with "imagem não pronta".
- In `removeCard`: delete the now-dead `card.bitmap?.close?.()` line.
- Safe because the picker loop and `uploadAll` are both strictly sequential —
  at most one decoded bitmap is ever live. Result: peak memory
  O(N·46 MB) → O(1·46 MB).

### A2. Card thumbnail from a 256 px blob, not the full-res file

- In `createImageCard`, while the bitmap from A1 is still open:
  `card.thumbBlob = await makeThumbnail(bitmap)` (existing helper, 256 px
  q0.75).
- Set the card thumb from that blob's object URL instead of the current
  full-file object URL in `buildCardElem` (either pass the blob in, or set
  `src` after `buildCardElem` returns and leave the builder's `src` line out).
  Revoke the object URL on the `<img>`'s `load` event.
- In `buildVariants`, reuse it: `const thumbBlob = card.thumbBlob ?? await makeThumbnail(bitmap)`.
- `removeCard` already revokes `.card-thumb` src — keep that working.

### A3. Lazy init: Tom Selects and video previews

One `IntersectionObserver` (`rootMargin: '200px'`), observing each card on
creation; on first intersection, initialize and unobserve. Also initialize on
first `focusin` of the card (covers keyboard/programmatic access before
scroll).

- **Tom Select** (both card kinds): keep the plain `<select multiple>` until
  activation, then run the existing `initPersonSelect` pair.
  - Batch defaults (`defaults.authors`/`providers`) currently applied via
    `card.authorTs.setValue(...)` at creation: store them as
    `card.pendingAuthors` / `card.pendingProviders` and apply at TS init.
  - Every reader of `card.authorTs.getValue()` (TTL builders — grep for
    `authorTs` / `providerTs`) must fall back to the pending arrays when the
    TS is not yet initialized. Add one helper (e.g. `personValues(card,
    'author')`) and use it everywhere.
  - `removeCard`/`destroyPersonSelect` must tolerate null TS.
  - `mintPerson` pushes new options into live instances via `personSelects`;
    late-initialized instances clone `[...personOptions]` at init, so they
    pick new persons up automatically — no extra work.
- **Video preview**: in `createVideoCard`, do not set `preview.src` at
  creation. On activation, set `preview.src = URL.createObjectURL(card.file)`.
  - The `loadedmetadata` handler is what sets `card.duration`, slider `max`,
    initial trim values, and **enables the send button** — it now runs at
    activation. `uploadVideoCard` must therefore not depend on
    `card.duration` being set before activation (its existing trim guards
    already reject a 0-length window, but verify the flow: an unactivated
    card's send button stays disabled, which is acceptable — activation
    happens as soon as the card is near the viewport or focused).
  - `removeCard` already revokes `.card-video-preview` src *if set* — verify
    the conditional survives.

### A4. Yield + per-file progress in the picker loop

In the `$('#files')` change handler loop (keep it sequential — dedup
requires it):

- Before each file: `$('#filesStatus').textContent = 'processando i/N — <nome>…'`.
- After each file: `await new Promise(r => setTimeout(r))` (one macrotask
  yield — lets the browser paint, run GC, and stay responsive).
- Keep the existing final tally line.

### A5. Screen wake lock during batch intake and uploadAll

- Helper: `navigator.wakeLock?.request('screen')` (feature-detected, failures
  swallowed); release in `finally`; re-acquire on `visibilitychange` →
  `visible` while a batch/upload run is still active.
- Wrap: the picker-loop body (only when `files.length > 5`) and the whole of
  `uploadAll`.
- Rationale: a max batch is ~30–60 min of foreground work
  (videos transcode in **real time**: audio pass + 720p pass + 360p pass ≈
  3× clip duration each — see the MediaRecorder/rAF design in
  `transcodeAtShortSide`; backgrounding kills it by design, the watchdog
  fires). The wake lock attacks the actual failure mode: screen sleeps →
  tab suspended → batch dies.

### A6 (optional, small). Cache video transcode outputs for retry

`card.processed` is declared (`{ audio, blob360, blob720 }`) but never
written — every `uploadVideoCard` retry redoes thumb + audio + two realtime
transcodes (~3× clip duration). After a successful local processing pass,
store the blobs + the trim values they were cut at on `card.processed`; on
retry, reuse iff trim values match. Compressed outputs are ~5–15 MB/card ×
≤20 cards — acceptable. Skip this item if anything is unclear; it is not
load-bearing.

### A7. Bookkeeping (mandatory)

- Bump `web/sw.js` `VERSION` (`phidro-v300` → next integer; check current
  value at execution time).
- Add a changelog entry in `web/index.html` inside
  `<details class="help-changelog">`, matching the existing format exactly
  (`<dt>DD/MM/YYYY · vNNN</dt><dd><ul><li>…`), in Portuguese, e.g.:
  *"Formulário de envio: lotes grandes (90+ fotos/vídeos) não travam mais o
  navegador do celular — memória constante, progresso por arquivo e tela
  mantida acesa durante processamento e envio."*
- All new comments/UI strings in Portuguese; identifiers in English.

### Phase A verification

1. Load the form in a desktop browser (surfaces syntax errors immediately —
   there is no JS tooling in this repo).
2. Desktop Chrome, DevTools → Memory: add a 90+ image batch (generate
   synthetic large JPEGs if needed); heap + GPU memory must stay ~flat per
   card (was: +~90 MB/card). All cards must appear, with per-file progress.
3. **Orientation regression (critical):** upload one portrait iPhone photo;
   confirm the stored `large.jpg` renders upright (run the backend locally:
   `pip install -r backend/requirements.txt && python backend/main.py`,
   `STORAGE_BACKEND=local`).
4. Dedup regression: re-add the same file twice in a batch → second rejected;
   re-add an already-uploaded image → rejected (server-hash path).
5. Tom Select: on a big batch, scroll to a late card, add an author (create
   a new person too), remove a card, use the batch defaults — all must work.
6. Video: add 5+ videos; previews appear when scrolled to; trim + upload one
   end-to-end against the local backend.
7. Real device (iOS Safari): the original failing batch (~68 mixed) must
   fully load and upload.

---

## 3. Phase B — HEIC originals end-to-end (no conversion in the common path)

**Design (decided, don't re-litigate):** iPhone Safari can decode HEIC
natively via `createImageBitmap`. Send the **raw HEIC file** as the
`original` variant; keep client-built JPEG `large`/`thumb`. `heic2any`
becomes a cold-path fallback for browsers without native HEIC decode
(desktop Chrome/Firefox). **No server-side conversion, no pillow-heif** — the
backend already accepts and correctly content-types `heic`/`heif` originals.

Verified backend facts (no backend code change expected):

- `POST /upload-image` (`backend/main.py`, search `variant == "original"`):
  original's extension whitelist is `jpg/jpeg/png/heic/heif` (else coerced to
  `jpg`; `jpeg`→`jpg`), stored at `photos/<phash>/original.<ext>` with correct
  content-type. `large`/`thumb` are always `.jpg`.
- SHACL (`web/data/shapes.ttl`): `ph:ImageShape` requires only `dcterms:date`
  + `schema:locationCreated` at Violation level; **no `sh:closed` anywhere,
  no contentUrl/extension constraints; variant URLs are not modeled in RDF
  at all** — clients derive `photos/<phash>/{original,large,thumb}` by
  convention.

### B1. Picker accept attribute

`<input type="file" id="files" accept="image/*,video/*" multiple>` →
`accept="image/*,image/heic,image/heif,video/*"`. With the explicit HEIC MIME,
iOS hands over the original bytes instead of transcoding at pick time
("Preparando…" disappears; picking 90 files gets much faster). Behavior
varies by iOS version — verify on device; both outcomes (JPEG or HEIC
delivered) are handled.

### B2. Native-decode-first in `createImageCard`

Restructure the HEIC branch: **try `createImageBitmap(file,
{ imageOrientation: 'from-image' })` first for all files.** Only if it throws
*and* `isHeicFile(file)`, fall back to the current heic2any conversion
(which reassigns `file` to a JPEG) and decode again. Keep the existing
error cards (`heic-unavailable`, `heic-convert-failed`, `decode-error`).

Consequences to preserve/verify:

- On the native path, `card.file` stays the **disk-backed raw HEIC** (also
  removes the in-memory-JPEG retention noted in §1.4).
- `exifr.parse(file, ...)` (runs after card creation) now parses the raw
  HEIC. exifr's full build reads HEIC metadata — EXIF auto-fill (date/GPS/
  bearing/focal) likely starts *working better* than today, since heic2any's
  canvas re-encode probably strips EXIF (the in-code comment claiming
  otherwise is unverified). If exifr fails on some HEIC, behavior degrades to
  today's (fields stay empty) — acceptable.
- `buildVariants` no-comp/no-anon path already does `originalBlob = card.file`
  with extension preserved → `original.heic` reaches the backend. With
  `comp`/`anon` checked the original is a canvas JPEG named `original.jpg` —
  unchanged, correct.
- `copyExifSegment(card.file, largeBlob)` has a non-JPEG guard (returns the
  target untouched), so `large.jpg` for HEIC uploads carries no embedded
  EXIF. Accepted: the metadata lives in the RDF, and the bit-exact original
  is preserved — the archival win is the point.
- **pHash compatibility risk (accepted, must verify):** HEIC pHashes were
  previously computed from the heic2any JPEG; natively decoded pixels may
  differ by a few bits. Threshold is Hamming ≤ 5. Verify: pick a HEIC whose
  converted form was already uploaded → must still be rejected as duplicate.
  If distances land near the threshold in testing, flag it in the summary —
  do not silently raise the threshold.

### B3. Record the original's format in RDF

In the image TTL emitter (`buildImageBlock` / the single-image TTL builder),
when the original variant will keep a non-`jpg` extension (HEIC native path;
also PNG picks), add to the image node:
`schema:encodingFormat "image/heic"` (or `"image/png"`).

- Reuses schema.org (repo convention: no new `ph:` term needed).
- `shapes.ttl` has no closed shapes → validates as-is. Parse a sample with
  `rdflib` and run one end-to-end upload against the local backend to
  confirm SHACL passes.

### B4. `app.js`: stop hard-coding `original.jpg` (also fixes a latent PNG bug)

`resolvePhotoUrl(phash, variant)` in server/CDN mode returns
`./photos/<phash>/<variant>.jpg` unconditionally — so "Baixar original"
(popup), `bulkDownloadPhotos(…, 'original', …)`, and the kit export would
404/mislabel any non-JPEG original. (This is *already* broken today for PNG
originals — B3+B4 fix that too.)

- Where photo models are built from `uploads.ttl` (search for the block
  assembling `{ file, thumb, full }` via `resolvePhotoUrl`), read the new
  optional `schema:encodingFormat` triple; map MIME → extension
  (`image/heic`→`heic`, `image/png`→`png`, default `jpg`); thread it into the
  `'original'` case of `resolvePhotoUrl` (extra parameter or a small lookup).
  `large`/`thumb` stay `.jpg`.
- Kit export writes `original.jpg` regardless of true type (search
  `[['large'` in app.js) — use the real extension there too. The localKit
  probe list already tries `original.{jpg,png,heic,jpeg}` — unchanged.
- Old catalog entries without the triple default to `.jpg` — backward
  compatible.

### B5. Bookkeeping + verification

- Bump `sw.js` `VERSION` again (or once if A+B ship together); changelog
  entry (PT), e.g.: *"Fotos HEIC do iPhone: seleção mais rápida (sem conversão
  no aparelho) e o arquivo original é preservado bit a bit no acervo."*
- Verify: on-device HEIC pick (card name ends `.heic`?); EXIF auto-fill
  populates; upload end-to-end; popup → "Baixar original" downloads the HEIC
  (server mode); markers/popup image (large.jpg) unaffected; desktop Chrome
  HEIC still works via heic2any fallback; dedup-vs-server check from B2;
  `python -m py_compile backend/main.py` only if the backend was touched
  (it shouldn't be).

---

## 4. Explicit non-goals (decided — do not do)

- **No server-side video transcoding.** Raw 30 s MOVs are 30–170 MB: over
  Cloud Run's 32 MiB HTTP/1 request cap, and ffmpeg would occupy the single
  pinned instance (min=max=1, `--workers 1`) for minutes, stalling everyone.
  Client-side realtime transcode stays.
- **No pillow-heif / server-side image conversion.** Not needed (see §3).
  If it is ever added later, the CPU work must run *outside* `_state_lock`
  (note: today `/upload-image` runs entirely *inside* it via `@serialized`).
- **No pHash algorithm/decode-path changes** beyond B2's source swap (e.g.
  do not use `createImageBitmap` resize options for the 32×32 downscale) —
  hashes must stay comparable with the server's existing catalog.
- **No parallelizing the picker loop** — in-batch dedup depends on sequential
  processing.
- **No re-introducing auth, no touching ETag/compression handlers** (see
  CLAUDE.md — both are load-bearing).
- Known pre-existing issues, out of scope: `upload_images.html` imports
  N3/exifr/heic2any/JSZip from CDNs without SRI (dynamic `import()` can't
  carry integrity; N3 here is *not* the vendored copy app.js uses);
  `existingPhashes` linear scan per file; EXIF fill racing the send button.

## 5. Suggested execution order

A1+A2 (one commit-sized change, the crash fix) → verify §2 items 1–4 →
A3–A5 (+A6 if confident) → verify 5–7 → A7 → **pause; user verifies on their
device** → Phase B (B1–B4) → B5 verification → done. Ask the user before
each commit.
