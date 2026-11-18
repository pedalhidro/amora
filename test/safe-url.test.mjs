// safeUrl — a checagem que decide se uma URL do catálogo pode virar href/src.
// O catálogo é escrito sem auth, então é ela que impede um `javascript:` ou
// `data:` gravado no link de uma pessoa ou de um passeio de virar link
// clicável. Existe em três lugares, que têm que concordar:
//   web/lib/utils.js      (pessoas.html, imagens.html)
//   web/memoria.html      (script clássico: cópia própria)
//   backend/mdhtml.py     (o HTML gerado no servidor — test/test_mdhtml.py)
// Os três leem os mesmos casos de test/safe-url-cases.json.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const root = new URL('..', import.meta.url);
const cases = JSON.parse(readFileSync(new URL('test/safe-url-cases.json', root), 'utf8'));

// A função é tirada do FONTE (o lib/utils.js usa `window` ao ser importado,
// e o memoria.html é uma página): é o que o navegador vai rodar.
function safeUrlFrom(file) {
  const src = readFileSync(new URL(file, root), 'utf8');
  const m = /function safeUrl\(url\) \{[\s\S]*?\n\}/.exec(src);
  assert.ok(m, `${file} tem a sua function safeUrl`);
  return new Function(`${m[0]}; return safeUrl;`)();
}

function check(fn, name) {
  for (const [url, ok] of cases) {
    const got = fn(url);
    assert.equal(got !== null, ok, `${name}(${JSON.stringify(url)}) → ${JSON.stringify(got)}`);
    if (ok) assert.equal(got, url.trim(), `${name} devolve a própria URL, sem o espaço em volta`);
  }
  assert.equal(fn(null), null);
  assert.equal(fn(undefined), null);
}

test('safeUrl (lib/utils.js) aceita só relativa, http(s) e mailto', () => {
  check(safeUrlFrom('web/lib/utils.js'), 'safeUrl');
});

test('a cópia do memoria.html decide igual', () => {
  check(safeUrlFrom('web/memoria.html'), 'memoria.safeUrl');
});

test('as páginas que montam link com dado do catálogo usam safeUrl', () => {
  for (const page of ['pessoas.html', 'imagens.html', 'memoria.html']) {
    const html = readFileSync(new URL(`web/${page}`, root), 'utf8');
    assert.match(html, /safeUrl\(/, `${page} chama safeUrl`);
  }
});
