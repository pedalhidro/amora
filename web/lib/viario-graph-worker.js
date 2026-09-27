// Pedal Hidrográfico — worker do grafo pré-cozido do viário de SP
// (sampa-viario-graph.bin, gerado por scripts/build-viario.py --graph).
//
// É a fonte PRIMÁRIA do "Menor energia pelo viário" (ver bakedViarioRoute em
// app.js). Mora num worker porque o grafo é grande — ~4,8 M nós, ~10 M arestas
// dirigidas — e no main thread ele prendia ~230 MB de typed arrays pro resto da
// sessão e travava a interface a cada rota (varredura O(N) + Dijkstra). Aqui:
//   • o app baixa o arquivo (pelo service worker, com progresso e timeout de
//     inatividade) e TRANSFERE o ArrayBuffer; o decode descarta o buffer cru;
//   • as arestas de CADEIA (nó i ↔ i+1, bit1 de flags) ficam implícitas — só
//     as explícitas (junções) viram CSR — e a varredura da bbox usa um índice
//     de blocos de nós consecutivos (a ordem do bake segue a do FGB, que é
//     Hilbert: os nós de uma bbox caem em poucos blocos);
//   • os buffers do Dijkstra têm o tamanho da BBOX (mapa global→local zerado
//     só nos nós usados), não do grafo inteiro;
//   • o app termina o worker quando o editor fecha/fica ocioso — libera tudo.
// A rota é IDÊNTICA à do código antigo no main thread: mesmos nós elegíveis,
// mesmo snap (1º mínimo na ordem dos índices), mesma ordem de relaxação dos
// vizinhos (cadeia pra trás, cadeia pra frente, explícitas na ordem do
// arquivo), mesmo heap binário e dist em float32.
//
// Custo v2 por aresta: GraphEngine.stepCost (graph-engine.js, vendorado do
// simujaules — a mesma fórmula do v2Edge do energy-worker e do v2EdgeCostFn do
// app.js). Mensagens (todas com reqId, ecoado na resposta):
//   {kind:'load', buf}                       → {kind:'loaded', N, E, ms}
//   {kind:'route', from, to, bb, cost}       → {kind:'done', path, deck, J, nAllowed, ms}
//        path = Float64Array [lat,lng,…] com as pontas reais costuradas; deck =
//        Uint8Array (1 = interior de tabuleiro); path null = sem caminho.
//   erro → {kind:'error', message}
/* eslint-env worker */
importScripts('./graph-engine.js');
const stepCost = self.GraphEngine.stepCost;

const BLOCK = 1024;          // nós por bloco do índice espacial
let G = null;                // grafo decodificado

// Decodifica o binário PHVG (little-endian; seções alinhadas a 4 bytes) —
// mesmo formato do decodeViarioGraph antigo do app.js. Nós em µgrau (1e-6),
// elevação em decímetros, flags bit0 = interior de tabuleiro, bit1 = aresta de
// cadeia pro nó i+1 (comprimento em chain[i], dm).
function decode(buf) {
  const dv = new DataView(buf);
  if (buf.byteLength < 24 || dv.getUint32(0, true) !== 0x47564850) // 'PHVG' LE
    throw new Error('grafo: magic inválido');
  const version = dv.getUint32(4, true);
  if (version !== 1) throw new Error(`grafo: versão ${version} não suportada`);
  const N = dv.getUint32(8, true);
  const NESC = dv.getUint32(12, true);
  const EX = dv.getUint32(16, true);
  let off = 24;
  const pad4 = () => { off = (off + 3) & ~3; };
  const view = (Ctor, len) => { pad4(); const v = new Ctor(buf, off, len); off += len * Ctor.BYTES_PER_ELEMENT; return v; };
  const dLat  = view(Int16Array, N);
  const dLng  = view(Int16Array, N);
  const elevV = view(Int16Array, N);   // dm
  const flagV = view(Uint8Array, N);
  const chainV = view(Uint16Array, N); // dm
  const escIdx = view(Uint32Array, NESC);
  const escLat = view(Int32Array, NESC);
  const escLng = view(Int32Array, NESC);
  const exU = view(Uint32Array, EX);
  const exV = view(Uint32Array, EX);
  const exD = view(Uint16Array, EX);   // dm
  if (off > buf.byteLength) throw new Error('grafo: arquivo truncado');

  // Cópias (não views): o buffer cru (~68 MB) morre no fim do decode.
  const elev = elevV.slice(), flags = flagV.slice(), chain = chainV.slice();

  // Deltas → coordenadas absolutas (µgrau). Sentinela dLat=-32768 → escape.
  // Na mesma passada: caixa de cada bloco de BLOCK nós consecutivos.
  const latU = new Int32Array(N), lngU = new Int32Array(N);
  const nb = Math.ceil(N / BLOCK);
  const blk = new Int32Array(nb * 4);   // [sul, norte, oeste, leste] por bloco
  let pLat = 0, pLng = 0, e = 0;
  for (let b = 0; b < nb; b++) {
    let s = 2147483647, n = -2147483648, w = 2147483647, ea = -2147483648;
    for (let i = b * BLOCK, end = Math.min(N, i + BLOCK); i < end; i++) {
      if (dLat[i] === -32768) {
        if (e >= NESC || escIdx[e] !== i) throw new Error('grafo: escape fora de ordem');
        pLat = escLat[e]; pLng = escLng[e]; e++;
      } else {
        pLat += dLat[i]; pLng += dLng[i];
      }
      latU[i] = pLat; lngU[i] = pLng;
      if (pLat < s) s = pLat; if (pLat > n) n = pLat;
      if (pLng < w) w = pLng; if (pLng > ea) ea = pLng;
    }
    blk[b * 4] = s; blk[b * 4 + 1] = n; blk[b * 4 + 2] = w; blk[b * 4 + 3] = ea;
  }

  // CSR SÓ das arestas explícitas (as de cadeia são implícitas). A ordem de
  // preenchimento (k crescente, u→v e v→u) é a mesma do CSR completo antigo.
  const xptr = new Uint32Array(N + 1);
  for (let k = 0; k < EX; k++) { xptr[exU[k] + 1]++; xptr[exV[k] + 1]++; }
  for (let i = 0; i < N; i++) xptr[i + 1] += xptr[i];
  const XE = xptr[N];
  const xt = new Uint32Array(XE);
  const xd = new Uint16Array(XE);
  const cursor = xptr.slice(0, N);
  for (let k = 0; k < EX; k++) {
    const u = exU[k], v = exV[k], d = exD[k];
    let c = cursor[u]++; xt[c] = v; xd[c] = d;
    c = cursor[v]++; xt[c] = u; xd[c] = d;
  }
  let nChain = 0;
  for (let i = 0; i + 1 < N; i++) if (flags[i] & 2) nChain++;
  return { N, latU, lngU, elev, flags, chain, xptr, xt, xd, blk, nb, loc: null, E: 2 * nChain + XE };
}

// Min-heap binário (prioridade f64 + id int) com deleção preguiçosa — o MESMO
// do app.js (class MinHeap), pra rota sair idêntica à do main thread antigo.
class MinHeap {
  constructor() { this.pri = []; this.id = []; }
  get size() { return this.id.length; }
  push(p, i) {
    const pri = this.pri, id = this.id;
    let c = id.length;
    pri.push(p); id.push(i);
    while (c > 0) {
      const par = (c - 1) >> 1;
      if (pri[par] <= pri[c]) break;
      const tp = pri[par]; pri[par] = pri[c]; pri[c] = tp;
      const ti = id[par];  id[par]  = id[c];  id[c]  = ti;
      c = par;
    }
  }
  pop() {
    const pri = this.pri, id = this.id;
    const top = id[0];
    const lp = pri.pop(), li = id.pop();
    if (id.length) {
      pri[0] = lp; id[0] = li;
      let c = 0; const m = id.length;
      while (true) {
        const l = 2 * c + 1, r = 2 * c + 2; let s = c;
        if (l < m && pri[l] < pri[s]) s = l;
        if (r < m && pri[r] < pri[s]) s = r;
        if (s === c) break;
        const tp = pri[s]; pri[s] = pri[c]; pri[c] = tp;
        const ti = id[s];  id[s]  = id[c];  id[c]  = ti;
        c = s;
      }
    }
    return top;
  }
}

// Roteia origem→destino restrito à bbox (paridade com o grafo por-bbox do FGB).
function route(g, from, to, bb, cost) {
  const t0 = performance.now();
  const { N, latU, lngU, elev, flags, chain, xptr, xt, xd, blk, nb } = g;
  const s6 = Math.round(bb.south * 1e6), n6 = Math.round(bb.north * 1e6);
  const w6 = Math.round(bb.west * 1e6),  e6 = Math.round(bb.east * 1e6);
  const fLat = Math.round(from.lat * 1e6), fLng = Math.round(from.lng * 1e6);
  const tLat = Math.round(to.lat * 1e6),   tLng = Math.round(to.lng * 1e6);
  // Mapa global → local (1-based; 0 = fora da bbox). Alocado uma vez por grafo
  // e zerado só nos nós que esta rota usou.
  if (!g.loc) g.loc = new Int32Array(N);
  const loc = g.loc;
  let glob = new Int32Array(1 << 16), nA = 0;
  let s = -1, t = -1, sD = Infinity, tD = Infinity;
  try {
    // Passe único sobre os blocos que tocam a bbox: marca os nós elegíveis e
    // acha o mais próximo de cada ponta (mesma métrica não escalada).
    for (let b = 0; b < nb; b++) {
      if (blk[b * 4 + 1] < s6 || blk[b * 4] > n6 || blk[b * 4 + 3] < w6 || blk[b * 4 + 2] > e6) continue;
      for (let i = b * BLOCK, end = Math.min(N, i + BLOCK); i < end; i++) {
        const la = latU[i], lg = lngU[i];
        if (la < s6 || la > n6 || lg < w6 || lg > e6) continue;
        if (nA === glob.length) { const gr = new Int32Array(glob.length * 2); gr.set(glob); glob = gr; }
        glob[nA] = i; loc[i] = ++nA;
        let dl = la - fLat, dg = lg - fLng;
        let d = dl * dl + dg * dg;
        if (d < sD) { sD = d; s = i; }
        dl = la - tLat; dg = lg - tLng;
        d = dl * dl + dg * dg;
        if (d < tD) { tD = d; t = i; }
      }
    }
    if (s < 0 || t < 0) return { path: null, nAllowed: nA, ms: performance.now() - t0 };

    const dist = new Float32Array(nA).fill(Infinity);
    const prev = new Int32Array(nA);
    const done = new Uint8Array(nA);
    const heap = new MinHeap();
    const ls = loc[s] - 1, lt = loc[t] - 1;
    dist[ls] = 0;
    heap.push(0, s);
    while (heap.size) {
      const u = heap.pop();
      const lu = loc[u] - 1;
      if (done[lu]) continue;
      done[lu] = 1;
      if (u === t) break;
      const du = dist[lu], hu = elev[u];
      // Vizinhos na ordem do CSR antigo: cadeia pra trás, cadeia pra frente,
      // explícitas.
      if (u > 0 && (flags[u - 1] & 2)) {
        const v = u - 1, lv = loc[v] - 1;
        if (lv >= 0 && !done[lv]) {
          const nd = du + stepCost(chain[v] * 0.1, (elev[v] - hu) * 0.1, cost);
          if (nd < dist[lv]) { dist[lv] = nd; prev[lv] = u; heap.push(nd, v); }
        }
      }
      if (u + 1 < N && (flags[u] & 2)) {
        const v = u + 1, lv = loc[v] - 1;
        if (lv >= 0 && !done[lv]) {
          const nd = du + stepCost(chain[u] * 0.1, (elev[v] - hu) * 0.1, cost);
          if (nd < dist[lv]) { dist[lv] = nd; prev[lv] = u; heap.push(nd, v); }
        }
      }
      for (let k = xptr[u], end = xptr[u + 1]; k < end; k++) {
        const v = xt[k], lv = loc[v] - 1;
        if (lv < 0 || done[lv]) continue;
        const nd = du + stepCost(xd[k] * 0.1, (elev[v] - hu) * 0.1, cost);
        if (nd < dist[lv]) { dist[lv] = nd; prev[lv] = u; heap.push(nd, v); }
      }
    }
    if (!done[lt]) return { path: null, nAllowed: nA, ms: performance.now() - t0 };

    // Caminho t→s pelos predecessores; as pontas reais entram costuradas.
    let len = 1;
    for (let v = t; v !== s; v = prev[loc[v] - 1]) len++;
    const path = new Float64Array((len + 2) * 2);
    const deck = new Uint8Array(len + 2);
    path[0] = from.lat; path[1] = from.lng;
    let j = len;
    for (let v = t; ; v = prev[loc[v] - 1]) {
      path[j * 2] = latU[v] / 1e6; path[j * 2 + 1] = lngU[v] / 1e6;
      deck[j] = flags[v] & 1;
      if (v === s) break;
      j--;
    }
    path[(len + 1) * 2] = to.lat; path[(len + 1) * 2 + 1] = to.lng;
    return { path, deck, J: dist[lt], nAllowed: nA, ms: performance.now() - t0 };
  } finally {
    for (let i = 0; i < nA; i++) loc[glob[i]] = 0;
  }
}

self.onmessage = (ev) => {
  const m = ev.data || {};
  const reqId = m.reqId;
  try {
    if (m.kind === 'load') {
      const t0 = performance.now();
      G = decode(m.buf);
      self.postMessage({ kind: 'loaded', reqId, N: G.N, E: G.E, ms: performance.now() - t0 });
    } else if (m.kind === 'route') {
      if (!G) throw new Error('grafo não carregado');
      const r = route(G, m.from, m.to, m.bb, m.cost);
      const transfer = r.path ? [r.path.buffer, r.deck.buffer] : [];
      self.postMessage({ kind: 'done', reqId, ...r }, transfer);
    }
  } catch (err) {
    self.postMessage({ kind: 'error', reqId, message: (err && err.message) || String(err) });
  }
};
