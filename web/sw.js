// Pedal Hidrográfico — service worker
//
// Two cache buckets, both STATIC_CACHE by default:
//   STATIC_CACHE  — app shell (HTML/CSS/JS/icons/manifest): stale-while-
//                    revalidate. Cached copy serves instantly; a network
//                    fetch runs in the background and updates the cache for
//                    the *next* page load. So redeploys propagate without
//                    users having to hard-refresh — they just get the new
//                    version on their second visit. Same-origin mutable
//                    state (tours.ttl, uploads.ttl, data_graphs.ttl,
//                    routes.json) is the exception: network-first, since the
//                    backend upserts them live and staleness there means
//                    stale data, not just a stale app shell.
//   RUNTIME_CACHE — map tiles, OSRM, elevation, etc. stale-while-revalidate.
//   FGB_CACHE     — blocos de 64 KB dos range requests dos FlatGeobuf, fora da
//                    VERSION (sobrevive a deploys). Ver a seção no fim.

// A numeração divergiu enquanto a branch `deploy` seguiu à frente da `main`:
// v370 foi emitido duas vezes (grafo do viário aqui, link de rotas salvas no
// origin) e v371/v372 saíram na `deploy` (busca de endereços, ⇄ inverter).
// v373 fica acima de tudo que já circulou, que é o que importa: se a VERSION
// não crescer, o service worker serve cache velho.
const VERSION = 'phidro-v414';
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;
// Cache de blocos dos FlatGeobuf (ver a seção lá embaixo). NÃO leva a VERSION
// no nome e fica fora da faxina do activate: os blocos são versionados pela
// ETag do arquivo, não pelo deploy do app — senão cada deploy jogaria fora
// dezenas de MB de viário já baixados.
const FGB_CACHE = 'phidro-fgb-blocks-v1';

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
  './img/amora-icon.png',
  './imagens.html',
  './pessoas.html',
  './upload_images.html',   // forms de envio/passeio: abrem do cache (SWR) em vez de baixar a cada modal
  './upload_tour.html',
  './censo.html',
  './fonts/fonts.css',
  './fonts/ibm-plex-mono-400.woff2',
  './fonts/ibm-plex-mono-400i.woff2',
  './fonts/ibm-plex-mono-600.woff2',
  './fonts/ibm-plex-mono-700.woff2',
  './lib/utils.js',
  './lib/n3.min.js',
  './lib/exifr.esm.js',   // autofill de EXIF no upload (vendorado; era jsdelivr)
  './lib/media-query.js',   // infra de consulta (Store N3 + Comunica lazy)
  './lib/energy-worker.js',
  './lib/graph-engine.js',   // importScripts()'d pelo energy-worker no boot
  './lib/tom-select.complete.min.js',
  './lib/tom-select.min.css',
  './lib/qrcode.js',
  './lib/leaflet/leaflet.js',
  './lib/leaflet/leaflet.css',
  './lib/leaflet-rotate/leaflet-rotate-src.js',   // rotação do mapa (GPL-3.0)
  './lib/leaflet/images/layers.png',
  './lib/leaflet/images/layers-2x.png',
  './lib/leaflet/images/marker-icon.png',
  './lib/leaflet/images/marker-icon-2x.png',
  './lib/leaflet/images/marker-shadow.png',
  './lib/locatecontrol/L.Control.Locate.min.js',
  './lib/locatecontrol/L.Control.Locate.min.css',
  './lib/flatgeobuf-geojson.min.js',   // leitor FGB do viário/água (range requests)
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
          .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE && k !== FGB_CACHE)
          .map((k) => caches.delete(k)),
      ),
    ),
  );
  self.clients.claim();
});

// Hosts whose responses we want to keep cached for offline / fast revisits.
// (photon.komoot.io — a busca de endereços — fica DE FORA de propósito: cada
// query de typeahead é única, então cachear não compra nada; hosts fora da
// lista passam direto pra rede, sem bloqueio.)
const RUNTIME_HOSTS = [
  /(^|\.)tile\.openstreetmap\.org$/,
  /(^|\.)server\.arcgisonline\.com$/,
  /(^|\.)telhas\.pedalhidrografi\.co$/,
  /(^|\.)cameratopo\.pedalhidrografi\.co$/,
  /(^|\.)raster\.geosampa\.prefeitura\.sp\.gov\.br$/,
  /(^|\.)api\.open-meteo\.com$/,
  /(^|\.)routing\.openstreetmap\.de$/,
  // jsdelivr fica só pelos lazy-loads do app.js (heic2any/jszip/geotiff);
  // Leaflet, n3 e exifr foram vendorados pra lib/ (unpkg/CDN saiu).
  /(^|\.)cdn\.jsdelivr\.net$/,
];

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Localização ao vivo: NUNCA cachear. As posições mudam a cada segundo e
  // o GET sai com Cache-Control: no-store — deixa passar direto pra rede.
  if (url.pathname.includes('/live-location')) return;  // cobre /live-locations tb

  // FlatGeobuf (viário/água/camadas OSM): NUNCA pelo staleWhileRevalidate —
  // o leitor busca fatias por Range (206) e o cache.match() IGNORA o header
  // Range, então um 200 completo cacheado seria servido como resposta a um
  // range request, corrompendo o parse. Range requests vão pro cache de
  // BLOCOS (fgbRangeResponse); o resto passa direto pra rede.
  if (url.pathname.endsWith('.fgb')) {
    if (req.headers.has('range')) event.respondWith(fgbRangeResponse(event));
    return;
  }

  // Same-origin: estado mutável usa network-first — qualquer upload/sync
  // novo aparece no próximo refresh sem o dance de dois-refreshes do
  // stale-while-revalidate. Inclui routes.json: o backend faz upsert
  // incremental nele a cada /upload-tour //delete-tour, então é tão "vivo"
  // quanto os TTLs. Inclui também /saved-routes e /saved-route/<id> (o
  // fetch com cache:'no-store' do cliente só ignora o cache HTTP, não o
  // Cache Storage do SW — sem essa entrada, salvar/excluir uma rota salva
  // reaparecia/sumia só depois de dois refreshes). `endsWith`/`includes`
  // (e não ===) pra funcionar também sob hosting com subpath (ex.: o
  // mirror legado em /rotas_app/).
  // Álbum /imagens/lista/<slug>[/<n>]: a página É o imagens.html (o backend
  // serve o mesmo arquivo nesse path; quem lê o path é o cliente). Sai do
  // cache do imagens.html em vez de guardar uma cópia por álbum/foto — e
  // abre offline.
  if (url.origin === self.location.origin && req.mode === 'navigate'
      && /\/imagens\/lista\/[^/]+(\/\d+)?\/?$/.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(
      new Request(new URL('./imagens.html', self.registration.scope).href), STATIC_CACHE));
    return;
  }

  if (url.origin === self.location.origin) {
    if (url.pathname.endsWith('/data/data_graphs.ttl')
        || url.pathname.endsWith('/data/uploads.ttl')
        || url.pathname.endsWith('/data/tours.ttl')
        || url.pathname.endsWith('/data/images.ttl')
        || url.pathname.endsWith('/data/images-geo.ttl')
        || url.pathname.endsWith('/data/identities.ttl')
        || url.pathname.endsWith('/data/lists.ttl')
        || url.pathname.endsWith('/routes.json')
        || url.pathname.includes('/saved-route')
        // Página de compartilhamento /route/<slug> (não pega o og.png, que
        // termina em .png): o redirect embutido aponta pro slug — servir uma
        // cópia velha depois de renomear a rota mandaria pro slug morto.
        || /\/route\/[a-z0-9][a-z0-9-]*$/.test(url.pathname)
        // Página por passeio /passeio/<slug> (o index SSR'ado): o conteúdo
        // muda a cada edição do passeio — network-first, com fallback pro
        // shell cacheado no networkFirst quando offline. (A forma de 2
        // segmentos /passeio/<ES>/<seq> não casa — a classe não inclui "/".)
        || /\/passeio\/[A-Za-z0-9-]+$/.test(url.pathname)) {
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
    const cached = await cache.match(req);
    if (cached) return cached;
    // Navegação offline pra um caminho nunca visitado (ex.: um
    // /passeio/<slug> recém-compartilhado): serve o shell do app — o
    // cliente abre o passeio pelo path (tryOpenTourFromPath).
    if (req.mode === 'navigate') {
      const shell = await cache.match('./index.html');
      if (shell) return shell;
    }
    return Response.error();
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

// ─── FlatGeobuf: cache de blocos dos range requests ─────────────────────────
// O leitor FGB pede fatias por Range (206) e nada no caminho guardava essas
// fatias: o Cache API recusa 206, a Cloudflare responde BYPASS (o arquivo é
// grande demais pro cache dela) e o cache HTTP do Chrome quase não ajuda
// (medido: 4 de 14 respostas num pan, ZERO depois de reabrir o navegador).
// Então o SW guarda ele mesmo: cada range vira blocos alinhados de FGB_BLOCK
// bytes, gravados como respostas 200 comuns sob chaves sintéticas
// (`<url>?__fgb=<versão>&b=<n>`), e só os blocos que faltam vão pra rede, em
// corridas contíguas (uma corrida = um range). Voltar numa área, desfazer um
// pan, aproximar o zoom ou abrir outra sessão sai do disco — e offline também.
//
// VERSÃO = ETag do arquivo, e ela vai NA CHAVE: blocos de duas gerações nunca
// se misturam num parse. A versão conhecida é revalidada a cada
// FGB_REVALIDATE_MS (o max-age do bucket) com um range de 1 byte; se mudou, os
// blocos velhos são apagados. Sem rede, segue na versão conhecida.
//
// Orçamento FIFO: o Cache API guarda a ordem de inserção, então acima de
// FGB_MAX_BLOCKS saem os mais antigos (não é LRU — ler não renova o bloco).
// Qualquer tropeço (range estranho, servidor que ignora Range, bloco
// corrompido) cai pra rede pura, como era antes do cache.
const FGB_BLOCK = 64 * 1024;
const FGB_MAX_BLOCKS = 4096;                    // 256 MB
const FGB_REVALIDATE_MS = 24 * 3600 * 1000;

const fgbMeta = new Map();       // url → {ver, total, checkedAt}
const fgbChecking = new Map();   // url → Promise da revalidação em voo
const fgbInflight = new Map();   // chave do bloco → Promise<ArrayBuffer>
let fgbCount = null;             // nº de entradas no FGB_CACHE (preguiçoso)
let fgbEvicting = null;

const fgbKey = (url, ver, i) => `${url}?__fgb=${ver}&b=${i}`;
const fgbMetaKey = (url) => `${url}?__fgbmeta`;

// {ver, total} de uma resposta 206; null se o servidor ignorou o Range ou não
// mandou um validador (aí não dá pra versionar — sem cache).
function fgbVersionOf(res) {
  if (res.status !== 206) return null;
  const total = Number((/\/(\d+)$/.exec(res.headers.get('content-range') || '') || [])[1]);
  const tag = res.headers.get('etag') || res.headers.get('last-modified') || '';
  const ver = tag.replace(/[^A-Za-z0-9]/g, '');
  return total && ver ? { ver, total, checkedAt: Date.now() } : null;
}

async function fgbSetMeta(cache, url, meta) {
  const old = fgbMeta.get(url);
  fgbMeta.set(url, meta);
  await cache.put(fgbMetaKey(url), new Response(JSON.stringify(meta),
    { headers: { 'Content-Type': 'application/json' } }));
  if (old && old.ver !== meta.ver) {
    // Arquivo novo: some com os blocos da geração anterior.
    const mine = `${url}?__fgb=`, keep = fgbKey(url, meta.ver, '');
    for (const k of await cache.keys()) {
      if (k.url.startsWith(mine) && !k.url.startsWith(keep)) await cache.delete(k);
    }
    fgbCount = null;
  }
}

async function fgbMetaFor(cache, url) {
  let meta = fgbMeta.get(url);
  if (!meta) {
    const r = await cache.match(fgbMetaKey(url));
    if (r) { try { meta = await r.json(); fgbMeta.set(url, meta); } catch (_) { meta = null; } }
  }
  if (meta && Date.now() - meta.checkedAt < FGB_REVALIDATE_MS) return meta;
  // Descobre/revalida a versão com 1 byte — uma vez só por arquivo, mesmo com
  // o leitor disparando vários ranges em paralelo.
  if (!fgbChecking.has(url)) {
    fgbChecking.set(url, (async () => {
      const res = await fetch(url, { headers: { Range: 'bytes=0-0' } });
      const fresh = fgbVersionOf(res);
      if (res.body) res.body.cancel().catch(() => {});
      if (!fresh) throw new Error(`sem range versionado (HTTP ${res.status})`);
      await fgbSetMeta(cache, url, fresh);
      return fresh;
    })().finally(() => fgbChecking.delete(url)));
  }
  try {
    return await fgbChecking.get(url);
  } catch (err) {
    if (meta) return meta;         // offline: segue com a versão conhecida
    throw err;
  }
}

// Busca os blocos [first, last] num range só e devolve um ArrayBuffer por bloco.
async function fgbFetchRun(cache, url, meta, first, last) {
  const a = first * FGB_BLOCK;
  const b = Math.min((last + 1) * FGB_BLOCK, meta.total) - 1;
  const ctrl = new AbortController();
  const res = await fetch(url, { headers: { Range: `bytes=${a}-${b}` }, signal: ctrl.signal });
  const got = fgbVersionOf(res);
  if (!got || got.ver !== meta.ver) {
    ctrl.abort();                  // um 200 aqui seria o arquivo INTEIRO
    // O arquivo mudou antes da revalidação: grava a versão nova (apagando os
    // blocos velhos) e deixa este range cair pra rede pura.
    if (got) await fgbSetMeta(cache, url, got);
    throw new Error(got ? 'arquivo mudou' : `range ignorado (HTTP ${res.status})`);
  }
  const buf = await res.arrayBuffer();
  if (buf.byteLength !== b - a + 1) throw new Error('range curto');
  const out = [];
  for (let off = 0; off < buf.byteLength; off += FGB_BLOCK) {
    out.push(buf.slice(off, Math.min(off + FGB_BLOCK, buf.byteLength)));
  }
  return out;
}

async function fgbStore(cache, url, ver, first, bufs) {
  await Promise.all(bufs.map((buf, k) => cache.put(fgbKey(url, ver, first + k),
    new Response(buf, { headers: { 'Content-Type': 'application/octet-stream' } }))));
  if (fgbCount === null) fgbCount = (await cache.keys()).length;
  else fgbCount += bufs.length;
  if (fgbCount <= FGB_MAX_BLOCKS || fgbEvicting) return;
  fgbEvicting = (async () => {
    const keys = (await cache.keys()).filter((k) => !k.url.endsWith('?__fgbmeta'));
    const drop = Math.max(0, keys.length - Math.floor(FGB_MAX_BLOCKS * 0.9));
    await Promise.all(keys.slice(0, drop).map((k) => cache.delete(k)));
    fgbCount = keys.length - drop;
  })().finally(() => { fgbEvicting = null; });
}

async function fgbServeRange(event) {
  const req = event.request;
  const m = /^bytes=(\d+)-(\d+)$/.exec(req.headers.get('range') || '');
  if (!m) return fetch(req);       // aberto/sufixo/múltiplo: o leitor não usa
  const url = req.url;
  const cache = await caches.open(FGB_CACHE);
  const meta = await fgbMetaFor(cache, url);
  const start = Number(m[1]);
  const end = Math.min(Number(m[2]), meta.total - 1);
  if (start > end) return fetch(req);
  const b0 = Math.floor(start / FGB_BLOCK), b1 = Math.floor(end / FGB_BLOCK);
  const idx = Array.from({ length: b1 - b0 + 1 }, (_, k) => b0 + k);

  // 1) O que já está no disco, ou chegando por um range vizinho em voo.
  const got = await Promise.all(idx.map((i) => {
    const key = fgbKey(url, meta.ver, i);
    return fgbInflight.get(key)
      || cache.match(key).then((r) => (r ? r.arrayBuffer() : null));
  }));

  // 2) O que falta, em corridas contíguas. Registra cada bloco em
  //    fgbInflight ANTES de qualquer await, pra um range paralelo esperar este
  //    download em vez de pedir os mesmos bytes de novo.
  const runs = [];
  idx.forEach((i, k) => {
    if (got[k]) return;
    const pending = fgbInflight.get(fgbKey(url, meta.ver, i));
    if (pending) { got[k] = pending; return; }
    const last = runs[runs.length - 1];
    if (last && last.last === i - 1) last.last = i;
    else runs.push({ first: i, last: i });
  });
  const writes = runs.map((r) => {
    const p = fgbFetchRun(cache, url, meta, r.first, r.last);
    const keys = [];
    for (let i = r.first; i <= r.last; i++) {
      const key = fgbKey(url, meta.ver, i);
      const bp = p.then((bufs) => bufs[i - r.first]);
      bp.catch(() => {});          // quem consome trata; aqui só evita o unhandled
      fgbInflight.set(key, bp);
      keys.push(key);
      got[i - b0] = bp;
    }
    // O bloco sai do "em voo" só depois de gravado — no meio-tempo quem
    // chegar ainda o encontra aqui, e não no disco.
    return p.then((bufs) => fgbStore(cache, url, meta.ver, r.first, bufs))
      .catch(() => {})
      .finally(() => { for (const key of keys) fgbInflight.delete(key); });
  });
  try { event.waitUntil(Promise.all(writes)); } catch (_) { /* evento já encerrado */ }

  // 3) Monta a fatia pedida a partir dos blocos.
  const bufs = await Promise.all(got);
  const out = new Uint8Array(end - start + 1);
  bufs.forEach((buf, k) => {
    const bStart = (b0 + k) * FGB_BLOCK;
    // Só o último bloco do ARQUIVO pode ser curto; curto no meio = corrompido.
    if (buf.byteLength !== FGB_BLOCK && bStart + buf.byteLength < meta.total) {
      throw new Error('bloco curto');
    }
    const from = Math.max(start, bStart);
    const to = Math.min(end + 1, bStart + buf.byteLength);
    out.set(new Uint8Array(buf, from - bStart, to - from), from - start);
  });
  return new Response(out, {
    status: 206,
    statusText: 'Partial Content',
    headers: {
      'Content-Type': 'application/octet-stream',
      'Content-Length': String(out.length),
      'Content-Range': `bytes ${start}-${end}/${meta.total}`,
      'Accept-Ranges': 'bytes',
    },
  });
}

async function fgbRangeResponse(event) {
  try {
    return await fgbServeRange(event);
  } catch (err) {
    console.warn('[sw] cache de blocos FGB → rede:', err.message);
    return fetch(event.request);
  }
}
