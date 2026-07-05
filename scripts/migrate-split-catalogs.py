#!/usr/bin/env python3
"""One-shot migração: separa os catálogos e renomeia as classes de mídia.

ANTES:  web/data/tours.ttl  (ph:Tour + ph:Association + ph:RouteReference +
                              schema:EventSeries + schema:Person)
        web/data/uploads.ttl (ph:Image + ph:Video + schema:Collection +
                              schema:Person duplicada)

DEPOIS: web/data/tours.ttl      — ph:Tour, ph:Association, ph:RouteReference,
                                   schema:EventSeries (SEM pessoas)
        web/data/identities.ttl — schema:Person (fonte única; resolve o
                                   duplicado pessoaDandan)
        web/data/images.ttl     — ph:StillImage, ph:MotionImage (+ nós
                                   derivados _geo/_hash) + schema:Collection

E re-tipagem das instâncias: `a ph:Image` → `a ph:StillImage`,
`a ph:Video` → `a ph:MotionImage` (os prefixos de IRI phd:image_/phd:video_
NÃO mudam — só a classe).

Cada sujeito raiz vai pro arquivo da sua classe, levando junto o fechamento:
nós derivados `<raiz>_*` (convenção de IRIs derivadas) e bnodes alcançáveis.
Bnodes órfãos (não referenciados) são descartados (limpeza).

One-shot e NÃO idempotente (split é operação de mão única). Recusa rodar se
images.ttl/identities.ttl já existem (a menos de --force). Use --dry-run pra
prever. Segue o padrão de migrate-bnodes-to-iris.py (rdflib, invariantes).

    python scripts/migrate-split-catalogs.py --dry-run
    python scripts/migrate-split-catalogs.py
"""
import argparse
import sys
from pathlib import Path

from rdflib import Graph, RDF, URIRef, BNode, Namespace

PH = Namespace("https://pedalhidrografi.co/terms#")
PHD = Namespace("https://pedalhidrografi.co/data/")
SCHEMA = Namespace("https://schema.org/")

DATA_DIR = Path(__file__).resolve().parent.parent / "web" / "data"

# Re-tipagem de mídia (classe antiga → nova). IRIs (phd:image_/phd:video_) ficam.
RETYPE = {
    PH.Image: PH.StillImage,
    PH.Video: PH.MotionImage,
}

# Classe raiz → arquivo destino. Aceita as duas formas de schema.org (https/http).
def _both(local):
    return [URIRef(SCHEMA + local), URIRef("http://schema.org/" + local)]

TYPE_FILE = {}
for t in _both("Person"):
    TYPE_FILE[t] = "identities"
for t in (PH.Tour, PH.Association, PH.RouteReference, *_both("EventSeries")):
    TYPE_FILE[t] = "tours"
for t in (PH.StillImage, PH.MotionImage, PH.Upload, *_both("Collection")):
    TYPE_FILE[t] = "images"

PREFIXES = {
    "ph": PH, "phd": PHD, "schema": SCHEMA,
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "pav": "http://purl.org/pav/",
    "nfo": "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#",
    "exif": "http://www.w3.org/2003/12/exif/ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "geo": "http://www.opengis.net/ont/geosparql#",
}


def load_source():
    g = Graph()
    for name in ("tours.ttl", "uploads.ttl"):
        p = DATA_DIR / name
        if p.exists():
            g.parse(str(p), format="turtle")
    return g


def retype(g):
    n = 0
    for old, new in RETYPE.items():
        for s in list(g.subjects(RDF.type, old)):
            g.remove((s, RDF.type, old))
            g.add((s, RDF.type, new))
            n += 1
    return n


def type_of_file(g, s):
    """Arquivo destino de um sujeito nomeado, pela sua rdf:type conhecida."""
    for t in g.objects(s, RDF.type):
        if t in TYPE_FILE:
            return TYPE_FILE[t]
    return None


def assign_files(g):
    """Mapeia CADA sujeito (nomeado + bnode) → arquivo destino, ou None (órfão)."""
    named = {s for s in g.subjects() if isinstance(s, URIRef)}
    subj_file = {}

    # Pass 1: raízes nomeadas tipadas.
    for s in named:
        f = type_of_file(g, s)
        if f:
            subj_file[s] = f

    # Pass 2: IRIs derivadas `<raiz>_suffix` herdam do parent nomeado mais longo.
    roots = list(subj_file.keys())
    for s in named:
        if s in subj_file:
            continue
        cands = [p for p in roots if str(s).startswith(str(p) + "_")]
        if cands:
            subj_file[s] = subj_file[max(cands, key=lambda x: len(str(x)))]

    # Pass 3: bnodes herdam do sujeito que os referencia (ponto fixo).
    changed = True
    while changed:
        changed = False
        for s, _p, o in g:
            if isinstance(o, BNode) and o not in subj_file and s in subj_file:
                subj_file[o] = subj_file[s]
                changed = True

    return subj_file


def build_targets(g, subj_file):
    out = {"tours": Graph(), "identities": Graph(), "images": Graph()}
    for name, ns in PREFIXES.items():
        for tg in out.values():
            tg.bind(name, ns)
    dropped = 0
    unassigned = set()
    for s, p, o in g:
        f = subj_file.get(s)
        if f is None:
            if isinstance(s, BNode):
                dropped += 1          # bnode órfão — descarta
            else:
                unassigned.add(s)     # sujeito nomeado sem destino — ERRO
            continue
        out[f].add((s, p, o))
    return out, dropped, unassigned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="sobrescreve mesmo se images.ttl/identities.ttl existirem")
    args = ap.parse_args()

    images_p = DATA_DIR / "images.ttl"
    ident_p = DATA_DIR / "identities.ttl"
    if (images_p.exists() or ident_p.exists()) and not args.force:
        print(f"ERRO: {images_p.name}/{ident_p.name} já existem — migração já rodou. "
              f"Use --force pra sobrescrever.", file=sys.stderr)
        return 2

    g = load_source()
    total_before = len(g)
    n_retype = retype(g)
    subj_file = assign_files(g)
    out, dropped, unassigned = build_targets(g, subj_file)

    if unassigned:
        print("ERRO: sujeitos nomeados sem destino (tipo desconhecido):", file=sys.stderr)
        for s in sorted(unassigned)[:20]:
            print(f"  {s}  types={list(g.objects(s, RDF.type))}", file=sys.stderr)
        return 3

    # Invariante: toda tripla foi para exatamente 1 arquivo (menos bnodes órfãos).
    total_after = sum(len(tg) for tg in out.values())
    assert total_after + dropped == total_before, (total_after, dropped, total_before)

    persons_leaked = sum(
        1 for f in ("tours", "images")
        for _ in out[f].subjects(RDF.type, URIRef(SCHEMA + "Person"))
    ) + sum(
        1 for f in ("tours", "images")
        for _ in out[f].subjects(RDF.type, URIRef("http://schema.org/Person"))
    )
    assert persons_leaked == 0, f"vazaram {persons_leaked} pessoas p/ tours/images"

    def counts(tg):
        c = {}
        for t in (PH.StillImage, PH.MotionImage, PH.Tour, PH.Association,
                  PH.RouteReference, URIRef(SCHEMA + "Person"),
                  URIRef(SCHEMA + "EventSeries"), URIRef(SCHEMA + "Collection")):
            n = len(list(tg.subjects(RDF.type, t)))
            if n:
                c[t.split("#")[-1].split("/")[-1]] = n
        return c

    print(f"origem: {total_before} triplas (tours.ttl + uploads.ttl)")
    print(f"re-tipadas ph:Image→StillImage / ph:Video→MotionImage: {n_retype}")
    print(f"bnodes órfãos descartados: {dropped}")
    for f in ("tours", "identities", "images"):
        print(f"  {f}.ttl: {len(out[f])} triplas  {counts(out[f])}")

    if args.dry_run:
        print("\n[dry-run] nada escrito.")
        return 0

    for f in ("tours", "identities", "images"):
        (DATA_DIR / f"{f}.ttl").write_text(out[f].serialize(format="turtle"))
    print(f"\nescrito: tours.ttl, identities.ttl, images.ttl em {DATA_DIR}")
    print("uploads.ttl agora é OBSOLETO — remova quando confirmar "
          "(git rm web/data/uploads.ttl / rm no bucket).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
