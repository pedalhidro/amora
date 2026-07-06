#!/usr/bin/env python3
"""One-shot (idempotente): remove o discriminador image_/video_ dos IRIs de
mídia, deixando o hash como localname opaco (uniforme com pessoas/passeios):

    …/midia/image_<phash>  →  …/midia/<phash>
    …/midia/video_<vhash>  →  …/midia/<vhash>

O tipo (foto/vídeo) segue derivável da CLASSE (ph:StillImage/ph:MotionImage),
não mais do prefixo do IRI. Reescreve sujeitos (mídia + derivados <iri>_geo/
_hash) e objetos (prov:generated do envio). Só toca images.ttl.

GUARDA: aborta se algum phash == algum vhash — nesse caso os dois virariam o
MESMO IRI (…/midia/<h>), fundindo uma foto e um vídeo. Improvável (espaços de
hash independentes de 64 bits) mas silencioso, então checamos.

Round-trip (images.ttl é bucket-first):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-media-drop-discriminator.py
    scripts/deploy-cloudrun.sh --state-only   # (guardado)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef

PH = Namespace("https://id.pedalhidrografi.co/terms#")
MED = "https://id.pedalhidrografi.co/midia/"

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "web" / "data" / "images.ttl"


def strip_discriminator(iri):
    s = str(iri)
    for pfx in ("image_", "video_"):
        if s.startswith(MED + pfx):
            return URIRef(MED + s[len(MED + pfx):])
    return iri


def main() -> int:
    g = Graph()
    g.parse(IMAGES, format="turtle")

    # Guarda de colisão phash==vhash (sobre o estado ATUAL, ainda com prefixo).
    def hashof(s):
        loc = str(s)[len(MED):]
        for pfx in ("image_", "video_"):
            if loc.startswith(pfx):
                return loc[len(pfx):]
        return loc
    phashes = {hashof(s) for s in g.subjects(RDF.type, PH.StillImage)}
    vhashes = {hashof(s) for s in g.subjects(RDF.type, PH.MotionImage)}
    collide = phashes & vhashes
    if collide:
        print(f"⚠ ABORT — {len(collide)} phash==vhash (fundiriam num só IRI): {sorted(collide)[:5]}")
        return 1

    changed = 0
    for s, p, o in list(g.triples((None, None, None))):
        ns, no = strip_discriminator(s), strip_discriminator(o)
        if ns is s and no is o:
            continue
        g.remove((s, p, o))
        g.add((ns, p, no))
        changed += 1

    still = set(g.subjects(RDF.type, PH.StillImage))
    motion = set(g.subjects(RDF.type, PH.MotionImage))
    leftover = [str(x) for x in set(g.all_nodes())
                if str(x).startswith(MED + "image_") or str(x).startswith(MED + "video_")]
    # todos os IRIs de mídia agora são …/midia/<16hex>?
    bad = [str(s) for s in (still | motion)
           if not (len(str(s)[len(MED):]) == 16 or "_" in str(s)[len(MED):])]
    print(f"triples reescritas: {changed} | still={len(still)} motion={len(motion)} | "
          f"resíduo image_/video_={len(leftover)}")
    if changed == 0:
        print("nada a fazer — já sem discriminador.")
        return 0
    if leftover:
        print(f"  ⚠ resíduo — abortando: {leftover[:3]}")
        return 1
    g.serialize(destination=IMAGES, format="turtle")
    print(f"images.ttl reescrito ({len(g)} triples).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
