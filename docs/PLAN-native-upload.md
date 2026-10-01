# Plan: native picker + background upload in the Capacitor shell (iOS + Android)

**Handoff plan — self-contained.** Written 2026-10-01 against `web/subir.html`
@ 1754 lines (sw `phidro-v420`), `capacitor/` on Capacitor 6.2.

> ⚠️ **Line numbers drift.** Re-locate every anchor by symbol name.
>
> ⚠️ **Read `CLAUDE.md` (repo root) first.** Load-bearing here: Portuguese
> comments/UI strings, English identifiers; bump `web/sw.js` `VERSION` + Ajuda
> changelog on any `web/` change; no backend auth; every push to `main`
> deploys `web/` to production; `capacitor/ios/` and `capacitor/android/` are
> generated and gitignored (anything native that must survive lives in a
> tracked dir or is re-applied by `run-ios.sh` / the plugin's own manifest).
>
> ⚠️ **Do the spikes (§8) before writing the real code.** Several assumptions
> below are verified only by reading Capacitor's source, not on a device.

## Status (2026-10-01) — Android built and tested on an emulator; iOS in progress

**On-device results (Android 15 emulator on the workbox, `google_apis` x86_64,
driven over adb + raw CDP into the app's WebView; backend = local copy):**

- **Spike A1 settled — the picker is the DOCUMENT picker, not the Photo
  Picker.** Measured with GPS-tagged JPEGs:

  | Route | GPS in the copy | Permissions |
  |---|---|---|
  | Photo Picker (`PickVisualMedia`) | **zeroed** (fields present, values NaN), even with `ACCESS_MEDIA_LOCATION` granted; `setRequireOriginal` on its URI → `UnsupportedOperationException` | none |
  | Photo Picker id → MediaStore URI + `setRequireOriginal` | kept | `READ_MEDIA_*` ("Allow all") + `ACCESS_MEDIA_LOCATION` → Play declaration |
  | **`ACTION_OPEN_DOCUMENT` (DocumentsUI, `media.documents` provider)** | **kept, byte-identical original, real file name** | **none** |

  So the plugin defaults to the document picker and declares no media
  permission at all (`source: 'photos'` still opens the Photo Picker, GPS-less,
  as a fallback). Requesting `ACCESS_MEDIA_LOCATION` alone would have shown
  "Allow Amora to access photos and videos?" — it's in the photos group.
  Re-check on real phones (other Android versions, OEM DocumentsUI).
- Full flow through the real UI (📤 → Escolher → 3 photos): uploaded,
  originals byte-identical, GPS in `images.ttl`, real names in the cells.
- Airplane mode → pick → HOME + `am kill` → network back: Android started a
  fresh process for `UploadWorker` and the photo was on the server **8 s**
  later; the "1 arquivo enviado pro amora" notification posted; reopening the
  app, `/subir` reconciled the cell ("enviada · em segundo plano").
- On Android the iframe DOES get its own `window.Capacitor`
  (`addDocumentStartJavaScript` reaches same-origin frames); the page still
  prefers the parent's, so both platforms behave the same.
- Debug builds log every `putBlob` base64 chunk to logcat (Capacitor's
  `loggingBehavior: debug`) — noisy, release builds don't.

**iOS (written, not yet compiled):** `ios/Sources/AmoraUploadPlugin/`
`Store.swift` (port of `Store.java`, except a `sending` job is NOT reset at
launch — a background transfer survives the app's death, so `UploadQueue`
reconciles with `getAllTasks` instead), `UploadQueue.swift` (public
`AmoraUploadQueue`: background `URLSession`, one upload task per job from a
streamed `body.bin`, backoff via `earliestBeginDate` so the OS schedules
retries with the app dead) and `AmoraUploadPlugin.swift` (PHPicker without
`photoLibrary:` → no permission prompt; `.current` so videos arrive as the
original HEVC with no transcode wait; photos as JPEG; file URL =
`bridge.portablePath`, i.e. `capacitor://localhost/_capacitor_file_…`).
`AmoraUpload.podspec` at the plugin root; `run-ios.sh` now re-applies the
AppDelegate `handleEventsForBackgroundURLSession` hook (tested idempotent on
a copy). Builds run from the workbox on the Mac over SSH (user `claude`,
`~/claude-builds/amora`), Simulator first (no signing).

Still open: videos on device, S3 (Cloudflare vs a native UA, needs production),
S6 (OEM battery killers, needs a real Xiaomi/Samsung), the >31 MiB stage chain.

### Earlier status (same day, before the emulator)

Branch `android-native-upload`. Done: steps 2–3 of §9 for **photos and
videos** (videos up to the 31 MiB single-request budget; the stage chain is
still TODO). Compiled with AGP 8.13 / SDK 36 and lint-clean; the web side is
exercised end-to-end in headless Chromium against a local backend with a
**mock plugin** implementing §3 (pick → hash → putBlob → enqueue → events →
real POST; a 503 that recovers, a 400 + ↻, a dedup, a reload mid-queue, the
plain web path, and the embedded-iframe path). Nothing has run on a real
phone yet: spikes A0, A1, S1-A (on device), S3, S5, S6 are still open.

What changed from the plan while building it:

- **Java, not Kotlin** (`AmoraUploadPlugin.java`, `Store.java`,
  `Uploader.java`, `UploadWorker.java`): Capacitor core and the other plugin
  are Java, and it avoids adding the Kotlin Gradle plugin to the shell.
- **One draining worker, not one WorkManager job per upload.** A single
  `UploadWorker` claims jobs from the manifest one at a time (one progress
  notification; the phone's uplink is the bottleneck anyway). Unique work
  `amora-upload-now` (expedited, network-constrained) is started by
  `enqueue`; `amora-upload-later` (delayed, REPLACE) wakes it for the next
  backoff. Retry/backoff/24 h cutoff live in `Store`, not in WorkManager.
- **No `body.bin` on Android:** the multipart body is streamed from the source
  files with `setFixedLengthStreamingMode`.
- **§6.2 resolved by reading Capacitor's source: option 1 works.** Capacitor
  registers the `server.url` authority with its local server, so
  `https://amora.pedalhidrografi.co/_capacitor_file_<abs path>` is served from
  disk, same-origin. Two gotchas: (a) its "Range" support is broken — it
  answers 206 with the WHOLE file from byte 0 — so the page always fetches
  whole files, never `<video src>` on them; (b) amora's service worker must
  not `respondWith` that path (`web/sw.js`), because a SW-initiated fetch
  bypasses the WebView interceptor. `readChunk` remains the fallback.
- **Contract additions** (§3): `retry({jobId})` (↻ on a failed job — only the
  native side still has the request), `pick()` also returns `failed[]` and a
  per-item `diag` (`requireOriginal`, `hasGps`) that answers spike A1 from the
  console log, and `meta` is opaque JSON the page uses to rebuild cells after
  a reload (album, tour, date flags).
- Permissions: only `POST_NOTIFICATIONS` (13+), asked on the first
  "Escolher"; denying it still picks (superseded the earlier
  `ACCESS_MEDIA_LOCATION` plan — see the table above).

**How to try it** (needs Remote Login on the Mac or a phone on USB there):
`npm install && npx cap sync android && ./run-android.sh` from `capacitor/`.
The web side ships with `web/` (gated on the plugin), so the phone must load
a `web/` that has it — i.e. after this branch is deployed, or point
`server.url` at a dev backend for the test.

---

## 1. Goal and scope

**One plugin, one JS contract, two native implementations.** The web side
(`subir.html`, `app.js`) talks to `Capacitor.Plugins.AmoraUpload` and never
branches on platform; only the plugin internals differ.

The pains differ per platform:

| | iOS (WKWebView) | Android (Chromium WebView) |
|---|---|---|
| Picker | **Looks frozen with videos**: WebKit asks Photos for a *compatible* representation, so iOS transcodes each HEVC clip before handing it over — no progress, picker still open (`WKFileUploadPanel.mm`). That's why `/subir` is photos-only on iOS (`#ios-video-note`). | Works; videos arrive as originals. |
| GPS | Survives in EXIF / moov. | **Probably stripped.** Since Android 10, media read without `ACCESS_MEDIA_LOCATION` + `MediaStore.setRequireOriginal()` comes with location redacted, and the system Photo Picker redacts by default. Photos without GPS never become map markers. **Spike A0 confirms whether today's uploads lose it.** |
| Uploads die | Screen off / app switch / 4G drop kills the `fetch`; `autoRetry` only resumes with the page visible. | Same, plus Doze and OEM battery killers (Xiaomi, Samsung) freezing the WebView process. |
| Video conversion | Slow: no VP9/VP8 encoding in WebCodecs → MediaRecorder, real-time. | Already fast: Chromium encodes VP8/VP9 + Opus via WebCodecs → the `mediabunny` path in `media-pipeline.js`. |

**Step 1 = the same two native capabilities on both:**

- **Pick** natively, into an app-owned store, with progress — iOS for the
  frozen picker, Android for the GPS. Both because the background uploader
  must read the original **from disk**, not from the WebView.
- **Upload** through the OS background transfer machinery — iOS background
  `URLSession`, Android `WorkManager` with a foreground-service notification.
  The request survives the app being suspended or killed and retries itself.

**Unchanged in step 1:** pHash/vHash, EXIF/moov parsing, large/thumb variants,
video conversion (iOS native conversion is step 2; Android probably never
needs it), TTL building, album minting, collage. The backend needs **no
changes** (§5).

**Non-goals:** share sheet / share target, "photos from this ride",
`upload_images.html` (the full form keeps the web path; port later).

## 2. Where the code lives

```
capacitor/plugins/amora-upload/                ← NEW, tracked
  package.json            "capacitor": {"ios": {"src": "ios"}, "android": {"src": "android"}}
  AmoraUpload.podspec     (the iOS shell uses CocoaPods — ios/App/Podfile)
  CONTRACT.md             §3 verbatim — the spec both sides implement
  ios/Sources/AmoraUploadPlugin/   (written — see Status)
    AmoraUploadPlugin.swift    CAPPlugin + CAPBridgedPlugin: JS-facing methods + PHPicker
    Store.swift                store + manifest + retry policy (same rules as Store.java)
    UploadQueue.swift          background URLSession (AmoraUploadQueue) + streamed multipart
  android/                     (built — see Status)
    build.gradle               + androidx.work, androidx.exifinterface
    src/main/AndroidManifest.xml    permissions + WorkManager FGS type (merged
                                    into the app by Gradle — no patch needed)
    src/main/java/co/pedalhidrografi/amora/upload/
      AmoraUploadPlugin.java   @CapacitorPlugin: JS-facing methods + picker
      Store.java               store + manifest + retry policy
      Uploader.java            streamed multipart POST (HttpURLConnection)
      UploadWorker.java        the draining Worker + foreground notification
capacitor/package.json         + "amora-upload": "file:plugins/amora-upload"
capacitor/run-ios.sh           + patch AppDelegate (§4.4), idempotent
```

`npx cap sync` picks the local package up like any npm plugin. The page
reaches it as `Capacitor.Plugins.AmoraUpload` — no `import`, same as
`BackgroundGeolocation` today (`app.js`, `liveIsNative`).

**Build machines:** Android builds and runs on this Linux box
(`run-android.sh`, the `android/` project already exists). iOS needs a Mac.
That's why the Android-first order in §9 is the one I recommend.

## 3. The contract (`apiVersion: 1`) — identical on both platforms

```ts
info(): { apiVersion: 1, platform: 'ios' | 'android' }   // platform: logs/UI copy only, never logic

pick({ videos: boolean, limit?: number /* 0 = sem limite */ }):
  { items: Array<{
      pickId: string,              // uuid; the file lives in the store until release/ack
      kind: 'image' | 'video',
      name: string, mime: string, size: number,
      url?: string,                // a URL the page can fetch (GET/HEAD + Range) — see §6.2
  }> }                             // user cancelled → items: []
  // emits 'pickProgress' {done, total} while files copy (iCloud, big videos)

readChunk({ pickId, offset, length }): { base64: string }   // fallback when `url` is absent
putBlob({ blobId?: string, base64: string }): { blobId: string, size: number }
  // JS → disk, appends when blobId is given; chunks ≤ 1 MiB of payload

enqueue({
  jobId: string,                   // JS-minted from the media hash; idempotent
  url: string,                     // absolute; host must equal the configured server.url host
  fields: Record<string, string>,  // ttl, id, staged…
  files: Array<{ field: string, filename: string, contentType: string,
                 source: { pickId: string } | { blobId: string } }>,
  after?: string,                  // jobId that must be `done` first (video stage chain)
  meta: { hash: string, kind: 'image' | 'video', label: string },
}): { jobId: string }

listJobs(): { jobs: Job[] }
retry({ jobId }): { retried: boolean }   // failed → queued, attempts and the 24 h window reset
cancel({ jobId }): void            // cancels the transfer, marks failed('cancelled')
ack({ jobId }): void               // JS recorded the final state → delete body/blobs/pick
release({ pickIds: string[] }): void   // picks never enqueued (dup, read error)

// event 'jobChanged' → Job
type Job = {
  jobId, meta, attempts: number,
  state: 'queued' | 'sending' | 'waiting' | 'done' | 'failed',
  sent?: number, total?: number,   // progress while sending
  nextAttemptAt?: number,          // ms epoch, state 'waiting'
  httpStatus?: number,
  response?: any,                  // parsed JSON body of the final response
  error?: string,
}
```

Shared semantics (both implementations must match — test them against the
same script, §9):

- `enqueue` with an existing `jobId` returns that job unchanged.
- **Retry policy:** transport error, 5xx, 408, 429 → `waiting`, retried with
  backoff (30 s, 2 min, 10 min, 30 min, then 1 h), up to 24 h → `failed`.
  Other 4xx → `failed` immediately with the server's JSON. The native side
  owns retries; JS never re-sends a job on its own.
- **Store:** an app-private directory that the OS does not purge and that is
  excluded from backups (iOS: `Application Support/amora-upload/` with
  `isExcludedFromBackup`; Android: `noBackupFilesDir/amora-upload/`):

  ```
  picks/<pickId>.<ext>
  blobs/<blobId>
  jobs/<jobId>/body.bin        multipart body, streamed to disk (never in memory)
  manifest.json                jobs + request specs, rewritten atomically
  ```

  A job is deleted on `ack`, or 7 days after reaching a final state; picks on
  `release`, on `ack` of the job using them, or after 7 days. Orphans are
  swept when the plugin loads.
- `User-Agent`: `Amora-<Platform>/<versão do app>` — see spike S3.

## 4. iOS implementation

### 4.1 Picker

- `PHPickerConfiguration()` **without** `photoLibrary:` → runs out of process,
  **no permission prompt**, no `NSPhotoLibraryUsageDescription`. The
  originals keep EXIF and the moov `©xyz`/`creationdate` that
  `media-pipeline.js` already reads.
- `filter`: `.images` or `.any(of: [.images, .videos])`; `selectionLimit` =
  `limit`; `selection = .ordered`.
- Video → `loadFileRepresentation(forTypeIdentifier: UTType.movie)` with
  `preferredAssetRepresentationMode = .current` (original HEVC, **no
  transcode**). Image → `UTType.jpeg` (`.compatible` — fast for stills, and
  the same class of bytes the web picker gives today, §10).
- The callback's URL is deleted when the callback returns: copy into
  `picks/` **inside** it. Report `pickProgress` from the `Progress` objects.

### 4.2 `url` for the page

`capacitor://localhost/_capacitor_file_<path>`. Capacitor's
`WebViewAssetHandler` serves it with `Access-Control-Allow-Origin` = the
configured `server.url`, GET/HEAD, Range → 206. (Keep `server.url` without a
trailing slash: the header is its `absoluteString` verbatim.)

### 4.3 Transport

- One `URLSessionConfiguration.background(withIdentifier:
  "co.pedalhidrografi.amora.upload")`, `sessionSendsLaunchEvents = true`,
  `isDiscretionary = false`, cellular allowed; created in plugin `load()` so
  it re-attaches to tasks that ran while the app was dead.
- `uploadTask(with:fromFile:)` (background sessions only take file bodies).
  Response JSON via `dataTask(_:didReceive:)`; finalize in
  `task(_:didCompleteWithError:)`. Backoff = a new task with
  `earliestBeginDate`.
- Enqueue in the **foreground** (right after the tap): tasks created in the
  background are always discretionary.

### 4.4 AppDelegate hook

`application(_:handleEventsForBackgroundURLSession:completionHandler:)` hands
the handler to the plugin, which calls it from
`urlSessionDidFinishEvents(forBackgroundURLSession:)`. Without it, results are
only processed at the next foreground launch and `waiting` retries can't be
re-armed while suspended. `AppDelegate.swift` lives in the gitignored `ios/`,
so `run-ios.sh` inserts the method idempotently (same pattern as
`apply_info_plist`; marker comment `// amora-upload`).

## 5. Backend: no changes needed (verify, don't edit)

- No auth by design → a native request needs no cookie/token.
- `/upload-image` and `/upload-video` are **upserts keyed by hash**
  (`upsert_image_in_uploads` / `upsert_video_in_uploads`, blobs
  content-addressed). A retry after a lost response rewrites the same state.
  The one side effect: each attempt mints its own `env:<ts>` `ph:Upload`
  audit node — acceptable, it's provenance of a real attempt.
- **32 MiB per request** (Cloud Run HTTP/1; `REQUEST_BODY_BUDGET` = 31 MiB in
  `upload_images.html`). Photos fit (original + ≤ 500 kB large + thumb).
  Videos over the budget: JS enqueues **a chain** — N
  `POST /stage-video/<vhash>` jobs (any subset of files each), then
  `/upload-video` with `staged=1`, linked by `after`. `409
  code=staging-missing` on the final job → JS re-enqueues the chain (staging
  is swept after 6 h).

## 6. Android implementation

### 6.1 Picker — GPS is the whole point here

The order to try, settled by spike A0/A1:

1. **Photo Picker** (`ActivityResultContracts.PickMultipleVisualMedia`) —
   no storage permission, the Play-policy-friendly path. **If** it keeps GPS
   when the app holds `ACCESS_MEDIA_LOCATION` (runtime permission, asked on
   the first pick with a Portuguese rationale), use it.
2. Otherwise **MediaStore with the original:** `READ_MEDIA_IMAGES` +
   `READ_MEDIA_VIDEO` (Android 13+; `READ_EXTERNAL_STORAGE` below) +
   `ACCESS_MEDIA_LOCATION`, open via `MediaStore.setRequireOriginal(uri)`.
   This needs our own picker UI (a grid over MediaStore) — more work. Android
   14+ "partial access" (`READ_MEDIA_VISUAL_USER_SELECTED`) still gives us
   the system's selection UI.
   **Play Store caveat:** since 2024 Google Play only lets apps declare
   `READ_MEDIA_*` if broad media access is core functionality, with a
   declaration form. Sideloaded APKs, F-Droid or a closed testing track are
   unaffected. **This is a distribution decision you have to make** before
   choosing option 2.
3. Last resort: keep whatever the picker gives and rely on today's
   "📍 Usar minha localização atual" for fresh photos (`#geo-note`).

Each `content://` URI is copied into `picks/` on a background dispatcher with
`pickProgress` (the URI grant can die with the process; the copy can't). The
store copy must keep the location bytes — verify with `exiftool` (A1).

### 6.2 `url` for the page — the Android catch

On Android, `WEBVIEW_SERVER_URL` is the *local* URL (`https://localhost`) even
with a remote `server.url`, and `WebViewLocalServer` sends **no CORS headers**.
So `https://localhost/_capacitor_file_…` is cross-origin to the amora page and
a `fetch()` would fail. Options, in order (spike S1-A):

1. Same-origin: `https://amora.pedalhidrografi.co/_capacitor_file_…`, **if**
   the local server intercepts the configured `server.url` host (it registers
   handlers per authority; check that the remote host is among them).
2. The plugin intercepts it itself: a `WebViewClient` subclass handling
   `shouldInterceptRequest` for `<amora>/_amora_pick_/<pickId>` (same-origin,
   Range-aware), delegating everything else to Capacitor's client.
3. No `url` at all → JS reads through `readChunk`. Fine for photos (≤ ~10 MB);
   too slow for big videos.

The contract already allows this: `url` is optional and the web side falls
back to `readChunk`.

### 6.3 Transport

- `WorkManager` with one `OneTimeWorkRequest` per job, unique work name =
  `jobId` (`ExistingWorkPolicy.KEEP` → idempotent `enqueue`),
  `Constraints(NetworkType.CONNECTED)`, `after` → `beginWith(a).then(b)`.
- The worker calls `setForeground(ForegroundInfo(notification,
  FOREGROUND_SERVICE_TYPE_DATA_SYNC))` → a progress notification
  "Enviando 12 imagens pro amora" (a UX plus: the user sees it's still
  going). Needs `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_DATA_SYNC`, and
  `POST_NOTIFICATIONS` (runtime prompt on Android 13+; if denied the work
  still runs, just without the notification). Declare WorkManager's
  `SystemForegroundService` with `foregroundServiceType="dataSync"` in the
  plugin manifest. (Android 15 caps `dataSync` at 6 h per 24 h — far beyond
  a batch.) Android 14's *user-initiated data transfer jobs* are the newer
  official API for this; WorkManager + FGS is chosen because it covers every
  Android version the shell supports with one code path.
- OkHttp `MultipartBody` streaming from `body.bin` (or built on the fly from
  the files — no need for a body file on Android, but keeping `body.bin`
  keeps the store identical to iOS). Backoff via `Result.retry()` with
  `setBackoffCriteria(EXPONENTIAL, 30 s)` + our own 24 h cutoff in the
  manifest, so the observable behaviour matches §3.
- No Application-level hook: WorkManager initializes itself and survives
  reboots; results land in the manifest and reach JS on the next
  `listJobs()` / `jobChanged`.

## 7. Web side (`web/subir.html` + a little `web/app.js`) — shared

### 7.1 Detection — the iframe gotcha (both platforms)

Capacitor injects its bridge into the **main frame only** — iOS with
`WKUserScript(forMainFrameOnly: true)` (`JSExport.swift`), Android with
`addDocumentStartJavaScript` scoped to the app origin (`Bridge.java`) — and in
the app `/subir` runs **inside a modal iframe**. So always go through the top
frame when embedded:

```js
// Shell nativo: a ponte do Capacitor é injetada no frame principal — dentro do
// iframe do app, usa a do `parent` (mesma origem). Sempre a do topo, pra iOS e
// Android se comportarem igual.
const CAP = (EMBEDDED ? window.parent?.Capacitor : null) || window.Capacitor;
const NATIVE_UP = CAP?.isNativePlatform?.() ? CAP.Plugins?.AmoraUpload : null;
let nativeUpload = false;   // decided after info(): apiVersion >= 1
```

**Version skew is the main design constraint:** `web/` ships to every shell
the moment it hits `main`, while native builds reach people through
TestFlight / Play / APK days or weeks later. Browsers and old shells have no
`AmoraUpload` → today's path untouched. A future `apiVersion: 2` web path must
keep the v1 branch while any v1 shell is still out there.

Listeners registered through `parent.Capacitor` run their callbacks in the
iframe's realm — **remove them on `pagehide`** (`handle.remove()`), or the
parent keeps calling into a dead document after the sheet navigates.

### 7.2 Picking

- Native mode: `#ios-video-note` stays hidden and videos are allowed. The
  `#picker` click is intercepted (`preventDefault` on the input) and calls
  `NATIVE_UP.pick({ videos: true })`; a status line shows `pickProgress`
  ("trazendo da galeria… 3/12").
- Per item: `url` → `fetch(url) → blob`; no `url` → `readChunk` loop. Then
  `new File([blob], name, { type: mime })`, set `item.pickId`, and **straight
  into today's `handlePickedFiles`**. The pipeline sees an ordinary `File`
  (spike S2 decides whether big videos can take this route).
- `blessMediaForGesture`: on iOS the shell needs no gesture (Capacitor sets
  `mediaTypesRequiringUserActionForPlayback = []`); on Android it's a no-op
  outside WebKit anyway. Calling it synchronously in the tap is harmless —
  keep one code path.
- `findDup` / read error → `release({ pickIds: [item.pickId] })`.

### 7.3 Sending

Split `postPhoto` / `postVideo` into **build** (TTL + list of parts) and
**on-success** (`existingPhashes.push`, `addShot`, `showSent`, `saveSession`,
`notifyParent`, `patchGeo`). The web path calls them around `postMedia` as
today. The native path:

1. `putBlob` the JS-made parts — photo: `large`, `thumb`; video: `audio`,
   `video360`, `video720`, `thumb` (≤ 1 MiB base64 chunks; photo parts are
   ~0.5 MB, so this is cheap).
2. `enqueue` — the `original` is sourced from `{ pickId }`: **the big file
   never crosses the bridge back.** Invariant: if JS replaced `item.file`
   (the `heic2any` branch of `decodeImage`), upload JS's bytes via `putBlob`
   instead. The server must receive exactly what was hashed.
3. Cell state `sending` → "na fila do aparelho — pode fechar o app".
4. `jobChanged`: `done` → on-success with `job.response`, then `ack`;
   `failed` → `fail(item, …)` with `kind` from `httpStatus` (no `autoRetry`);
   `waiting` → "sem rede — tentamos de novo sozinhos".

`autoRetry`, the wake lock and `beforeunload` stay for the **JS stages**
(read, hash, convert) — the WebView must be in the foreground for those. Once
enqueued, an item no longer needs the page.

### 7.4 Session, form-state contract, app

- **Restore:** on load in native mode, `listJobs()` and merge with
  `phidro:subirSessao` by `meta.hash`. Jobs finished while the page was dead
  become sent cells; `failed` jobs become `err` cells with ↻ (re-enqueue).
  Unknown jobs (session expired after 12 h) are shown as "enviadas em segundo
  plano" and acked.
- **`phidro-form-state`:** `busy` counts only items in JS stages; items whose
  only remaining work is a native job are not `dirty`, and the form sets
  `keepsOnClose: true` — closing the sheet loses nothing.
- **`app.js`** (main frame, lives the whole session) listens to `jobChanged`
  only to **observe**: a `done` while the `/subir` sheet is closed marks
  media dirty → `reloadPhotos()` (as with `phidro-media-changed`) + a toast
  "N imagens enviadas em segundo plano". Only `/subir` `ack`s; the 7-day
  sweep covers a `/subir` that is never reopened.

### 7.5 Housekeeping

`sw.js` `VERSION` bump + Ajuda changelog. If `subir.html` imports a new name
from `media-pipeline.js`, bump `?api=N`. `capacitor/README.md`: the plugin,
the iOS AppDelegate patch, the Android permissions and why.

## 8. Spikes — on devices, before the real code

| # | Platform | Question | Pass condition | If it fails |
|---|---|---|---|---|
| A0 | Android | **Do today's uploads lose GPS?** Send a photo + a video known to have GPS through `/subir` in Chrome **and** in the current shell; check `exiftool` on the stored `original.*` and whether a marker appears. | — (settles how much §6.1 matters) | — |
| A1 | Android | Photo Picker + `ACCESS_MEDIA_LOCATION`: does the copied file keep GPS (photo EXIF and video `©xyz`)? | GPS present | §6.1 option 2 (MediaStore + own picker) → Play decision |
| S1 | iOS | Can `https://amora…` `fetch()` `capacitor://localhost/_capacitor_file_…` from the main frame **and** the iframe, with `WKAppBoundDomains` on? | 200 + blob in both | `readChunk` for photos; videos jump to step 2 (native conversion) |
| S1-A | Android | Which of §6.2's options gives the page a same-origin, Range-capable URL? | Option 1 or 2 works | `readChunk` (photos fine; cap native-mode video size) |
| S2 | both | WebView memory for `fetch().blob()` of a 300 MB clip, then vhash + conversion | No crash on a 2–3 GB RAM phone | `File`-like shim (`size`, `name`, `type`, `slice` over Range, object URL = the pick URL) for the video helpers |
| S3 | both | Does Cloudflare in front of amora challenge/403 an `Amora-*` UA POST (CFNetwork / OkHttp)? | 200 on `/upload-image` | WAF skip rule for the upload paths, or send the WebView's UA |
| S4 | iOS | iPhone HDR (HLG/Dolby Vision) HEVC → canvas → MediaRecorder | Normal colours in the 360p | HDR assets as `.compatible` (accepting the wait), or step 2 (AVFoundation tone-maps) |
| S5 | both | `parent.Capacitor.Plugins.AmoraUpload` call + listener from the iframe, then navigate the iframe | Works; no errors after `pagehide` | Route plugin calls through `postMessage` to `app.js` |
| S6 | Android | WorkManager + FGS on a Xiaomi/Samsung with battery optimisation on: lock the phone mid-batch for 10 min | Batch finishes | Ask once to exempt from battery optimisation (Portuguese rationale) |

A0 needs no code — do it today. S1/S1-A + S5 are a ~50-line throwaway
plugin per platform (pick one file, return its URL).

## 9. Build order (recommended: Android first)

Android first because it builds on this Linux box, so the shared parts (the
contract, `subir.html`, `app.js`) can be iterated without a Mac. iOS then
implements a contract that is already proven against a real web side.
(If the collective is mostly on iPhones and iOS's frozen picker is the
urgent pain, swap 2 and 4 — the contract makes the order free.)

1. Spikes: A0 now; then A1, S1-A, S5 (Android), S3, S6.
2. **Android plugin**: store + manifest + WorkManager + multipart, photos
   only; `listJobs`/`ack`/`cancel`. Drive it from Chrome DevTools
   (`chrome://inspect`) attached to the shell before touching `subir.html`.
3. **Web side** (§7) for photos + `app.js` observer. Ship to `main` (inert
   without the plugin), then an Android build.
4. Spikes S1, S4 (iOS, on a Mac); **iOS plugin** to the same contract +
   `run-ios.sh` AppDelegate patch; TestFlight.
5. Videos on both: lift the iOS photos-only stopgap in native mode, the stage
   chain for > 31 MiB, HDR per S4.

**Contract test:** one JS script, run from the web inspector of each shell
(DevTools on Android, Safari Web Inspector on iOS), exercising every method
and the retry states against a local backend (`dev-cloudrun.sh --local-data`
on a LAN IP — `enqueue` checks the host, so allow it in a debug build).

**Test matrix:** desktop Chrome + Safari iOS + Chrome Android (web path,
regression); old shells without the plugin (web path); new shells (native
path). Per path: mixed batch of 30 photos + 3 videos, one duplicate, one
already on the server, airplane mode mid-batch, app killed mid-batch, sheet
closed mid-batch, phone locked 10 min.

## 10. Risks worth naming

- **Hash parity.** The pHash depends on the decode engine (iPhone vs Chrome
  already differ by ~14 bits — that's why `SAME_SHOT_*` exists). iOS photos
  via `.compatible` get Photos' own JPEG conversion; iOS videos via
  `.current` hash the HEVC original rather than the H.264 transcode. Android
  decodes in Chromium like desktop Chrome, so it's closest to the existing
  corpus. `SAME_SHOT_*` stays the net; the same clip sent through both paths
  may not dedup. Accepted.
- **Two retry systems.** JS `autoRetry` must never touch an item that has a
  native job: `pickId` + `jobId` on an item ⇒ native owns it.
- **Two native codebases (Swift + Kotlin) in a JS/Python house.** Keep the
  contract small, versioned, and written down once (`CONTRACT.md`); keep all
  product logic (hashing, TTL, albums, copy) in JS.
- **Android distribution** (§6.1): Play's media-permission policy may force
  option 1 or a declaration; decide the channel (Play / closed testing / APK)
  before building option 2.
