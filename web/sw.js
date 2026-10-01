// Pedal Hidrográfico — service worker
//
// Caches. Só os DOIS primeiros levam a VERSION no nome (e somem no deploy
// seguinte); os outros guardam o que não depende da versão do app e ficam fora
// da faxina do activate:
//   STATIC_CACHE  — o app de UM deploy: o shell do mapa (index + JS/CSS/lib/
//                    fontes) e as páginas dos modais, PRÉ-BAIXADOS inteiros na
//                    instalação e servidos cache-first (ver "Instalação").
//   RUNTIME_CACHE — APIs de terceiros (open-meteo, OSRM): stale-while-revalidate.
//   DATA_CACHE    — estado mutável same-origin (routes.json, data/*.ttl, rotas
//                    salvas): network-first com TIMEOUT (ver networkFirst).
//   MEDIA_CACHE   — miniaturas de fotos/clipes: cache-first, teto FIFO.
//   TILE_CACHE    — tiles das camadas de mapa com crossOrigin: cache-first, teto FIFO.
//   CDN_CACHE     — libs do jsDelivr (URL com versão fixa = conteúdo imutável).
//   GRAPH_CACHE   — o grafo pré-cozido do viário (sampa-viario-graph.bin, ~68 MB).
//   FGB_CACHE     — blocos de 64 KB dos range requests dos FlatGeobuf. Ver a seção no fim.
// Resposta OPACA (no-cors de outra origem) nunca entra em cache: o navegador
// cobra de cota um "padding" por resposta (~7 MB cada no Chrome) — 600
// miniaturas estourariam a cota. Onde o host manda Access-Control-Allow-Origin,
// o SW busca em modo CORS ele mesmo (miniaturas via 302 pro bucket, jsDelivr)
// ou a camada pede com crossOrigin (tiles); o resto passa direto pra rede.

// A numeração divergiu enquanto a branch `deploy` seguiu à frente da `main`:
// v370 foi emitido duas vezes (grafo do viário aqui, link de rotas salvas no
// origin) e v371/v372 saíram na `deploy` (busca de endereços, ⇄ inverter).
// v373 fica acima de tudo que já circulou, que é o que importa: se a VERSION
// não crescer, o service worker serve cache velho.
const VERSION = 'phidro-v420';
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;
const DATA_CACHE = 'phidro-data-v1';
const MEDIA_CACHE = 'phidro-media-v1';
const TILE_CACHE = 'phidro-tiles-v1';
const CDN_CACHE = 'phidro-cdn-v1';
const GRAPH_CACHE = 'phidro-graph-v1';
// Cache de blocos dos FlatGeobuf (ver a seção lá embaixo). NÃO leva a VERSION
// no nome e fica fora da faxina do activate: os blocos são versionados pela
// ETag do arquivo, não pelo deploy do app — senão cada deploy jogaria fora
// dezenas de MB de viário já baixados.
const FGB_CACHE = 'phidro-fgb-blocks-v1';
const KEEP_CACHES = new Set([STATIC_CACHE, RUNTIME_CACHE, DATA_CACHE, MEDIA_CACHE,
  TILE_CACHE, CDN_CACHE, GRAPH_CACHE, FGB_CACHE]);

const SCOPE = new URL(self.registration.scope);
const abs = (rel) => new URL(rel, SCOPE).href;

// ─── Instalação ─────────────────────────────────────────────────────────────
// O app de um deploy entra INTEIRO ou não entra. SHELL_ASSETS vai num addAll
// (atômico): se um arquivo falhar (4G fraco), a instalação falha e o SW
// anterior — com o conjunto anterior, completo — segue no controle; o navegador
// tenta de novo na próxima navegação ou no registration.update() que o app
// chama ao voltar pro primeiro plano. Tudo com {cache: 'no-cache'}: revalida
// com o servidor em vez de aceitar a cópia do cache HTTP (a Cloudflare põe
// max-age=14400 no JS/CSS — era assim que um index.html novo rodava com o
// app.js de antes, e o shell offline de um deploy nascia sem app.js/style.css).
// Servidos cache-first, os arquivos de dois deploys nunca se misturam: versão
// nova = VERSION nova = SW novo, que assume (skipWaiting + claim); a página
// aberta segue no código velho e o app avisa "Nova versão disponível" (toque =
// recarregar). Sem ?v= nas URLs: este precache é o único mecanismo de versão.
// (Cliente SEM SW — ex. o shell Capacitor — fica com o cache HTTP: a origem
// manda no-cache no JS/CSS, mas o "Browser Cache TTL" da Cloudflare o reescreve
// pra max-age=14400; "Respect Existing Headers" lá resolve esses também.)
//
// Arquivo novo carregado pelo index.html ou pelo app.js no boot → SHELL_ASSETS
// (tem que existir no deploy: um 404 aqui trava a atualização de todo mundo).
// Ícones ficam de fora: quem os usa é o sistema, na hora de instalar o app.
const SHELL_ASSETS = [
  './index.html',
  './manifest.json',
  './style.css',
  './app.js',
  './lib/utils.js',                 // import do app.js
  './lib/n3.min.js',                // parser dos TTL (ensureN3): sem ele, nada de fotos/passeios
  './lib/media-query.js',
  './lib/leaflet/leaflet.css',
  './lib/leaflet/leaflet.js',
  './lib/leaflet/images/layers.png',
  './lib/leaflet/images/layers-2x.png',
  './lib/leaflet/images/marker-icon.png',
  './lib/leaflet/images/marker-icon-2x.png',
  './lib/leaflet/images/marker-shadow.png',
  './lib/leaflet-rotate/leaflet-rotate-src.js',   // rotação do mapa (GPL-3.0)
  './lib/locatecontrol/L.Control.Locate.min.js',
  './lib/locatecontrol/L.Control.Locate.min.css',
  './lib/qrcode.js',
  './lib/flatgeobuf-geojson.min.js',   // leitor FGB do viário/água (range requests)
  './fonts/fonts.css',
  './fonts/ibm-plex-mono-400.woff2',
  './fonts/ibm-plex-mono-400i.woff2',
  './fonts/ibm-plex-mono-600.woff2',
  './fonts/ibm-plex-mono-700.woff2',
  './img/amora-icon.png',
];
// Páginas dos modais (iframes) + o que elas carregam. Best-effort: a que falhar
// baixa na primeira abertura online e fica neste deploy.
const PAGE_ASSETS = [
  './imagens.html',
  './pessoas.html',
  './censo.html',
  './subir.html',
  './upload_images.html',
  './upload_tour.html',
  './lib/media-pipeline.js',        // import do subir.html
  './lib/exifr.esm.js',             // autofill de EXIF (app, subir, upload)
  './lib/tom-select.complete.min.js',
  './lib/tom-select.min.css',
  './lib/energy-worker.js',
  './lib/graph-engine.js',          // importScripts()'d pelo energy-worker e pelo viario-graph-worker
  './lib/viario-graph-worker.js',   // decode + Dijkstra do grafo do viário (Traçar "pelo viário")
];
// Dados pro PRIMEIRO boot offline: na 1ª visita a página carrega antes de o SW
// existir, então nada disso passou por ele. Só entram se faltarem no DATA_CACHE
// (depois disso o network-first os mantém) — e sem {cache:'no-cache'}: a página
// acabou de baixá-los, o cache HTTP revalida com um 304.
const DATA_WARM = [
  './routes.json',
  './data/data_graphs.ttl',
  './data/tours.ttl',
  './data/images-geo.ttl',
  './data/identities.ttl',
  './data/lists.ttl',
];

const SHELL_PATHS = new Set([...SHELL_ASSETS, ...PAGE_ASSETS].map((u) => new URL(u, SCOPE).pathname));

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);
    const fresh = (u) => new Request(u, { cache: 'no-cache' });
    await cache.addAll(SHELL_ASSETS.map(fresh));
    const pages = await Promise.allSettled(PAGE_ASSETS.map((u) => cache.add(fresh(u))));
    pages.forEach((r, i) => {
      if (r.status === 'rejected') console.warn(`[sw] sem ${PAGE_ASSETS[i]}: ${r.reason?.message}`);
    });
    await carryForward().catch((err) => console.warn('[sw] carry-forward:', err?.message));
    await warmData().catch(() => {});
  })());
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const k of await caches.keys()) {
      if (!KEEP_CACHES.has(k)) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

// O que vale entre deploys e as versões antigas guardavam em caches com a
// VERSION no nome (routes.json/dumps no -static, grafo e libs do jsDelivr no
// -runtime) vai pro cache sem versão ANTES de o activate apagar os antigos —
// sem isso o deploy que trouxe este esquema jogaria fora os dados offline e os
// 34 MB do grafo. Roda na instalação (não no activate) pra não segurar os
// fetches: enquanto isto roda quem atende a página ainda é o SW anterior.
// Código antigo NÃO é copiado — o precache novo o substitui.
async function carryForward() {
  for (const name of await caches.keys()) {
    if (KEEP_CACHES.has(name) || !name.startsWith('phidro-v')) continue;
    const old = await caches.open(name);
    for (const req of await old.keys()) {
      const dest = persistentCacheFor(new URL(req.url));
      if (!dest) continue;
      const cache = await caches.open(dest);
      if (await cache.match(req)) continue;
      const res = await old.match(req);
      if (res && res.status === 200) await cache.put(req, res).catch(() => {});
    }
  }
}

function persistentCacheFor(url) {
  if (url.origin === SCOPE.origin) {
    const rel = relPath(url);
    return rel != null && isDataRel(rel) ? DATA_CACHE : null;
  }
  if (isGraphUrl(url)) return GRAPH_CACHE;
  if (url.hostname === 'cdn.jsdelivr.net') return CDN_CACHE;
  return null;
}

async function warmData() {
  const cache = await caches.open(DATA_CACHE);
  await Promise.allSettled(DATA_WARM.map(async (u) => {
    if (await cache.match(abs(u))) return;
    const res = await fetch(abs(u));
    if (res.ok && res.status === 200) await cache.put(abs(u), res);
  }));
}

// ─── Roteamento ─────────────────────────────────────────────────────────────
// Caminho relativo ao escopo do SW ('' = raiz); null fora do escopo.
function relPath(url) {
  return url.pathname.startsWith(SCOPE.pathname) ? url.pathname.slice(SCOPE.pathname.length) : null;
}

// Estado mutável que o backend atualiza ao vivo: routes.json (upsert a cada
// Tour CRUD), os dumps data/*.ttl (+ tour-iri-map.json) e as rotas salvas
// (/saved-routes, /saved-route/<id> — o fetch com cache:'no-store' do cliente
// só pula o cache HTTP, não este).
function isDataRel(rel) {
  return rel === 'routes.json'
    || /^data\/[\w.-]+\.(?:ttl|json)$/.test(rel)
    || /^saved-routes?(?:\/|$)/.test(rel);
}

// /passeio/<id numérico> é o link LEGADO (?tour=<n> dos tempos pré-slug): só o
// backend sabe a qual slug ele virou (303) — esse vai pra rede.
const LEGACY_TOUR_RE = /^passeio\/\d{1,6}$/;
const PAGE_RELS = new Set(PAGE_ASSETS.filter((u) => u.endsWith('.html')).map((u) => u.slice(2)));

// Navegação que abre uma página do app: devolve o ARQUIVO que o backend serve
// nesse caminho (e que está no precache deste deploy). Sai do disco, na hora, e
// sempre casado com o JS/CSS do mesmo deploy:
//   / e /index.html (qualquer query — ?tour=<id> o cliente resolve);
//   /passeio/<slug>: o backend manda o index SSR'ado (título/OG/JSON-LD/<article>
//     pra crawler e sem-JS). Com o SW, o app abre o passeio pelo path
//     (tryOpenTourFromPath) — nada do SSR é usado —, então vem o shell: sem
//     esperar a rede em 4G fraco e sem o risco de um HTML de um deploy novo
//     rodar com o JS de um deploy velho logo depois de publicar;
//   /imagens/lista/<slug>[/<n>] (o álbum), /pessoas/<slug> e /subir: o backend
//     serve imagens.html / pessoas.html / subir.html nesses caminhos e o
//     cliente lê o path (as tags de preview de link são pros robôs).
function shellPageFor(rel) {
  if (rel === '' || rel === 'index.html') return 'index.html';
  if (/^passeio\/[A-Za-z0-9-]+$/.test(rel) && !LEGACY_TOUR_RE.test(rel)) return 'index.html';
  if (/^imagens\/lista\/[^/]+(?:\/\d+)?\/?$/.test(rel)) return 'imagens.html';
  if (/^pessoas\/[^/]+$/.test(rel)) return 'pessoas.html';
  if (rel === 'subir') return 'subir.html';
  if (PAGE_RELS.has(rel)) return rel;
  return null;
}

// Hosts de tiles (camadas de mapa). Só as requisições CORS (camada com
// crossOrigin — conferido que o host manda Access-Control-Allow-Origin) entram
// no TILE_CACHE; as no-cors (opacas) passam direto e ficam com o cache HTTP.
const TILE_HOSTS = [
  /(^|\.)tile\.openstreetmap\.org$/,
  /(^|\.)server\.arcgisonline\.com$/,
  /(^|\.)telhas\.pedalhidrografi\.co$/,
  /(^|\.)cameratopo\.pedalhidrografi\.co$/,
  /^mtpi\.pedalhidrografi\.co$/,          // MTPI global v1/v2 (WebP no R2)
  /(^|\.)raster\.geosampa\.prefeitura\.sp\.gov\.br$/,
  // Tiles VETORIAIS (MVT) do OpenInfraMap — energia/água/telecom/petróleo e
  // gás. Vêm por fetch() (destination vazio), não por <img>: entram pelo
  // `.pbf` no teste abaixo. Projeto voluntário: o cache poupa o servidor deles.
  /^openinframap\.org$/,
];
// APIs de terceiros que vale guardar (stale-while-revalidate, por deploy).
// (photon.komoot.io — a busca de endereços — fica DE FORA de propósito: cada
// query de typeahead é única, então cachear não compra nada; hosts fora das
// listas passam direto pra rede, sem bloqueio.)
const RUNTIME_HOSTS = [
  /(^|\.)telhas\.pedalhidrografi\.co$/,     // ph-cycle-network.geojson
  /^busao\.bicisampa\.info$/,               // metrô e trens (rail.geojson + rail-lines.json)
  /(^|\.)api\.open-meteo\.com$/,
  /(^|\.)routing\.openstreetmap\.de$/,
];

function isGraphUrl(url) {
  return /(^|\.)telhas\.pedalhidrografi\.co$/.test(url.hostname)
    && url.pathname.endsWith('/sampa-viario-graph.bin');
}

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

  if (url.origin === SCOPE.origin) {
    const rel = relPath(url);
    // Fora do escopo, ou conteúdo negociado (?format=ttl|md — Turtle/Markdown
    // pra quem abre o IRI no navegador): direto pra rede.
    if (rel == null || url.searchParams.has('format')) return;

    // Mídia (o backend 302a pro bucket). Miniaturas: MEDIA_CACHE. large.jpg:
    // rede, com a miniatura de reserva offline. Originais, vídeos/áudios dos
    // clipes (range requests do <video>) e artes: direto — nunca guardar
    // (o "Baixar originais" enchia o cache com dezenas de MB de originais).
    if (/^photos\/[^/]+\/thumb\.jpg$/.test(rel) || /^clips\/[^/]+\.thumb\.jpg$/.test(rel)) {
      event.respondWith(mediaThumbResponse(event, rel.startsWith('clips/') ? CLIP_THUMB_REFRESH_MS : PHOTO_THUMB_REFRESH_MS));
      return;
    }
    if (/^photos\/[^/]+\/large\.jpg$/.test(rel)) {
      event.respondWith(photoLargeResponse(event, abs(rel.replace(/large\.jpg$/, 'thumb.jpg'))));
      return;
    }
    if (/^(?:photos|clips|tour_assets)\//.test(rel)) return;

    if (isDataRel(rel)) {
      // O manifesto VoID é um shim estático (o backend não o muta): sai do
      // disco na hora e revalida em 2º plano — em 4G fraco a carga das fotos
      // (manifesto → dumps) pagava DOIS timeouts em série.
      event.respondWith(rel === 'data/data_graphs.ttl'
        ? staleWhileRevalidate(event, DATA_CACHE)
        : networkFirst(event, DATA_CACHE));
      return;
    }

    if (req.mode === 'navigate') {
      const page = shellPageFor(rel);
      if (page) { event.respondWith(shellResponse(event, page)); return; }
      // Link compartilhável de rota salva: a página só redireciona o humano
      // pra /#rt=<slug> — sem rede (ou em 4G fraco) o SW faz o mesmo.
      const rt = /^route\/([a-z0-9][a-z0-9-]*)$/.exec(rel);
      if (rt) {
        event.respondWith(networkFirst(event, DATA_CACHE,
          () => Response.redirect(abs(`./#rt=${rt[1]}`), 302), { fallbackWhenSlow: true }));
        return;
      }
      if (LEGACY_TOUR_RE.test(rel)) {
        event.respondWith(networkFirst(event, DATA_CACHE, () => shellResponse(event, 'index.html')));
        return;
      }
    }

    // Código/estático do deploy (JS/CSS/fontes/páginas .html): cache-first no
    // cache da versão. O resto (páginas SSR como /memoria, feed, imagens de
    // preview…): stale-while-revalidate, também por versão.
    if (SHELL_PATHS.has(url.pathname) || /\.(?:m?js|css|html|woff2?)$/.test(url.pathname)) {
      event.respondWith(cacheFirst(event, STATIC_CACHE, { ignoreSearch: req.mode === 'navigate' }));
    } else {
      event.respondWith(staleWhileRevalidate(event, STATIC_CACHE));
    }
    return;
  }

  // Grafo pré-cozido do viário: cache-first num cache SEM versão (era
  // stale-while-revalidate no RUNTIME_CACHE — 34 MB de novo a cada deploy, e
  // outra cópia inteira em 2º plano a cada uso). Range passa direto.
  if (isGraphUrl(url)) {
    if (!req.headers.has('range')) event.respondWith(graphResponse(event));
    return;
  }

  if (TILE_HOSTS.some((re) => re.test(url.hostname))
      && (req.destination === 'image' || url.pathname.endsWith('.pbf'))) {
    if (req.mode === 'cors') event.respondWith(tileResponse(event));
    return;   // no-cors: resposta opaca — sem cache do SW (o cache HTTP segue valendo)
  }

  // jsDelivr (lazy-loads do app.js e o Comunica da galeria): as URLs têm versão
  // fixa, então cache-first e sem revalidar.
  if (url.hostname === 'cdn.jsdelivr.net') {
    event.respondWith(cdnResponse(event));
    return;
  }

  if (RUNTIME_HOSTS.some((re) => re.test(url.hostname))) {
    event.respondWith(staleWhileRevalidate(event, RUNTIME_CACHE));
    return;
  }

  // Everything else: pass through.
});

// waitUntil fora do tick do evento só vale enquanto o respondWith está
// pendente; depois disso lança — aí a promessa roda sem estender o SW.
function extend(event, p) {
  try { event.waitUntil(p.catch(() => {})); } catch (_) { /* evento encerrado */ }
}

// ─── Estratégias ────────────────────────────────────────────────────────────
// Página do app pelo precache. Faltando (página opcional que falhou no
// precache, cache despejado), busca o ARQUIVO da página — não a URL navegada,
// que em /passeio/<slug> viria SSR'ada — e guarda pra próxima.
async function shellResponse(event, rel) {
  const cache = await caches.open(STATIC_CACHE);
  const key = abs(rel);
  const hit = await cache.match(key);
  if (hit) return hit;
  try {
    const res = await fetch(key, { cache: 'no-cache' });
    if (res.ok && res.status === 200 && !res.redirected) {
      extend(event, cache.put(key, res.clone()));
      return res;
    }
  } catch (_) { /* offline */ }
  return fetch(event.request).catch(() => Response.error());
}

async function cacheFirst(event, cacheName, { ignoreSearch = false } = {}) {
  const req = event.request;
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreSearch });
  if (hit) return hit;
  // Pula o cache HTTP (max-age da Cloudflare): o que entra aqui fica até o
  // próximo deploy e tem que ser o arquivo DESTE.
  let res;
  try {
    res = await fetch(req.mode === 'navigate' ? req : new Request(req, { cache: 'no-cache' }));
  } catch (err) {
    // Sem rede: um import versionado por query (`lib/media-pipeline.js?api=N`
    // do /subir) cai no arquivo pré-cacheado sem a query — é o deste deploy.
    const loose = await cache.match(req, { ignoreSearch: true });
    if (loose) return loose;
    throw err;
  }
  if (res.ok && res.status === 200 && res.type === 'basic') extend(event, cache.put(req, res.clone()));
  return res;
}

async function staleWhileRevalidate(event, cacheName) {
  const req = event.request;
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  let put = null;
  const net = fetch(req).then((res) => {
    // Só respostas boas e legíveis: nada de redirect/erro/opaca no cache.
    if (res && res.ok && res.status === 200 && res.type !== 'opaque') put = cache.put(req, res.clone());
    return res;
  });
  extend(event, net.then(() => put));
  return cached || net.catch(() => Response.error());
}

// Rede primeiro — mas com TIMEOUT. Em 4G fraco ("lie-fi") a conexão fica de pé
// sem trazer bytes e o fetch só falha no timeout do sistema (dezenas de
// segundos), enquanto routes.json/TTLs bons esperavam no disco — e, com ETag,
// a rede quase sempre responderia 304 (a cópia já é a atual). Passados
// NET_TIMEOUT_MS sem resposta, serve a cópia e deixa a rede terminar em 2º
// plano atualizando o cache (a próxima carga já sai nova). Sem cópia, espera a
// rede mesmo (não há o que servir) — a não ser que `fallbackWhenSlow`.
const NET_TIMEOUT_MS = 3500;
const SLOW = Symbol('slow');
async function networkFirst(event, cacheName, fallback = null, { fallbackWhenSlow = false } = {}) {
  const req = event.request;
  const cache = await caches.open(cacheName);
  let put = null;
  const net = fetch(req).then((res) => {
    if (res.ok && res.status === 200 && res.type === 'basic') put = cache.put(req, res.clone());
    return res;
  });
  extend(event, net.then(() => put));
  let timer;
  const slow = new Promise((resolve) => { timer = setTimeout(resolve, NET_TIMEOUT_MS, SLOW); });
  try {
    const first = await Promise.race([net, slow]);
    if (first !== SLOW) return first;
    const cached = await cache.match(req);
    if (cached) return cached;
    if (fallback && fallbackWhenSlow) return await fallback();
    return await net;
  } catch (_) {
    const cached = await cache.match(req);
    if (cached) return cached;
    if (fallback) return await fallback();
    return Response.error();
  } finally {
    clearTimeout(timer);
  }
}

// ─── Mídia, tiles, CDN: caches sem versão com teto FIFO ─────────────────────
// Mesmo esquema do FGB_CACHE: o Cache API guarda a ordem de inserção, então
// acima do teto saem os ~10 % mais antigos (put de uma chave existente a joga
// pro fim — tile revisto se renova). Contagem preguiçosa, por cache.
const MEDIA_MAX = 3000;      // miniaturas ~20 KB → ≤ ~60 MB
const TILE_MAX = 3000;       // tiles ~20–50 KB → ≤ ~100 MB
const capState = new Map();  // nome do cache → {count, evicting}

async function cappedPut(cacheName, key, res, max) {
  const cache = await caches.open(cacheName);
  await cache.put(key, res);
  let st = capState.get(cacheName);
  if (!st) { st = { count: null, evicting: null }; capState.set(cacheName, st); }
  if (st.count === null) st.count = (await cache.keys()).length;
  else st.count++;
  if (st.count <= max || st.evicting) return;
  st.evicting = (async () => {
    const keys = await cache.keys();
    const drop = Math.max(0, keys.length - Math.floor(max * 0.9));
    await Promise.all(keys.slice(0, drop).map((k) => cache.delete(k)));
    st.count = keys.length - drop;
  })().finally(() => { st.evicting = null; });
}

// Resposta "limpa" pra guardar: corpo inteiro + os headers legíveis + o
// instante da busca (o Date de uma resposta CORS não é legível).
async function stamped(res) {
  const headers = new Headers(res.headers);
  headers.delete('content-length');      // o blob já vem decodificado
  headers.delete('content-encoding');
  headers.set('x-sw-fetched-at', String(Date.now()));
  return new Response(await res.blob(), { status: 200, headers });
}
const ageOf = (res) => Date.now() - (Number(res.headers.get('x-sw-fetched-at')) || 0);

// Miniaturas (./photos/<phash>/thumb.jpg, ./clips/<vhash>.thumb.jpg). A página
// pede same-origin em no-cors (fundo CSS do marcador, <img>); o backend 302a
// pro bucket, e no-cors + redirect cross-origin = resposta opaca. O SW busca a
// mesma URL em modo CORS (o bucket manda Access-Control-Allow-Origin: *) e
// guarda uma resposta legível, sob a URL same-origin. Foto é endereçada pelo
// pHash da imagem (não muda); clipe, pelo vHash da FONTE — excluir e reenviar
// com outro recorte troca a miniatura —, então a de clipe se renova antes.
const PHOTO_THUMB_REFRESH_MS = 30 * 86400 * 1000;
const CLIP_THUMB_REFRESH_MS = 86400 * 1000;
async function mediaThumbResponse(event, refreshMs) {
  const req = event.request;
  const cache = await caches.open(MEDIA_CACHE);
  const hit = await cache.match(req.url);
  if (hit) {
    if (ageOf(hit) > refreshMs) extend(event, mediaThumbFetch(req.url).catch(() => {}));
    return hit;
  }
  let res;
  try {
    res = await mediaThumbFetch(req.url, event);
  } catch (_) {
    // Offline — ou um bucket sem CORS: tenta a rede crua (opaca, sem cache).
    return fetch(req).catch(() => Response.error());
  }
  return res;
}
async function mediaThumbFetch(url, event = null) {
  const res = await fetch(url, { mode: 'cors' });
  if (!res.ok || res.status !== 200) return res;
  const out = await stamped(res);
  const p = cappedPut(MEDIA_CACHE, url, out.clone(), MEDIA_MAX);
  if (event) extend(event, p); else await p.catch(() => {});
  return out;
}

// large.jpg (popup, galeria): rede. Offline, a miniatura guardada no lugar —
// borrada, mas melhor que o popup vazio.
async function photoLargeResponse(event, thumbUrl) {
  try {
    return await fetch(event.request);
  } catch (err) {
    const hit = await caches.open(MEDIA_CACHE).then((c) => c.match(thumbUrl));
    return hit || Response.error();
  }
}

// Tiles (só CORS): cache-first; o que tem mais de uma semana volta a ser
// buscado em 2º plano (o max-age dos hosts é de 1–7 dias).
const TILE_REFRESH_MS = 7 * 86400 * 1000;
async function tileResponse(event) {
  const req = event.request;
  const cache = await caches.open(TILE_CACHE);
  const hit = await cache.match(req.url);
  if (hit) {
    if (ageOf(hit) > TILE_REFRESH_MS) extend(event, tileFetch(req).catch(() => {}));
    return hit;
  }
  return tileFetch(req, event);
}
async function tileFetch(req, event = null) {
  const res = await fetch(req);
  if (res.ok && res.status === 200 && res.type === 'cors') {
    const copy = res.clone();
    const p = stamped(copy).then((out) => cappedPut(TILE_CACHE, req.url, out, TILE_MAX));
    if (event) extend(event, p); else await p.catch(() => {});
  }
  return res;
}

async function cdnResponse(event) {
  const req = event.request;
  const cache = await caches.open(CDN_CACHE);
  const hit = await cache.match(req.url);
  if (hit) return hit;
  let res;
  try {
    // <script> clássico sem crossorigin = no-cors = opaca; a mesma URL em
    // CORS (o jsDelivr manda ACAO: *) é legível e serve pro <script> igual.
    res = await fetch(req.url, { mode: 'cors', credentials: 'omit' });
  } catch (_) {
    return fetch(req).catch(() => Response.error());
  }
  if (res.ok && res.status === 200) extend(event, cache.put(req.url, res.clone()));
  return res;
}

// ─── Grafo pré-cozido do viário ─────────────────────────────────────────────
// Cache-first; revalidado no máximo 1×/24 h em 2º plano com um HEAD (ETag
// exposta pelo telhas): mudou (re-bake), baixa o novo em 2º plano e o velho
// segue servindo até o novo estar inteiro no cache. O download vai por um
// fetch PRÓPRIO do SW (sem o signal da página): se o app desistir no meio (o
// timeout dele), o SW termina de gravar e a próxima tentativa sai do disco.
// Uma tentativa com download já em voo espera por ele em vez de abrir uma
// segunda cópia dos 34 MB.
const GRAPH_REVALIDATE_MS = 24 * 3600 * 1000;
let graphInflight = null;    // resolve quando o download em voo terminou de gravar (ou falhou)
let graphChecking = null;
const graphMetaKey = (url) => `${url}?__meta`;
const etagOf = (res) => (res.headers.get('etag') || '').replace(/^W\//, '');

// Marca o download em voo desde o INÍCIO do fetch (não só quando chegam os
// headers) — uma 2ª tentativa nesse meio-tempo também espera por ele.
function trackGraphDownload(p) {
  const done = p.catch(() => {});
  graphInflight = done;
  done.finally(() => { if (graphInflight === done) graphInflight = null; });
  return p;
}

async function graphResponse(event) {
  const url = event.request.url;
  const cache = await caches.open(GRAPH_CACHE);
  let hit = await cache.match(url);
  if (!hit && graphInflight) {
    await graphInflight;
    hit = await cache.match(url);
  }
  if (hit) {
    extend(event, graphRevalidate(cache, url, hit));
    return hit;
  }
  const download = fetch(url, { mode: 'cors', credentials: 'omit' }).then((res) => ({
    res, stored: res.ok && res.status === 200 ? graphStore(cache, url, res.clone()) : null,
  }));
  trackGraphDownload(download.then(({ stored }) => stored));
  const { res, stored } = await download;
  if (stored) extend(event, stored);
  return res;
}

async function graphStore(cache, url, res) {
  await cache.put(url, res);
  await cache.put(graphMetaKey(url), new Response(JSON.stringify({ checkedAt: Date.now() })));
}

async function graphRevalidate(cache, url, hit) {
  const m = await cache.match(graphMetaKey(url));
  const meta = m ? await m.json().catch(() => null) : null;
  if ((meta && Date.now() - meta.checkedAt < GRAPH_REVALIDATE_MS) || graphChecking || graphInflight) return;
  graphChecking = (async () => {
    const head = await fetch(url, { method: 'HEAD', mode: 'cors', credentials: 'omit', cache: 'no-store' });
    if (!head.ok) return;
    const known = etagOf(hit), fresh = etagOf(head);
    if (known && fresh && known !== fresh) {
      await trackGraphDownload(fetch(url, { mode: 'cors', credentials: 'omit', cache: 'no-store' })
        .then((res) => (res.ok && res.status === 200 ? graphStore(cache, url, res) : null)));
      return;
    }
    await cache.put(graphMetaKey(url), new Response(JSON.stringify({ checkedAt: Date.now() })));
  })().finally(() => { graphChecking = null; });
  await graphChecking;
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
// blocos velhos são apagados. Sem rede, segue na versão conhecida. Com rede
// ruim também: a leitura espera a revalidação no máximo FGB_REVALIDATE_WAIT_MS
// (rede boa responde em centenas de ms e o parse inteiro já sai na versão
// nova, como antes) e depois segue na conhecida, com os blocos do disco,
// enquanto a revalidação termina em 2º plano — antes ela prendia TODA leitura
// do arquivo até o timeout do sistema (dezenas de s em 4G fraco). A troca de
// versão no meio de um parse, que já podia acontecer quando o arquivo muda no
// servidor durante a leitura, fica restrita a esse caso de rede ruim + arquivo
// novo (os FGB mudam no máximo 1×/semana).
//
// Orçamento FIFO: o Cache API guarda a ordem de inserção, então acima de
// FGB_MAX_BLOCKS saem os mais antigos (não é LRU — ler não renova o bloco).
// Qualquer tropeço (range estranho, servidor que ignora Range, bloco
// corrompido) cai pra rede pura, como era antes do cache.
const FGB_BLOCK = 64 * 1024;
const FGB_MAX_BLOCKS = 4096;                    // 256 MB
const FGB_REVALIDATE_MS = 24 * 3600 * 1000;
const FGB_REVALIDATE_WAIT_MS = 2500;
const FGB_RETRY_MS = 5 * 60 * 1000;             // revalidação que falhou: tenta de novo em 5 min

const fgbMeta = new Map();       // url → {ver, total, checkedAt}
const fgbChecking = new Map();   // url → Promise da revalidação em voo
const fgbSlow = new Set();       // urls cuja revalidação em voo já estourou a espera
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
    })().catch((err) => {
      // Sem rede: segue na versão conhecida e só tenta de novo daqui a pouco
      // (só em memória) — senão cada leitura reabriria a espera.
      const known = fgbMeta.get(url);
      if (known) fgbMeta.set(url, { ...known, checkedAt: Date.now() - FGB_REVALIDATE_MS + FGB_RETRY_MS });
      throw err;
    }).finally(() => { fgbChecking.delete(url); fgbSlow.delete(url); }));
  }
  const check = fgbChecking.get(url);
  if (!meta) return await check;   // versão desconhecida: sem ela não há o que ler do disco
  // Versão conhecida, mas vencida: espera a revalidação só um pouco (ver o
  // cabeçalho da seção); estourou uma vez, as leituras seguintes não esperam.
  if (fgbSlow.has(url)) return meta;
  let timer;
  const waited = await Promise.race([
    check.catch(() => meta),        // offline: segue com a versão conhecida
    new Promise((resolve) => { timer = setTimeout(resolve, FGB_REVALIDATE_WAIT_MS, null); }),
  ]);
  clearTimeout(timer);
  if (waited) return waited;
  if (fgbChecking.get(url) === check) fgbSlow.add(url);
  return meta;
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
