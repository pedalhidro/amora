#!/usr/bin/env python3
"""One-shot migração: IRIs de pessoa opacas + resolvíveis.

Renomeia toda pessoa de `phd:pessoa<Slug>`
(`https://pedalhidrografi.co/data/pessoa<Slug>`) para um IRI OPACO e estável no
namespace de identidade neutro:

    https://id.pedalhidrografi.co/pessoas/<slug8>

onde `<slug8>` é um id aleatório de 8 chars (base32 Crockford, sem i/l/o/u),
mintado UMA vez e congelado — nunca derivado do handle editável. A parte legível
do nome vive em schema:name / schema:alternateName.

Também injeta `schema:mainEntityOfPage` apontando pra página humana servida pelo
amora (`https://amora.pedalhidrografi.co/pessoas/<slug8>`).

A associação old→new fica em `scripts/person-iri-map.json` (commitada) pra a
migração ser REPRODUTÍVEL: rodar em prod usa os MESMOS slugs do seed commitado;
pessoas que só existem em prod ganham slug novo e são anexadas ao mapa.

Roda sobre os 3 catálogos já separados (identities/tours/images) e reescreve
todas as referências (sujeito E objeto). Idempotente: se não há mais
`phd:pessoa*`, é no-op.

    python scripts/migrate-person-iris.py --dry-run
    python scripts/migrate-person-iris.py
"""
import argparse
import json
import secrets
import sys
from pathlib import Path

from rdflib import Graph, RDF, URIRef, Namespace

PHD = "https://pedalhidrografi.co/data/"
PES = "https://id.pedalhidrografi.co/pessoas/"
PAGE_BASE = "https://amora.pedalhidrografi.co/pessoas/"
SCHEMA = Namespace("https://schema.org/")
MAIN_ENTITY_OF_PAGE = URIRef(SCHEMA + "mainEntityOfPage")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "data"
MAP_PATH = Path(__file__).resolve().parent / "person-iri-map.json"
CATALOGS = ("identities.ttl", "tours.ttl", "images.ttl")

# Crockford base32 (sem i, l, o, u — evita ambiguidade visual).
_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
PERSON_PREFIX = PHD + "pessoa"


def rand_slug(n=8):
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


def load_map():
    if MAP_PATH.exists():
        return json.loads(MAP_PATH.read_text())
    return {}


def collect_persons():
    """IRIs phd:pessoa* que aparecem em qualquer catálogo (sujeito ou objeto)."""
    persons = set()
    for name in CATALOGS:
        p = DATA_DIR / name
        if not p.exists():
            continue
        g = Graph()
        g.parse(str(p), format="turtle")
        for s, _pred, o in g:
            for term in (s, o):
                if isinstance(term, URIRef) and str(term).startswith(PERSON_PREFIX):
                    persons.add(str(term))
    return persons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    persons = collect_persons()
    if not persons:
        print("Nenhuma pessoa phd:pessoa* encontrada — migração já feita (no-op).")
        return 0

    iri_map = load_map()          # old_iri -> new_iri (persistido)
    used_slugs = {v.rsplit("/", 1)[-1] for v in iri_map.values()}
    new_assignments = 0
    for old in sorted(persons):
        if old in iri_map:
            continue
        slug = rand_slug()
        while slug in used_slugs:
            slug = rand_slug()
        used_slugs.add(slug)
        iri_map[old] = PES + slug
        new_assignments += 1

    print(f"pessoas a renomear: {len(persons)}  "
          f"(novos slugs mintados agora: {new_assignments}; "
          f"do mapa existente: {len(persons) - new_assignments})")

    # Reescreve os 3 catálogos aplicando o mapa (sujeito + objeto) e injeta
    # schema:mainEntityOfPage em cada pessoa (só no identities.ttl, onde ela é
    # definida).
    rewrites = {URIRef(k): URIRef(v) for k, v in iri_map.items()}
    changed_files = []
    for name in CATALOGS:
        p = DATA_DIR / name
        if not p.exists():
            continue
        g = Graph()
        g.parse(str(p), format="turtle")
        out = Graph()
        for pfx, ns in g.namespaces():
            out.bind(pfx, ns)
        out.bind("pes", PES)
        n_ref = 0
        for s, pred, o in g:
            ns_, np_, no_ = rewrites.get(s, s), pred, rewrites.get(o, o)
            if ns_ is not s or no_ is not o:
                n_ref += 1
            out.add((ns_, np_, no_))
        # mainEntityOfPage por pessoa definida neste arquivo.
        n_page = 0
        for person in set(out.subjects(RDF.type, URIRef(SCHEMA + "Person"))) | \
                set(out.subjects(RDF.type, URIRef("http://schema.org/Person"))):
            if not str(person).startswith(PES):
                continue
            slug = str(person).rsplit("/", 1)[-1]
            page = URIRef(PAGE_BASE + slug)
            if (person, MAIN_ENTITY_OF_PAGE, page) not in out:
                out.add((person, MAIN_ENTITY_OF_PAGE, page))
                n_page += 1
        if n_ref or n_page:
            changed_files.append((name, out, n_ref, n_page))
            print(f"  {name}: {n_ref} referência(s) reescrita(s), "
                  f"{n_page} mainEntityOfPage adicionada(s)")

    # Invariante: nenhum phd:pessoa* restante nos grafos de saída.
    for name, out, _r, _p in changed_files:
        leftover = [str(t) for t in set(out.all_nodes())
                    if isinstance(t, URIRef) and str(t).startswith(PERSON_PREFIX)]
        assert not leftover, f"{name}: sobraram phd:pessoa* → {leftover[:3]}"

    if args.dry_run:
        print("\n[dry-run] nada escrito (nem o mapa).")
        return 0

    MAP_PATH.write_text(json.dumps(iri_map, indent=2, ensure_ascii=False) + "\n")
    for name, out, _r, _p in changed_files:
        (DATA_DIR / name).write_text(out.serialize(format="turtle"))
    print(f"\nescrito: {[n for n, *_ in changed_files]} + {MAP_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
