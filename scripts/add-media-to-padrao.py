#!/usr/bin/env python
"""One-off: adiciona TODAS as mídias (ph:Image + ph:Video) já no catálogo à
lista padrão "Padrão" (phd:list_padrao), modelada como schema:Collection.

Antes:
    phd:image_<phash> a ph:Image ; ... .
Depois:
    phd:list_padrao a schema:Collection ; schema:name "Padrão" .
    phd:image_<phash> a ph:Image ; ... ; schema:isPartOf phd:list_padrao .

O pertencimento é uma aresta direta na mídia (`schema:isPartOf`), então
round-trip'a limpo pelo purge/upsert do backend (a mídia é o sujeito). A lista
em si é um sujeito top-level (como as schema:EventSeries dos passeios), com
rótulo em schema:name.

Idempotente: rodar de novo num arquivo já migrado não adiciona nada (pula
mídias que já apontam pra Padrão). Invariantes: nenhuma mídia perde triples;
o número de mídias membras nunca diminui; a Padrão sempre existe ao final.

Por que rodar como round-trip guardado (uploads.ttl é estado do servidor):
    bash scripts/pull-cloudrun.sh
    python scripts/add-media-to-padrao.py
    python -c "import rdflib; rdflib.Graph().parse('web/data/uploads.ttl')"
    bash scripts/deploy-cloudrun.sh --state-only   # depois: POST /reload

Uso:
    python scripts/add-media-to-padrao.py            # migra e escreve
    python scripts/add-media-to-padrao.py --dry-run  # só conta, não escreve
"""
import sys
from pathlib import Path

from rdflib import Graph, URIRef, Literal, RDF

WEB = Path(__file__).resolve().parent.parent / "web"
UPLOADS = WEB / "data" / "uploads.ttl"

PH = "https://id.pedalhidrografi.co/terms#"
SCHEMA = "https://schema.org/"
PHD = "https://pedalhidrografi.co/data/"

PH_IMAGE = URIRef(PH + "Image")
PH_VIDEO = URIRef(PH + "Video")
SCHEMA_COLLECTION = URIRef(SCHEMA + "Collection")
SCHEMA_NAME = URIRef(SCHEMA + "name")
SCHEMA_ISPARTOF = URIRef(SCHEMA + "isPartOf")

LIST_PADRAO = URIRef(PHD + "list_padrao")
PADRAO_LABEL = "Padrão"


def main():
    dry = "--dry-run" in sys.argv
    if not UPLOADS.exists():
        print(f"[erro] não achei {UPLOADS}")
        return 1

    g = Graph()
    g.parse(UPLOADS, format="turtle")
    n_before = len(g)

    # Garante a lista Padrão como schema:Collection com rótulo.
    added_list = False
    if (LIST_PADRAO, RDF.type, SCHEMA_COLLECTION) not in g:
        g.add((LIST_PADRAO, RDF.type, SCHEMA_COLLECTION))
        g.add((LIST_PADRAO, SCHEMA_NAME, Literal(PADRAO_LABEL)))
        added_list = True

    media = set(g.subjects(RDF.type, PH_IMAGE)) | set(g.subjects(RDF.type, PH_VIDEO))
    n_media = len(media)
    added = 0
    for m in media:
        if (m, SCHEMA_ISPARTOF, LIST_PADRAO) not in g:
            g.add((m, SCHEMA_ISPARTOF, LIST_PADRAO))
            added += 1

    n_after = len(g)
    members = len(set(g.subjects(SCHEMA_ISPARTOF, LIST_PADRAO)))

    print(f"Mídias no catálogo: {n_media} ({len(set(g.subjects(RDF.type, PH_IMAGE)))} imagens, "
          f"{len(set(g.subjects(RDF.type, PH_VIDEO)))} vídeos)")
    print(f"Lista Padrão criada agora: {'sim' if added_list else 'não (já existia)'}")
    print(f"Membros adicionados: {added}")
    print(f"Total de membros da Padrão: {members}")
    print(f"Triples: {n_before} -> {n_after}")

    # Invariante básico.
    assert members == n_media, f"esperava {n_media} membros, achei {members}"

    if dry:
        print("[dry-run] nada escrito.")
        return 0
    if added == 0 and not added_list:
        print("Nada a fazer (já migrado).")
        return 0
    g.serialize(destination=str(UPLOADS), format="turtle")
    print(f"Escrito: {UPLOADS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
