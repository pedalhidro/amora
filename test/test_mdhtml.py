"""Testes do backend/mdhtml.py — o conversor Markdown → HTML que põe o conteúdo
de cada página no HTML pra quem não roda JavaScript. O que mais importa aqui é
a segurança: o texto do catálogo é escrito sem auth e chega cru no Markdown,
então nada dele pode virar marcação, atributo ou link com esquema perigoso.

    python3 test/test_mdhtml.py

Sem dependências (o 
> test
> node --test "test/*.test.mjs"

TAP version 13
# (node:4621) [MODULE_TYPELESS_PACKAGE_JSON] Warning: Module type of file:///home/user/amora/web/lib/tokens.js is not specified and it doesn't parse as CommonJS.
# Reparsing as ES module because module syntax was detected. This incurs a performance overhead.
# To eliminate this warning, add "type": "module" to /home/user/amora/package.json.
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: tokens.css, tokens.js e as tabelas do documento estão em dia (rode npm run build:tokens)
ok 1 - tokens.css, tokens.js e as tabelas do documento estão em dia (rode npm run build:tokens)
  ---
  duration_ms: 5.606617
  type: 'test'
  ...
# Subtest: ref é a paleta: sem aliases
ok 2 - ref é a paleta: sem aliases
  ---
  duration_ms: 0.256029
  type: 'test'
  ...
# Subtest: todo papel tem descrição e usage da lista
ok 3 - todo papel tem descrição e usage da lista
  ---
  duration_ms: 0.532985
  type: 'test'
  ...
# Subtest: papéis apontam para a paleta (a ordem de empilhamento é número puro)
ok 4 - papéis apontam para a paleta (a ordem de empilhamento é número puro)
  ---
  duration_ms: 0.312413
  type: 'test'
  ...
# Subtest: nenhum literal de cor fora dos tokens
ok 5 - nenhum literal de cor fora dos tokens
  ---
  duration_ms: 16.049628
  type: 'test'
  ...
# Subtest: nenhum z-index numérico no style.css
ok 6 - nenhum z-index numérico no style.css
  ---
  duration_ms: 1.267248
  type: 'test'
  ...
# Subtest: o CSS lê só papéis que existem, nunca a paleta nem os nomes curtos
ok 7 - o CSS lê só papéis que existem, nunca a paleta nem os nomes curtos
  ---
  duration_ms: 5.564735
  type: 'test'
  ...
# Subtest: todo caminho tokens.x.y lido pelo app.js existe
ok 8 - todo caminho tokens.x.y lido pelo app.js existe
  ---
  duration_ms: 3.149464
  type: 'test'
  ...
# Subtest: theme-color e o manifesto batem com os tokens de brand
ok 9 - theme-color e o manifesto batem com os tokens de brand
  ---
  duration_ms: 0.596043
  type: 'test'
  ...
# Subtest: os pares de contraste declarados passam; exceções ficam registradas
ok 10 - os pares de contraste declarados passam; exceções ficam registradas
  ---
  duration_ms: 0.744552
  type: 'test'
  ...
# Subtest: todo recurso gerado está no precache do service worker
ok 11 - todo recurso gerado está no precache do service worker
  ---
  duration_ms: 0.240474
  type: 'test'
  ...
# Subtest: icons.js e os ícones do index.html estão em dia (rode npm run build:icons)
ok 12 - icons.js e os ícones do index.html estão em dia (rode npm run build:icons)
  ---
  duration_ms: 2.961383
  type: 'test'
  ...
# Subtest: todo ícone usado está no vocabulário, e todo ícone do vocabulário é usado
ok 13 - todo ícone usado está no vocabulário, e todo ícone do vocabulário é usado
  ---
  duration_ms: 4.009742
  type: 'test'
  ...
# Subtest: nenhum emoji ou glifo como ícone nos botões do index.html
ok 14 - nenhum emoji ou glifo como ícone nos botões do index.html
  ---
  duration_ms: 0.810861
  type: 'test'
  ...
1..14
# tests 14
# suites 0
# pass 14
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 106.45452 cobre só os .mjs de design)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from mdhtml import md_to_html, inline, safe_url, md_escape  # noqa: E402


def eq(a, b):
    assert a == b, f"\n got: {a!r}\nwant: {b!r}"
eq(inline("a <b> & \"c\""), "a &lt;b&gt; &amp; &quot;c&quot;")
eq(inline("[x](https://a.b/c?d=1&e=2)"), '<a href="https://a.b/c?d=1&amp;e=2">x</a>')
eq(inline("[x](javascript:alert(1))"), 'x)')           # esquema recusado: vira texto
eq(inline("[x](JaVaScRiPt:alert`1`)"), 'x')
eq(inline("![a\"b](data:text/html,x)"), 'a&quot;b')
eq(inline("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;")
eq(inline("<https://x.y/z>"), '<a href="https://x.y/z">https://x.y/z</a>')
eq(inline("<javascript:x>"), "&lt;javascript:x&gt;")
eq(inline("**Data:** `2026` e **[n](/p)**"), '<strong>Data:</strong> <code>2026</code> e <strong><a href="/p">n</a></strong>')
eq(inline("[![foto \\[1\\]](/t.jpg)](/midia/abc)"),
   '<a href="/midia/abc"><img src="/t.jpg" alt="foto [1]" loading="lazy" decoding="async"></a>')
eq(inline("[" + md_escape("PH 1 [especial] | x") + "](/p)"), '<a href="/p">PH 1 [especial] | x</a>')
eq(inline('[x](/a"onmouseover="1)'), 'x')
eq(inline("adutora_de_cotia * 2 * 3"), "adutora_de_cotia * 2 * 3")
eq(inline("[x](https://s/a)", lambda u: u.replace("https://s", "")), '<a href="/a">x</a>')
assert safe_url("//evil.example/x") == "//evil.example/x" and safe_url(" vbscript:x") is None
assert safe_url("/a b") is None and safe_url("x\njavascript:1") is None
eq(md_to_html("# T\n\ntexto um\nlinha dois\n\n- a\n  cont\n- b\n\n> q1\n> q2\n\n## H #\n"),
   "<h1>T</h1>\n<p>texto um linha dois</p>\n<ul>\n<li>a cont</li>\n<li>b</li>\n</ul>\n"
   "<blockquote><p>q1 q2</p></blockquote>\n<h2>H</h2>")
eq(md_to_html("| a | b |\n|---|---|\n| 1 | x\\|y |\n| 2 |\n"),
   "<table>\n<thead><tr><th>a</th><th>b</th></tr></thead>\n<tbody>\n"
   "<tr><td>1</td><td>x|y</td></tr>\n<tr><td>2</td><td></td></tr>\n</tbody>\n</table>")
eq(md_to_html("# T", heading_offset=1), "<h2>T</h2>")
eq(md_to_html("<img src=x onerror=alert(1)>\n\n</article><script>1</script>"),
   "<p>&lt;img src=x onerror=alert(1)&gt;</p>\n<p>&lt;/article&gt;&lt;script&gt;1&lt;/script&gt;</p>")
# o llms.txt inteiro converte sem deixar markup cru
h = md_to_html((ROOT / 'web' / 'llms.txt').read_text(encoding='utf-8'))
assert "<h1>amora" in h and h.count("<li>") > 15 and "<blockquote>" in h
assert not re.search(r"<(?!/?(?:h[1-6]|p|ul|li|a|code|strong|blockquote|img|table|thead|tbody|tr|th|td)\b)", h), "tag inesperada"
print("mdhtml ok")
