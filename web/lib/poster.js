// Arte de anúncio (☰ ações → 🎨): editor de pôster sobre o PRÓPRIO mapa, em
// passos (pensado pro celular): 1 rota · 2 informações · 3 mapa · 4 rótulos ·
// 5 texto do post · 6 publicar (Censo Hidrográfico + sabiá).
//
// Como funciona — e por que assim:
//  - O #map vira o palco: ganha o tamanho REAL da arte em px de CSS (1080×1350
//    no 4:5) e é encolhido por `transform: scale(s)` pra caber na tela. O
//    Leaflet 1.9 desconta a escala do contêiner nos eventos (arrastar, roda, a
//    pinça do leaflet-rotate), então todas as camadas visíveis, a ordem de
//    empilhamento e a rotação vêm de graça — e o que se vê é o que sai: uma
//    linha de 3 px na tela tem 3 px na arte.
//  - A arte (rótulos, caixa, imagens, atribuição) é desenhada num <canvas>
//    dentro do #map pela MESMA função que desenha a exportação (renderArt).
//  - Um <svg> por cima só tem as áreas de toque e as alças — e só do que o
//    passo atual edita (STEPS[].hits): no passo do mapa, todo toque move o
//    mapa; no dos rótulos, a caixa não atrapalha.
//  - Exportar compõe os panes do Leaflet num canvas — <img>, <canvas> e <svg>,
//    cada um com a cadeia de transforms/opacidades de CSS até o mapa (inclusive
//    o rotate do rotatePane) — e desenha a arte por cima (composeMap).
//  - Rótulos ficam presos ao CHÃO (lat/lng das pontas e do meio da curva):
//    mover, girar ou dar zoom depois leva os rótulos junto. Caixa e imagens
//    ficam presas à arte.
//  - Publicar: o passeio vai pro Censo pelo POST /upload-tour de sempre (a arte
//    no campo `announcement`, que a hospeda no bucket) e o sabiá abre numa aba
//    nova com o post pré-preenchido pelo fragmento `#amora=` (a arte vai pela
//    URL pública que o Censo devolveu). Quem publica de fato é a pessoa, lá.
// O estado inteiro (inclusive o enquadramento e o passo) persiste em
// localStorage.

import { fmtDateTime, randPersonSlug, saveFile, showToast, TTL_PREFIXES, turtleEscape } from './utils.js';

const STATE_KEY = 'phidro:poster:v1';
const STATE_VERSION = 2;
const SVGNS = 'http://www.w3.org/2000/svg';
const ROUTE_PANE = 'posterRoute';
const PAS_NS = 'https://id.pedalhidrografi.co/passeio/';
const SABIA_URL = 'https://sabia.pedalhidrografi.co/';
// Host gravado no catálogo (link da rota, página do passeio). Nunca o de um
// servidor de desenvolvimento — foi assim que o PH/96 ficou com localhost.
const PUBLIC_ORIGIN = /^(localhost|127\.0\.0\.1|\[::1\])$|\.localhost$/.test(location.hostname)
  ? 'https://amora.pedalhidrografi.co' : location.origin;

// hits: o que o toque na arte edita naquele passo. size: altura da folha no
// celular (short = sobra mais arte à vista; tall = formulário).
const STEPS = [
  { id: 'route',   title: 'Rota',          hits: [],                 size: 'short' },
  { id: 'info',    title: 'Informações',   hits: ['box', 'image'],   size: 'tall' },
  { id: 'map',     title: 'Mapa',          hits: [],                 size: 'short' },
  { id: 'labels',  title: 'Rótulos',       hits: ['label'],          size: 'short' },
  { id: 'text',    title: 'Texto do post', hits: [],                 size: 'tall' },
  { id: 'publish', title: 'Publicar',      hits: [],                 size: 'tall' },
];
// Séries do Censo (ser:<código>) e como o título da arte as chama.
const SERIES = {
  PH: 'Pedal Hidrográfico',
  S: 'Pedal Hidrográfico Suado',
  BT: 'Bicicletografia',
  BP: 'Bicipassarinhada',
  SESC: 'SESC',
  Hidroviagem: 'Hidroviagem',
};
const FORMATS = {
  '4x5':  { w: 1080, h: 1350, label: '4:5 · feed (1080×1350)' },
  '1x1':  { w: 1080, h: 1080, label: '1:1 · quadrado (1080×1080)' },
  '9x16': { w: 1080, h: 1920, label: '9:16 · story (1080×1920)' },
};
// Fontes vendoradas em fonts/ (OFL). Fredoka no lugar da Genty Sans do
// anúncio-modelo (PH 111, feito no Canva), que não é livre.
const FONTS = {
  fredoka:      { label: 'Arredondada (Fredoka)',          family: 'Fredoka',       weight: 600 },
  chunk:        { label: 'Serifada grossa (ChunkFive)',    family: 'ChunkFive',     weight: 400 },
  'opensans-b': { label: 'Sem serifa negrito (Open Sans)', family: 'Open Sans',     weight: 700 },
  opensans:     { label: 'Sem serifa (Open Sans)',         family: 'Open Sans',     weight: 400 },
  plex:         { label: 'Mono (IBM Plex)',                family: 'IBM Plex Mono', weight: 600 },
};
const fontCss = (st) => {
  const f = FONTS[st.font] || FONTS.fredoka;
  return `${f.weight} ${st.size}px "${f.family}", sans-serif`;
};
// Cores do anúncio-modelo: rios #ffbd59, morros #ff751f, anomalias #c2ffe1,
// saída/chegada #c1ff72. Tamanhos em px da arte de 1080 de largura. `place`:
// o que o toque no mapa posiciona ("toque onde fica o rio").
const KINDS = {
  rio:      { label: 'Rio',      color: '#ffbd59', size: 30, text: '',       place: 'o rio' },
  morro:    { label: 'Morro',    color: '#ff751f', size: 22, text: '',       place: 'o morro' },
  anomalia: { label: 'Anomalia', color: '#c2ffe1', size: 20, text: '',       place: 'a anomalia' },
  saida:    { label: 'Saída',    color: '#c1ff72', size: 29, text: 'sai ',   place: 'a saída' },
  chegada:  { label: 'Chegada',  color: '#c1ff72', size: 29, text: 'chega ', place: 'a chegada' },
  livre:    { label: 'Texto',    color: '#ffffff', size: 24, text: '',       place: 'o texto' },
};
const HALOS = { shadow: 'Sombra', outline: 'Contorno', none: 'Nenhum' };
const SWATCHES = ['#ffbd59', '#ff751f', '#c2ffe1', '#c1ff72', '#ffffff', '#000000'];
// Temas da caixa: fundo, faixa (gradiente) e cor dos textos.
const BOX_THEMES = {
  caqui:   { label: 'Cáqui', fill: '#898759', band: ['#4f9e3a', '#86c24f'], text: '#000000' },
  agua:    { label: 'Água',  fill: '#867627', band: ['#4a4115', '#6b5d1f'], text: '#ffffff' },
  noite:   { label: 'Noite', fill: '#1d2433', band: ['#2a6f97', '#3fa7a0'], text: '#ffffff' },
  claro:   { label: 'Claro', fill: '#fdfbf3', band: ['#c1ff72', '#86c24f'], text: '#000000' },
};

const uid = () => Math.random().toString(36).slice(2, 10);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const num = (v, d) => (Number.isFinite(+v) ? +v : d);

function textStyle(over = {}) {
  return { font: 'fredoka', size: 30, color: '#ffffff', spacing: 0,
    halo: 'shadow', haloColor: '#000000', haloSize: 1, ...over };
}
// Caixa do anúncio-modelo: cáqui opaco com uma faixa verde translúcida
// embaixo; título em ChunkFive, subtítulo em Open Sans negrito, data na faixa.
// x/y dos textos em unidades da caixa; y = linha de base. `bind`: o texto vem
// das informações do passeio (passo 2) até alguém escrever outro por cima.
function defaultBox(W) {
  const w = 640, h = 184;
  const t = (bind, y, font, size) => ({
    id: uid(), bind, text: '', x: w / 2, y, align: 'center',
    ...textStyle({ font, size, color: '#000000', halo: 'none' }),
  });
  return {
    x: W - w - 18, y: 18, w, h, k: 1, radius: 18,
    fill: '#898759', fillOpacity: 1,
    band: true, bandColor: '#4f9e3a', bandColor2: '#86c24f', bandOpacity: 0.85, bandH: 54,
    texts: [
      t('title', 66, 'chunk', 56),
      t('name', 112, 'opensans-b', 34),
      t('when', 166, 'fredoka', 26),
    ],
  };
}
function defaultInfo() {
  return { series: 'PH', number: '', name: '', date: '', time: '20:00', meeting: '', arrival: '' };
}
function defaultState() {
  return {
    v: STATE_VERSION, step: 1, format: '4x5', attribution: true,
    route: { src: '', width: 8, color: '#ffffff', casing: true, casingColor: '#1d1d1b', casingWidth: 2 },
    routeName: '',
    view: null,
    info: defaultInfo(),
    box: defaultBox(FORMATS['4x5'].w),
    labels: [],
    images: [],
    caption: '', captionEdited: false,
    alt: '', altEdited: false,
    // Passeio do Censo desta arte: `key` (série/número) amarra o tourId — mudou
    // a edição, é outro passeio (não sobrescreve o da semana passada).
    censo: { key: '', tourId: '', url: '', linkTourId: '', linkName: '' },
  };
}
const isLL = (p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]);
function loadState() {
  const d = defaultState();
  let s = null;
  try { s = JSON.parse(localStorage.getItem(STATE_KEY) || 'null'); } catch { s = null; }
  if (!s || (s.v !== 1 && s.v !== STATE_VERSION)) return d;
  // v1 (antes dos passos) não tinha textos vinculados: a caixa volta ao padrão.
  const box = s.v === STATE_VERSION && s.box ? { ...d.box, ...s.box,
    texts: Array.isArray(s.box.texts) ? s.box.texts.map((t) => ({ ...textStyle(), ...t, id: t.id || uid() })) : d.box.texts,
  } : d.box;
  return {
    ...d, ...s, v: STATE_VERSION, box,
    step: clamp(Math.round(num(s.step, 1)), 1, STEPS.length),
    format: FORMATS[s.format] ? s.format : d.format,
    route: { ...d.route, ...(s.route || {}) },
    info: { ...d.info, ...(s.info || {}) },
    censo: { ...d.censo, ...(s.censo || {}) },
    labels: (Array.isArray(s.labels) ? s.labels : [])
      .filter((l) => l && isLL(l.a) && isLL(l.b))
      .map((l) => ({ ...textStyle(), ...l, c: isLL(l.c) ? l.c : null, id: l.id || uid() })),
    images: (Array.isArray(s.images) ? s.images : [])
      .filter((i) => i && typeof i.src === 'string' && i.w > 0 && i.h > 0),
  };
}
const fmtHour = (t) => {
  const m = /^(\d{1,2}):(\d{2})/.exec(t || '');
  return m ? `${+m[1]}h${m[2] === '00' ? '' : m[2]}` : '';
};
const fmtDateBR = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? `${m[3]}/${m[2]}` : '';
};
// Texto em base64url (UTF-8) — o fragmento #amora= do sabiá.
function b64url(text) {
  const bytes = new TextEncoder().encode(text);
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// ─── Texto ao longo de um caminho ────────────────────────────────────────────
const _measure = document.createElement('canvas').getContext('2d');
const _advCache = new Map();
const graphemes = (() => {
  if (typeof Intl !== 'undefined' && Intl.Segmenter) {
    const seg = new Intl.Segmenter('pt', { granularity: 'grapheme' });
    return (s) => Array.from(seg.segment(s), (x) => x.segment);
  }
  return (s) => Array.from(s);
})();
// Avanço de cada grafema JÁ com o kerning do par anterior: largura do prefixo
// até ele menos a do prefixo anterior. Desenhando letra a letra (necessário na
// curva) o espaçamento fica igual ao da palavra inteira.
function advances(text, st) {
  const key = `${fontCss(st)}|${text}`;
  let hit = _advCache.get(key);
  if (hit) return hit;
  _measure.font = fontCss(st);
  const chars = graphemes(text);
  const adv = [];
  let prev = 0, acc = '';
  for (const ch of chars) {
    acc += ch;
    const w = _measure.measureText(acc).width;
    adv.push(w - prev);
    prev = w;
  }
  hit = { chars, adv, width: prev };
  if (_advCache.size > 800) _advCache.clear();
  _advCache.set(key, hit);
  return hit;
}
const runWidth = (text, st) => {
  const { width, chars } = advances(text, st);
  return width + st.spacing * Math.max(0, chars.length - 1);
};
// Centra o texto no caminho; o que passa das pontas segue a tangente delas.
function placeGlyphs(text, st, path) {
  const { chars, adv } = advances(text, st);
  const total = runWidth(text, st);
  const start = (path.len - total) / 2;
  let s = start;
  const glyphs = [];
  for (let i = 0; i < chars.length; i++) {
    const p = path.at(s + adv[i] / 2);
    glyphs.push({ ch: chars[i], x: p.x, y: p.y, a: p.a });
    s += adv[i] + st.spacing;
  }
  return { glyphs, start, total };
}
// Quadrática que PASSA por M em t = ½ (a alça do meio fica sobre a curva).
function bezierPath(A, B, M) {
  const Q = { x: 2 * M.x - (A.x + B.x) / 2, y: 2 * M.y - (A.y + B.y) / 2 };
  const N = 64;
  const pt = (t) => {
    const u = 1 - t;
    return { x: u * u * A.x + 2 * u * t * Q.x + t * t * B.x, y: u * u * A.y + 2 * u * t * Q.y + t * t * B.y };
  };
  const tan = (t) => {
    const u = 1 - t;
    const dx = 2 * u * (Q.x - A.x) + 2 * t * (B.x - Q.x);
    const dy = 2 * u * (Q.y - A.y) + 2 * t * (B.y - Q.y);
    return dx || dy ? Math.atan2(dy, dx) : Math.atan2(B.y - A.y, B.x - A.x);
  };
  const cum = [0];
  let prev = pt(0);
  for (let i = 1; i <= N; i++) {
    const p = pt(i / N);
    cum.push(cum[i - 1] + Math.hypot(p.x - prev.x, p.y - prev.y));
    prev = p;
  }
  const len = cum[N];
  const a0 = tan(0), a1 = tan(1);
  return {
    len,
    at(s) {
      if (s <= 0 || len < 1e-6) return { x: A.x + Math.cos(a0) * s, y: A.y + Math.sin(a0) * s, a: a0 };
      if (s >= len) { const r = s - len; return { x: B.x + Math.cos(a1) * r, y: B.y + Math.sin(a1) * r, a: a1 }; }
      let lo = 0, hi = N;
      while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (cum[mid] < s) lo = mid; else hi = mid; }
      const t = (lo + (s - cum[lo]) / ((cum[hi] - cum[lo]) || 1)) / N;
      const p = pt(t);
      return { x: p.x, y: p.y, a: tan(t) };
    },
  };
}
// Desenha os grafemas posicionados: 1º passe o efeito (sombra/contorno) de
// TODOS, 2º o preenchimento — senão a sombra de uma letra cobriria a anterior.
// A sombra sai pelo truque do deslocamento: a letra é desenhada FORA da tela e
// só a sombra (shadowOffset, em px de dispositivo) cai no lugar — funciona em
// todo navegador, sem ctx.filter. `dy` desce a linha de base abaixo do caminho;
// `k` é a escala do contexto (a caixa), pra sombra acompanhar.
function drawGlyphs(g, glyphs, st, dy = 0, k = 1) {
  if (!glyphs.length) return;
  g.save();
  g.font = fontCss(st);
  g.textAlign = 'center';
  g.textBaseline = 'alphabetic';
  const base = g.getTransform();
  const each = (fn) => {
    for (const gl of glyphs) {
      g.save();
      g.translate(gl.x, gl.y);
      g.rotate(gl.a);
      fn(gl);
      g.restore();
    }
  };
  const hs = Math.max(0, num(st.haloSize, 1));
  if (st.halo === 'shadow' && hs > 0) {
    const FAR = 8000;
    g.setTransform(new DOMMatrix([1, 0, 0, 1, -FAR, 0]).multiply(base));
    g.shadowColor = st.haloColor || '#000';
    g.shadowBlur = st.size * 0.05 * hs * k;
    g.shadowOffsetX = FAR + st.size * 0.07 * hs * k;
    g.shadowOffsetY = st.size * 0.07 * hs * k;
    g.fillStyle = '#000';
    each((gl) => g.fillText(gl.ch, 0, dy));
    g.shadowColor = 'transparent';
    g.setTransform(base);
  } else if (st.halo === 'outline' && hs > 0) {
    g.lineJoin = 'round';
    g.miterLimit = 2;
    g.lineWidth = st.size * 0.16 * hs;
    g.strokeStyle = st.haloColor || '#000';
    each((gl) => g.strokeText(gl.ch, 0, dy));
  }
  g.fillStyle = st.color;
  each((gl) => g.fillText(gl.ch, 0, dy));
  g.restore();
}
function roundRectPath(g, x, y, w, h, r) {
  r = clamp(r, 0, Math.min(w, h) / 2);
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}
// Linhas de um texto da caixa como grafemas posicionados (unidades da caixa)
// + o retângulo que ele ocupa (área de toque). `text`: o texto efetivo (o de
// um texto vinculado vem das informações do passeio — ver textOf).
function layoutBoxText(t, text = t.text) {
  const lh = t.size * 1.15;
  const glyphs = [];
  const lines = String(text ?? '').split('\n');
  let minX = Infinity, maxX = -Infinity;
  lines.forEach((line, i) => {
    const total = runWidth(line, t);
    const x0 = t.align === 'left' ? t.x : t.align === 'right' ? t.x - total : t.x - total / 2;
    const y = t.y + i * lh;
    glyphs.push(...placeGlyphs(line, t, { len: total, at: (s) => ({ x: x0 + s, y, a: 0 }) }).glyphs);
    minX = Math.min(minX, x0);
    maxX = Math.max(maxX, x0 + total);
  });
  if (!(maxX > minX)) { minX = t.x - t.size / 2; maxX = t.x + t.size / 2; }
  const n = lines.length;
  return { glyphs, rect: { x: minX, y: t.y - t.size * 0.82, w: maxX - minX, h: (n - 1) * lh + t.size * 1.1 } };
}
function slugify(s) {
  return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'arte';
}
const WEEKDAYS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function fmtPosterDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  if (!m) return '';
  const d = new Date(+m[1], +m[2] - 1, +m[3]);
  return `${WEEKDAYS[d.getDay()]} ${+m[3]} ${MONTHS[+m[2] - 1]} ${m[1]}`;
}

// ─── Composição do mapa (exportação) ─────────────────────────────────────────
// Matriz de um elemento relativa ao pai: left/top (todo pane/tile do Leaflet é
// absolute em 0,0, mas por via das dúvidas) e o transform com a origem dele.
function localMatrix(cs) {
  let m = new DOMMatrix();
  if (cs.position === 'absolute' || cs.position === 'relative') {
    const l = parseFloat(cs.left), t = parseFloat(cs.top);
    if (l || t) m = m.translate(l || 0, t || 0);
  }
  if (cs.transform && cs.transform !== 'none') {
    const [ox, oy] = cs.transformOrigin.split(' ').map((v) => parseFloat(v) || 0);
    m = m.translate(ox, oy).multiply(new DOMMatrix(cs.transform)).translate(-ox, -oy);
  }
  return m;
}
// Lista de desenho (ordem de pintura): folhas <img>/<canvas>/<svg>, irmãos
// ordenados por z-index (estável na ordem do DOM). A opacidade é multiplicada
// até a folha — exato pros panes do Leaflet, onde cada renderizador SVG/canvas
// é uma folha só e os tiles não se sobrepõem.
function collectLeaves(el, M, alpha, out) {
  const cs = getComputedStyle(el);
  if (cs.display === 'none' || cs.visibility === 'hidden') return;
  const a = alpha * num(parseFloat(cs.opacity), 1);
  if (a < 0.004) return;
  const m = M.multiply(localMatrix(cs));
  const tag = el.tagName.toLowerCase();
  if (tag === 'img') {
    if (el.complete && el.naturalWidth) out.push({ kind: 'img', el, m, a, w: el.offsetWidth || el.width, h: el.offsetHeight || el.height, filter: cs.filter, tile: true });
    return;
  }
  if (tag === 'canvas') {
    if (el.width && el.height) out.push({ kind: 'canvas', el, m, a, w: el.offsetWidth || el.width, h: el.offsetHeight || el.height, filter: cs.filter, tile: el.classList.contains('leaflet-tile') });
    return;
  }
  if (tag === 'svg') {
    const w = el.width?.baseVal?.value || parseFloat(cs.width) || 0;
    const h = el.height?.baseVal?.value || parseFloat(cs.height) || 0;
    if (w && h) out.push({ kind: 'svg', el, m, a, w, h, filter: cs.filter });
    return;
  }
  const kids = Array.from(el.children, (c, i) => ({ c, i, z: parseInt(getComputedStyle(c).zIndex, 10) || 0 }));
  kids.sort((p, q) => p.z - q.z || p.i - q.i);
  for (const { c } of kids) collectLeaves(c, m, a, out);
}
const SVG_STYLE_PROPS = ['display', 'visibility', 'opacity', 'fill', 'fill-opacity', 'fill-rule',
  'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray', 'stroke-dashoffset',
  'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit'];
// SVG do Leaflet → imagem (2× pra linha fina não borrar quando o pane gira).
// Os estilos computados vão inline: classes de CSS do app não existem dentro
// de uma imagem SVG.
async function rasterizeSvg(svg, w, h) {
  const clone = svg.cloneNode(true);
  const src = svg.querySelectorAll('*');
  const dst = clone.querySelectorAll('*');
  for (let i = 0; i < src.length; i++) {
    const cs = getComputedStyle(src[i]);
    dst[i].setAttribute('style', SVG_STYLE_PROPS.map((p) => `${p}:${cs.getPropertyValue(p)}`).join(';'));
  }
  clone.removeAttribute('style');
  clone.removeAttribute('class');
  clone.setAttribute('xmlns', SVGNS);
  if (!clone.getAttribute('viewBox')) clone.setAttribute('viewBox', `0 0 ${w} ${h}`);
  clone.setAttribute('width', String(w * 2));
  clone.setAttribute('height', String(h * 2));
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml;charset=utf-8' }));
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    return img;
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
// Tile sem crossOrigin (sara1930…) sujaria o canvas: rebusca em CORS. Host que
// não manda Access-Control-Allow-Origin fica de fora (e é avisado).
async function cleanImageSource(img, signal) {
  const src = img.currentSrc || img.src;
  let url;
  try { url = new URL(src, document.baseURI); } catch { return null; }
  if (img.crossOrigin != null || url.origin === location.origin || url.protocol === 'data:' || url.protocol === 'blob:') return img;
  const res = await fetch(url.href, { mode: 'cors', credentials: 'omit', cache: 'no-store', signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return createImageBitmap(await res.blob());
}


export function createPoster(ctx) {
  const { map } = ctx;
  const mapEl = map.getContainer();
  let state = loadState();
  let active = false;
  let scale = 1;
  let sel = null;                 // { type: 'label'|'box'|'text'|'image', id }
  let placing = null;             // id do rótulo recém-criado: o próximo toque no mapa o posiciona
  let saved = null;               // o mapa/página como estavam antes de abrir
  let route = { latlngs: null, pois: [], key: '', slug: '', id: '', name: '' };
  let routeLayers = [];
  let savedRoutes = null;
  const routeStateCache = new Map();
  const imgCache = new Map();
  let lastLayout = { labels: new Map(), box: null };
  let drag = null;
  let downAt = null;
  let raf = 0;
  let quotaWarned = false;
  let busy = '';                  // 'export' | 'censo' — trava os botões
  const COARSE = !!window.matchMedia?.('(pointer: coarse)').matches;

  const step = () => STEPS[state.step - 1];
  const hitsOn = (kind) => step().hits.includes(kind);
  const dims = () => FORMATS[state.format] || FORMATS['4x5'];
  const findLabel = (id) => state.labels.find((l) => l.id === id);
  const findText = (id) => state.box.texts.find((t) => t.id === id);
  const findImage = (id) => state.images.find((i) => i.id === id);
  const toLL = (p) => {
    const ll = map.containerPointToLatLng(L.point(p.x, p.y));
    return [+ll.lat.toFixed(6), +ll.lng.toFixed(6)];
  };
  const toPt = (ll) => map.latLngToContainerPoint(ll);

  // ─── Informações do passeio → textos ───────────────────────────────────────
  const seriesTitle = () => {
    const i = state.info;
    return `${SERIES[i.series] || i.series || ''} ${i.number || ''}`.trim();
  };
  const whenLine = () => {
    const i = state.info;
    return [fmtPosterDate(i.date), fmtHour(i.time), i.meeting.trim()].filter(Boolean).join(' ');
  };
  // Texto efetivo de um texto da caixa: vinculado = das informações (com um
  // marcador enquanto o campo está vazio, pra caixa nunca sair em branco).
  function textOf(t) {
    if (!t.bind) return t.text;
    if (t.bind === 'title') return state.info.number ? seriesTitle() : `${SERIES[state.info.series] || 'Pedal Hidrográfico'} 000`;
    if (t.bind === 'name') return state.info.name.trim() || 'nome do passeio';
    if (t.bind === 'when') return state.info.date || state.info.meeting.trim() ? whenLine() : 'dia · hora · ponto de encontro';
    return t.text;
  }
  const routeLink = () => (route.slug ? `${PUBLIC_ORIGIN}/route/${route.slug}` : '');
  function makeCaption() {
    const i = state.info;
    const lines = [];
    const head = [seriesTitle(), i.name.trim()].filter(Boolean).join(' · ');
    if (head) lines.push(head, '');
    const when = [fmtPosterDate(i.date), i.time ? `às ${fmtHour(i.time)}` : ''].filter(Boolean).join(' ');
    if (when) lines.push(`📅 ${when}`);
    if (i.meeting.trim()) lines.push(`📍 saída: ${i.meeting.trim()}`);
    if (i.arrival.trim()) lines.push(`🏁 chegada: ${i.arrival.trim()}`);
    if (routeLink()) lines.push(`🗺️ rota: ${routeLink()}`);
    const rivers = state.labels.filter((l) => l.kind === 'rio' && l.text.trim()).map((l) => l.text.trim());
    if (rivers.length) lines.push('', `seguindo as águas: ${[...new Set(rivers)].join(', ')}`);
    return lines.join('\n').trim();
  }
  // Descrição da arte pra leitor de tela (vai como texto alternativo no sabiá;
  // o Mastodon exige). Tudo o que a imagem diz em texto.
  function makeAlt() {
    const i = state.info;
    const parts = [`Arte de divulgação: ${[seriesTitle(), i.name.trim()].filter(Boolean).join(', ')}`];
    const when = [fmtPosterDate(i.date), fmtHour(i.time)].filter(Boolean).join(', ');
    if (when) parts.push(when);
    if (i.meeting.trim()) parts.push(`saída: ${i.meeting.trim()}`);
    if (i.arrival.trim()) parts.push(`chegada: ${i.arrival.trim()}`);
    let s = `${parts.join('; ')}.`;
    if (route.latlngs) s += ' Mapa do relevo com o traçado da rota em destaque.';
    const byKind = (k) => [...new Set(state.labels.filter((l) => l.kind === k && l.text.trim()).map((l) => l.text.trim()))];
    const named = [['rio', 'Rios'], ['morro', 'Morros'], ['anomalia', 'Anomalias']]
      .map(([k, label]) => { const v = byKind(k); return v.length ? `${label}: ${v.join(', ')}.` : ''; })
      .filter(Boolean);
    if (named.length) s += ` ${named.join(' ')}`;
    if (state.images.length) s += ` ${state.images.length === 1 ? 'Um logo' : `${state.images.length} logos`} de apoio.`;
    return s;
  }
  function refreshAutoTexts() {
    if (!state.captionEdited) state.caption = makeCaption();
    if (!state.altEdited) state.alt = makeAlt();
  }

  // ─── Persistência ──────────────────────────────────────────────────────────
  let saveTimer = 0;
  function persistSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(persistNow, 400); }
  function persistNow() {
    clearTimeout(saveTimer);
    if (active) {
      const c = map.getCenter();
      state.view = { lat: +c.lat.toFixed(6), lng: +c.lng.toFixed(6), zoom: +map.getZoom().toFixed(3), bearing: +(map.getBearing?.() || 0).toFixed(2) };
    }
    try { localStorage.setItem(STATE_KEY, JSON.stringify(state)); }
    catch {
      // Logos grandes estouram a cota: guarda o resto sem elas.
      try { localStorage.setItem(STATE_KEY, JSON.stringify({ ...state, images: [] })); } catch { /* sem storage */ }
      if (!quotaWarned && state.images.length) {
        quotaWarned = true;
        showToast('As imagens não cabem no armazenamento deste aparelho — elas ficam só até recarregar a página.', 6000);
      }
    }
  }

  // ─── DOM ───────────────────────────────────────────────────────────────────
  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : v);
    }
    for (const kid of kids.flat()) if (kid != null) n.append(kid);
    return n;
  };
  const artCanvas = el('canvas', { class: 'poster-art', 'aria-hidden': 'true' });
  const uiSvg = document.createElementNS(SVGNS, 'svg');
  uiSvg.setAttribute('class', 'poster-ui');
  const uiGroups = {};
  for (const g of ['labels', 'box', 'images', 'sel']) {
    uiGroups[g] = document.createElementNS(SVGNS, 'g');
    uiSvg.appendChild(uiGroups[g]);
  }
  const panel = buildPanel();
  const q = (s) => panel.querySelector(s);

  function buildPanel() {
    const p = el('aside', { class: 'poster-panel', 'aria-label': 'Arte de anúncio' });
    const seriesOpts = Object.entries(SERIES).map(([k, v]) => `<option value="${k}">${k} · ${v}</option>`).join('');
    const themeBtns = Object.entries(BOX_THEMES).map(([k, t]) =>
      `<button type="button" class="poster-theme" data-act="theme" data-theme="${k}" style="--fill:${t.fill};--band:${t.band[1]};--txt:${t.text}">${t.label}</button>`).join('');
    const kindBtns = Object.entries(KINDS).map(([k, K]) =>
      `<button type="button" class="secondary-btn poster-kind" data-act="add-label" data-kind="${k}" style="--kind:${K.color}">+ ${K.label}</button>`).join('');
    const formatOpts = Object.entries(FORMATS).map(([k, f]) => `<option value="${k}">${f.label}</option>`).join('');
    p.innerHTML = `
      <header class="poster-head">
        <button type="button" class="secondary-btn poster-collapse" aria-expanded="true" aria-label="Recolher o painel" title="Recolher/abrir o painel">▾</button>
        <ol class="poster-steps">${STEPS.map((s, i) =>
          `<li><button type="button" data-goto="${i + 1}" aria-label="Passo ${i + 1}: ${s.title}" title="${s.title}">${i + 1}</button></li>`).join('')}</ol>
        <button type="button" class="secondary-btn poster-exit" data-act="exit" aria-label="Sair do editor de arte (fica guardado)" title="Sair (a arte fica guardada)">✕</button>
      </header>
      <div class="poster-body">
        <h2 class="poster-step-title" tabindex="-1"></h2>
        <section class="poster-sel" hidden></section>

        <section class="poster-step" data-step="1">
          <p class="poster-hint">Escolha a rota que vai no mapa da arte.</p>
          <input type="search" class="poster-search" data-k="route-q" placeholder="Buscar rota salva…" aria-label="Buscar rota salva" enterkeyhint="search">
          <div class="poster-route-list" role="listbox" aria-label="Rotas"></div>
          <button type="button" class="secondary-btn poster-wide-btn" data-act="edit-route">✏️ Desenhar ou ajustar no Traçar</button>
          <p class="poster-hint">No Traçar, quando terminar, toque em <b>🎨 Voltar pra arte</b>.</p>
        </section>

        <section class="poster-step" data-step="2">
          <div class="poster-banner" data-k="tour-link" hidden></div>
          <div class="poster-pair">
            <label class="poster-field">Série<select data-k="info.series">${seriesOpts}</select></label>
            <label class="poster-field poster-narrow">Número<input type="number" inputmode="numeric" min="1" step="1" data-k="info.number"></label>
          </div>
          <label class="poster-field">Nome do passeio<input type="text" data-k="info.name" placeholder="ex.: jurubatuba acima noturno" enterkeyhint="next" autocomplete="off"></label>
          <div class="poster-pair">
            <label class="poster-field">Data<input type="date" data-k="info.date"></label>
            <label class="poster-field poster-narrow">Horário<input type="time" data-k="info.time" step="300"></label>
          </div>
          <label class="poster-field">Ponto de encontro<input type="text" data-k="info.meeting" placeholder="ex.: parque do povo" enterkeyhint="next" autocomplete="off"></label>
          <label class="poster-field">Chegada <small>(opcional)</small><input type="text" data-k="info.arrival" placeholder="ex.: cptm autódromo" enterkeyhint="done" autocomplete="off"></label>
          <h3>Caixa da arte</h3>
          <p class="poster-hint">Os textos acima aparecem na caixa. Arraste a caixa na arte pra mudar de lugar; toque num texto dela pra trocar fonte, tamanho ou cor.</p>
          <div class="poster-row"><label>Tamanho</label><input type="range" min="0.4" max="2" step="0.01" data-k="box.k" aria-label="Tamanho da caixa"></div>
          <div class="poster-themes" role="group" aria-label="Cores da caixa">${themeBtns}</div>
          <div class="poster-row">
            <button type="button" class="secondary-btn" data-act="sel-box">✎ Mais ajustes da caixa</button>
            <button type="button" class="secondary-btn" data-act="add-image">+ Logo / imagem</button>
            <input type="file" accept="image/*" hidden data-k="image-file">
          </div>
          <div class="poster-chips" data-list="images"></div>
        </section>

        <section class="poster-step" data-step="3">
          <p class="poster-hint">Arraste a arte pra mover o mapa · pinça ou roda = zoom · dois dedos ou Shift+roda = girar.</p>
          <div class="poster-banner" data-k="other-routes" hidden>As outras rotas do coletivo estão aparecendo no fundo.
            <button type="button" class="secondary-btn" data-act="hide-routes">Esconder as outras rotas</button></div>
          <button type="button" class="secondary-btn poster-wide-btn" data-act="fit">⌖ Enquadrar a rota</button>
          <div class="poster-row"><label>Girar</label><input type="range" min="-180" max="180" step="1" data-k="bearing" aria-label="Girar o mapa (graus)"><output></output>
            <button type="button" class="secondary-btn" data-act="north" title="Norte pra cima" aria-label="Norte pra cima">N↑</button></div>
          <div class="poster-row"><label>Zoom</label>
            <button type="button" class="secondary-btn poster-sq" data-act="zoom-out" aria-label="Menos zoom">−</button>
            <button type="button" class="secondary-btn poster-sq" data-act="zoom-in" aria-label="Mais zoom">+</button></div>
          <div class="poster-row"><label>Formato</label><select data-k="format" aria-label="Formato da arte">${formatOpts}</select></div>
          <div class="poster-row"><label>Linha da rota</label><input type="range" min="1" max="40" step="0.5" data-k="route.width" aria-label="Espessura da linha da rota"><output></output></div>
          <div class="poster-row"><label>Cor da linha</label><input type="color" data-k="route.color" aria-label="Cor da linha da rota">
            <label class="poster-inline"><input type="checkbox" data-k="route.casing"> contorno</label>
            <input type="color" data-k="route.casingColor" aria-label="Cor do contorno"></div>
          <details class="poster-layers-wrap"><summary>⧉ Camadas do fundo</summary><div class="poster-layers"></div></details>
        </section>

        <section class="poster-step" data-step="4">
          <p class="poster-hint">Toque num tipo, escreva o nome e toque na arte onde ele fica. Depois dá pra arrastar; as bolinhas das pontas esticam e giram, a do meio curva.</p>
          <div class="poster-kinds">${kindBtns}</div>
          <div class="poster-chips" data-list="labels"></div>
          <button type="button" class="secondary-btn poster-wide-btn" data-act="poi-labels" hidden>+ Rótulos dos pontos marcados na rota</button>
        </section>

        <section class="poster-step" data-step="5">
          <label class="poster-field">Legenda do post <span class="poster-count" data-count="caption"></span>
            <textarea data-k="caption" rows="9"></textarea></label>
          <button type="button" class="secondary-btn" data-act="caption-reset">↺ Refazer com as informações</button>
          <p class="poster-hint">Os primeiros 500 caracteres vão pra todas as redes (o Mastodon só aceita isso); o Instagram e o WhatsApp levam até 2150.</p>
          <label class="poster-field">Descrição da imagem <small>(pra quem usa leitor de tela)</small>
            <textarea data-k="alt" rows="4"></textarea></label>
          <button type="button" class="secondary-btn" data-act="alt-reset">↺ Refazer a descrição</button>
        </section>

        <section class="poster-step" data-step="6">
          <ul class="poster-check" data-k="checklist"></ul>
          <label class="poster-field" data-k="route-name-wrap" hidden>Nome da rota <small>(vira o link /route/…)</small>
            <input type="text" data-k="routeName" autocomplete="off"></label>
          <div class="poster-banner" data-k="censo-mode"></div>
          <button type="button" class="primary-btn poster-big" data-act="censo">📊 Salvar no Censo Hidrográfico</button>
          <div class="poster-result" data-k="censo-result" role="status" aria-live="polite"></div>
          <button type="button" class="primary-btn poster-big" data-act="sabia">📣 Abrir no sabiá pra publicar</button>
          <p class="poster-hint" data-k="sabia-hint"></p>
          <div class="poster-row">
            <button type="button" class="secondary-btn" data-act="export-png">⤓ Baixar PNG</button>
            <button type="button" class="secondary-btn" data-act="export-jpg">⤓ JPG</button>
          </div>
          <label class="poster-inline poster-row"><input type="checkbox" data-k="attribution"> Créditos das camadas no canto da arte</label>
          <button type="button" class="secondary-btn poster-danger" data-act="reset">🗑 Começar uma arte nova</button>
        </section>
      </div>
      <footer class="poster-foot">
        <button type="button" class="secondary-btn" data-act="prev">← Voltar</button>
        <button type="button" class="primary-btn" data-act="next">Próximo →</button>
      </footer>`;
    p.addEventListener('click', onPanelClick);
    p.addEventListener('input', onPanelInput);
    p.addEventListener('change', onPanelInput);
    // Enter num campo de uma linha pula pro próximo (no celular é o "seguinte"
    // do teclado) em vez de não fazer nada.
    p.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' || e.isComposing || !(e.target instanceof HTMLInputElement)) return;
      if (/^(checkbox|radio|range|color|file|button)$/.test(e.target.type)) return;
      e.preventDefault();
      const fields = [...e.target.closest('section')?.querySelectorAll('input:not([type=hidden]):not([type=range]):not([type=checkbox]):not([type=color]):not([type=file]), select, textarea') || []]
        .filter((f) => f.getClientRects().length);
      const next = fields[fields.indexOf(e.target) + 1];
      if (next) next.focus(); else e.target.blur();
    });
    p.querySelector('.poster-collapse').addEventListener('click', () => {
      const c = p.classList.toggle('collapsed');
      const b = p.querySelector('.poster-collapse');
      b.setAttribute('aria-expanded', String(!c));
      b.setAttribute('aria-label', c ? 'Abrir o painel' : 'Recolher o painel');
      b.textContent = c ? '▴' : '▾';
      layout();
    });
    p.querySelector('[data-k="image-file"]').addEventListener('change', (e) => {
      const f = e.target.files?.[0];
      e.target.value = '';
      if (f) addImage(f);
    });
    return p;
  }

  // ─── Passos ────────────────────────────────────────────────────────────────
  function goStep(n, { focus = true } = {}) {
    n = clamp(n, 1, STEPS.length);
    if (sel) select(null);
    placing = null;
    state.step = n;
    renderStep();
    if (focus) {
      q('.poster-body').scrollTop = 0;
      q('.poster-step-title').focus({ preventScroll: true });
    }
    requestAnimationFrame(layout);
    persistSoon();
  }
  function renderStep() {
    const s = step();
    panel.dataset.size = s.size;
    q('.poster-step-title').textContent = `${state.step} · ${s.title}`;
    for (const sec of panel.querySelectorAll('.poster-step')) sec.hidden = +sec.dataset.step !== state.step;
    panel.querySelectorAll('[data-goto]').forEach((b) => {
      const n = +b.dataset.goto;
      b.classList.toggle('done', n < state.step);
      if (n === state.step) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
    });
    q('[data-act="prev"]').hidden = state.step === 1;
    const next = q('[data-act="next"]');
    next.textContent = state.step === STEPS.length ? '✓ Concluir' : `${STEPS[state.step].title} →`;
    if (state.step === 1) renderRouteList();
    if (state.step === 2) renderInfo();
    if (state.step === 3) syncMapControls();
    if (state.step === 4) renderLists();
    if (state.step === 5) renderText();
    if (state.step === 6) renderPublish();
    renderSelPanel();
    requestRender();
  }

  // ─── Passo 1: rota ─────────────────────────────────────────────────────────
  async function loadRouteList() {
    try {
      const res = await fetch('./saved-routes', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      savedRoutes = (await res.json()).routes || [];
    } catch (err) {
      savedRoutes = [];
      console.warn('[poster] rotas salvas:', err);
    }
    if (active && state.step === 1) renderRouteList();
  }
  function renderRouteList() {
    const box = q('.poster-route-list');
    const needle = (q('[data-k="route-q"]').value || '').trim().toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '');
    const items = [];
    const draft = ctx.readTraceDraft?.();
    if (draft) items.push({ src: 'draft', name: '✏️ Rascunho do Traçar', meta: draft.n ? `“${draft.n}” · ${draft.wp.length} pontos` : `${draft.wp.length} pontos` });
    for (const r of savedRoutes || []) {
      const km = Number.isFinite(r.distMeters) ? `${(r.distMeters / 1000).toFixed(1).replace('.', ',')} km` : '';
      const when = r.updated ? new Date(r.updated).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) : '';
      items.push({ src: `saved:${r.slug || r.id}`, name: r.name || r.slug || r.id, meta: [km, when].filter(Boolean).join(' · ') });
    }
    items.push({ src: '', name: 'Sem rota', meta: 'só o mapa' });
    const flat = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const shown = items.filter((it) => !needle || it.src === state.route.src || flat(it.name).includes(needle));
    box.replaceChildren(...shown.map((it) => el('button', {
      type: 'button', role: 'option', class: 'poster-route', 'aria-selected': String(it.src === (state.route.src || '')),
      onclick: () => chooseRoute(it.src),
    }, el('span', { class: 'poster-route-name' }, it.name), el('span', { class: 'poster-route-meta' }, it.meta))));
    if (savedRoutes === null) box.append(el('p', { class: 'poster-hint' }, 'Carregando as rotas salvas…'));
    else if (!(savedRoutes || []).length) box.append(el('p', { class: 'poster-hint' }, 'Nenhuma rota salva encontrada (precisa do servidor do amora).'));
  }
  async function chooseRoute(src) {
    state.route.src = src;
    renderRouteList();
    await loadRoute();
    if (route.latlngs) fitRoute();
    persistSoon();
  }
  // Geometria de um estado no formato de compartilhamento ({wp, sg}): sg[i-1]
  // é o caminho que CHEGA no waypoint i; sem ele, reta.
  function geometryFromShareState(st) {
    const out = [];
    const pois = [];
    const wp = Array.isArray(st?.wp) ? st.wp : [];
    const sg = Array.isArray(st?.sg) ? st.sg : null;
    let prevOk = false;
    wp.forEach((w, i) => {
      if (!Array.isArray(w) || !Number.isFinite(w[0]) || !Number.isFinite(w[1])) { prevOk = false; return; }
      const seg = sg && prevOk && i > 0 ? ctx.decodePolyline(sg[i - 1]) : null;
      if (seg && out.length) out.push(...seg.slice(1));
      else out.push([w[0], w[1]]);
      if (w[3] && w[2]) pois.push({ lat: w[0], lng: w[1], name: String(w[2]) });
      prevOk = true;
    });
    return { latlngs: out, pois };
  }
  // Rascunho do Traçar (formato do snapshot(): cada ponto traz o `path` que
  // chega nele).
  function geometryFromDraft(d) {
    const out = [];
    const pois = [];
    for (const w of d?.wp || []) {
      const p = w.path || w.pathFromPrev;
      const path = Array.isArray(p) && p.length > 1 ? p : null;
      if (path && out.length) out.push(...path.slice(1).map((q_) => [q_[0] ?? q_.lat, q_[1] ?? q_.lng]));
      else out.push([w.lat, w.lng]);
      if (w.isPoi && w.name) pois.push({ lat: w.lat, lng: w.lng, name: String(w.name) });
    }
    return { latlngs: out, pois };
  }
  async function loadRoute() {
    const src = state.route.src || '';
    route = { latlngs: null, pois: [], key: src, slug: '', id: '', name: '' };
    try {
      if (src === 'draft') {
        const d = ctx.readTraceDraft?.();
        Object.assign(route, geometryFromDraft(d), { name: d?.n || '' });
      } else if (src.startsWith('saved:')) {
        const key = src.slice(6);
        let st = routeStateCache.get(key);
        if (!st) {
          const res = await fetch(`./saved-route/${encodeURIComponent(key)}`, { cache: 'no-store' });
          if (!res.ok) throw new Error(res.status === 404 ? 'rota não encontrada no servidor' : `HTTP ${res.status}`);
          st = await res.json();
          routeStateCache.set(key, st);
        }
        if (state.route.src !== src) return;   // trocou no meio do fetch
        Object.assign(route, geometryFromShareState(st), { slug: st.slug || key, id: st.id || '', name: st.n || key });
      }
    } catch (err) {
      showToast(`Não deu pra carregar a rota: ${err.message}`);
    }
    if (route.latlngs && route.latlngs.length < 2) route.latlngs = null;
    drawRoute();
    q('[data-act="poi-labels"]').hidden = !route.pois.length;
  }
  function drawRoute() {
    for (const l of routeLayers) map.removeLayer(l);
    routeLayers = [];
    if (!active || !route.latlngs) return;
    const r = state.route;
    const base = { pane: ROUTE_PANE, interactive: false, lineCap: 'round', lineJoin: 'round', opacity: 1 };
    if (r.casing && r.casingWidth > 0) {
      routeLayers.push(L.polyline(route.latlngs, { ...base, color: r.casingColor, weight: r.width + 2 * r.casingWidth }).addTo(map));
    }
    routeLayers.push(L.polyline(route.latlngs, { ...base, color: r.color, weight: r.width }).addTo(map));
  }
  function restyleRoute() {
    if (routeLayers.length !== (state.route.casing && state.route.casingWidth > 0 ? 2 : 1)) { drawRoute(); return; }
    const r = state.route;
    if (routeLayers.length === 2) routeLayers[0].setStyle({ color: r.casingColor, weight: r.width + 2 * r.casingWidth });
    routeLayers[routeLayers.length - 1].setStyle({ color: r.color, weight: r.width });
  }
  // Enquadra a rota já girada: bbox dos pontos projetados no rumo atual.
  function fitRoute() {
    if (!route.latlngs) { showToast('Escolha uma rota no passo 1.'); return; }
    const { w: W, h: H } = dims();
    const pad = Math.min(W, H) * 0.08;
    const z0 = map.getZoom();
    const th = ((map.getBearing?.() || 0) * Math.PI) / 180;
    const c = Math.cos(th), s = Math.sin(th);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const ll of route.latlngs) {
      const p = map.project(L.latLng(ll[0], ll[1]), z0);
      const x = p.x * c - p.y * s, y = p.x * s + p.y * c;
      if (x < x0) x0 = x; if (x > x1) x1 = x;
      if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    const k = Math.min((W - 2 * pad) / Math.max(x1 - x0, 1), (H - 2 * pad) / Math.max(y1 - y0, 1));
    const z = clamp(z0 + Math.log2(k), map.getMinZoom(), map.getMaxZoom());
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    map.setView(map.unproject(L.point(cx * c + cy * s, -cx * s + cy * c), z0), z, { animate: false });
  }

  // ─── Passo 2: informações + caixa ──────────────────────────────────────────
  const tourEntry = () => (route.slug || route.id ? ctx.findTourEntry?.(route.slug, route.id) : null);
  function renderInfo() {
    const i = state.info;
    for (const k of Object.keys(i)) {
      const f = q(`[data-k="info.${k}"]`);
      if (f && document.activeElement !== f) f.value = i[k];
    }
    const nf = q('[data-k="info.number"]');
    const sug = ctx.nextSeriesNumber?.(i.series);
    nf.placeholder = sug ? `próximo: ${sug}` : '';
    q('[data-k="box.k"]').value = String(state.box.k);
    const entry = tourEntry();
    const ban = q('[data-k="tour-link"]');
    ban.hidden = !entry;
    if (entry) {
      const n = entry.number || entry.numbers?.[0];
      ban.replaceChildren(
        el('span', {}, `Esta rota é do passeio «${entry.name}»${n ? ` (${n.source} ${n.value})` : ''}${entry.date ? `, ${fmtDateBR(entry.date)}` : ''}.`),
        el('button', { type: 'button', class: 'secondary-btn', onclick: () => useTourEntry(entry) }, 'Usar os dados dele'));
    }
    renderLists();
  }
  // Arte pra um passeio que JÁ está no Censo: puxa os dados e o salvar do
  // passo 6 atualiza ESSE passeio em vez de criar outro.
  function useTourEntry(entry) {
    const n = entry.number || entry.numbers?.[0];
    if (n && SERIES[n.source]) { state.info.series = n.source; state.info.number = String(n.value); }
    if (entry.name) state.info.name = entry.name.toLowerCase();
    if (entry.date) state.info.date = String(entry.date).slice(0, 10);
    const id = /\/passeio\/([^/?#]+)$/.exec(entry.tourIri || '')?.[1] || '';
    state.censo.linkTourId = id;
    state.censo.linkName = entry.name || '';
    refreshAutoTexts();
    renderInfo();
    requestRender();
    persistSoon();
    showToast('Dados do passeio carregados — complete o horário e o ponto de encontro.');
  }
  function applyTheme(key) {
    const t = BOX_THEMES[key];
    if (!t) return;
    Object.assign(state.box, { fill: t.fill, fillOpacity: 1, band: true, bandColor: t.band[0], bandColor2: t.band[1] });
    for (const tx of state.box.texts) tx.color = t.text;
    requestRender();
    persistSoon();
  }

  // ─── Passo 3: mapa ─────────────────────────────────────────────────────────
  // Camada "Rotas cadastradas" (todas as rotas do coletivo) ligada: no passo
  // do mapa, um toque a desliga — no celular o painel de camadas é miúdo.
  const routesLayerCb = () => document.querySelector('.layer-row input[type="checkbox"][data-id="routes"]');
  function syncMapControls() {
    q('[data-k="other-routes"]').hidden = !routesLayerCb()?.checked;
    const r = state.route;
    const set = (k, v) => { const i = q(`[data-k="${k}"]`); if (!i) return; if (i.type === 'checkbox') i.checked = !!v; else i.value = String(v); };
    set('format', state.format);
    set('route.width', r.width);
    set('route.color', r.color);
    set('route.casing', r.casing);
    set('route.casingColor', r.casingColor);
    q('[data-k="route.width"]').nextElementSibling.textContent = `${r.width} px`;
    syncBearing();
  }
  function syncBearing() {
    const b = Math.round((((map.getBearing?.() || 0) + 540) % 360) - 180);
    const i = q('[data-k="bearing"]');
    if (document.activeElement !== i) i.value = String(b);
    i.nextElementSibling.textContent = `${b}°`;
  }

  // ─── Passo 4: rótulos ──────────────────────────────────────────────────────
  // Caminho do rótulo em px do palco. Lido sempre da esquerda pra direita: se
  // o mapa girou e a corda aponta pra trás, as pontas trocam de papel.
  function labelLayout(lb, text = lb.text) {
    let A = toPt(lb.a), B = toPt(lb.b);
    const M = lb.c ? toPt(lb.c) : L.point((A.x + B.x) / 2, (A.y + B.y) / 2);
    if (B.x < A.x) [A, B] = [B, A];
    const path = bezierPath(A, B, M);
    const placed = placeGlyphs(text || '', lb, path);
    const hit = [];
    const step_ = Math.max(4, lb.size / 3);
    for (let s = placed.start; s <= placed.start + placed.total + 0.01; s += step_) {
      const p = path.at(s);
      hit.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`);
    }
    if (hit.length < 2) hit.push(`${A.x},${A.y}`, `${B.x},${B.y}`);
    const guide = [];
    for (let i = 0; i <= 24; i++) { const p = path.at((path.len * i) / 24); guide.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`); }
    return { glyphs: placed.glyphs, hit: hit.join(' '), guide: guide.join(' '), A: toPt(lb.a), B: toPt(lb.b), M };
  }
  function setLabelCenter(lb, center, half) {
    lb.a = toLL({ x: center.x - half, y: center.y });
    lb.b = toLL({ x: center.x + half, y: center.y });
    lb.c = null;
  }
  function addLabel(kind) {
    const K = KINDS[kind] || KINDS.livre;
    const { w: W, h: H } = dims();
    const lb = { id: uid(), kind, text: K.text, ...textStyle({ color: K.color, size: K.size }), a: null, b: null, c: null };
    // Em cascata pelo meio da arte, pra rótulos novos não nascerem empilhados;
    // saída/chegada já nascem na ponta da rota.
    let center = { x: W / 2, y: H / 2 + ((state.labels.length % 7) - 3) * K.size * 1.6 };
    const ends = route.latlngs;
    if (ends && (kind === 'saida' || kind === 'chegada')) {
      const p = toPt(kind === 'saida' ? ends[0] : ends[ends.length - 1]);
      center = { x: clamp(p.x, 80, W - 80), y: clamp(p.y - K.size * 1.6, 40, H - 40) };
    }
    setLabelCenter(lb, center, Math.max(60, runWidth(K.text || 'xxxxxxxx', lb) / 2 + lb.size * 0.3));
    state.labels.push(lb);
    placing = lb.id;
    select({ type: 'label', id: lb.id }, { focusText: true });
    persistSoon();
  }
  function labelsFromPois() {
    const { w: W, h: H } = dims();
    let n = 0;
    for (const p of route.pois) {
      const name = p.name.trim();
      if (!name) continue;
      const kind = /^(rio|c[óo]rrego|ribeir[ãa]o|riacho|nascente|represa|lago|cachoeira)\b/i.test(name) ? 'rio'
        : /^(morro|colina|serra|pico|espig[ãa]o|cume|mirante)\b/i.test(name) ? 'morro' : 'anomalia';
      const K = KINDS[kind];
      const lb = { id: uid(), kind, text: name.toLowerCase(), ...textStyle({ color: K.color, size: K.size }), c: null };
      const c = toPt([p.lat, p.lng]);
      setLabelCenter(lb, { x: clamp(c.x, 0, W), y: clamp(c.y - K.size, 0, H) }, runWidth(lb.text, lb) / 2 + 8);
      state.labels.push(lb);
      n++;
    }
    showToast(n ? `${n} rótulo${n > 1 ? 's' : ''} criado${n > 1 ? 's' : ''} dos pontos da rota.` : 'A rota não tem pontos com nome.');
    persistSoon();
    renderLists();
    requestRender();
  }
  // Rótulo reto: o comprimento acompanha o texto digitado (mantendo o centro e
  // a direção). Curvo, fica como está — o desenho da curva é do usuário.
  function fitLabelLength(lb) {
    if (lb.c) return;
    const A = toPt(lb.a), B = toPt(lb.b);
    const len = Math.hypot(B.x - A.x, B.y - A.y) || 1;
    const ux = (B.x - A.x) / len, uy = (B.y - A.y) / len;
    let mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
    const half = runWidth(lb.text || '', lb) / 2 + lb.size * 0.3;
    // Crescendo perto da borda (saída/chegada na ponta da rota), desliza pra
    // dentro da arte em vez de sumir pela beirada.
    const { w: W, h: H } = dims();
    const m = 12;
    const ex = Math.abs(ux) * half + Math.abs(uy) * lb.size * 0.6;
    const ey = Math.abs(uy) * half + Math.abs(ux) * lb.size * 0.6;
    if (2 * ex < W - 2 * m) mx += mx - ex < m ? m - (mx - ex) : mx + ex > W - m ? W - m - (mx + ex) : 0;
    if (2 * ey < H - 2 * m) my += my - ey < m ? m - (my - ey) : my + ey > H - m ? H - m - (my + ey) : 0;
    lb.a = toLL({ x: mx - ux * half, y: my - uy * half });
    lb.b = toLL({ x: mx + ux * half, y: my + uy * half });
  }
  // Ângulo da corda na tela, em (-90, 90] (o texto nunca fica de cabeça pra baixo).
  function labelAngle(lb) {
    const A = toPt(lb.a), B = toPt(lb.b);
    let a = (Math.atan2(B.y - A.y, B.x - A.x) * 180) / Math.PI;
    if (a > 90) a -= 180; else if (a <= -90) a += 180;
    return Math.round(a);
  }
  // Gira o rótulo (pontas e alça do meio) em torno do centro até `deg`.
  function setLabelAngle(lb, deg) {
    const A = toPt(lb.a), B = toPt(lb.b);
    const M = lb.c ? toPt(lb.c) : null;
    const cx = (A.x + B.x) / 2, cy = (A.y + B.y) / 2;
    const d = ((deg - labelAngle(lb)) * Math.PI) / 180;
    const rot = (P) => ({ x: cx + (P.x - cx) * Math.cos(d) - (P.y - cy) * Math.sin(d), y: cy + (P.x - cx) * Math.sin(d) + (P.y - cy) * Math.cos(d) });
    lb.a = toLL(rot(A));
    lb.b = toLL(rot(B));
    if (M) lb.c = toLL(rot(M));
  }
  function duplicateLabel(lb) {
    const off = 30;
    const A = toPt(lb.a), B = toPt(lb.b);
    const copy = { ...lb, id: uid(), a: toLL({ x: A.x + off, y: A.y + off }), b: toLL({ x: B.x + off, y: B.y + off }) };
    if (lb.c) { const M = toPt(lb.c); copy.c = toLL({ x: M.x + off, y: M.y + off }); }
    state.labels.push(copy);
    select({ type: 'label', id: copy.id });
    persistSoon();
  }

  // ─── Imagens ───────────────────────────────────────────────────────────────
  function imageEl(im) {
    let img = imgCache.get(im.id);
    if (!img || img._src !== im.src) {
      img = new Image();
      img._src = im.src;
      img.onload = () => requestRender();
      img.src = im.src;
      imgCache.set(im.id, img);
    }
    return img;
  }
  async function addImage(file) {
    try {
      const bmp = await createImageBitmap(file);
      const MAX = 1080;
      const k = Math.min(1, MAX / Math.max(bmp.width, bmp.height));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(bmp.width * k));
      c.height = Math.max(1, Math.round(bmp.height * k));
      c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
      bmp.close?.();
      // WebP guarda transparência e é bem menor que PNG; sem encoder WebP o
      // navegador devolve PNG sozinho.
      const src = c.toDataURL('image/webp', 0.9);
      const { w: W } = dims();
      const w = Math.min(300, c.width), h = w * (c.height / c.width);
      const im = { id: uid(), src, x: W - w - 24, y: state.box.y + state.box.h * state.box.k + 16, w, h };
      state.images.push(im);
      select({ type: 'image', id: im.id });
      persistSoon();
    } catch (err) {
      showToast(`Não deu pra abrir a imagem: ${err.message}`);
    }
  }

  // ─── Desenho da arte ───────────────────────────────────────────────────────
  function attributionText() {
    const a = map.attributionControl?._attributions || {};
    const parts = [];
    for (const [html, n] of Object.entries(a)) {
      if (!n) continue;
      // DOMParser: documento inerte (nada de carregar <img> de uma atribuição custom).
      const t = new DOMParser().parseFromString(html, 'text/html').body.textContent.trim();
      if (t && !parts.includes(t)) parts.push(t);
    }
    return parts.join(' · ');
  }
  // Desenha a arte inteira em `g` (o canvas da prévia ou o da exportação: os
  // dois têm o tamanho da arte). Devolve o layout pro <svg> de interação. Na
  // prévia, um rótulo ainda sem texto aparece como o nome do tipo, apagadinho.
  function renderArt(g, { preview = false } = {}) {
    const { w: W, h: H } = dims();
    const out = { labels: new Map(), box: null };
    for (const lb of state.labels) {
      if (!lb.text.trim()) {
        if (!preview || sel?.id !== lb.id) continue;
        const lay = labelLayout(lb, (KINDS[lb.kind] || KINDS.livre).label.toLowerCase());
        out.labels.set(lb.id, lay);
        g.save();
        g.globalAlpha = 0.5;
        drawGlyphs(g, lay.glyphs, lb, lb.size * 0.32);
        g.restore();
        continue;
      }
      const lay = labelLayout(lb);
      out.labels.set(lb.id, lay);
      drawGlyphs(g, lay.glyphs, lb, lb.size * 0.32);
    }
    const b = state.box;
    if (b && !b.hidden) {
      g.save();
      g.translate(b.x, b.y);
      g.scale(b.k, b.k);
      roundRectPath(g, 0, 0, b.w, b.h, b.radius);
      if (b.fillOpacity > 0) {
        g.globalAlpha = clamp(b.fillOpacity, 0, 1);
        g.fillStyle = b.fill;
        g.fill();
        g.globalAlpha = 1;
      }
      if (b.band && b.bandH > 0 && b.bandOpacity > 0) {
        g.save();
        roundRectPath(g, 0, 0, b.w, b.h, b.radius);
        g.clip();
        const y0 = b.h - Math.min(b.bandH, b.h);
        const grad = g.createLinearGradient(0, 0, b.w, 0);
        grad.addColorStop(0, b.bandColor);
        grad.addColorStop(1, b.bandColor2 || b.bandColor);
        g.globalAlpha = clamp(b.bandOpacity, 0, 1);
        g.fillStyle = grad;
        g.fillRect(0, y0, b.w, b.h - y0);
        g.restore();
      }
      const texts = new Map();
      for (const t of b.texts) {
        const lay = layoutBoxText(t, textOf(t));
        texts.set(t.id, lay);
        drawGlyphs(g, lay.glyphs, t, 0, b.k);
      }
      g.restore();
      out.box = { texts };
    }
    for (const im of state.images) {
      const img = imageEl(im);
      if (img.complete && img.naturalWidth) g.drawImage(img, im.x, im.y, im.w, im.h);
    }
    if (state.attribution) {
      const text = attributionText();
      if (text) {
        const st = textStyle({ font: 'plex', size: 14, color: 'rgba(255,255,255,0.92)', halo: 'outline', haloColor: 'rgba(0,0,0,0.75)', haloSize: 1.2 });
        let w = runWidth(text, st);
        if (w > W - 24) { st.size = Math.max(8, st.size * ((W - 24) / w)); w = runWidth(text, st); }
        const y = H - 12;
        drawGlyphs(g, placeGlyphs(text, st, { len: w, at: (s) => ({ x: W - 12 - w + s, y, a: 0 }) }).glyphs, st);
      }
    }
    return out;
  }

  // ─── Camada de interação (SVG) ─────────────────────────────────────────────
  // Nós por chave, atualizados no lugar: recriar o nó debaixo do dedo soltaria
  // o arraste em curso.
  const uiNodes = new Map();
  let uiGen = 0;
  function uiNode(group, key, tag, attrs) {
    let n = uiNodes.get(key);
    if (!n || n.tagName !== tag || n.parentNode !== uiGroups[group]) {
      n?.remove();
      n = document.createElementNS(SVGNS, tag);
      uiGroups[group].appendChild(n);
      uiNodes.set(key, n);
    }
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
    n._gen = uiGen;
    return n;
  }
  function renderUi(lay) {
    uiGen++;
    const u = 1 / scale;                                   // 1 px de tela
    // Alça = bolinha visível pequena + alvo de toque maior e invisível por
    // cima (no dedo, a bolinha do tamanho do alvo cobria o rótulo inteiro).
    const handle = (key, x, y, op, id, cls) => {
      const cx = x.toFixed(1), cy = y.toFixed(1);
      uiNode('sel', `${key}:v`, 'circle', { cx, cy, r: 6 * u, class: `poster-handle ${cls || ''}`, 'stroke-width': 2 * u });
      uiNode('sel', key, 'circle', { cx, cy, r: (COARSE ? 18 : 9) * u, 'data-op': op, 'data-id': id, class: `poster-hit ${cls || ''}` });
    };
    const outline = (key, x, y, w, h) => uiNode('sel', key, 'rect', {
      x, y, width: Math.max(1, w), height: Math.max(1, h), class: 'poster-outline',
      'stroke-width': 1.5 * u, 'stroke-dasharray': `${6 * u} ${4 * u}`,
    });
    if (hitsOn('label')) {
      for (const lb of state.labels) {
        const l = lay.labels.get(lb.id);
        if (!l) continue;
        uiNode('labels', `l:${lb.id}`, 'polyline', {
          points: l.hit, 'data-op': 'label', 'data-id': lb.id, class: 'poster-hit',
          'stroke-width': Math.max(lb.size * 1.15, 14 * u), 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
        });
      }
    }
    const b = state.box;
    if (b && lay.box && hitsOn('box')) {
      uiNode('box', 'box', 'rect', { x: b.x, y: b.y, width: b.w * b.k, height: b.h * b.k, 'data-op': 'box', 'data-id': 'box', class: 'poster-hit' });
      for (const t of b.texts) {
        const r = lay.box.texts.get(t.id)?.rect;
        if (!r) continue;
        uiNode('box', `t:${t.id}`, 'rect', { x: b.x + r.x * b.k, y: b.y + r.y * b.k, width: r.w * b.k, height: r.h * b.k,
          'data-op': 'text', 'data-id': t.id, class: 'poster-hit' });
      }
    }
    if (hitsOn('image')) {
      for (const im of state.images) {
        uiNode('images', `i:${im.id}`, 'rect', { x: im.x, y: im.y, width: im.w, height: im.h, 'data-op': 'image', 'data-id': im.id, class: 'poster-hit' });
      }
    }
    // Seleção por cima de tudo.
    if (sel?.type === 'label') {
      const lb = findLabel(sel.id), l = lay.labels.get(sel.id);
      if (lb && l) {
        uiNode('sel', 'guide', 'polyline', { points: l.guide, class: 'poster-guide', 'stroke-width': 1.5 * u, 'stroke-dasharray': `${5 * u} ${4 * u}` });
        handle('ha', l.A.x, l.A.y, 'label-a', lb.id, 'h-pt');
        handle('hb', l.B.x, l.B.y, 'label-b', lb.id, 'h-pt');
        handle('hc', l.M.x, l.M.y, 'label-c', lb.id, 'h-curve');
      }
    } else if ((sel?.type === 'box' || sel?.type === 'text') && b) {
      const bw = b.w * b.k, bh = b.h * b.k;
      outline('obox', b.x, b.y, bw, bh);
      if (sel.type === 'text') {
        const r = lay.box?.texts.get(sel.id)?.rect;
        if (r) outline('otext', b.x + r.x * b.k, b.y + r.y * b.k, r.w * b.k, r.h * b.k);
      }
      handle('hk', b.x + bw, b.y + bh, 'box-k', 'box', 'h-k');
      handle('hw', b.x + bw, b.y + bh / 2, 'box-w', 'box', 'h-w');
      handle('hh', b.x + bw / 2, b.y + bh, 'box-h', 'box', 'h-h');
    } else if (sel?.type === 'image') {
      const im = findImage(sel.id);
      if (im) {
        outline('oimg', im.x, im.y, im.w, im.h);
        handle('hik', im.x + im.w, im.y + im.h, 'image-k', im.id, 'h-k');
      }
    }
    for (const [k, n] of uiNodes) if (n._gen !== uiGen) { n.remove(); uiNodes.delete(k); }
  }
  function requestRender() {
    if (raf || !active) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      if (!active) return;
      const g = artCanvas.getContext('2d');
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.clearRect(0, 0, artCanvas.width, artCanvas.height);
      lastLayout = renderArt(g, { preview: true });
      renderUi(lastLayout);
    });
  }

  // ─── Layout do palco ───────────────────────────────────────────────────────
  // Teclado do celular: a folha sobe junto (visualViewport), senão o campo
  // focado ficava atrás do teclado.
  function syncKeyboard() {
    const vv = window.visualViewport;
    const kb = vv ? Math.max(0, window.innerHeight - vv.height - vv.offsetTop) : 0;
    panel.style.setProperty('--poster-kb', `${Math.round(kb)}px`);
    layout();
  }
  function layout() {
    if (!active) return;
    const { w: W, h: H } = dims();
    const pr = panel.getBoundingClientRect();
    const vw = window.innerWidth, vh = window.innerHeight;
    const mobile = window.matchMedia('(max-width: 760px)').matches;
    const aw = mobile ? vw : Math.max(200, pr.left);
    const ah = mobile ? Math.max(120, pr.top) : vh;
    const pad = mobile ? 8 : 20;
    scale = Math.max(0.05, Math.min(1, (aw - 2 * pad) / W, (ah - 2 * pad) / H));
    const left = (aw - W * scale) / 2, top = (ah - H * scale) / 2;
    Object.assign(mapEl.style, {
      position: 'fixed', left: `${left}px`, top: `${top}px`,
      width: `${W}px`, height: `${H}px`,
      transform: `scale(${scale})`, transformOrigin: '0 0',
    });
    if (artCanvas.width !== W || artCanvas.height !== H) {
      artCanvas.width = W;
      artCanvas.height = H;
      artCanvas.style.width = `${W}px`;
      artCanvas.style.height = `${H}px`;
    }
    uiSvg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    uiSvg.setAttribute('width', String(W));
    uiSvg.setAttribute('height', String(H));
    map.invalidateSize();   // pan: o centro fica no lugar
    requestRender();
  }

  // ─── Arrastes ──────────────────────────────────────────────────────────────
  const stagePoint = (e) => {
    const r = mapEl.getBoundingClientRect();
    return { x: (e.clientX - r.left) / scale, y: (e.clientY - r.top) / scale };
  };
  function onUiDown(e) {
    const t = e.target.closest?.('[data-op]');
    if (!t || e.button > 0) return;
    e.stopPropagation();
    e.preventDefault();
    const { op, id } = t.dataset;
    const type = op.startsWith('label') ? 'label' : op.startsWith('image') ? 'image' : op === 'text' ? 'text' : 'box';
    if (!(sel && sel.type === type && sel.id === id) && !(type === 'box' && sel?.type === 'text' && op !== 'box')) {
      select({ type, id });
    }
    if (type === 'label') placing = null;
    const snap = {};
    if (type === 'label') {
      const lb = findLabel(id);
      if (!lb) return;
      snap.A = toPt(lb.a); snap.B = toPt(lb.b); snap.M = lb.c ? toPt(lb.c) : null;
    } else if (type === 'image') {
      Object.assign(snap, findImage(id));
    } else if (type === 'text') {
      const tx = findText(id);
      snap.x = tx.x; snap.y = tx.y;
    } else {
      const b = state.box;
      Object.assign(snap, { x: b.x, y: b.y, w: b.w, h: b.h, k: b.k });
    }
    drag = { op, id, x0: e.clientX, y0: e.clientY, pid: e.pointerId, snap, moved: false };
    try { t.setPointerCapture(e.pointerId); } catch { /* sem captura: os listeners de window bastam */ }
    window.addEventListener('pointermove', onDragMove);
    window.addEventListener('pointerup', onDragEnd);
    window.addEventListener('pointercancel', onDragEnd);
  }
  function onDragMove(e) {
    if (!drag || e.pointerId !== drag.pid) return;
    const dx = (e.clientX - drag.x0) / scale, dy = (e.clientY - drag.y0) / scale;
    if (!drag.moved && Math.hypot(dx, dy) * scale < 3) return;
    drag.moved = true;
    const s = drag.snap;
    const p = stagePoint(e);
    const add = (P) => ({ x: P.x + dx, y: P.y + dy });
    switch (drag.op) {
      case 'label': {
        const lb = findLabel(drag.id);
        lb.a = toLL(add(s.A)); lb.b = toLL(add(s.B));
        if (s.M) lb.c = toLL(add(s.M));
        break;
      }
      case 'label-a': findLabel(drag.id).a = toLL(add(s.A)); break;
      case 'label-b': findLabel(drag.id).b = toLL(add(s.B)); break;
      case 'label-c': {
        const lb = findLabel(drag.id);
        const A = toPt(lb.a), B = toPt(lb.b);
        // Perto da corda = reto (ímã): é assim que se desfaz uma curva no dedo.
        const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
        lb.c = Math.hypot(p.x - mx, p.y - my) < 8 / scale ? null : toLL(p);
        break;
      }
      case 'box': state.box.x = s.x + dx; state.box.y = s.y + dy; break;
      case 'box-k': {
        // Escala uniforme pela projeção do ponteiro na diagonal da caixa.
        const vx = s.w * s.k, vy = s.h * s.k;
        const k = s.k * (((p.x - s.x) * vx + (p.y - s.y) * vy) / (vx * vx + vy * vy));
        state.box.k = clamp(k, 0.2, 5);
        break;
      }
      case 'box-w': state.box.w = Math.max(40, (p.x - s.x) / s.k); break;
      case 'box-h': state.box.h = Math.max(30, (p.y - s.y) / s.k); break;
      case 'text': {
        const t = findText(drag.id);
        t.x = s.x + dx / state.box.k; t.y = s.y + dy / state.box.k;
        break;
      }
      case 'image': { const im = findImage(drag.id); im.x = s.x + dx; im.y = s.y + dy; break; }
      case 'image-k': {
        const im = findImage(drag.id);
        const k = ((p.x - s.x) * s.w + (p.y - s.y) * s.h) / (s.w * s.w + s.h * s.h);
        const kk = clamp(k, 20 / Math.max(s.w, s.h), 20);
        im.w = s.w * kk; im.h = s.h * kk;
        break;
      }
      default: break;
    }
    requestRender();
  }
  function onDragEnd(e) {
    if (!drag || (e && e.pointerId !== drag.pid)) return;
    window.removeEventListener('pointermove', onDragMove);
    window.removeEventListener('pointerup', onDragEnd);
    window.removeEventListener('pointercancel', onDragEnd);
    if (drag.moved) {
      persistSoon();
      if (drag.op === 'box-k') { const i = q('[data-k="box.k"]'); if (i) i.value = String(state.box.k); }
      if (drag.op.startsWith('label')) syncLabelAngleInput();
    }
    drag = null;
  }
  function onUiDblClick(e) {
    const t = e.target.closest?.('[data-op]');
    if (!t) return;
    e.stopPropagation();
    e.preventDefault();
    const field = panel.querySelector('.poster-sel [data-field="text"]');
    if (field) { field.focus(); field.select?.(); }
  }

  // ─── Seleção + painel do selecionado ───────────────────────────────────────
  function select(next, { focusText = false } = {}) {
    // Rótulo que ficou sem texto some ao perder a seleção (criado sem querer).
    if (sel?.type === 'label' && sel.id !== next?.id) {
      const prev = findLabel(sel.id);
      if (prev && !prev.text.trim()) state.labels = state.labels.filter((l) => l.id !== prev.id);
      if (placing === sel.id) placing = null;
    }
    sel = next;
    renderSelPanel();
    renderLists();
    requestRender();
    if (focusText) {
      const f = panel.querySelector('.poster-sel [data-field="text"]');
      if (f) {
        panel.classList.remove('collapsed');
        f.focus({ preventScroll: true });
        // "sai " / "chega ": cursor no fim pra completar; senão, seleciona tudo.
        if (/\s$/.test(f.value)) f.setSelectionRange(f.value.length, f.value.length);
        else f.select();
      }
    }
  }
  function selectedObject() {
    if (!sel) return null;
    if (sel.type === 'label') return findLabel(sel.id);
    if (sel.type === 'text') return findText(sel.id);
    if (sel.type === 'image') return findImage(sel.id);
    if (sel.type === 'box') return state.box;
    return null;
  }
  const row = (label, ...kids) => el('div', { class: 'poster-row' }, label ? el('label', {}, label) : null, ...kids);
  // Controles de estilo de texto (rótulo ou texto da caixa), ligados direto ao objeto.
  function styleControls(st, onChange, { size = true } = {}) {
    const frag = document.createDocumentFragment();
    const fontSel = el('select', { 'aria-label': 'Fonte' });
    for (const [k, f] of Object.entries(FONTS)) fontSel.append(el('option', { value: k }, f.label));
    fontSel.value = st.font;
    fontSel.addEventListener('change', () => { st.font = fontSel.value; onChange(); });
    frag.append(row('Fonte', fontSel));
    if (size) frag.append(sizeControl(st, onChange));
    const sp = el('input', { type: 'range', min: -5, max: 40, step: 0.5, value: st.spacing, 'aria-label': 'Espaçamento entre letras' });
    const spOut = el('output', {}, `${st.spacing}`);
    sp.addEventListener('input', () => { st.spacing = num(sp.value, 0); spOut.textContent = `${st.spacing}`; onChange(); });
    frag.append(row('Espaçamento', sp, spOut));
    const color = el('input', { type: 'color', value: /^#[0-9a-f]{6}$/i.test(st.color) ? st.color : '#ffffff', 'aria-label': 'Cor do texto' });
    color.addEventListener('input', () => { st.color = color.value; onChange(); });
    const sw = el('span', { class: 'poster-swatches' });
    for (const c of SWATCHES) {
      sw.append(el('button', { type: 'button', class: 'poster-swatch', style: `background:${c}`, title: c, 'aria-label': `Cor ${c}`,
        onclick: () => { st.color = c; color.value = c; onChange(); } }));
    }
    frag.append(row('Cor', color, sw));
    const halo = el('select', { 'aria-label': 'Efeito' });
    for (const [k, v] of Object.entries(HALOS)) halo.append(el('option', { value: k }, v));
    halo.value = st.halo;
    const haloC = el('input', { type: 'color', value: /^#[0-9a-f]{6}$/i.test(st.haloColor) ? st.haloColor : '#000000', 'aria-label': 'Cor do efeito' });
    const haloS = el('input', { type: 'range', min: 0, max: 3, step: 0.1, value: st.haloSize, 'aria-label': 'Intensidade do efeito' });
    halo.addEventListener('change', () => { st.halo = halo.value; onChange(); });
    haloC.addEventListener('input', () => { st.haloColor = haloC.value; onChange(); });
    haloS.addEventListener('input', () => { st.haloSize = num(haloS.value, 1); onChange(); });
    frag.append(row('Efeito', halo, haloC, haloS));
    return frag;
  }
  function sizeControl(st, onChange) {
    const size = el('input', { type: 'range', min: 8, max: 160, step: 1, value: st.size, 'aria-label': 'Tamanho do texto' });
    const sizeN = el('input', { type: 'number', min: 4, max: 400, step: 1, value: st.size, inputmode: 'numeric', 'aria-label': 'Tamanho do texto (px)' });
    const setSize = (v) => { st.size = clamp(num(v, st.size), 4, 400); size.value = st.size; sizeN.value = st.size; onChange(); };
    size.addEventListener('input', () => setSize(size.value));
    sizeN.addEventListener('change', () => setSize(sizeN.value));
    return row('Tamanho', size, sizeN);
  }
  function syncLabelAngleInput() {
    const lb = sel?.type === 'label' ? findLabel(sel.id) : null;
    const i = q('.poster-sel [data-field="angle"]');
    if (!lb || !i) return;
    i.value = String(labelAngle(lb));
    i.nextElementSibling.textContent = `${i.value}°`;
  }
  function renderSelPanel() {
    const box = q('.poster-sel');
    let obj = selectedObject();
    // Só o que o passo atual edita.
    if (obj && sel.type === 'label' && !hitsOn('label')) obj = null;
    if (obj && (sel.type === 'box' || sel.type === 'text') && !hitsOn('box')) obj = null;
    if (obj && sel.type === 'image' && !hitsOn('image')) obj = null;
    box.hidden = !obj;
    box.replaceChildren();
    if (!obj) return;
    const changed = () => { requestRender(); persistSoon(); };
    const head = (title, doneLabel = '✓ Pronto') => el('div', { class: 'poster-sel-head' }, el('strong', {}, title),
      el('button', { type: 'button', class: 'secondary-btn', onclick: () => select(null) }, doneLabel));
    if (sel.type === 'label') {
      const lb = obj;
      const K = KINDS[lb.kind] || KINDS.livre;
      box.append(head(`Rótulo · ${K.label}`));
      const text = el('input', { type: 'text', value: lb.text, 'data-field': 'text', 'aria-label': 'Texto do rótulo',
        placeholder: `nome d${K.place.startsWith('a ') ? 'a' : 'o'} ${K.label.toLowerCase()}`, enterkeyhint: 'done', autocomplete: 'off' });
      text.addEventListener('input', () => { lb.text = text.value; fitLabelLength(lb); renderLists(); changed(); });
      text.addEventListener('keydown', (e) => { if (e.key === 'Enter') text.blur(); });
      box.append(row('', text));
      if (placing === lb.id) box.append(el('p', { class: 'poster-place' }, `👆 Agora toque na arte onde fica ${K.place}.`));
      box.append(sizeControl(lb, () => { fitLabelLength(lb); changed(); }));
      const ang = el('input', { type: 'range', min: -90, max: 90, step: 1, value: labelAngle(lb), 'data-field': 'angle', 'aria-label': 'Ângulo do rótulo' });
      const angOut = el('output', {}, `${labelAngle(lb)}°`);
      ang.addEventListener('input', () => { setLabelAngle(lb, num(ang.value, 0)); angOut.textContent = `${ang.value}°`; changed(); });
      box.append(row('Ângulo', ang, angOut));
      const kind = el('select', { 'aria-label': 'Tipo' });
      for (const [k, KK] of Object.entries(KINDS)) kind.append(el('option', { value: k }, KK.label));
      kind.value = lb.kind || 'livre';
      kind.addEventListener('change', () => {
        lb.kind = kind.value; lb.color = KINDS[kind.value].color;
        renderSelPanel(); renderLists(); changed();
      });
      const more = el('details', { class: 'poster-more' }, el('summary', {}, 'Mais opções (tipo, fonte, cor, efeito)'));
      more.append(row('Tipo', kind), styleControls(lb, () => { fitLabelLength(lb); changed(); }, { size: false }));
      box.append(more);
      box.append(el('div', { class: 'poster-row' },
        el('button', { type: 'button', class: 'secondary-btn', onclick: () => { lb.c = null; changed(); } }, '⌒ Endireitar'),
        el('button', { type: 'button', class: 'secondary-btn', onclick: () => duplicateLabel(lb) }, '⧉ Duplicar'),
        el('button', { type: 'button', class: 'secondary-btn poster-danger', onclick: () => deleteSelected() }, '🗑 Excluir')));
    } else if (sel.type === 'text') {
      const t = obj;
      box.append(head('Texto da caixa'));
      if (t.bind) {
        box.append(el('p', { class: 'poster-hint' }, `Vem das informações acima: “${textOf(t)}”.`),
          el('button', { type: 'button', class: 'secondary-btn', onclick: () => { t.text = textOf(t); delete t.bind; renderSelPanel(); changed(); } },
            '✎ Escrever outro texto aqui'));
      } else {
        const text = el('textarea', { rows: 2, 'data-field': 'text', 'aria-label': 'Texto' });
        text.value = t.text;
        text.addEventListener('input', () => { t.text = text.value; changed(); });
        box.append(row('', text));
      }
      const align = el('select', { 'aria-label': 'Alinhamento' });
      for (const [k, v] of [['left', 'à esquerda'], ['center', 'centralizado'], ['right', 'à direita']]) align.append(el('option', { value: k }, v));
      align.value = t.align;
      align.addEventListener('change', () => {
        // Troca o alinhamento sem o texto sair do lugar: a âncora vai pra nova borda.
        const r = layoutBoxText(t, textOf(t)).rect;
        t.align = align.value;
        t.x = t.align === 'left' ? r.x : t.align === 'right' ? r.x + r.w : r.x + r.w / 2;
        changed();
      });
      box.append(row('Alinhar', align));
      box.append(styleControls(t, changed));
      box.append(el('div', { class: 'poster-row' },
        el('button', { type: 'button', class: 'secondary-btn', onclick: () => select({ type: 'box', id: 'box' }) }, '← Caixa'),
        el('button', { type: 'button', class: 'secondary-btn poster-danger', onclick: () => deleteSelected() }, '🗑 Excluir texto')));
    } else if (sel.type === 'box') {
      const b = obj;
      box.append(head('Caixa do anúncio'));
      const color = (key, label) => {
        const i = el('input', { type: 'color', value: b[key], 'aria-label': label });
        i.addEventListener('input', () => { b[key] = i.value; changed(); });
        return i;
      };
      const range = (key, min, max, step_, label) => {
        const i = el('input', { type: 'range', min, max, step: step_, value: b[key], 'aria-label': label });
        i.addEventListener('input', () => { b[key] = num(i.value, b[key]); changed(); });
        return i;
      };
      const bandCb = el('input', { type: 'checkbox' });
      bandCb.checked = !!b.band;
      bandCb.addEventListener('change', () => { b.band = bandCb.checked; changed(); });
      box.append(
        el('p', { class: 'poster-hint' }, 'O canto ⤡ aumenta/diminui tudo junto; as alças da direita e de baixo mudam só o fundo. Toque num texto da caixa pra mudar a fonte ou arraste-o.'),
        el('div', { class: 'poster-row' },
          el('button', { type: 'button', class: 'secondary-btn', onclick: () => addBoxText() }, '+ Texto'),
          el('button', { type: 'button', class: 'secondary-btn', onclick: () => fitBoxToTexts() }, '↔ Ajustar ao texto')),
        row('Fundo', color('fill', 'Cor do fundo'), range('fillOpacity', 0, 1, 0.05, 'Opacidade do fundo')),
        row('Cantos', range('radius', 0, 90, 1, 'Arredondamento dos cantos')),
        el('div', { class: 'poster-row' }, el('label', { class: 'poster-inline' }, bandCb, ' Faixa'),
          color('bandColor', 'Cor da faixa (esquerda)'), color('bandColor2', 'Cor da faixa (direita)')),
        row('Faixa', range('bandH', 0, 400, 1, 'Altura da faixa'), range('bandOpacity', 0, 1, 0.05, 'Opacidade da faixa')),
        el('div', { class: 'poster-row' },
          el('button', { type: 'button', class: 'secondary-btn', onclick: () => resetBox() }, '↺ Caixa padrão')));
    } else if (sel.type === 'image') {
      box.append(head('Imagem'),
        el('p', { class: 'poster-hint' }, 'Arraste pra mover; o canto ⤡ muda o tamanho.'),
        el('div', { class: 'poster-row' },
          el('button', { type: 'button', class: 'secondary-btn poster-danger', onclick: () => deleteSelected() }, '🗑 Excluir imagem')));
    }
  }
  function renderLists() {
    const lab = q('[data-list="labels"]');
    lab.replaceChildren(...state.labels.filter((lb) => lb.text.trim() || sel?.id === lb.id).map((lb) => el('button', {
      type: 'button', class: `poster-chip${sel?.type === 'label' && sel.id === lb.id ? ' active' : ''}`,
      style: `--kind:${lb.color}`, onclick: () => select({ type: 'label', id: lb.id }),
    }, lb.text.trim() || `(${(KINDS[lb.kind] || KINDS.livre).label.toLowerCase()})`)));
    const imgs = q('[data-list="images"]');
    imgs.replaceChildren(...state.images.map((im, i) => el('button', {
      type: 'button', class: `poster-chip${sel?.type === 'image' && sel.id === im.id ? ' active' : ''}`,
      onclick: () => select({ type: 'image', id: im.id }),
    }, `🖼 imagem ${i + 1}`)));
  }
  function deleteSelected() {
    if (!sel) return;
    if (sel.type === 'label') state.labels = state.labels.filter((l) => l.id !== sel.id);
    else if (sel.type === 'image') { state.images = state.images.filter((i) => i.id !== sel.id); imgCache.delete(sel.id); }
    else if (sel.type === 'text') state.box.texts = state.box.texts.filter((t) => t.id !== sel.id);
    else return;
    sel = null;
    select(null);
    persistSoon();
  }
  function addBoxText() {
    const b = state.box;
    const last = b.texts[b.texts.length - 1];
    const t = { id: uid(), text: 'texto', x: b.w / 2, y: last ? last.y + last.size * 1.2 : b.h / 2, align: 'center',
      ...textStyle({ font: last?.font || 'fredoka', size: last?.size || 26, color: last?.color || '#000000', halo: 'none' }) };
    b.texts.push(t);
    select({ type: 'text', id: t.id }, { focusText: true });
    persistSoon();
  }
  // Fundo ao redor dos textos (margem de 24): os textos centralizados ficam no meio.
  function fitBoxToTexts() {
    const b = state.box;
    if (!b.texts.length) return;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const t of b.texts) {
      const r = layoutBoxText(t, textOf(t)).rect;
      x0 = Math.min(x0, r.x); x1 = Math.max(x1, r.x + r.w);
      y0 = Math.min(y0, r.y); y1 = Math.max(y1, r.y + r.h);
    }
    const m = 24;
    const dx = m - x0, dy = Math.max(0, m - y0);
    for (const t of b.texts) { t.x += dx; t.y += dy; }
    b.x -= dx * b.k;
    b.y -= dy * b.k;
    b.w = x1 - x0 + 2 * m;
    b.h = Math.max(b.h, y1 + dy + m * 0.6);
    requestRender();
    persistSoon();
  }
  function resetBox() {
    state.box = defaultBox(dims().w);
    select({ type: 'box', id: 'box' });
    persistSoon();
  }

  // ─── Passo 5: texto do post ────────────────────────────────────────────────
  function renderText() {
    refreshAutoTexts();
    const c = q('[data-k="caption"]'), a = q('[data-k="alt"]');
    if (document.activeElement !== c) c.value = state.caption;
    if (document.activeElement !== a) a.value = state.alt;
    updateCount();
  }
  function updateCount() {
    const n = (state.caption || '').length;
    const out = q('[data-count="caption"]');
    out.textContent = `${n} / 2150`;
    out.classList.toggle('over', n > 2150);
  }

  // ─── Passo 6: publicar ─────────────────────────────────────────────────────
  const censoKey = () => `${state.info.series}/${state.info.number || ''}`;
  // Passeio que o salvar vai gravar: o desta arte (mesma edição), senão o
  // passeio já cadastrado que a pessoa escolheu no passo 2; vazio = novo.
  function censoTarget() {
    const c = state.censo;
    if (c.tourId && c.key === censoKey()) return { id: c.tourId, kind: 'self' };
    if (c.linkTourId) return { id: c.linkTourId, kind: 'link' };
    return { id: '', kind: 'new' };
  }
  const censoReady = () => state.censo.url && state.censo.key === censoKey() && state.censo.tourId;
  function renderPublish() {
    refreshAutoTexts();
    const i = state.info;
    const list = q('[data-k="checklist"]');
    const item = (ok, text, goto) => el('li', { class: ok ? 'ok' : 'todo' },
      el('span', { 'aria-hidden': 'true' }, ok ? '✓' : '•'), ' ', text,
      goto && !ok ? ' ' : null,
      goto && !ok ? el('button', { type: 'button', class: 'linkbtn', onclick: () => goStep(goto) }, 'completar') : null);
    const routeTxt = !state.route.src ? 'Sem rota (opcional)'
      : state.route.src === 'draft' ? 'Rota: rascunho do Traçar — vai ser salva no servidor com o nome abaixo'
        : `Rota: ${route.name || state.route.src.slice(6)}`;
    list.replaceChildren(
      item(true, routeTxt),
      item(!!(i.name.trim() && i.date), i.name.trim() && i.date
        ? `${seriesTitle()} · ${i.name.trim()} · ${fmtPosterDate(i.date)} ${fmtHour(i.time)}` : 'Falta o nome ou a data do passeio', 2),
      item(!!i.meeting.trim(), i.meeting.trim() ? `Saída: ${i.meeting.trim()}` : 'Falta o ponto de encontro', 2),
      item(!!state.caption.trim(), state.caption.trim() ? `Legenda: ${state.caption.length} caracteres` : 'Falta a legenda', 5),
      item(!!state.alt.trim(), state.alt.trim() ? 'Descrição da imagem pronta' : 'Falta a descrição da imagem', 5));
    const rn = q('[data-k="route-name-wrap"]');
    rn.hidden = state.route.src !== 'draft';
    const rnIn = q('[data-k="routeName"]');
    if (!state.routeName) state.routeName = route.name || i.name.trim();
    if (document.activeElement !== rnIn) rnIn.value = state.routeName;
    const tgt = censoTarget();
    const mode = q('[data-k="censo-mode"]');
    mode.replaceChildren();
    if (tgt.kind === 'self') {
      mode.append(el('span', {}, 'Já está no Censo — salvar de novo atualiza o mesmo passeio.'));
    } else if (tgt.kind === 'link') {
      mode.append(el('span', {}, `Vai atualizar o passeio «${state.censo.linkName}» que já está no Censo. `),
        el('button', { type: 'button', class: 'linkbtn', onclick: () => { state.censo.linkTourId = ''; state.censo.linkName = ''; renderPublish(); persistSoon(); } },
          'Criar um passeio novo em vez disso'));
    } else {
      mode.append(el('span', {}, 'Vai criar um passeio novo no Censo, com a arte, a rota e as informações.'));
    }
    const res = q('[data-k="censo-result"]');
    if (censoReady()) {
      res.className = 'poster-result ok';
      res.replaceChildren(el('span', {}, '✓ Salvo no Censo · '),
        el('a', { href: `${PUBLIC_ORIGIN}/passeio/${state.censo.tourId}`, target: '_blank', rel: 'noopener' }, 'ver o passeio ↗'));
    } else if (!res.classList.contains('err')) {
      res.className = 'poster-result';
      res.replaceChildren();
    }
    q('[data-k="attribution"]').checked = !!state.attribution;
    q('[data-act="censo"]').disabled = !!busy;
    const sab = q('[data-act="sabia"]');
    sab.disabled = !censoReady() || !!busy;
    q('[data-k="sabia-hint"]').textContent = censoReady()
      ? 'Abre o sabiá numa aba nova com a arte, a legenda e o evento da agenda preenchidos. Lá você confere e publica no Instagram, WhatsApp, Telegram, Mastodon e na Agenda.'
      : 'Primeiro salve no Censo — a arte fica hospedada lá e o sabiá a busca de lá.';
  }
  async function saveRoute(name) {
    const d = ctx.draftShareState?.(name);
    if (!d) throw new Error('o rascunho do Traçar sumiu — volte ao passo 1');
    const post = async (id) => {
      const res = await fetch('./save-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, state: d.state, id: id || undefined }),
      });
      return { res, data: await res.json().catch(() => ({})) };
    };
    let { res, data } = await post(d.sid);
    if (res.status === 409 && data.id) {
      if (!confirm(`Já existe uma rota chamada “${data.name || name}” no servidor.\nSubstituir o traçado dela por este?`)) {
        throw new Error(`já existe uma rota “${data.name || name}” — escolha outro nome pra rota`);
      }
      ({ res, data } = await post(data.id));
    }
    if (!res.ok) throw new Error(data.error || `rota: HTTP ${res.status}`);
    return data;   // { id, slug }
  }
  function buildTourTtl(id, routeSlug) {
    const i = state.info;
    const iri = `pas:${id}`;
    const props = [
      'a ph:Tour',
      `dcterms:title "${turtleEscape(i.name.trim())}"`,
      `dcterms:date "${fmtDateTime(`${i.date} ${i.time || '00:00'}`)}"^^xsd:dateTime`,
    ];
    let aux = '';
    const nEd = parseInt(i.number, 10);
    if (Number.isInteger(nEd) && nEd > 0) {
      const ed = `<${PAS_NS}${i.series}/${nEd}>`;
      props.push(`ph:inSeriesEdition ${ed}`);
      aux += `${ed} a ph:SeriesEdition ;\n    ph:inEventSeries ser:${i.series} ;\n    ph:sequenceInSeries ${nEd} .\n`;
    }
    if (i.meeting.trim()) props.push(`ph:departureLocation "${turtleEscape(i.meeting.trim())}"`);
    if (i.arrival.trim()) props.push(`ph:arrivalLocation "${turtleEscape(i.arrival.trim())}"`);
    let derived = '';
    if (routeSlug) {
      props.push(`ph:linkRoute ${iri}_route`);
      derived = `\n${iri}_route a ph:RouteReference ;\n    schema:url <${PUBLIC_ORIGIN}/route/${encodeURIComponent(routeSlug)}> ;\n    schema:provider ph:amora .\n`;
    }
    return `${TTL_PREFIXES}\n\n${aux}\n${iri}\n    ${props.join(' ;\n    ')} .\n${derived}`;
  }
  async function saveCenso() {
    if (busy) return;
    const i = state.info;
    const res = q('[data-k="censo-result"]');
    const fail = (msg, goto) => {
      res.className = 'poster-result err';
      res.replaceChildren(el('span', {}, msg));
      if (goto) res.append(' ', el('button', { type: 'button', class: 'linkbtn', onclick: () => goStep(goto) }, 'ir pro passo'));
    };
    if (!i.name.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(i.date)) { fail('Falta o nome ou a data do passeio.', 2); return; }
    busy = 'censo';
    renderPublish();
    const btn = q('[data-act="censo"]');
    const label = btn.textContent;
    btn.textContent = 'Salvando…';
    res.className = 'poster-result';
    res.replaceChildren(el('span', {}, 'Gerando a arte e salvando…'));
    try {
      let routeSlug = '';
      if (state.route.src === 'draft') {
        const name = (state.routeName || '').trim();
        if (!name) throw new Error('dê um nome à rota (ele vira o link)');
        const r = await saveRoute(name);
        routeSlug = r.slug;
        state.route.src = `saved:${r.slug}`;
        routeStateCache.delete(r.slug);
        route.slug = r.slug; route.id = r.id; route.name = name;
        loadRouteList();
      } else if (state.route.src.startsWith('saved:')) {
        routeSlug = route.slug || state.route.src.slice(6);
      }
      const blob = await renderPosterBlob('image/jpeg');
      const tgt = censoTarget();
      const id = tgt.id || randPersonSlug();
      const fd = new FormData();
      fd.append('ttl', buildTourTtl(id, routeSlug));
      if (tgt.id) fd.append('mode', 'patch');
      fd.append('announcement', new File([blob], `anuncio-${slugify(i.name)}.jpg`, { type: 'image/jpeg' }));
      const r = await fetch('./upload-tour', { method: 'POST', body: fd });
      const json = await r.json().catch(() => ({}));
      if (!r.ok || !json.ok) {
        if (json.error === 'shacl') {
          const det = (json.details || []).join(' · ');
          // A recusa mais comum: a edição (PH 112…) já é de outro passeio.
          if (/edição de série/i.test(det)) {
            throw Object.assign(new Error(`já existe um passeio ${i.series} ${i.number} no Censo. Confira o número — ou, se a arte é pra esse passeio, use “Usar os dados dele” no passo 2.`), { goto: 2 });
          }
          throw new Error(`o Censo recusou: ${(json.details || []).slice(0, 3).join(' · ') || 'dados inválidos'}`);
        }
        throw new Error(json.error || `HTTP ${r.status}`);
      }
      state.censo = { ...state.censo, key: censoKey(), tourId: json.tour_id || id, url: json.announcement_url || '' };
      if (!state.censo.url) throw new Error('o servidor não devolveu o endereço da arte');
      persistNow();
      ctx.onTourChanged?.();
      res.className = 'poster-result ok';
      busy = '';
      renderPublish();
      showToast('Passeio salvo no Censo Hidrográfico.');
    } catch (err) {
      console.error('[poster] censo:', err);
      busy = '';
      fail(`Não deu pra salvar: ${err.message}`, err.goto);
      renderPublish();
    } finally {
      busy = '';
      btn.textContent = label;
      q('[data-act="censo"]').disabled = false;
    }
  }
  // O sabiá recebe tudo pelo fragmento (nunca vai pro servidor dele nem pros
  // logs da Cloudflare) e busca a arte na URL pública do Censo. Âncora com
  // target=_blank, não window.open: no app da tela de início e no shell
  // nativo é o que abre o navegador de verdade.
  function openSabia() {
    if (!censoReady()) return;
    const i = state.info;
    const title = [seriesTitle(), i.name.trim()].filter(Boolean).join(' · ');
    const payload = {
      v: 1, source: 'amora', title,
      text: state.caption,
      images: [{ url: state.censo.url, alt: state.alt }],
      event: { title, start: `${i.date}T${i.time || '00:00'}`, place: i.meeting.trim(), text: state.caption },
      link: `${PUBLIC_ORIGIN}/passeio/${state.censo.tourId}`,
    };
    const a = el('a', { href: `${SABIA_URL}#amora=${b64url(JSON.stringify(payload))}`, target: '_blank', rel: 'noopener' });
    document.body.append(a);
    a.click();
    a.remove();
  }

  // ─── Eventos do painel ─────────────────────────────────────────────────────
  function onPanelClick(e) {
    const g = e.target.closest('[data-goto]');
    if (g) { goStep(+g.dataset.goto); return; }
    const b = e.target.closest('[data-act]');
    if (!b) return;
    const act = b.dataset.act;
    if (act === 'exit') close();
    else if (act === 'next') { if (state.step === STEPS.length) close(); else goStep(state.step + 1); }
    else if (act === 'prev') goStep(state.step - 1);
    else if (act === 'edit-route') editInTracer();
    else if (act === 'export-png') exportImage('image/png');
    else if (act === 'export-jpg') exportImage('image/jpeg');
    else if (act === 'fit') fitRoute();
    else if (act === 'hide-routes') {
      const cb = routesLayerCb();
      if (cb?.checked) { cb.checked = false; cb.dispatchEvent(new Event('change', { bubbles: true })); }
      syncMapControls();
    }
    else if (act === 'poi-labels') labelsFromPois();
    else if (act === 'north') map.setBearing?.(0);
    else if (act === 'zoom-in') map.setZoom(map.getZoom() + 0.25, { animate: false });
    else if (act === 'zoom-out') map.setZoom(map.getZoom() - 0.25, { animate: false });
    else if (act === 'add-label') addLabel(b.dataset.kind);
    else if (act === 'sel-box') select({ type: 'box', id: 'box' });
    else if (act === 'theme') applyTheme(b.dataset.theme);
    else if (act === 'add-image') q('[data-k="image-file"]').click();
    else if (act === 'caption-reset') { state.captionEdited = false; renderText(); persistSoon(); }
    else if (act === 'alt-reset') { state.altEdited = false; renderText(); persistSoon(); }
    else if (act === 'censo') saveCenso();
    else if (act === 'sabia') openSabia();
    else if (act === 'reset') {
      if (!confirm('Começar uma arte nova? Rota, informações, rótulos e textos saem; a caixa, os logos e o formato ficam.')) return;
      const keep = { format: state.format, box: state.box, images: state.images, attribution: state.attribution, route: { ...state.route, src: '' } };
      state = { ...defaultState(), ...keep };
      select(null);
      loadRoute();
      goStep(1);
    }
  }
  function onPanelInput(e) {
    const k = e.target.dataset?.k;
    if (!k) return;
    const t = e.target;
    const v = t.type === 'checkbox' ? t.checked : t.type === 'range' ? num(t.value, 0) : t.value;
    if (k === 'route-q') { renderRouteList(); return; }
    if (k.startsWith('info.')) {
      state.info[k.slice(5)] = String(v);
      if (k === 'info.series' && e.type === 'change') renderInfo();
      refreshAutoTexts();
    } else if (k.startsWith('route.')) {
      state.route[k.slice(6)] = v;
      if (k === 'route.width') t.nextElementSibling.textContent = `${v} px`;
      restyleRoute();
    } else if (k === 'box.k') {
      state.box.k = clamp(num(v, 1), 0.2, 5);
    } else if (k === 'format') {
      if (e.type !== 'change') return;
      state.format = v;
      // A caixa e as imagens não podem ficar fora da arte nova.
      const { w: W, h: H } = dims();
      const b = state.box;
      b.x = clamp(b.x, 0, Math.max(0, W - b.w * b.k));
      b.y = clamp(b.y, 0, Math.max(0, H - b.h * b.k));
      for (const im of state.images) { im.x = clamp(im.x, 0, Math.max(0, W - im.w)); im.y = clamp(im.y, 0, Math.max(0, H - im.h)); }
      layout();
    } else if (k === 'bearing') {
      map.setBearing?.(v);
      t.nextElementSibling.textContent = `${v}°`;
    } else if (k === 'caption') {
      state.caption = String(v);
      state.captionEdited = true;
      updateCount();
    } else if (k === 'alt') {
      state.alt = String(v);
      state.altEdited = true;
    } else if (k === 'routeName') {
      state.routeName = String(v);
    } else if (k === 'attribution') {
      state.attribution = v;
    } else return;
    requestRender();
    persistSoon();
  }
  // Rota pelo Traçar: fecha o editor de arte, abre o Traçar com a rota (salva
  // ou o rascunho) e o app mostra "🎨 Voltar pra arte".
  async function editInTracer() {
    const src = state.route.src || '';
    let saved_ = null;
    if (src.startsWith('saved:')) {
      const st = routeStateCache.get(src.slice(6));
      saved_ = { id: st?.id || src.slice(6), name: st?.n || route.name };
    }
    close();
    ctx.editRoute?.(saved_);
  }

  // ─── Eventos globais enquanto aberto ───────────────────────────────────────
  // Cliques no mapa não abrem nada (popups de rota, foto perto do toque, OIM…):
  // a captura no documento chega antes de todo listener do app e do Leaflet.
  // Um toque sem arraste fora da arte posiciona o rótulo recém-criado, ou tira
  // a seleção.
  function onDocPointerDown(e) {
    if (mapEl.contains(e.target)) downAt = { x: e.clientX, y: e.clientY };
  }
  function onDocClick(e) {
    if (!mapEl.contains(e.target) || e.target.closest?.('.poster-ui [data-op]')) return;
    e.stopImmediatePropagation();
    if (!downAt || Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y) >= 6) return;
    const lb = placing && sel?.id === placing ? findLabel(placing) : null;
    if (lb && hitsOn('label')) {
      const p = stagePoint(e);
      const A = toPt(lb.a), B = toPt(lb.b);
      const half = Math.max(Math.hypot(B.x - A.x, B.y - A.y) / 2, 20);
      setLabelCenter(lb, p, half);
      fitLabelLength(lb);
      placing = null;
      renderSelPanel();
      requestRender();
      persistSoon();
      return;
    }
    if (sel) select(null);
  }
  function onDocContextMenu(e) {
    if (mapEl.contains(e.target)) { e.stopImmediatePropagation(); e.preventDefault(); }
  }
  function onKey(e) {
    if (!active || e.defaultPrevented) return;
    const tgt = e.target;
    if (tgt && (tgt.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(tgt.tagName))) return;
    if (document.querySelector('.modal:not([hidden])')) return;
    if (e.key === 'Escape' && sel) { e.preventDefault(); select(null); return; }
    if ((e.key === 'Delete' || e.key === 'Backspace') && sel && sel.type !== 'box') { e.preventDefault(); deleteSelected(); return; }
    const arrows = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (arrows[e.key] && sel) {
      e.preventDefault();
      const step_ = e.shiftKey ? 10 : 1;
      const [dx, dy] = arrows[e.key].map((v) => v * step_);
      const obj = selectedObject();
      if (sel.type === 'label') {
        const mv = (ll) => { const P = toPt(ll); return toLL({ x: P.x + dx, y: P.y + dy }); };
        obj.a = mv(obj.a); obj.b = mv(obj.b); if (obj.c) obj.c = mv(obj.c);
      } else if (sel.type === 'text') { obj.x += dx / state.box.k; obj.y += dy / state.box.k; }
      else { obj.x += dx; obj.y += dy; }
      requestRender();
      persistSoon();
    }
  }
  const onMapChange = () => requestRender();
  const onMapIdle = () => { syncBearing(); syncLabelAngleInput(); persistSoon(); };
  const onRotate = () => { syncBearing(); requestRender(); };
  const stopToMap = (e) => { if (e.target.closest?.('[data-op]')) e.stopPropagation(); };

  // ─── Abrir / fechar ────────────────────────────────────────────────────────
  // opts.routeSrc: rota a usar (a volta do Traçar passa 'draft'); opts.step.
  async function open(opts = {}) {
    if (active) return;
    ctx.beforeOpen?.();
    const lp = document.querySelector('.layer-panel');
    saved = {
      center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing?.() || 0,
      zoomSnap: map.options.zoomSnap, zoomDelta: map.options.zoomDelta,
      wheelPx: map.options.wheelPxPerZoomLevel, zoomAnimated: map._zoomAnimated,
      css: mapEl.style.cssText,
      lp, lpParent: lp?.parentNode, lpNext: lp?.nextSibling, lpInert: lp?.inert,
    };
    active = true;
    if (opts.routeSrc != null) state.route.src = opts.routeSrc;
    if (opts.step) state.step = clamp(opts.step, 1, STEPS.length);
    if (!map.getPane(ROUTE_PANE)) {
      const pane = map.createPane(ROUTE_PANE, map.getPane('rotatePane') || undefined);
      pane.style.zIndex = '450';
      pane.style.pointerEvents = 'none';
    }
    // Zoom fino (enquadrar um pôster pede mais que níveis inteiros) e sem a
    // animação de zoom: com ela os rótulos (desenhados no canvas da arte)
    // ficariam 250 ms atrás do mapa a cada passo da roda.
    map.options.zoomSnap = 0.05;
    map.options.zoomDelta = 0.25;
    map.options.wheelPxPerZoomLevel = 120;
    map._zoomAnimated = false;
    document.body.classList.add('poster-mode');
    document.body.appendChild(panel);
    mapEl.append(artCanvas, uiSvg);
    if (lp) { lp.inert = false; q('.poster-layers').appendChild(lp); }
    uiSvg.addEventListener('pointerdown', onUiDown);
    uiSvg.addEventListener('dblclick', onUiDblClick);
    for (const t of ['mousedown', 'touchstart']) uiSvg.addEventListener(t, stopToMap, { passive: true });
    document.addEventListener('pointerdown', onDocPointerDown, true);
    document.addEventListener('click', onDocClick, true);
    document.addEventListener('contextmenu', onDocContextMenu, true);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', layout);
    window.visualViewport?.addEventListener('resize', syncKeyboard);
    window.visualViewport?.addEventListener('scroll', syncKeyboard);
    map.on('move zoom viewreset resize', onMapChange);
    map.on('rotate', onRotate);
    map.on('moveend zoomend rotateend', onMapIdle);
    map.closePopup();
    renderStep();
    layout();
    if (state.view) {
      map.setView([state.view.lat, state.view.lng], state.view.zoom, { animate: false });
      map.setBearing?.(state.view.bearing || 0);
    }
    ensureFonts().then(requestRender);
    const list = loadRouteList();
    await loadRoute();
    if (!active) return;
    // Voltando do Traçar (ou primeira vez com rota): enquadra.
    if (route.latlngs && (opts.routeSrc != null || !state.view)) fitRoute();
    renderStep();
    await list;
  }
  function close() {
    if (!active) return;
    persistNow();
    onDragEnd();
    select(null);
    active = false;
    if (raf) { cancelAnimationFrame(raf); raf = 0; }
    uiSvg.removeEventListener('pointerdown', onUiDown);
    uiSvg.removeEventListener('dblclick', onUiDblClick);
    for (const t of ['mousedown', 'touchstart']) uiSvg.removeEventListener(t, stopToMap);
    document.removeEventListener('pointerdown', onDocPointerDown, true);
    document.removeEventListener('click', onDocClick, true);
    document.removeEventListener('contextmenu', onDocContextMenu, true);
    document.removeEventListener('keydown', onKey);
    window.removeEventListener('resize', layout);
    window.visualViewport?.removeEventListener('resize', syncKeyboard);
    window.visualViewport?.removeEventListener('scroll', syncKeyboard);
    map.off('move zoom viewreset resize', onMapChange);
    map.off('rotate', onRotate);
    map.off('moveend zoomend rotateend', onMapIdle);
    for (const l of routeLayers) map.removeLayer(l);
    routeLayers = [];
    artCanvas.remove();
    uiSvg.remove();
    panel.remove();
    const { lp, lpParent, lpNext, lpInert } = saved;
    if (lp && lpParent) { lpParent.insertBefore(lp, lpNext && lpNext.parentNode === lpParent ? lpNext : null); lp.inert = !!lpInert; }
    document.body.classList.remove('poster-mode');
    mapEl.style.cssText = saved.css;
    map.options.zoomSnap = saved.zoomSnap;
    map.options.zoomDelta = saved.zoomDelta;
    map.options.wheelPxPerZoomLevel = saved.wheelPx;
    map._zoomAnimated = saved.zoomAnimated;
    map.invalidateSize();
    map.setView(saved.center, saved.zoom, { animate: false });
    map.setBearing?.(saved.bearing);
    ctx.afterClose?.();
  }
  function ensureFonts() {
    if (!document.fonts?.load) return Promise.resolve();
    const faces = Object.values(FONTS).map((f) => `${f.weight} 32px "${f.family}"`);
    return Promise.all(faces.map((f) => document.fonts.load(f).catch(() => null)))
      .then(() => { _advCache.clear(); });
  }

  // ─── Exportação ────────────────────────────────────────────────────────────
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  // Espera os tiles da vista: GridLayer.isLoading + nenhum <img> pendente.
  async function waitMapIdle(maxMs = 15000) {
    const t0 = performance.now();
    await sleep(350);
    while (performance.now() - t0 < maxMs) {
      let loading = false;
      map.eachLayer((l) => { if (typeof l.isLoading === 'function' && l.isLoading()) loading = true; });
      const pane = map.getPane('rotatePane') || map.getPane('mapPane');
      if (!loading && ![...pane.querySelectorAll('img')].some((i) => !i.complete)) {
        await sleep(300);   // o fade dos tiles recém-chegados
        return true;
      }
      await sleep(200);
    }
    return false;
  }
  async function composeMap(g, signal) {
    const ops = [];
    collectLeaves(map.getPane('mapPane'), new DOMMatrix(), 1, ops);
    const failed = new Set();
    await Promise.all(ops.map(async (op) => {
      try {
        if (op.kind === 'img') op.src = await cleanImageSource(op.el, signal);
        else if (op.kind === 'svg') op.src = await rasterizeSvg(op.el, op.w, op.h);
        else op.src = op.el;
      } catch {
        op.src = null;
        if (op.kind === 'img') { try { failed.add(new URL(op.el.src).hostname); } catch { failed.add('?'); } }
      }
    }));
    g.imageSmoothingQuality = 'high';
    for (const op of ops) {
      if (!op.src) continue;
      g.save();
      g.setTransform(op.m);
      g.globalAlpha = op.a;
      if (op.filter && op.filter !== 'none') g.filter = op.filter;
      // Tiles vizinhos desenhados um a um deixam um fio na emenda (a borda
      // suavizada deixa ver a camada de baixo — pior girado ou em zoom
      // fracionário): cada tile transborda ~½ px de saída pros vizinhos.
      const e = op.tile ? 0.5 / (Math.hypot(op.m.a, op.m.b) || 1) : 0;
      g.drawImage(op.src, -e, -e, op.w + 2 * e, op.h + 2 * e);
      g.restore();
    }
    return failed;
  }
  // A arte final como Blob (mapa composto + arte por cima). Avisa por toast o
  // que ficou de fora.
  async function renderPosterBlob(type) {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 30000);
    try {
      await ensureFonts();
      if (!(await waitMapIdle())) showToast('Alguns tiles demoraram — a imagem pode sair com buracos.', 4000);
      await Promise.all(state.images.map((im) => imageEl(im).decode().catch(() => null)));
      const { w: W, h: H } = dims();
      const c = document.createElement('canvas');
      c.width = W;
      c.height = H;
      const g = c.getContext('2d');
      g.fillStyle = getComputedStyle(mapEl).backgroundColor || '#ddd';
      g.fillRect(0, 0, W, H);
      const failed = await composeMap(g, ac.signal);
      g.setTransform(1, 0, 0, 1, 0, 0);
      renderArt(g);
      if (failed.size) showToast(`Ficaram de fora tiles sem permissão de exportar (CORS): ${[...failed].join(', ')}.`, 7000);
      return await new Promise((res, rej) => {
        try { c.toBlob((b) => (b ? res(b) : rej(new Error('o navegador não gerou a imagem'))), type, 0.92); }
        catch (err) { rej(err); }
      });
    } catch (err) {
      if (err?.name === 'SecurityError') throw new Error('uma camada ligada não permite exportar (CORS) — desligue-a no passo 3');
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
  async function exportImage(type) {
    if (busy) return;
    busy = 'export';
    try {
      showToast('Gerando a imagem…', 2500);
      const blob = await renderPosterBlob(type);
      const ext = type === 'image/jpeg' ? 'jpg' : 'png';
      const fname = `anuncio-${slugify(state.info.name || textOf(state.box.texts[0] || { text: '' }))}.${ext}`;
      const kb = `${Math.round(blob.size / 1024)} KB`;
      // No toque a folha de compartilhar só abre DENTRO de um toque, e a
      // composição leva mais que a janela dele: 2º toque.
      if (ctx.needsShareTap?.(blob, fname, type)) {
        ctx.showActionToast({
          id: 'poster', text: `Arte pronta (${kb}).`, action: '💾 Salvar imagem',
          onAction: () => { ctx.hideActionToast('poster'); saveFile(blob, fname, { type }); },
        });
      } else {
        const r = await saveFile(blob, fname, { type });
        if (r !== 'cancelled') showToast(`Arte salva: ${fname} (${kb}).`);
      }
    } catch (err) {
      console.error('[poster] exportar:', err);
      showToast(`Falha ao gerar a imagem: ${err.message}`, 6000);
    } finally {
      busy = '';
    }
  }

  return { open, close, isOpen: () => active };
}
