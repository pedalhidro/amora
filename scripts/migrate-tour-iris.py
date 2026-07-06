#!/usr/bin/env python3
"""One-shot (idempotente): move os IRIs de PASSEIO e de SÉRIE pro host resolvível
id.pedalhidrografi.co, trocando o id numérico do passeio por um slug aleatório
Crockford base32 (como as pessoas):

    https://pedalhidrografi.co/data/tour_<numid>  → https://id.pedalhidrografi.co/passeio/<slug8>
    https://pedalhidrografi.co/data/<SÉRIE>       → https://id.pedalhidrografi.co/serie/<SÉRIE>
      (SÉRIE ∈ PH, BT, BP, S, SESC)

Reescreve (em tours.ttl): sujeitos de passeio + seus derivados (tour_<id>_route),
sujeitos de série + as referências ph:inEventSeries. NÃO toca em phd:assoc_*
(edições — ficam pra P5) nem em ph:inSeriesEdition (aponta pros assoc_). Em
images.ttl reescreve ph:capturedDuring. Em routes.json reescreve as chaves
tourIri. Emite scripts/tour-iri-map.json (mapa velho↔novo) pra continuidade de
deep links (?tour=<numid> antigo) e guids do feed.

Idempotente: passeios já em pas: são pulados; o mapa é preservado/estendido.

Round-trip de estado (tours.ttl + images.ttl + routes.json são bucket-first):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-tour-iris.py
    scripts/deploy-cloudrun.sh --state-only   # (guardado — sincroniza os 3 juntos)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import json
import secrets
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef

PHD = "https://pedalhidrografi.co/data/"
PAS = "https://id.pedalhidrografi.co/passeio/"
SER = "https://id.pedalhidrografi.co/serie/"
PH = Namespace("https://id.pedalhidrografi.co/terms#")
SCHEMA = Namespace("https://schema.org/")

REPO = Path(__file__).resolve().parent.parent
TOURS = REPO / "web" / "data" / "tours.ttl"
IMAGES = REPO / "web" / "data" / "images.ttl"
ROUTES = REPO / "web" / "routes.json"
IRI_MAP = REPO / "web" / "data" / "tour-iri-map.json"

SERIES_CODES = {"PH", "BT", "BP", "S", "SESC"}
CROCKFORD = "0123456789abcdefghjkmnpqrstvwxyz"   # sem i,l,o,u — igual às pessoas


def mint_slug(taken):
    while True:
        s = "".join(secrets.choice(CROCKFORD) for _ in range(8))
        if s not in taken:
            taken.add(s)
            return s


def load_map():
    if IRI_MAP.exists():
        m = json.loads(IRI_MAP.read_text())
        return m.get("byOldId", {}), m.get("byNewSlug", {})
    return {}, {}


def main() -> int:
    g = Graph()
    g.parse(TOURS, format="turtle")

    by_old, by_new = load_map()
    taken = set(by_new.keys())

    # 1) Descobre os passeios ainda em phd:tour_ e garante slug pra cada um.
    tours = [str(s) for s in g.subjects(RDF.type, PH.Tour) if str(s).startswith(PHD + "tour_")]
    for t in tours:
        old = t[len(PHD + "tour_"):]
        if old not in by_old:
            slug = mint_slug(taken)
            by_old[old] = slug
            by_new[slug] = old

    def remap(iri):
        s = str(iri)
        if s.startswith(PHD + "tour_"):
            rest = s[len(PHD + "tour_"):]
            base, _, suffix = rest.partition("_")   # "87" | "87_route"
            slug = by_old.get(base)
            if slug is None:
                return iri
            return URIRef(PAS + slug + (("_" + suffix) if suffix else ""))
        if s.startswith(PHD) and s[len(PHD):] in SERIES_CODES:
            return URIRef(SER + s[len(PHD):])
        return iri

    # 2) Reescreve tours.ttl (sujeito + objeto; predicados nunca são passeio/série).
    changed = 0
    for s, p, o in list(g.triples((None, None, None))):
        ns, no = remap(s), remap(o)
        if ns is s and no is o:
            continue
        g.remove((s, p, o))
        g.add((ns, p, no))
        changed += 1
    g.bind("pas", PAS)
    g.bind("ser", SER)

    # 3) images.ttl — ph:capturedDuring phd:tour_<id> → pas:<slug>.
    gi = Graph()
    gi.parse(IMAGES, format="turtle")
    img_changed = 0
    for s, o in list(gi.subject_objects(PH.capturedDuring)):
        no = remap(o)
        if no is not o:
            gi.remove((s, PH.capturedDuring, o))
            gi.add((s, PH.capturedDuring, no))
            img_changed += 1
    gi.bind("pas", PAS)

    # 4) routes.json — chaves tourIri.
    routes = json.loads(ROUTES.read_text()) if ROUTES.exists() else {"routes": []}
    rj_changed = 0
    for entry in routes.get("routes", []):
        ti = entry.get("tourIri")
        if ti and ti.startswith(PHD + "tour_"):
            nti = str(remap(URIRef(ti)))
            if nti != ti:
                entry["tourIri"] = nti
                rj_changed += 1

    # Sanidade.
    leftover_tours = [str(s) for s in g.subjects(RDF.type, PH.Tour) if str(s).startswith(PHD + "tour_")]
    leftover_series = [str(s) for s in g.subjects(RDF.type, SCHEMA.EventSeries) if str(s).startswith(PHD)]
    leftover_cap = [str(o) for o in gi.objects(None, PH.capturedDuring) if str(o).startswith(PHD + "tour_")]
    print(f"tours.ttl reescritas: {changed} | images capturedDuring: {img_changed} | routes.json: {rj_changed}")
    print(f"passeios mapeados: {len(by_old)} | resíduo tour_={len(leftover_tours)} série={len(leftover_series)} cap={len(leftover_cap)}")

    if changed == 0 and img_changed == 0 and rj_changed == 0:
        print("nada a fazer — já migrado.")
        # ainda assim garante o mapa em disco.
        IRI_MAP.write_text(json.dumps({"byOldId": by_old, "byNewSlug": by_new}, indent=2, ensure_ascii=False) + "\n")
        return 0
    if leftover_tours or leftover_series or leftover_cap:
        print(f"  ⚠ RESÍDUO no host antigo — abortando sem gravar: {(leftover_tours+leftover_series+leftover_cap)[:3]}")
        return 1

    g.serialize(destination=TOURS, format="turtle")
    gi.serialize(destination=IMAGES, format="turtle")
    ROUTES.write_text(json.dumps(routes, ensure_ascii=False, separators=(",", ":")) + "\n")
    IRI_MAP.write_text(json.dumps({"byOldId": by_old, "byNewSlug": by_new}, indent=2, ensure_ascii=False) + "\n")
    print(f"OK. Mapa em {IRI_MAP.relative_to(REPO)} ({len(by_old)} passeios).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
