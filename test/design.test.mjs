// As regras do design system (docs/DESIGN-VISUAL.md). Adaptado de
// bicibusaosampa/test/design.test.js (GPL-3.0-or-later, por Andrei).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { buildTokens, DESIGN_DOC, OUT_CSS, OUT_JS, PAGE_ALIASES, resolveContexts, resolveValue, updateDesignDoc } from '../scripts/build-tokens.mjs';
import { tokens } from '../web/lib/tokens.js';
import { buildIconsJs, loadIcons, OUT_JS as ICONS_JS, updateIndexIcons, VOCABULARY } from '../scripts/build-icons.mjs';

const ROOT = join(import.meta.dirname, '..');
const read = (path) => readFileSync(join(ROOT, path), 'utf8');
const NS = 'info.pedalhidrografi';
const all = resolveContexts();
const roles = [...all.values()].filter((t) => t.path[0] !== 'ref');
const meta = (t) => t.$extensions?.[NS] ?? {};

// Variáveis definidas em tempo de execução, fora dos tokens.
const RUNTIME_VARS = ['--band', '--clip-intensity', '--clip-marker-border', '--clip-marker-size', '--clip-max-scale', '--clip-min-scale', '--fill', '--kind', '--live-color', '--photo-cone-opacity', '--photo-density-scale', '--photo-dx', '--photo-dy', '--photo-hover-scale', '--photo-scale', '--poster-kb', '--txt', '--visible-size'];

// Os arquivos já migrados. As páginas embutidas e o poster.js ainda não: DESIGN-VISUAL.md, "O que falta".
const SOURCES = ['web/style.css', 'web/index.html', 'web/app.js'];
const withoutData = (text) => text.replace(/\/\/ cores-de-dados: início[\s\S]*?\/\/ cores-de-dados: fim/g, '');

test('tokens.css, tokens.js e as tabelas do documento estão em dia (rode npm run build:tokens)', () => {
  const { css, js, tables } = buildTokens();
  assert.equal(readFileSync(OUT_CSS, 'utf8'), css);
  assert.equal(readFileSync(OUT_JS, 'utf8'), js);
  const doc = readFileSync(DESIGN_DOC, 'utf8');
  assert.equal(doc, updateDesignDoc(doc, tables));
});

test('ref é a paleta: sem aliases', () => {
  for (const t of all.values()) {
    if (t.path[0] === 'ref') assert.ok(typeof t.$value !== 'string' || !t.$value.startsWith('{'), `${t.path.join('.')} é um alias`);
  }
});

const USAGE = ['text', 'icon', 'background', 'border', 'outline', 'line', 'fill', 'shadow', 'text-shadow', 'font', 'theme-color', 'z-index'];

test('todo papel tem descrição e usage da lista', () => {
  for (const t of roles) {
    assert.ok(t.$description, `${t.path.join('.')} sem $description`);
    assert.ok(meta(t).usage?.length, `${t.path.join('.')} sem usage`);
    for (const u of meta(t).usage) assert.ok(USAGE.includes(u), `${t.path.join('.')}: usage "${u}" desconhecido`);
  }
});

test('papéis apontam para a paleta (a ordem de empilhamento é número puro)', () => {
  const isRef = (v) => typeof v === 'string' && /^\{ref\.[^}]+\}$/.test(v);
  for (const t of roles) {
    const key = t.path.join('.');
    if (key.startsWith('ui.layer.')) { assert.equal(typeof t.$value, 'number', key); continue; }
    if (t.$type === 'shadow') { assert.ok(isRef(t.$value.color), `${key}: a cor da sombra vem da paleta`); continue; }
    assert.ok(isRef(t.$value), `${key} = ${JSON.stringify(t.$value)} não aponta para a paleta`);
  }
});

test('nenhum literal de cor fora dos tokens', () => {
  const literal = /(?<![&\w])#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})\b|\b(?:rgba?|hsla?|hwb|oklab|oklch)\(/gi;
  const named = /:\s*[^;{}]*(?<![-\w])(?:white|black|red|green|blue|yellow|orange|purple|pink|gray|grey|teal|cyan)(?![-\w])[^;{}]*;/gi;
  for (const file of SOURCES) {
    let text = withoutData(read(file));
    // O index.html não lê CSS na meta theme-color (conferida abaixo).
    if (file.endsWith('index.html')) text = text.replace(/<meta name="theme-color"[^>]*>/, '');
    const css = file.endsWith('.css');
    if (css) text = text.replace(/\/\*[\s\S]*?\*\//g, (c) => c.replace(/[^\n]/g, ' '));
    const found = text.split('\n').flatMap((line, i) => (line.match(literal) || (css && line.match(named)) ? [`${file}:${i + 1}: ${line.trim().slice(0, 120)}`] : []));
    assert.deepEqual(found, [], 'use um token (docs/DESIGN-VISUAL.md, "Mudar uma cor")');
  }
});

test('nenhum z-index numérico no style.css', () => {
  const found = read('web/style.css').split('\n').flatMap((line, i) => (/z-index:\s*\d/.test(line) ? [`style.css:${i + 1}: ${line.trim()}`] : []));
  assert.deepEqual(found, []);
});

test('o CSS lê só papéis que existem, nunca a paleta nem os nomes curtos', () => {
  const defined = new Set([...read('web/lib/tokens.css').matchAll(/^\s*(--[\w-]+):/gm)].map((m) => m[1]));
  for (const file of SOURCES) {
    for (const [, name] of read(file).matchAll(/var\((--[\w-]+)/g)) {
      assert.ok(!name.startsWith('--ref-'), `${file} lê ${name}: use um papel, nunca a paleta`);
      assert.ok(!(name in PAGE_ALIASES), `${file} lê o nome curto ${name}: use ${PAGE_ALIASES[name]}`);
      assert.ok(defined.has(name) || RUNTIME_VARS.includes(name), `${file} lê ${name}, que nenhum token define`);
    }
  }
});

test('todo caminho tokens.x.y lido pelo app.js existe', () => {
  for (const [, path] of read('web/app.js').matchAll(/\btokens\.((?:map|ui|brand)(?:\.\w+)+)/g)) {
    let o = tokens;
    for (const k of path.split('.')) {
      assert.ok(o && typeof o === 'object' && k in o, `tokens.${path} não existe`);
      o = o[k];
    }
    assert.equal(typeof o, 'string', `tokens.${path} não é um valor`);
  }
});

test('theme-color e o manifesto batem com os tokens de brand', () => {
  const manifest = JSON.parse(read('web/manifest.json'));
  assert.equal(manifest.theme_color, tokens.brand.theme);
  assert.equal(manifest.background_color, tokens.brand.splash);
  assert.equal(read('web/index.html').match(/<meta name="theme-color" content="([^"]+)"/)[1], tokens.brand.theme);
});

// Contraste WCAG 2.x, com translúcidas compostas sobre o que está atrás.
const linear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const luminance = ([r, g, b]) => 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
const over = (top, under) => top.components.map((c, i) => c * (top.alpha ?? 1) + under[i] * (1 - (top.alpha ?? 1)));
const ratio = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

test('os pares de contraste declarados passam; exceções ficam registradas', () => {
  const color = (path) => resolveValue(all, all.get(path).$value);
  const page = color('ui.surface.page').components;
  for (const t of roles) {
    for (const rule of meta(t).contrast ?? []) {
      const bg = over(color(rule.against), page);
      const r = ratio(over(color(t.path.join('.')), bg), bg);
      const where = `${t.path.join('.')} sobre ${rule.against}: ${r.toFixed(2)}:1`;
      if (rule.departure) {
        assert.ok(rule.departure.reason && rule.departure.since, `${where}: exceção precisa de motivo e data`);
        assert.ok(r < rule.min, `${where} já passa: tire a exceção`);
      } else {
        assert.ok(r >= rule.min, `${where}, precisa de ${rule.min}:1`);
      }
    }
  }
});

test('todo recurso gerado está no precache do service worker', () => {
  const sw = read('web/sw.js');
  for (const f of ['./lib/tokens.css', './lib/tokens.js', './lib/icons.js']) assert.ok(sw.includes(`'${f}'`), `${f} fora do SHELL_ASSETS`);
});

const vocabulary = JSON.parse(readFileSync(VOCABULARY, 'utf8'));

test('icons.js e os ícones do index.html estão em dia (rode npm run build:icons)', () => {
  const icons = loadIcons();
  assert.equal(readFileSync(ICONS_JS, 'utf8'), buildIconsJs(icons));
  const html = read('web/index.html');
  assert.equal(html, updateIndexIcons(html, icons));
  assert.ok(!/<i data-icon=/.test(html), 'ainda há <i data-icon>: rode npm run build:icons');
});

test('todo ícone usado está no vocabulário, e todo ícone do vocabulário é usado', () => {
  const html = read('web/index.html');
  const js = read('web/app.js');
  const used = new Set([
    ...[...html.matchAll(/data-icon="([\w-]+)"/g)].map((m) => m[1]),
    ...[...js.matchAll(/uiIcon\('([\w-]+)'/g)].map((m) => m[1]),
    ...[...js.matchAll(/setTopbarLabel\(\w+, '([\w-]+)'/g)].map((m) => m[1]),
    ...[...js.matchAll(/uiIcon\(\w+ \? '([\w-]+)' : '([\w-]+)'\)/g)].flatMap((m) => [m[1], m[2]]),
  ]);
  for (const name of used) assert.ok(vocabulary.icons[name], `"${name}" não está no vocabulário`);
  for (const name of Object.keys(vocabulary.icons)) assert.ok(used.has(name), `"${name}" está no vocabulário e ninguém usa`);
});

test('nenhum emoji ou glifo como ícone nos botões do index.html', () => {
  const glyph = /[\u{1F300}-\u{1FAFF}\u2600-\u27BF\u2B00-\u2BFF\u25A0-\u25FF\u2300-\u23FF\u21B0-\u21FF]/u;
  const html = read('web/index.html').replace(/<!--[\s\S]*?-->/g, '').replace(/<svg[\s\S]*?<\/svg>/g, '');
  const found = [...html.matchAll(/<button\b[^>]*>([\s\S]*?)<\/button>/g)].filter((m) => glyph.test(m[1])).map((m) => m[0].slice(0, 100));
  assert.deepEqual(found, [], 'use um ícone do vocabulário (docs/DESIGN-VISUAL.md, "Ícones")');
});
