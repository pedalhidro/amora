// Pedal Hidrográfico — service worker
//
// Two cache buckets, both stale-while-revalidate:
//   STATIC_CACHE  — app shell (HTML/CSS/JS/icons/routes.json/manifest).
//                    Cached copy serves instantly; a network fetch runs in
//                    the background and updates the cache for the *next*
//                    page load. So redeploys propagate without users having
//                    to hard-refresh — they just get the new version on
//                    their second visit.
//   RUNTIME_CACHE — map tiles, OSRM, elevation, etc. Same strategy.

const VERSION = 'phidro-v274';
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;

// Pre-cache only the entry HTML and small steady assets. app.js and
// style.css carry a deploy-time `?v=<ts>` query string, so pre-caching them
// here under the un-versioned URL would just waste a fetch — they get
// cached on first real load via the stale-while-revalidate path.
const STATIC_ASSETS = [
  './',
  './index.html',
  './routes.json',
  './manifest.json',
  './icon.svg',
  './icon-192.png',
  './icon-512.png',
  './icon-512-maskable.png',
  './apple-touch-icon.png',
  './lib/utils.js',
  './lib/n3.min.js',
  './lib/energy-worker.js',
  './lib/tom-select.complete.min.js',
  './lib/tom-select.min.css',
  './lib/qrcode.js',
  './lib/leaflet/leaflet.js',
  './lib/leaflet/leaflet.css',
  './lib/leaflet/images/layers.png',
  './lib/leaflet/images/layers-2x.png',
  './lib/leaflet/images/marker-icon.png',
  './lib/leaflet/images/marker-icon-2x.png',
  './lib/leaflet/images/marker-shadow.png',
  './lib/locatecontrol/L.Control.Locate.min.js',
  './lib/locatecontrol/L.Control.Locate.min.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) =>
      // Some assets may 404 in dev (e.g. before routes.json is built); use
      // cache.add per-item with catch so install doesn't fail the whole batch.
      Promise.all(
        STATIC_ASSETS.map((url) =>
          cache.add(url).catch((err) => console.warn(`[sw] skip ${url}: ${err.message}`)),
        ),
      ),
    ),
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k)),
      ),
    ),
  );
  self.clients.claim();
});

// Hosts whose responses we want to keep cached for offline / fast revisits.
const RUNTIME_HOSTS = [
  /(^|\.)tile\.openstreetmap\.org$/,
  /(^|\.)server\.arcgisonline\.com$/,
  /(^|\.)telhas\.pedalhidrografi\.co$/,
  /(^|\.)raster\.geosampa\.prefeitura\.sp\.gov\.br$/,
  /(^|\.)api\.open-meteo\.com$/,
  /(^|\.)routing\.openstreetmap\.de$/,
  // jsdelivr fica só pelos lazy-loads do app.js (exifr/heic2any/jszip/
  // geotiff); Leaflet & cia foram vendorados pra lib/ (unpkg saiu).
  /(^|\.)cdn\.jsdelivr\.net$/,
];

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Localização ao vivo: NUNCA cachear. As posições mudam a cada segundo e
  // o GET sai com Cache-Control: no-store — deixa passar direto pra rede.
  if (url.pathname.includes('/live-location')) return;  // cobre /live-locations tb

  // Same-origin: estado mutável usa network-first — qualquer upload/sync
  // novo aparece no próximo refresh sem o dance de dois-refreshes do
  // stale-while-revalidate. Inclui routes.json: o backend faz upsert
  // incremental nele a cada /upload-tour //delete-tour, então é tão "vivo"
  // quanto os TTLs. `endsWith` (e não ===) pra funcionar também sob
  // hosting com subpath (ex.: o mirror legado em /rotas_app/).
  if (url.origin === self.location.origin) {
    if (url.pathname.endsWith('/data/data_graphs.ttl')
        || url.pathname.endsWith('/data/uploads.ttl')
        || url.pathname.endsWith('/data/tours.ttl')
        || url.pathname.endsWith('/routes.json')) {
      event.respondWith(networkFirst(req, STATIC_CACHE));
    } else {
      event.respondWith(staleWhileRevalidate(req, STATIC_CACHE));
    }
    return;
  }

  // Allowlisted third-party hosts: stale-while-revalidate.
  if (RUNTIME_HOSTS.some((re) => re.test(url.host))) {
    event.respondWith(staleWhileRevalidate(req, RUNTIME_CACHE));
    return;
  }

  // Everything else: pass through.
});

// Tenta rede primeiro; cai pra cache só se a rede falhar (offline).
async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res && res.ok && res.status === 200) cache.put(req, res.clone());
    return res;
  } catch (_) {
    return (await cache.match(req)) || Response.error();
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req)
    .then((res) => {
      // Only cache successful, non-opaque responses to avoid filling cache
      // with failed/redirect garbage.
      if (res && res.ok && res.status === 200) cache.put(req, res.clone());
      return res;
    })
    .catch(() => cached || Response.error());
  return cached || fetchPromise;
}
