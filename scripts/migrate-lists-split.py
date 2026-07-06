#!/usr/bin/env python3
"""One-shot (idempotente): separa as listas/álbuns (schema:Collection) de
web/data/images.ttl para um catálogo próprio web/data/lists.ttl, renomeando os
IRIs de `phd:list_<slug>` (https://pedalhidrografi.co/data/list_<slug>) para
`lst:<slug>` (https://id.pedalhidrografi.co/listas/<slug>).

Preserva EXATAMENTE o pertencimento atual (as arestas schema:isPartOf são só
reapontadas pro novo IRI; nenhuma mídia é adicionada/removida de nenhuma lista).
A completude da lista "Padrão" (hoje parcial) é uma decisão de produto à parte —
este script não a toca.

Faz, de forma idempotente:
  1. Coleta todo sujeito `a schema:Collection` em images.ttl cujo IRI começa com
     phd:list_ (ou já com lst:, em re-execução).
  2. Escreve cada um em lists.ttl como lst:<slug> (upsert).
  3. Remove as declarações de Collection de images.ttl.
  4. Reaponta `schema:isPartOf phd:list_<slug>` → `lst:<slug>` nas mídias.

Round-trip de estado (images.ttl é bucket-first; lists.ttl passa a ser):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-lists-split.py
    scripts/deploy-cloudrun.sh --state-only   # (guardado)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef, Literal

PHD = Namespace("https://pedalhidrografi.co/data/")
LST = Namespace("https://id.pedalhidrografi.co/listas/")
SCHEMA = Namespace("https://schema.org/")

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "web" / "data" / "images.ttl"
LISTS = REPO / "web" / "data" / "lists.ttl"

OLD_LIST_PREFIX = str(PHD) + "list_"


def new_iri(old):
    """phd:list_<slug> → lst:<slug>; lst:<slug> fica igual (idempotência)."""
    s = str(old)
    if s.startswith(OLD_LIST_PREFIX):
        return URIRef(str(LST) + s[len(OLD_LIST_PREFIX):])
    return old  # já migrado


def main() -> int:
    gi = Graph()
    gi.parse(IMAGES, format="turtle")
    before = len(gi)

    # Coleta Collections de images.ttl (phd:list_* — e lst:* se re-execução).
    colls = {s for s in gi.subjects(RDF.type, SCHEMA.Collection)
             if isinstance(s, URIRef)
             and (str(s).startswith(OLD_LIST_PREFIX) or str(s).startswith(str(LST)))}

    gl = Graph()
    if LISTS.exists():
        gl.parse(LISTS, format="turtle")

    # 1+2) move cada Collection pra lists.ttl com o novo IRI (upsert).
    moved = 0
    for c in sorted(colls, key=str):
        ni = new_iri(c)
        # limpa def anterior no destino (upsert)
        for s, p, o in list(gl.triples((ni, None, None))):
            gl.remove((s, p, o))
        for s, p, o in gi.triples((c, None, None)):
            gl.add((ni, p, o))
        moved += 1

    # 3) remove as Collections de images.ttl.
    for c in colls:
        for t in list(gi.triples((c, None, None))):
            gi.remove(t)

    # 4) reaponta schema:isPartOf pro novo IRI.
    rewired = 0
    for s, o in list(gi.subject_objects(SCHEMA.isPartOf)):
        ni = new_iri(o)
        if ni != o:
            gi.remove((s, SCHEMA.isPartOf, o))
            gi.add((s, SCHEMA.isPartOf, ni))
            rewired += 1

    print(f"Collections movidas p/ lists.ttl: {moved} | isPartOf reapontadas: {rewired}")
    for c in sorted(colls, key=str):
        members = sum(1 for _ in gi.subjects(SCHEMA.isPartOf, new_iri(c)))
        print(f"  {new_iri(c)}  ({members} membros)")

    if moved == 0 and rewired == 0:
        print("nada a fazer — já migrado.")
        return 0

    gl.bind("lst", LST)
    gl.bind("schema", SCHEMA)
    gl.serialize(destination=LISTS, format="turtle")
    gi.serialize(destination=IMAGES, format="turtle")
    print(f"images.ttl: {before} → {len(gi)} triples | lists.ttl: {len(gl)} triples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
