#!/usr/bin/env python3
"""One-shot (idempotente): tipa como ph:GeoreferencedImage toda mídia de
web/data/images.ttl que tem schema:locationCreated.

Contexto: a coordenada/data da mídia virou sh:Warning (opcional) na base
ph:Image; o subconjunto COM GPS — que o mapa renderiza como marcador — ganhou
o mixin ph:GeoreferencedImage (obrigatório ter coordenada, por SHACL). Os
emitters novos (upload_images.html, build-clips.py) já acrescentam o tipo;
este script faz o backfill do catálogo existente.

Round-trip de estado (images.ttl é bucket-first):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-georeferenced.py
    scripts/deploy-cloudrun.sh --state-only    # (guardado)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF

PH = Namespace("https://pedalhidrografi.co/terms#")
SCHEMA = Namespace("https://schema.org/")

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "web" / "data" / "images.ttl"


def main() -> int:
    g = Graph()
    g.parse(IMAGES, format="turtle")
    before = len(g)

    media = set(g.subjects(RDF.type, PH.StillImage)) | set(
        g.subjects(RDF.type, PH.MotionImage))
    added = skipped_no_geo = already = 0
    for m in sorted(media):
        has_geo = next(g.objects(m, SCHEMA.locationCreated), None) is not None
        if not has_geo:
            skipped_no_geo += 1
            continue
        if (m, RDF.type, PH.GeoreferencedImage) in g:
            already += 1
            continue
        g.add((m, RDF.type, PH.GeoreferencedImage))
        added += 1

    print(f"mídias: {len(media)} | +tipo: {added} | já tinham: {already} | "
          f"sem GPS (intocadas): {skipped_no_geo}")
    if added == 0:
        print("nada a fazer — images.ttl inalterado.")
        return 0

    g.serialize(destination=IMAGES, format="turtle")
    print(f"images.ttl reescrito ({before} → {len(g)} triples).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
