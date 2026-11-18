"""Markdown → HTML, só o subconjunto que o próprio backend escreve.

Cada página do amora tem UM renderer de conteúdo, em Markdown (ver os
`_render_*_markdown` em main.py). Esse Markdown sai de dois jeitos:

  - cru, pra quem pede `Accept: text/markdown` (agentes);
  - convertido por aqui e injetado no HTML da página, pra quem não roda
    JavaScript — crawlers de busca, bots de preview e os leitores de página
    dos LLMs, que pedem `text/html` e recebiam só o esqueleto do app.

Uma fonte só: o que o agente lê em Markdown é o que o crawler lê em HTML.

NÃO é um Markdown geral. Cobre o que os renderers emitem — títulos, parágrafos,
listas de um nível, citações, tabelas de pipe; e, na linha: links, imagens,
`código`, **negrito**, <autolinks> e escapes com barra invertida.

Segurança: o texto do catálogo é escrito por qualquer pessoa (o backend não tem
auth) e os renderers o interpolam SEM escapar. Então tudo o que sai daqui é
escapado, nenhum HTML de entrada sobrevive, e URL com esquema que não seja
http(s)/mailto (javascript:, data:, …) vira texto. Sem dependências.
"""
import re
from html import escape

_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
_SAFE_SCHEME_RE = re.compile(r"^(?:https?|mailto):", re.I)
_BAD_URL_CHARS_RE = re.compile(r"[\x00-\x20\x7f<>\"'`\\]")


def safe_url(url):
    """A URL, se pode ir num href/src; senão None. Relativa passa; com esquema,
    só http, https e mailto."""
    url = (url or "").strip()
    if not url or _BAD_URL_CHARS_RE.search(url):
        return None
    if _SCHEME_RE.match(url) and not _SAFE_SCHEME_RE.match(url):
        return None
    return url


def md_escape(text):
    """Texto do catálogo pra dentro de um rótulo de link ou célula de tabela:
    escapa o que quebraria a sintaxe ao redor (`[`, `]`, `|`, barra invertida)."""
    return re.sub(r"([\\\[\]|])", r"\\\1", str(text or ""))


# Um token de linha por alternativa, na ordem de precedência.
_INLINE_RE = re.compile(
    r"\\(?P<esc>[\\`*_\[\]()<>#|!\-])"
    r"|`(?P<code>[^`\n]+)`"
    r"|!\[(?P<alt>(?:\\.|[^\]\\])*)\]\((?P<src>[^)\s]+)\)"
    # O rótulo de um link aceita uma imagem dentro: [![alt](src)](href).
    r"|\[(?P<label>(?:!\[(?:\\.|[^\]\\])*\]\([^)\s]+\)|\\.|[^\]\\])*)\]\((?P<href>[^)\s]+)\)"
    r"|<(?P<auto>(?:https?://|mailto:)[^>\s]+)>"
    r"|\*\*(?P<bold>(?:\\.|[^*\\]|\*(?!\*))+)\*\*"
)
_UNESCAPE_RE = re.compile(r"\\([\\`*_\[\]()<>#|!\-])")


def _plain(text):
    """Texto de um alt: sem os escapes de Markdown."""
    return _UNESCAPE_RE.sub(r"\1", text)


def inline(text, rewrite_url=None):
    """Uma linha de Markdown → HTML de linha (escapado)."""
    fix = rewrite_url or (lambda u: u)
    out, pos = [], 0
    for m in _INLINE_RE.finditer(text):
        out.append(escape(text[pos:m.start()]))
        pos = m.end()
        if m.group("esc") is not None:
            out.append(escape(m.group("esc")))
        elif m.group("code") is not None:
            out.append(f"<code>{escape(m.group('code'))}</code>")
        elif m.group("src") is not None:
            src = safe_url(m.group("src"))
            alt = _plain(m.group("alt"))
            out.append(f'<img src="{escape(fix(src))}" alt="{escape(alt)}" '
                       'loading="lazy" decoding="async">' if src else escape(alt))
        elif m.group("href") is not None:
            href = safe_url(m.group("href"))
            label = inline(m.group("label"), rewrite_url)
            out.append(f'<a href="{escape(fix(href))}">{label}</a>' if href else label)
        elif m.group("auto") is not None:
            href = safe_url(m.group("auto"))
            shown = escape(m.group("auto"))
            out.append(f'<a href="{escape(fix(href))}">{shown}</a>' if href else shown)
        else:
            out.append(f"<strong>{inline(m.group('bold'), rewrite_url)}</strong>")
    out.append(escape(text[pos:]))
    return "".join(out)


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_ITEM_RE = re.compile(r"^\s{0,3}[-*]\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip() for c in _CELL_SPLIT_RE.split(line)]


def _starts_block(line):
    return bool(_HEADING_RE.match(line) or _ITEM_RE.match(line)
                or _QUOTE_RE.match(line) or line.lstrip().startswith("|"))


def md_to_html(md, rewrite_url=None, heading_offset=0):
    """Markdown (o subconjunto do backend) → HTML de bloco. `rewrite_url`
    reescreve cada URL já validada (ex.: absoluta do próprio site → relativa);
    `heading_offset` rebaixa os títulos (1 = `#` vira <h2>) quando o bloco
    entra numa página que já tem o seu <h1>."""
    def il(s):
        return inline(s, rewrite_url)

    lines = str(md or "").replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = _HEADING_RE.match(line)
        if m:
            level = min(6, len(m.group(1)) + heading_offset)
            out.append(f"<h{level}>{il(m.group(2))}</h{level}>")
            i += 1
            continue
        if _ITEM_RE.match(line):
            items = []
            while i < n:
                m = _ITEM_RE.match(lines[i])
                if m:
                    items.append([m.group(1)])
                    i += 1
                # Linha de continuação do item (o llms.txt quebra as linhas).
                elif lines[i].strip() and not _starts_block(lines[i]):
                    items[-1].append(lines[i].strip())
                    i += 1
                else:
                    break
            out.append("<ul>\n" + "\n".join(
                f"<li>{il(' '.join(parts))}</li>" for parts in items) + "\n</ul>")
            continue
        if _QUOTE_RE.match(line):
            parts = []
            while i < n and _QUOTE_RE.match(lines[i]):
                parts.append(_QUOTE_RE.match(lines[i]).group(1).strip())
                i += 1
            out.append(f"<blockquote><p>{il(' '.join(p for p in parts if p))}</p></blockquote>")
            continue
        if (line.lstrip().startswith("|") and i + 1 < n
                and _TABLE_SEP_RE.match(lines[i + 1])):
            head = _cells(line)
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            html = ["<table>", "<thead><tr>"
                    + "".join(f"<th>{il(c)}</th>" for c in head) + "</tr></thead>", "<tbody>"]
            for r in rows:
                r = (r + [""] * len(head))[:len(head)]
                html.append("<tr>" + "".join(f"<td>{il(c)}</td>" for c in r) + "</tr>")
            html += ["</tbody>", "</table>"]
            out.append("\n".join(html))
            continue
        parts = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not _starts_block(lines[i]):
            parts.append(lines[i].strip())
            i += 1
        out.append(f"<p>{il(' '.join(parts))}</p>")
    return "\n".join(out)
