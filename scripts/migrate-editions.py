#!/usr/bin/env python3
"""One-shot (idempotente): converte as FILIAÇÕES de série (ex-ph:Association,
`phd:assoc_<ES>_<n>`) em EDIÇÕES de série com IRI própria e resolvível:

    phd:assoc_<ES>_<n>  a ph:Association   →   <…/passeio/<ES>/<n>>  a ph:SeriesEdition

O IRI da edição usa o path /passeio/<ES>/<seq> (o `/` impede CURIE — vira IRI
completa). A classe passa a ser ph:SeriesEdition (ex-ph:Association).

Resolve a COLISÃO assoc_BP_4 (compartilhada por tour_87 e tour_95 — dois pedais
ambos chamados "BP 4"): tour_95 fica com …/passeio/BP/4 (seq 4); tour_87 ganha
uma edição distinta …/passeio/BP/3-5 (seq AINDA 4 — a duplicata é intencional,
foi uma colisão de numeração). Cada edição passa a ser realizada por EXATAMENTE
um passeio (SHACL cuida disso).

Só mexe em tours.ttl (as edições moram lá). Idempotente: se já não há
phd:assoc_*, não faz nada.

Round-trip (tours.ttl é bucket-first):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-editions.py
    scripts/deploy-cloudrun.sh --state-only   # (guardado)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef, Literal

PHD = "https://pedalhidrografi.co/data/"
PAS = "https://id.pedalhidrografi.co/passeio/"
SER = "https://id.pedalhidrografi.co/serie/"
PH = Namespace("https://id.pedalhidrografi.co/terms#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

REPO = Path(__file__).resolve().parent.parent
TOURS = REPO / "web" / "data" / "tours.ttl"
IRI_MAP = REPO / "web" / "data" / "tour-iri-map.json"

ASSOC_PREFIX = PHD + "assoc_"


def edition_iri(es, seq):
    return URIRef(f"{PAS}{es}/{seq}")


def main() -> int:
    g = Graph()
    g.parse(TOURS, format="turtle")

    assocs = [s for s in g.subjects(RDF.type, PH.Association)
              if str(s).startswith(ASSOC_PREFIX)]
    if not assocs:
        print("nada a fazer — nenhum phd:assoc_* (já migrado?).")
        return 0

    by_old = json.loads(IRI_MAP.read_text())["byOldId"]
    # slug do tour_87 (recebe a edição desambiguada BP/3-5).
    slug_87 = by_old.get("87")
    tour_87 = URIRef(PAS + slug_87) if slug_87 else None

    # 1) Mapa assoc_<ES>_<n> → edição <…/passeio/<ES>/<n>>.
    edition_of = {}
    for a in assocs:
        rest = str(a)[len(ASSOC_PREFIX):]         # "BP_4", "SESC_1"
        es, _, seq = rest.rpartition("_")          # rpartition: último "_" separa o n
        edition_of[a] = edition_iri(es, seq)

    changed = 0
    # 2) Reescreve cada nó de filiação → edição (sujeito + classe + triples).
    for a, ed in edition_of.items():
        for _, p, o in list(g.triples((a, None, None))):
            g.remove((a, p, o))
            # ph:Association → ph:SeriesEdition
            if p == RDF.type and o == PH.Association:
                g.add((ed, RDF.type, PH.SeriesEdition))
            else:
                g.add((ed, p, o))
            changed += 1
    # 3) Atualiza as arestas tour → filiação (ph:inSeriesEdition).
    for s, o in list(g.subject_objects(PH.inSeriesEdition)):
        if o in edition_of:
            g.remove((s, PH.inSeriesEdition, o))
            g.add((s, PH.inSeriesEdition, edition_of[o]))
            changed += 1

    # 4) SPLIT da colisão BP_4: tour_87 deixa de apontar BP/4 e ganha BP/3-5.
    bp4 = edition_iri("BP", "4")
    bp35 = edition_iri("BP", "3-5")
    split_done = False
    if tour_87 is not None and (tour_87, PH.inSeriesEdition, bp4) in g:
        g.remove((tour_87, PH.inSeriesEdition, bp4))
        g.add((tour_87, PH.inSeriesEdition, bp35))
        # nova edição, seq AINDA 4 (duplicata intencional)
        g.add((bp35, RDF.type, PH.SeriesEdition))
        g.add((bp35, PH.inEventSeries, URIRef(SER + "BP")))
        g.add((bp35, PH.sequenceInSeries, Literal("4", datatype=XSD.positiveInteger)))
        split_done = True

    g.bind("pas", PAS)
    g.bind("ser", SER)

    # Sanidade: cada edição realizada por exatamente 1 passeio?
    from collections import Counter
    realizers = Counter()
    for s, o in g.subject_objects(PH.inSeriesEdition):
        realizers[o] += 1
    shared = {str(k): v for k, v in realizers.items() if v > 1}
    leftover = [str(s) for s in g.subjects(RDF.type, PH.Association) if str(s).startswith(ASSOC_PREFIX)]

    print(f"edições: {len(edition_of)} | triples reescritas: {changed} | split BP_4: {split_done}")
    print(f"resíduo ph:Association: {len(leftover)} | edições c/ >1 passeio: {shared or 'nenhuma ✓'}")
    if leftover or shared:
        print("  ⚠ inconsistência — abortando sem gravar.")
        return 1

    g.serialize(destination=TOURS, format="turtle")
    print(f"tours.ttl reescrito ({len(g)} triples).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
