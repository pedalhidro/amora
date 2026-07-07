#!/usr/bin/env python
"""One-off: adiciona TODAS as mídias (ph:StillImage + ph:MotionImage) já no
catálogo à lista padrão "Padrão" (lst:padrao), modelada como schema:Collection.

Antes:
    med:<hash> a ph:StillImage ; ... .
Depois:
    med:<hash> a ph:StillImage ; ... ; schema:isPartOf lst:padrao .

(`lst:padrao a schema:Collection ; schema:name "Padrão"` já existe em
web/data/lists.ttl — um catálogo próprio, listado em CATALOG_DUMPS junto de
tours.ttl/images.ttl/identities.ttl. Este script NUNCA escreve em lists.ttl;
ele só confere que a lista já está declarada lá antes de apontar mídias pra
ela.)

O pertencimento é uma aresta direta na mídia (`schema:isPartOf`), então
round-trip'a limpo pelo purge/upsert do backend (a mídia é o sujeito).

Idempotente: rodar de novo num arquivo já migrado não adiciona nada às mídias
que já apontam pra Padrão (mas ainda adiciona as que faltam, ex.: mídia nova
importada depois da primeira rodada). Invariantes: nenhuma mídia perde
triples; o número de mídias membras nunca diminui; ao final, toda mídia do
catálogo é membra da Padrão.

Por que rodar como round-trip guardado (images.ttl é estado do servidor):
    bash scripts/pull-cloudrun.sh
    python scripts/add-media-to-padrao.py
    python -c "import rdflib; rdflib.Graph().parse('web/data/images.ttl')"
    bash scripts/deploy-cloudrun.sh --state-only   # depois: POST /reload

Uso:
    python scripts/add-media-to-padrao.py            # migra e escreve
    python scripts/add-media-to-padrao.py --dry-run  # só conta, não escreve
"""
import sys
from pathlib import Path

from rdflib import Graph, URIRef, RDF

WEB = Path(__file__).resolve().parent.parent / "web"
IMAGES = WEB / "data" / "images.ttl"
LISTS = WEB / "data" / "lists.ttl"

PH = "https://id.pedalhidrografi.co/terms#"
SCHEMA = "https://schema.org/"
LST = "https://id.pedalhidrografi.co/listas/"

PH_STILL_IMAGE = URIRef(PH + "StillImage")
PH_MOTION_IMAGE = URIRef(PH + "MotionImage")
SCHEMA_COLLECTION = URIRef(SCHEMA + "Collection")
SCHEMA_ISPARTOF = URIRef(SCHEMA + "isPartOf")

LIST_PADRAO = URIRef(LST + "padrao")


def main():
    dry = "--dry-run" in sys.argv
    if not IMAGES.exists():
        print(f"[erro] não achei {IMAGES}")
        return 1

    # A lista Padrão em si vive em lists.ttl, um catálogo separado — este
    # script não a cria nem a modifica ali, só confere que já existe.
    list_exists = False
    if LISTS.exists():
        lg = Graph()
        lg.parse(LISTS, format="turtle")
        list_exists = (LIST_PADRAO, RDF.type, SCHEMA_COLLECTION) in lg
    if not list_exists:
        print(f"[aviso] {LIST_PADRAO} não está declarada como schema:Collection "
              f"em {LISTS} — confira/crie a lista lá antes de confiar neste "
              f"script (ele só aponta mídias pra ela, não a declara).")

    g = Graph()
    g.parse(IMAGES, format="turtle")
    n_before = len(g)

    media = set(g.subjects(RDF.type, PH_STILL_IMAGE)) | set(g.subjects(RDF.type, PH_MOTION_IMAGE))
    n_media = len(media)
    added = 0
    for m in media:
        if (m, SCHEMA_ISPARTOF, LIST_PADRAO) not in g:
            g.add((m, SCHEMA_ISPARTOF, LIST_PADRAO))
            added += 1

    n_after = len(g)
    members = len(set(g.subjects(SCHEMA_ISPARTOF, LIST_PADRAO)))

    print(f"Mídias no catálogo: {n_media} ({len(set(g.subjects(RDF.type, PH_STILL_IMAGE)))} imagens, "
          f"{len(set(g.subjects(RDF.type, PH_MOTION_IMAGE)))} vídeos)")
    print(f"Lista Padrão já declarada em lists.ttl: {'sim' if list_exists else 'não'}")
    print(f"Membros adicionados: {added}")
    print(f"Total de membros da Padrão: {members}")
    print(f"Triples: {n_before} -> {n_after}")

    # Invariante básico.
    assert members == n_media, f"esperava {n_media} membros, achei {members}"

    if dry:
        print("[dry-run] nada escrito.")
        return 0
    if added == 0:
        print("Nada a fazer (já migrado).")
        return 0
    g.serialize(destination=str(IMAGES), format="turtle")
    print(f"Escrito: {IMAGES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
