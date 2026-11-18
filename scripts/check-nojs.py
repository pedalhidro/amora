#!/usr/bin/env python3
"""Confere que o acervo chega no HTML pra quem NÃO roda JavaScript.

Buscadores, bots de preview e os leitores de página dos LLMs pedem text/html e
não executam scripts. Este script faz o mesmo com uma URL de cada tipo — home,
passeio, Memória, série, galeria, álbum, mídia, pessoas, pessoa, censo, rota
salva —, joga fora <script>/<style> e o que sobra tem que ser o CONTEÚDO da
página: o mesmo título da representação Markdown, texto de verdade, e nenhum
"Carregando…" que nunca termina. Ver "Conteúdo sem JavaScript" no CLAUDE.md.

    python3 scripts/check-nojs.py                         # produção
    python3 scripts/check-nojs.py http://127.0.0.1:8000   # backend local

As URLs de exemplo são descobertas no próprio site (sitemap, índices em
Markdown, /saved-routes). Só leitura; sem dependências. Sai com 1 se alguma
página falhar."""
import html
import json
import re
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://amora.pedalhidrografi.co").rstrip("/")
UA = "amora-check-nojs/1 (+https://amora.pedalhidrografi.co/llms.txt)"


def get(path, accept="text/html,application/xhtml+xml,*/*;q=0.8"):
    """(status, url final, corpo) — segue redirects, como um crawler."""
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, BASE + path, ""


def visible_text(page):
    """O texto que sobra sem scripts, estilos e marcação — o que um conversor
    HTML→texto entrega pro modelo."""
    page = re.sub(r"(?is)<(script|style|template|noscript|svg|head)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return " ".join(html.unescape(page).split())


def md_title(path):
    """O título (# …) da representação Markdown da página, sem a marcação."""
    _, _, md = get(path + ("&" if "?" in path else "?") + "format=md", accept="text/markdown")
    m = re.search(r"^# (.+)$", md, re.M)
    title = m.group(1) if m else ""
    return re.sub(r"[`*\\]", "", title).strip(), md


def first(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None


def discover():
    """Uma URL de cada tipo, tirada do próprio site."""
    pages = [("home", "/"), ("Memória", "/memoria"), ("galeria", "/imagens.html"),
             ("pessoas", "/pessoas.html"), ("censo", "/censo.html")]
    _, _, sitemap = get("/sitemap.xml", accept="application/xml")
    tour = first(r"<loc>[^<]*?(/passeio/[^<]+)</loc>", sitemap)
    serie = first(r"<loc>[^<]*?(/serie/[^<]+)</loc>", sitemap)
    _, _, people = get("/pessoas.html?format=md", accept="text/markdown")
    person = first(r"\((?:https?://[^/)]+)?(/pessoas/[0-9a-z]{8})\)", people)
    _, _, gallery = get("/imagens.html?format=md", accept="text/markdown")
    album = first(r"\((?:https?://[^/)]+)?(/imagens/lista/[^)]+)\)", gallery)
    media = None
    if album:
        _, _, album_md = get(album + "?format=md", accept="text/markdown")
        media = first(r"\((?:https?://[^/)]+)?(/midia/[0-9a-f]{16})\)", album_md)
    route = None
    try:
        routes = json.loads(get("/saved-routes", accept="application/json")[2]).get("routes", [])
        route = next((f"/route/{r['slug']}" for r in routes if r.get("slug")), None)
    except (ValueError, AttributeError):
        pass
    for label, path in (("passeio", tour), ("série", serie), ("pessoa", person),
                        ("álbum", album), ("mídia", media), ("rota salva", route)):
        if path:
            pages.append((label, path))
        else:
            print(f"  (sem exemplo de {label} neste site — pulando)")
    return pages


def main():
    print(f"Sem JavaScript, em {BASE}:\n")
    failed = 0
    for label, path in discover():
        status, final, page = get(path)
        text = visible_text(page)
        title, md = md_title(path)
        problems = []
        if status != 200:
            problems.append(f"HTTP {status}")
        if label == "home":
            # Em Markdown a home abre com o llms.txt (guia pra agentes); em HTML,
            # com a apresentação. O que as duas têm em comum são as listas.
            if "Passeios recentes" not in text:
                problems.append("a lista de passeios recentes não está no HTML")
        elif title and title not in text:
            problems.append(f"o título da página não está no HTML: “{title[:50]}”")
        if "Carregando" in text:
            problems.append("o texto ainda tem um “Carregando…”")
        if len(text) < 80:
            problems.append(f"só {len(text)} caracteres de texto")
        links = len(re.findall(r"(?i)<a\s[^>]*href=", page))
        where = "" if final.rstrip("/") == (BASE + path).rstrip("/") else f" → {final[len(BASE):]}"
        print(f"{'FALHOU' if problems else 'ok    '} {label:10s} {path[:56]}{where}")
        print(f"         {len(text)} caracteres de texto · {links} links · começa com: "
              f"{text[:70]!r}")
        for p in problems:
            print(f"         ✗ {p}")
        failed += bool(problems)
    print(f"\n{'HÁ PÁGINAS SEM CONTEÚDO' if failed else 'Todas as páginas trazem o conteúdo no HTML.'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
