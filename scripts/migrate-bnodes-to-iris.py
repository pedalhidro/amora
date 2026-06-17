#!/usr/bin/env python
"""One-off: converte os blank nodes de tours.ttl e uploads.ttl em IRIs
derivadas determinísticas `phd:<pai>_<papel>`, pra que a deleção/merge no
backend deixe de precisar percorrer bnodes alcançáveis a partir do sujeito.

Antes:
    phd:tour_1 ph:energyEstimate [ a qudt:QuantityValue ; qudt:numericValue 142.0 ] .
Depois:
    phd:tour_1 ph:energyEstimate phd:tour_1_energy .
    phd:tour_1_energy a qudt:QuantityValue ; qudt:numericValue 142.0 .

As IRIs derivadas têm o IRI do pai como prefixo (`<pai>_`), então apagar um
sujeito = apagar (pai, *, *) + os sujeitos `phd:<pai>_*` — sem traversal.

Idempotente: rodar de novo num arquivo já migrado não acha mais bnodes a
converter (0 conversões). Invariantes checados: contagem de triples não muda,
zero bnodes sobram, e a contagem de violations SHACL do catálogo não muda.

Uso:
    python scripts/migrate-bnodes-to-iris.py            # migra e escreve
    python scripts/migrate-bnodes-to-iris.py --dry-run  # só checa, não escreve
"""
import sys
from pathlib import Path

from rdflib import Graph, URIRef, BNode

WEB = Path(__file__).resolve().parent.parent / "web"
DATA = WEB / "data"

PH = "https://pedalhidrografi.co/terms#"
SCHEMA = "https://schema.org/"
NFO = "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#"

# predicado (que hoje aponta pra um bnode) -> sufixo do papel na IRI derivada.
# A cardinalidade de cada um é maxCount 1 nas shapes, então `<pai>_<papel>`
# nunca colide.
ROLE = {
    URIRef(SCHEMA + "locationCreated"): "geo",
    URIRef(NFO + "hasHash"): "hash",
    URIRef(PH + "energyEstimate"): "energy",
    URIRef(PH + "measuredEnergy"): "measured",
    URIRef(PH + "linkRoute"): "route",
}


def migrate_graph(g: Graph) -> int:
    """Reaponta os bnodes-objeto dos predicados conhecidos pra IRIs derivadas
    e move as triples internas do bnode pra a nova IRI. Retorna nº convertido."""
    todo = []
    for pred, role in ROLE.items():
        for parent, bn in sorted(g.subject_objects(pred)):
            if isinstance(bn, BNode) and isinstance(parent, URIRef):
                todo.append((parent, pred, bn, role))
    for parent, pred, bn, role in todo:
        new_iri = URIRef(f"{parent}_{role}")
        g.remove((parent, pred, bn))
        g.add((parent, pred, new_iri))
        for p, o in list(g.predicate_objects(bn)):
            g.remove((bn, p, o))
            g.add((new_iri, p, o))
    return len(todo)


def _violation_count(catalog: Graph, ont: Graph, shapes: Graph) -> int:
    import pyshacl
    from rdflib.namespace import Namespace
    SH = Namespace("http://www.w3.org/ns/shacl#")
    merged = catalog + ont
    _conforms, results, _txt = pyshacl.validate(
        merged, shacl_graph=shapes, inference="rdfs", advanced=True)
    return len(list(results.subjects(SH.resultSeverity, SH.Violation)))


def main(dry_run: bool) -> int:
    files = [DATA / "tours.ttl", DATA / "uploads.ttl"]
    graphs = {}
    before_triples = {}
    for f in files:
        g = Graph().parse(data=f.read_text(encoding="utf-8"), format="turtle")
        graphs[f] = g
        before_triples[f] = len(g)

    # baseline SHACL: catálogo completo (tours+uploads) ANTES da migração
    try:
        shapes = Graph().parse(data=(DATA / "shapes.ttl").read_text(), format="turtle")
        ont = Graph().parse(data=(DATA / "ontology.ttl").read_text(), format="turtle")
        baseline_catalog = Graph()
        for g in graphs.values():
            baseline_catalog += g
        before_viol = _violation_count(baseline_catalog, ont, shapes)
    except Exception as e:  # pyshacl ausente ou erro — segue só com checks estruturais
        print(f"  (SHACL pulado: {e})")
        shapes = ont = None
        before_viol = None

    total = 0
    for f, g in graphs.items():
        n = migrate_graph(g)
        total += n
        remaining = {x for t in g for x in t if isinstance(x, BNode)}
        assert not remaining, f"{f.name}: {len(remaining)} bnodes sobraram após migração"
        assert len(g) == before_triples[f], (
            f"{f.name}: contagem de triples mudou "
            f"({before_triples[f]} -> {len(g)})")
        print(f"  {f.name}: {n} bnodes -> IRIs, {len(g)} triples (inalterado)")

    if shapes is not None:
        after_catalog = Graph()
        for g in graphs.values():
            after_catalog += g
        after_viol = _violation_count(after_catalog, ont, shapes)
        assert after_viol == before_viol, (
            f"SHACL violations mudaram: {before_viol} -> {after_viol}")
        print(f"  SHACL violations no catálogo: {after_viol} (inalterado)")

    print(f"Total: {total} bnodes convertidos.")
    if dry_run:
        print("--dry-run: nada escrito.")
        return 0
    for f, g in graphs.items():
        g.serialize(destination=str(f), format="turtle")
        print(f"  escrito: {f.relative_to(WEB.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(dry_run="--dry-run" in sys.argv))
