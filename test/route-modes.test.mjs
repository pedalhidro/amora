// Traçar: o modo de roteamento é POR TRECHO. Este teste cobre o que é puro —
// o código `sm` do estado de compartilhamento (rota salva no servidor, link
// #st=) e a dedução do modo nos estados antigos, que só guardavam o modo do
// seletor. As funções moram no web/app.js (que não importa no Node: é o app
// inteiro), entre os marcadores "modos por trecho: início/fim" — o teste lê
// esse bloco do fonte. O comportamento do editor (trocar o seletor não refaz
// nada; arrastar refaz só os dois trechos do ponto) é conferido no navegador.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const src = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');
const block = /\/\/ ── modos por trecho: início[\s\S]*?\/\/ ── modos por trecho: fim ──/.exec(src);
assert.ok(block, 'web/app.js tem o bloco "modos por trecho"');
const { segModesToString, segModeFromState } =
  new Function(`${block[0]}\n; return { segModesToString, segModeFromState };`)();

const MODES = ['straight', 'cycling', 'foot', 'energy', 'energy_road'];

test('cada modo do seletor tem a sua letra, e a letra volta pro modo', () => {
  const options = [...readFileSync(new URL('../web/index.html', import.meta.url), 'utf8')
    .matchAll(/<option value="([a-z_]+)">/g)].map((m) => m[1]);
  // os modos do <select id="trace-routing-mode"> (o GPX-connect repete os mesmos)
  for (const mode of MODES) assert.ok(options.includes(mode), `o seletor tem "${mode}"`);
  const sm = segModesToString(MODES);
  assert.equal(sm, 'scfer');
  assert.equal(new Set(sm).size, MODES.length, 'letras distintas');
  MODES.forEach((mode, k) => assert.equal(segModeFromState(sm, 'straight', k, 0), mode));
});

test('trecho sem proveniência vira "-" e volta null', () => {
  assert.equal(segModesToString(['cycling', null, undefined, 'bogus', 'foot']), 'c---f');
  assert.equal(segModeFromState('c---f', 'cycling', 1, 9), null);
  assert.equal(segModeFromState('c', 'cycling', 5, 9), null, 'além do fim do sm');
});

test('com `sm`, o modo do seletor (`rm`) não decide nada', () => {
  // rota mista salva com o seletor em Reta: os trechos seguem os seus modos
  assert.equal(segModeFromState('fss', 'straight', 0, 4), 'foot');
  assert.equal(segModeFromState('fss', 'cycling', 1, 2), 'straight');
});

test('estado antigo (sem `sm`), seletor roteado: trecho com geometria herda o modo', () => {
  assert.equal(segModeFromState(undefined, 'energy_road', 0, 37), 'energy_road');
  assert.equal(segModeFromState(null, 'cycling', 3, 2), 'cycling', 'quadra reta (2 pontos) também');
  assert.equal(segModeFromState(undefined, 'cycling', 0, 0), null, 'sem geometria guardada: quem carrega refaz');
});

test('estado antigo em Reta: toda reta é de propósito; geometria é traçado importado', () => {
  assert.equal(segModeFromState(undefined, 'straight', 0, 0), 'straight');
  assert.equal(segModeFromState(undefined, 'straight', 0, 2), 'straight');
  assert.equal(segModeFromState(undefined, 'straight', 0, 40), null);
});

test('modo desconhecido no estado não inventa proveniência', () => {
  assert.equal(segModeFromState(undefined, 'teleporte', 0, 9), null);
  assert.equal(segModeFromState(undefined, undefined, 0, 9), null);
  assert.equal(segModeFromState('x', 'cycling', 0, 9), null);
});
