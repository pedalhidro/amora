// Pedal Hidrográfico — utility helpers
// First ES module extracted from app.js. Pure functions and the toast UI;
// no state coupling to other subsystems. Também é a biblioteca comum das
// páginas dos modais (forms, censo, galeria, pessoas) — elas importam
// `./lib/utils.js?api=N` (ver o comentário do import no subir.html: o .js
// fica até 4 h no cache da Cloudflare; suba o N em TODAS as páginas quando
// uma delas passar a importar um nome novo daqui). Nada aqui tem efeito
// colateral no import — o app.js também carrega este módulo.

// null/undefined viram '' (nunca "undefined" no HTML).
export function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
}

export function escapeXml(s) {
  return String(s).replace(/[<>&"']/g, (c) =>
    ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[c],
  );
}

// hh:mm:ss formatter for the trace metrics + tooltip lines.
export function formatHMS(sec) {
  const total = Math.max(0, Math.round(sec));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n) => String(n).padStart(2, '0');
  if (h > 0) return `${h}h ${pad(m)}m ${pad(s)}s`;
  return `${m}m ${pad(s)}s`;
}

// Run an async fn over an array with at most `limit` calls in flight at once.
export async function mapConcurrent(items, limit, fn) {
  const out = new Array(items.length);
  let next = 0;
  async function worker() {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      out[i] = await fn(items[i], i);
    }
  }
  const n = Math.min(limit, items.length);
  await Promise.all(Array.from({ length: n }, () => worker()));
  return out;
}

// Earth-surface distance (haversine) in metres. Used by the route stats
// computation in the build script and by the editor's segment finder.
export function haversineMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const rad = (d) => (d * Math.PI) / 180;
  const dLat = rad(lat2 - lat1);
  const dLon = rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Lightweight non-blocking toast for one-shot status messages. The DOM
// element is read once and cached; subsequent calls reuse the same node.
let toastEl = null;
let toastTimer = null;
export function showToast(msg, ms = 3500) {
  if (!toastEl) toastEl = document.getElementById('toast');
  if (!toastEl) return;
  // Tornar visível ANTES de escrever o texto: o #toast é um live region
  // (role=status / aria-live=polite); enquanto [hidden] ele fica fora da
  // árvore de acessibilidade, então mudar o texto com ele oculto não é
  // anunciado. Desocultar primeiro garante que a mudança vire um update.
  toastEl.hidden = false;
  toastEl.classList.remove('fade');
  toastEl.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.add('fade');
    setTimeout(() => { toastEl.hidden = true; }, 300);
  }, ms);
}

// Salva/compartilha um arquivo gerado no cliente (GPX, QR, ZIP, JSON…) — o
// ÚNICO caminho de download do app. No celular (ponteiro grosso) e no shell
// nativo, com Web Share nível 2, abre a folha de compartilhar do sistema: no
// iPhone é por ela que o arquivo chega no WhatsApp, Garmin/Komoot, Instagram,
// Fotos ou "Salvar em Arquivos" (o <a download> caía em Arquivos › Downloads,
// e no shell Capacitor não salvava NADA — o WKWebView do Capacitor não trata
// download). No desktop (e sem Web Share) segue o <a download> de sempre.
// Chame DENTRO do gesto do usuário e sem await antes: o navigator.share
// consome a ativação transitória (5 s no WebKit) — sem ela cai no download.
// Devolve 'shared' | 'downloaded' | 'cancelled' (o usuário fechou a folha);
// quem chama só mostra o aviso de sucesso depois disso.
export async function saveFile(blob, filename, { type } = {}) {
  const mime = type || blob.type || 'application/octet-stream';
  let coarse = false;
  try { coarse = window.matchMedia('(pointer: coarse)').matches; } catch (_) { /* sem matchMedia */ }
  const cap = window.Capacitor;
  const native = !!(cap && typeof cap.isNativePlatform === 'function' && cap.isNativePlatform());
  if ((coarse || native) && typeof navigator.share === 'function' && typeof File === 'function') {
    let data = null;
    try { data = { files: [new File([blob], filename, { type: mime })] }; } catch (_) { data = null; }
    // Sem ativação (o arquivo levou mais que a janela do gesto pra ficar
    // pronto), o share rejeitaria — vai direto pro download.
    const active = !navigator.userActivation || navigator.userActivation.isActive;
    let shareable = false;
    try { shareable = !!data && active && (!navigator.canShare || navigator.canShare(data)); } catch (_) { shareable = false; }
    if (shareable) {
      try {
        await navigator.share(data);
        return 'shared';
      } catch (err) {
        if (err && err.name === 'AbortError') return 'cancelled';
        // NotAllowedError (gesto perdido), TypeError (tipo recusado)… → download
      }
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revogar cedo é seguro (o WebKit estende a vida do blob: durante a checagem
  // de navegação do download), mas não há pressa.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
  return 'downloaded';
}

// localStorage with try/catch so private-mode / quota-exceeded errors don't
// crash flow. Returns null on read failure, false on write failure, true on
// successful write.
export const storage = {
  get(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); return true; } catch { return false; }
  },
  remove(key) {
    try { localStorage.removeItem(key); return true; } catch { return false; }
  },
};

// ─── Páginas dos modais (forms, censo, galeria, pessoas) ─────────────────

// Literal Turtle de UMA linha ("…"): quebras viram \n escapado. Vale também
// pra narrativa: o multipart/form-data converte toda quebra CRUA dos campos de
// texto em CRLF (o spec manda; WebKit e Blink fazem) — com um """longo""" o \r
// entrava no literal gravado.
export function turtleEscape(s) {
  return String(s ?? '').replace(/\\/g, '\\\\').replace(/"/g, '\\"')
    .replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t');
}

// Prefixos dos fragmentos Turtle que os forms enviam (superconjunto: um
// prefixo declarado e não usado não muda nenhuma triple). O `remove=` do
// mode=patch NÃO depende destes — o backend expande os CURIEs com a tabela
// dele (TOUR_PATCH_PREFIXES).
export const TTL_PREFIXES = [
  '@prefix dcterms: <http://purl.org/dc/terms/> .',
  '@prefix exif:    <http://www.w3.org/2003/12/exif/ns#> .',
  '@prefix nfo:     <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#> .',
  '@prefix pav:     <http://purl.org/pav/> .',
  '@prefix ph:      <https://id.pedalhidrografi.co/terms#> .',
  '@prefix phd:     <https://pedalhidrografi.co/data/> .',
  '@prefix pas:     <https://id.pedalhidrografi.co/passeio/> .',
  '@prefix ser:     <https://id.pedalhidrografi.co/serie/> .',
  '@prefix pes:     <https://id.pedalhidrografi.co/pessoas/> .',
  '@prefix med:     <https://id.pedalhidrografi.co/midia/> .',
  '@prefix lst:     <https://id.pedalhidrografi.co/listas/> .',
  '@prefix prov:    <http://www.w3.org/ns/prov#> .',
  '@prefix qudt:    <http://qudt.org/schema/qudt/> .',
  '@prefix schema:  <https://schema.org/> .',
  '@prefix unit:    <http://qudt.org/vocab/unit/> .',
  '@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .',
].join('\n');

// Slug minúsculo da IRI de lista/álbum (lst:<slug>). IDÊNTICO ao
// slugifyList do app.js: a MESMA lista criada em lugares diferentes (app,
// galeria, form completo, /subir) tem que cair na mesma IRI — mudou aqui,
// mude lá.
export function slugifyList(name) {
  return String(name || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'lista';
}

// Slug Crockford base32 (8 chars) de pessoa nova — pes:<slug>.
export function randPersonSlug(n = 8) {
  const A = '0123456789abcdefghjkmnpqrstvwxyz';
  const b = crypto.getRandomValues(new Uint8Array(n));
  let s = '';
  for (let i = 0; i < n; i++) s += A[b[i] & 31];
  return s;
}

// iPhone/iPad (inclui o iPadOS que se apresenta como Mac).
export const IS_IOS = /iP(hone|ad|od)/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

// Página embutida no iframe de um modal do app?
export const EMBEDDED = window.self !== window.top;

// Embutida: pinça dentro da folha não pode deixar o APP inteiro com zoom (o
// Safari do iOS ignora user-scalable=no; estes são os eventos de gesto do
// WebKit). Standalone mantém o zoom por pinça (acessibilidade).
export function blockEmbeddedPinch() {
  if (!EMBEDDED) return;
  for (const t of ['gesturestart', 'gesturechange']) document.addEventListener(t, (e) => e.preventDefault(), { passive: false });
}
// Embutida: esconde o que o modal do app já mostra (título, lede, nav…) e
// bloqueia a pinça. Devolve EMBEDDED.
export function setupEmbeddedPage(hide = []) {
  if (!EMBEDDED) return false;
  for (const sel of hide) document.querySelector(sel)?.style.setProperty('display', 'none');
  blockEmbeddedPinch();
  return true;
}

// <script> clássico sob demanda (UMDs vendorados em ./lib/). `src` resolve
// contra o base do DOCUMENTO, não deste módulo.
export function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.onload = () => resolve(); s.onerror = () => reject(new Error(`falha ao carregar ${src}`));
    document.head.appendChild(s);
  });
}
// N3.js VENDORADO (UMD → window.N3), uma vez só (memoizado; uma falha libera
// uma nova tentativa).
let _n3P = null;
export function loadN3() {
  return _n3P ||= (window.N3 ? Promise.resolve() : loadScript('./lib/n3.min.js'))
    .then(() => window.N3, (e) => { _n3P = null; throw e; });
}
// Tom Select — UMD vendorado (sem CDN).
export async function loadTomSelect() {
  if (!window.TomSelect) await loadScript('./lib/tom-select.complete.min.js');
  return window.TomSelect;
}
// heic2any: HEIC → JPEG no cliente, só pra Chrome/Firefox (o Safari decodifica
// HEIC nativo). Import memoizado por promise: o boot não espera 1,35 MB que só
// o primeiro HEIC fora do Safari usa, e N cards concorrentes não disparam N
// imports. Resolve com a função, ou null se o CDN falhar.
let _heicP = null;
export function heic2anyReady() {
  return _heicP ||= import('https://esm.sh/heic2any@0.0.4')
    .then((m) => m.default)
    .catch(() => { console.warn('heic2any indisponível — HEIC só funciona no Safari.'); return null; });
}

// ─── Forms de passeio (upload_tour, backfill_tours) ──────────────────────

// "AAAA-MM-DD HH:MM[:SS]" (ou com 'T') → xsd:dateTime em -03:00. Os campos
// são texto livre 24h: o datetime-local cru renderizava mm/dd/yyyy + AM/PM em
// locale en-US, sem como forçar formato.
export function fmtDateTime(value) {
  if (!value) return null;
  const v = value.trim().replace(' ', 'T');
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/.test(v)) {
    throw new Error(`data inválida: "${value}" — use AAAA-MM-DD HH:MM (24h)`);
  }
  return v.length === 16 ? `${v}:00-03:00` : `${v}-03:00`;
}
// "HH:MM" ou "HH:MM:SS" → xsd:duration; qualquer outra forma → null (um
// campo só, ex.: "45", virava "PT45HundefinedM0S", inválido).
export function parseDuration(value) {
  if (!value) return null;
  const parts = value.split(':').map((p) => parseInt(p, 10));
  if (parts.length !== 2 && parts.length !== 3) return null;
  if (parts.some((n) => !Number.isFinite(n) || n < 0)) return null;
  const [h, m, s = 0] = parts;
  return `PT${h}H${m}M${s}S`;
}

// Picker nativo de data+hora por trás de um campo de texto 24h. O texto
// "AAAA-MM-DD HH:MM" segue sendo o valor canônico; o 📅 abre o picker e copia a
// escolha pro texto (disparando `input` e `change`). `seedFrom()` dá o valor
// inicial do picker quando o campo está vazio (ex.: Chegou em abre no dia do
// Partiu em). No toque (ou iOS) o datetime-local REAL, transparente, fica por
// cima do 📅 (.dt-overlay — CSS da página) e o toque abre a roda nativa: no
// iOS showPicker() existe mas NÃO abre nada em input de data/hora (WebKit bug
// 261703) e também não lança.
export function attachDateTimePicker(input, seedFrom) {
  const overlay = IS_IOS || !!window.matchMedia?.('(pointer: coarse)').matches;
  // Teclado de TEXTO (o inputmode=numeric dava no iPhone um teclado só de
  // dígitos, sem '-', ':' nem espaço) e sem autocorreção mexendo na data.
  input.setAttribute('autocapitalize', 'off');
  input.setAttribute('autocorrect', 'off');
  input.spellcheck = false;
  const wrap = document.createElement('div');
  wrap.className = 'dt-field' + (overlay ? ' dt-overlay' : '');
  input.parentNode.insertBefore(wrap, input);
  wrap.appendChild(input);
  const picker = document.createElement('input');
  picker.type = 'datetime-local';
  picker.tabIndex = -1;
  picker.setAttribute('aria-hidden', 'true');
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'pick';
  btn.textContent = '📅';
  btn.title = 'Escolher data e hora no calendário';
  btn.setAttribute('aria-label', 'Escolher data e hora');
  const pickWrap = document.createElement('span');
  pickWrap.className = 'pick-wrap';
  pickWrap.append(btn, picker);
  wrap.append(pickWrap);
  const toPicker = (txt) => {
    const v = (txt || '').trim().replace(' ', 'T');
    return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(v) ? v.slice(0, 16) : '';
  };
  const seed = () => { picker.value = toPicker(input.value) || toPicker(seedFrom?.()) || ''; };
  // Sobreposto, o toque vai direto pro picker: semeia antes de a roda abrir
  // (o pointerdown vem antes do foco; o foco cobre teclado/acessibilidade).
  picker.addEventListener('pointerdown', seed);
  picker.addEventListener('focus', seed);
  btn.addEventListener('click', () => {
    seed();
    // showPicker() exige gesto do usuário (estamos num click) e elemento
    // renderizado. No iOS quem abre a roda é o foco (dentro do gesto); idem
    // em browser sem showPicker ou quando ele lança.
    try {
      if (!IS_IOS && typeof picker.showPicker === 'function') picker.showPicker();
      else { picker.focus(); picker.click(); }
    } catch (_) { picker.focus(); picker.click(); }
  });
  const commit = () => {
    if (!picker.value) return;
    input.value = picker.value.slice(0, 16).replace('T', ' ');
    input.dispatchEvent(new Event('input',  { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  };
  picker.addEventListener('change', commit);
  picker.addEventListener('input', commit);   // iOS: a roda emite input a cada giro
}
