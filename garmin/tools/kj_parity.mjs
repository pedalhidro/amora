#!/usr/bin/env node
// Paridade do modelo de energia do campo de dados "Quilojaules" com o amora.
//
//   node garmin/tools/kj_parity.mjs                 # perfil sintético
//   node garmin/tools/kj_parity.mjs pedal.json      # saída do fit_to_json.py
//   node garmin/tools/kj_parity.mjs pedal.json --at=60,300   # o que o campo mostra aos 60 s e 300 s
//
// O campo (garmin/quilojaules/source/KjModel.mc) calcula a energia do MODELO
// em fluxo, amostra a amostra, com a mesma receita que o amora usa pra
// estimar os kJ de uma rota (`simulateRide` em web/app.js): perfil reamostrado
// a passo fixo de 30 m, deadband de 2 m, rolamento em toda a distância, arrasto
// só fora das subidas, gravidade com recuperação ε ponderada pela queda.
//
// `KjModel` abaixo é o ESPELHO linha a linha do KjModel.mc (mude os dois
// juntos). Este script confere o espelho contra o código DE VERDADE do amora:
// extrai `simulateRide`/`readCost`/`deadbandElev` do web/app.js e roda sobre o
// mesmo perfil. Também mostra a sensibilidade ao passo (5/10/30/50 m), o custo
// de fazer a conta em float de 32 bits (o Float do Monkey C) e, de referência,
// a soma por aresta do `GraphEngine.stepCost` (o custo do roteamento).
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const APP_JS = readFileSync(join(ROOT, 'web', 'app.js'), 'utf8');

// ── Espelho do KjModel.mc ────────────────────────────────────────────────
export class KjModel {
  // p: {mass, crr, cda, rho, kEff, powerFlat, climbThr, deadbandM, stepM}
  constructor(p, f32 = false) {
    const f = f32 ? Math.fround : (x) => x;
    this.f = f;
    const G = 9.81;
    const kEff = Math.min(1, Math.max(0.1, p.kEff));
    const vf = KjModel.flatSpeed(p.powerFlat, p.mass, p.crr, p.cda, p.rho);
    const aero = 0.5 * p.rho * p.cda * vf * vf;        // J por metro, antes do k_eff
    this.aRoll = f((p.crr * p.mass * G) / kEff / 1000); // kJ por metro
    this.aAero = f(aero / kEff / 1000);
    this.beta = f((p.mass * G) / kEff / 1000);          // kJ por metro de subida
    this.abRatio = f(p.crr + aero / (p.mass * G));
    this.climbThr = f(p.climbThr);
    this.tau = f(p.deadbandM);
    this.step = f(p.stepM);
    this.total = KjModel.newAcc();
    this.lap = KjModel.newAcc();
    this.started = false;
    this.lastS = 0; this.lastH = 0; this.nodeS = 0; this.y = 0;
    this.edge = 0;      // soma por aresta (segCost) — base da potência estimada
  }

  // Velocidade de equilíbrio no plano (Newton na cúbica), como o
  // solveSpeedAtGradient do amora com gradiente 0.
  static flatSpeed(power, mass, crr, cda, rho) {
    const a = 0.5 * rho * cda;
    const b = mass * 9.81 * crr;
    let v = 5;
    for (let i = 0; i < 60; i++) {
      const fv = a * v * v * v + b * v - power;
      const fp = 3 * a * v * v + b;
      if (Math.abs(fp) < 1e-12) break;
      const dv = fv / fp;
      v -= dv;
      if (v < 0.1) v = 0.1;
      if (Math.abs(dv) < 1e-7) break;
    }
    return Math.max(0.5, v);
  }

  // [x, wRoll, wAero, wClimb, hPlus, hMinus, epsNum, epsDen]
  static newAcc() { return [0, 0, 0, 0, 0, 0, 0, 0]; }

  // Uma amostra (distância acumulada em m, altitude em m ou null).
  feed(s, h) {
    const f = this.f;
    if (h == null) h = this.lastH;
    if (!this.started) {
      this.started = true;
      this.lastS = s; this.lastH = h; this.nodeS = s; this.y = h;
      return;
    }
    if (s > this.lastS) {
      while (f(this.nodeS + this.step) <= s) {
        this.nodeS = f(this.nodeS + this.step);
        const frac = f(f(this.nodeS - this.lastS) / f(s - this.lastS));
        const hN = f(this.lastH + f(f(h - this.lastH) * frac));
        const yPrev = this.y;
        if (hN > f(this.y + this.tau)) this.y = f(hN - this.tau);
        else if (hN < f(this.y - this.tau)) this.y = f(hN + this.tau);
        this.addSegment(this.step, f(this.y - yPrev));
      }
      this.lastS = s;
    }
    this.lastH = h;
  }

  // kJ de UM trecho com o ε local — tem que ser o GraphEngine.stepCost.
  segCost(d, dh) {
    const f = this.f;
    if (dh >= 0) {
      let c = f(f(this.aRoll * d) + f(this.beta * dh));
      if (dh < f(this.climbThr * d)) c = f(c + f(this.aAero * d));
      return c;
    }
    const drop = -dh;
    let eps = f(f(this.abRatio * d) / drop);
    if (eps > 1) eps = 1;
    eps = f(eps - 0.13);
    if (eps < 0) eps = 0;
    const e = f(f(f(this.aRoll * d) + f(this.aAero * d)) - f(f(eps * this.beta) * drop));
    return e < 0 ? 0 : e;
  }

  // Soma por aresta + o trecho em andamento (do último nó à última amostra).
  liveEdge() {
    const f = this.f;
    const part = f(this.lastS - this.nodeS);
    if (!this.started || part <= 0) return this.edge;
    let yLive = this.y;
    if (this.lastH > f(this.y + this.tau)) yLive = f(this.lastH - this.tau);
    else if (this.lastH < f(this.y - this.tau)) yLive = f(this.lastH + this.tau);
    return f(this.edge + this.segCost(part, f(yLive - this.y)));
  }

  addSegment(seg, dh) {
    const f = this.f;
    this.edge = f(this.edge + this.segCost(seg, dh));
    for (const a of [this.total, this.lap]) {
      a[0] = f(a[0] + seg);
      a[1] = f(a[1] + f(this.aRoll * seg));
      if (dh >= 0) {
        a[4] = f(a[4] + dh);
        a[3] = f(a[3] + f(this.beta * dh));
        if (dh < f(this.climbThr * seg)) a[2] = f(a[2] + f(this.aAero * seg));
      } else {
        const drop = -dh;
        a[5] = f(a[5] + drop);
        a[2] = f(a[2] + f(this.aAero * seg));
        let epsCoast = f(f(this.abRatio * seg) / drop);
        if (epsCoast > 1) epsCoast = 1;
        a[6] = f(a[6] + f(epsCoast * drop));
        a[7] = f(a[7] + drop);
      }
    }
  }

  // kJ de um acumulador (o total ou o da volta).
  static energy(a, beta, f = (x) => x) {
    let eps = a[7] > 0 ? f(f(a[6] / a[7]) - 0.13) : 0;
    if (eps < 0) eps = 0; else if (eps > 1) eps = 1;
    const e = f(f(f(a[1] + a[2]) + a[3]) - f(f(eps * beta) * a[5]));
    return e < 0 ? 0 : e;
  }

  kj() { return KjModel.energy(this.total, this.beta, this.f); }
  lapKj() { return KjModel.energy(this.lap, this.beta, this.f); }
  newLap() { this.lap = KjModel.newAcc(); }
}

// ── Código real do amora, extraído do app.js ─────────────────────────────
function extractFunction(name) {
  const start = APP_JS.indexOf(`\nfunction ${name}(`);
  if (start < 0) throw new Error(`função ${name} não encontrada em web/app.js`);
  const end = APP_JS.indexOf('\n}\n', start);
  return APP_JS.slice(start, end + 3);
}

function amoraDefaults() {
  const start = APP_JS.indexOf('const DEFAULT_PARAMS = {');
  const end = APP_JS.indexOf('\n};', start);
  // eslint-disable-next-line no-new-func
  return new Function(`return ${APP_JS.slice(start + 'const DEFAULT_PARAMS = '.length, end + 2)}`)();
}

function amoraSimulate(prof, p) {
  const src = ['solveSpeedAtGradient', 'powerFor', 'segmentSpeed', 'deadbandElev',
    'readCost', 'simulateRide'].map(extractFunction).join('\n');
  // eslint-disable-next-line no-new-func
  const make = new Function('G', 'assembleLatLngs', 'buildRecipeProfile',
    `${src}\nreturn simulateRide;`);
  return make(9.81, () => [0, 0], () => prof)(p);
}

// Perfil da receita (buildRecipeProfile do amora) a partir da série amostrada.
function recipeProfile(S, H, step) {
  const total = S[S.length - 1];
  const s = [];
  for (let x = S[0]; x < total; x += step) s.push(x);
  if (!s.length || total - s[s.length - 1] >= 1) s.push(total); else s[s.length - 1] = total;
  const h = new Float64Array(s.length);
  let j = 0;
  for (let k = 0; k < s.length; k++) {
    while (j < S.length - 2 && S[j + 1] < s[k]) j++;
    const span = S[j + 1] - S[j];
    const fr = span > 0 ? (s[k] - S[j]) / span : 0;
    h[k] = H[j] + (H[j + 1] - H[j]) * fr;
  }
  return { s, h, total };
}

// ── Entrada ──────────────────────────────────────────────────────────────
function syntheticRide() {
  // 40 km: ondulação + uma serra + ruído de barômetro, 1 amostra por segundo
  // a ~6 m/s com paradas (distância repetida, altitude derivando).
  const S = [], H = [], P = [], T = [];
  let s = 0, seed = 7;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2 ** 32; };
  for (let t = 0; s < 40000; t++) {
    const stopped = (t % 900) > 860;
    if (!stopped) s += 4 + 4 * rnd();
    const h = 760 + 25 * Math.sin(s / 900) + 8 * Math.sin(s / 130)
      + (s > 15000 && s < 22000 ? (s - 15000) * 0.045 : s >= 22000 ? Math.max(0, 315 - (s - 22000) * 0.06) : 0)
      + (rnd() - 0.5) * 0.6;
    S.push(s); H.push(h); P.push(stopped ? 0 : 60 + 80 * rnd()); T.push(t);
  }
  return { s: S, h: H, p: P, t: T, laps: [] };
}

function load(path) {
  if (!path) return syntheticRide();
  const d = JSON.parse(readFileSync(path, 'utf8'));
  let last = d.h.find((v) => v != null) ?? 0;
  d.h = d.h.map((v) => (v == null ? last : (last = v)));
  return d;
}

// --at=60,120,300 → imprime o que o campo deve mostrar nesses segundos.
const AT = (process.argv.find((x) => x.startsWith('--at=')) || '--at=').slice(5)
  .split(',').filter(Boolean).map(Number);

// ── Relatório ────────────────────────────────────────────────────────────
const ride = load(process.argv[2]);
const def = amoraDefaults();
const base = {
  mass: def.mass, crr: def.crr, cda: def.cda, rho: def.rho, kEff: def.kEff,
  powerFlat: def.powerFlat, climbThr: def.slopeFlatThreshold,
  deadbandM: def.deadbandM, stepM: 30,
};
const run = (p, f32) => {
  const m = new KjModel(p, f32);
  for (let i = 0; i < ride.s.length; i++) m.feed(ride.s[i], ride.h[i]);
  return m;
};
const fmt = (x) => x.toFixed(1).padStart(9);
const km = (ride.s[ride.s.length - 1] - ride.s[0]) / 1000;
console.log(`pedal: ${km.toFixed(1)} km, ${ride.s.length} amostras`);
console.log(`parâmetros (defaults do amora): ${JSON.stringify(base)}`);

const m30 = run(base, false);
const amora = amoraSimulate(recipeProfile(ride.s, ride.h, 30), { ...def });
const amoraKj = amora.eLegJ / 1000;
console.log(`\nmodelo em fluxo (espelho do KjModel.mc), 30 m: ${fmt(m30.kj())} kJ`);
console.log(`amora simulateRide sobre o mesmo perfil:        ${fmt(amoraKj)} kJ`);
const rel = Math.abs(m30.kj() - amoraKj) / amoraKj;
console.log(`diferença: ${(rel * 100).toFixed(3)} %  (subida ${m30.total[4].toFixed(0)} m × ${amora.ascentM.toFixed(0)} m, ε ${amora.epsUsed.toFixed(3)})`);

let relEdge = 0, absEdge = 0;
const m32 = run(base, true);
const rel32 = Math.abs(m32.kj() - m30.kj()) / m30.kj();
console.log(`\nmesma conta em float32 (Float do Monkey C):     ${fmt(m32.kj())} kJ  (${(rel32 * 100).toFixed(4)} %)`);

console.log('\nsensibilidade ao passo (com deadband de 2 m):');
for (const step of [5, 10, 30, 50]) {
  const m = run({ ...base, stepM: step }, false);
  console.log(`  ${String(step).padStart(2)} m: ${fmt(m.kj())} kJ  (${((m.kj() / m30.kj() - 1) * 100).toFixed(1).padStart(5)} %)  h+ ${m.total[4].toFixed(0)} m`);
}
const raw = run({ ...base, deadbandM: 0, stepM: 5 }, false);
console.log(`   5 m sem deadband: ${fmt(raw.kj())} kJ  (${((raw.kj() / m30.kj() - 1) * 100).toFixed(1)} %)  h+ ${raw.total[4].toFixed(0)} m`);

// Referência: soma por aresta do custo de roteamento (GraphEngine.stepCost)
// sobre o mesmo perfil de 30 m com deadband.
{
  const require = createRequire(import.meta.url);
  const GE = require(join(ROOT, 'web', 'lib', 'graph-engine.js'));
  const prof = recipeProfile(ride.s, ride.h, 30);
  const cost = { aRoll: m30.aRoll, aAero: m30.aAero, beta: m30.beta,
    climbThr: m30.climbThr, abRatio: m30.abRatio, epsOffset: 0.13 };
  let y = prof.h[0], e = 0;
  for (let i = 1; i < prof.s.length; i++) {
    const yPrev = y, hi = prof.h[i];
    if (hi > y + 2) y = hi - 2; else if (hi < y - 2) y = hi + 2;
    e += GE.stepCost(prof.s[i] - prof.s[i - 1], y - yPrev, cost);
  }
  console.log(`\nsoma por aresta — GraphEngine.stepCost do amora: ${fmt(e)} kJ  (${((e / m30.kj() - 1) * 100).toFixed(1)} % do total)`);
  console.log(`soma por aresta — segCost do espelho:           ${fmt(m30.edge)} kJ`);
  relEdge = Math.abs(m30.edge - e) / e;
  absEdge = Math.abs(m30.edge - e);
}

// Potência estimada (o número grande do campo): energia por aresta dos
// últimos 30 s ÷ tempo, amostrada 1×/s como no QuilojaulesField.mc.
{
  const m = new KjModel(base, false);
  const WINDOW = 31, MIN_MS = 5000;
  const T = [], E = [], est = [];
  let neg = 0;
  for (let i = 0; i < ride.s.length; i++) {
    m.feed(ride.s[i], ride.h[i]);
    T.push(ride.t[i] * 1000); E.push(m.liveEdge());
    if (i > 0 && E[i] < E[i - 1] - 1e-9) neg++;
    const j = Math.max(0, i - (WINDOW - 1));
    const dt = T[i] - T[j];
    if (dt < MIN_MS) continue;
    let p = (E[i] - E[j]) * 1e6 / dt;
    if (p < 0) p = 0; else if (p > 3000) p = 3000;
    est.push(Math.round(p));
    if (AT.includes(Math.round(ride.t[i]))) {
      console.log(`  aos ${String(Math.round(ride.t[i])).padStart(4)} s: est. ${m.kj().toFixed(0)} kJ · ${Math.round(p)} W`);
    }
  }
  const sorted = [...est].sort((a, b) => a - b);
  const q = (x) => sorted[Math.min(sorted.length - 1, Math.floor(x * sorted.length))];
  const mean = est.reduce((a, b) => a + b, 0) / est.length;
  const span = ride.t[ride.t.length - 1] - ride.t[0];
  console.log(`\npotência estimada (30 s): média ${mean.toFixed(0)} W · mediana ${q(0.5)} W · p95 ${q(0.95)} W · máx ${q(1)} W`);
  console.log(`  energia por aresta ÷ tempo total = ${(m.edge * 1000 / span).toFixed(0)} W; passos em que a energia ao vivo recuou: ${neg} de ${ride.s.length}`);
  if (process.argv[2] && ride.p && ride.p.some((v) => v != null)) {
    const ps = ride.p.filter((v) => v != null);
    console.log(`  potência MEDIDA no arquivo: média ${(ps.reduce((a, b) => a + b, 0) / ps.length).toFixed(0)} W (contexto)`);
  }
}

if (process.argv[2] && ride.p && ride.p.some((v) => v != null)) {
  let j = 0;
  for (let i = 1; i < ride.t.length; i++) {
    const dt = Math.min(5, ride.t[i] - ride.t[i - 1]);
    if (ride.p[i] != null && dt > 0) j += ride.p[i] * dt;
  }
  console.log(`\nmedido no pedal (∫P·dt): ${fmt(j / 1000)} kJ — outra pessoa, outra massa e outra potência: é contexto, não validação`);
}

// Voltas: a soma das energias por volta difere do total (o ε é ponderado
// dentro de cada janela), mas tem que ficar perto.
{
  const m = new KjModel(base, false);
  const marks = (ride.laps && ride.laps.length > 1) ? ride.laps.slice(1)
    : [ride.t[Math.floor(ride.t.length / 3)], ride.t[Math.floor(2 * ride.t.length / 3)]];
  let k = 0, sum = 0;
  for (let i = 0; i < ride.s.length; i++) {
    if (k < marks.length && ride.t[i] >= marks[k]) { sum += m.lapKj(); m.newLap(); k++; }
    m.feed(ride.s[i], ride.h[i]);
  }
  sum += m.lapKj();
  console.log(`\nvoltas: ${k + 1}; soma das voltas ${fmt(sum)} kJ × total ${fmt(m.kj())} kJ`);
}

// Tolerância: 0,2 % OU o custo de ~1 trecho de 30 m — o fluxo não conta o
// resto final (< 30 m) do pedal, e num pedal curto isso passa de 0,2 %.
const SEG_KJ = 0.6;
let ok = true;
if (rel > 0.002 && Math.abs(m30.kj() - amoraKj) > SEG_KJ) { console.error('FALHA: o espelho divergiu do simulateRide do amora (> 0,2 %)'); ok = false; }
if (rel32 > 0.002 && Math.abs(m32.kj() - m30.kj()) > SEG_KJ) { console.error('FALHA: float32 perde precisão demais (> 0,2 %)'); ok = false; }
if (relEdge > 0.002 && absEdge > SEG_KJ) { console.error('FALHA: o segCost do espelho divergiu do GraphEngine.stepCost (> 0,2 %)'); ok = false; }
console.log(ok ? '\nOK' : '\nFALHOU');
process.exit(ok ? 0 : 1);
