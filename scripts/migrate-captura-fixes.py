#!/usr/bin/env python3
"""Conserta duas inconsistências do catálogo achadas pela auditoria de captura.

Ambas são reparos de CATÁLOGO — não dá pra fazer por `POST /upload-tour`:

1. **Arte de anúncio apontando pra host local.** O `PH/96` ficou com
   `schema:image <http://localhost:8080/tour_assets/ph96/announcement.jpg>`.
   Um backend de desenvolvimento gravou no dado o host pelo qual o cliente
   chegou (`request.host_url`), e esse TTL depois subiu pra produção — onde a
   IRI não resolve pra ninguém. O blob em si está no bucket, certinho; só a
   IRI aponta pro lugar errado. (A recorrência já foi fechada: o backend agora
   usa `PUBLIC_BASE_URL`, e as shapes avisam. Ver backend/main.py.)

2. **`ph:sequenceInSeries` com datatype divergente.** A edição `BP/3-5` é a
   ÚNICA das 115 escrita como `"4"^^xsd:positiveInteger`; as outras 114 usam
   o inteiro solto do Turtle (`4`), que é `xsd:integer`. A shape pedia
   `xsd:positiveInteger` e por isso reprovava as 114 — uma constraint morta,
   avisando sempre. A shape virou `xsd:integer` + `sh:minInclusive 1`
   (semanticamente a mesma coisa) e este script normaliza a outlier.

Por que um script e não um patch pelo endpoint: o `/upload-tour` purga o
passeio e seus nós DERIVADOS (`pas:<slug>_*`) antes de mesclar o TTL novo. A
edição (`…/passeio/BP/3-5`) é um sujeito PRÓPRIO, de chave natural — não é nó
derivado, então não é purgada. Re-declará-la num patch ADICIONARIA o literal
novo sem tirar o velho, deixando dois `ph:sequenceInSeries` e violando o
`sh:maxCount 1`. Reparo de sujeito não-derivado é território de migração.

Idempotente: rodar de novo não faz nada. Caminho de uso (round-trip guardado):

    bash scripts/pull-cloudrun.sh --data-only
    python scripts/migrate-captura-fixes.py            # --dry-run é o default
    python scripts/migrate-captura-fixes.py --apply
    bash scripts/deploy-cloudrun.sh --state-only
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import rdflib
from rdflib import Literal, URIRef
from rdflib.namespace import XSD

REPO = Path(__file__).resolve().parents[1]
TOURS = REPO / "web" / "data" / "tours.ttl"

PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#")
SCHEMA = rdflib.Namespace("https://schema.org/")

# Como o GCSStateStore monta a URL pública (backend/storage.py:222).
BUCKET_BASE = "https://storage.googleapis.com/phidro-state"
HOST_LOCAL = re.compile(r"^(https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?|file://)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="grava (default: só mostra)")
    ap.add_argument("--bucket-base", default=BUCKET_BASE)
    a = ap.parse_args()

    g = rdflib.Graph()
    g.parse(TOURS, format="turtle")
    mudou = 0

    # ── 1. schema:image em host local → URL pública do bucket ─────────────
    for tour, img in list(g.subject_objects(SCHEMA.image)):
        if not isinstance(img, URIRef) or not HOST_LOCAL.match(str(img)):
            continue
        # Preserva o caminho a partir de tour_assets/ — o blob já está lá.
        m = re.search(r"(tour_assets/.+)$", str(img))
        if not m:
            print(f"  ⚠ {tour} tem arte local sem caminho tour_assets/: {img} — pulando")
            continue
        nova = URIRef(f"{a.bucket_base.rstrip('/')}/{m.group(1)}")
        print(f"  arte  {str(tour).rsplit('/', 1)[-1]}")
        print(f"          de: {img}")
        print(f"        para: {nova}")
        if a.apply:
            g.remove((tour, SCHEMA.image, img))
            g.add((tour, SCHEMA.image, nova))
        mudou += 1

    # ── 2. ph:sequenceInSeries: xsd:positiveInteger → xsd:integer ─────────
    for ed, seq in list(g.subject_objects(PH.sequenceInSeries)):
        if not isinstance(seq, Literal) or seq.datatype != XSD.positiveInteger:
            continue
        nova = Literal(int(seq))          # rdflib serializa como inteiro solto (xsd:integer)
        print(f"  seq   {str(ed).replace('https://id.pedalhidrografi.co/passeio/', '')}: "
              f"\"{seq}\"^^xsd:positiveInteger → {int(seq)}")
        if a.apply:
            g.remove((ed, PH.sequenceInSeries, seq))
            g.add((ed, PH.sequenceInSeries, nova))
        mudou += 1

    if not mudou:
        print("nada a consertar — o catálogo já está normalizado.")
        return

    if not a.apply:
        print(f"\n{mudou} correções pendentes. Rode com --apply pra gravar.")
        return

    TOURS.write_text(g.serialize(format="turtle"), encoding="utf-8")
    print(f"\n✓ {mudou} correções gravadas em {TOURS}")
    print("  Agora: bash scripts/deploy-cloudrun.sh --state-only && "
          "curl -X POST https://amora.pedalhidrografi.co/reload")


if __name__ == "__main__":
    main()
