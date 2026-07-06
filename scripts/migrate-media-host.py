#!/usr/bin/env python3
"""One-shot (idempotente): move os IRIs de MÍDIA e de ENVIO de web/data/images.ttl
para o host resolvível id.pedalhidrografi.co, mantendo o hash como identidade
(Opção A — só o host muda, o discriminador image_/video_ e o hash ficam):

    https://pedalhidrografi.co/data/image_<phash>  → https://id.pedalhidrografi.co/midia/image_<phash>
    https://pedalhidrografi.co/data/video_<vhash>  → https://id.pedalhidrografi.co/midia/video_<vhash>
    https://pedalhidrografi.co/data/upload_<ts>    → https://id.pedalhidrografi.co/envio/<ts>

Reescreve em QUALQUER posição (sujeito/objeto): os sujeitos de mídia + seus nós
derivados (image_<ph>_geo / _hash), a atividade de envio (upload_<ts>), e a
referência prov:generated (upload → mídia). NÃO toca em phd:tour_* (fica pra P4)
nem em nada fora desses três prefixos. Blobs (photos/<phash>/…), dedup e
/delete-* seguem intactos — dependem do hash, que não muda.

Round-trip de estado (images.ttl é bucket-first):
    scripts/pull-cloudrun.sh --data-only
    python3 scripts/migrate-media-host.py
    scripts/deploy-cloudrun.sh --state-only   # (guardado)
    curl -X POST https://amora.pedalhidrografi.co/reload
"""
import sys
from pathlib import Path

from rdflib import Graph, URIRef

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "web" / "data" / "images.ttl"

OLD = "https://pedalhidrografi.co/data/"
MED = "https://id.pedalhidrografi.co/midia/"
ENV = "https://id.pedalhidrografi.co/envio/"

# (prefixo antigo completo, prefixo novo completo). Ordem importa: image_/video_/
# upload_ são disjuntos, mas mantemos explícito. upload_<ts> → envio/<ts> (o
# path /envio/ já carrega o sentido de "envio", então o local perde o upload_).
RULES = [
    (OLD + "image_", MED + "image_"),
    (OLD + "video_", MED + "video_"),
    (OLD + "upload_", ENV),
]


def remap(iri):
    s = str(iri)
    for old, new in RULES:
        if s.startswith(old):
            return URIRef(new + s[len(old):])
    return iri


def main() -> int:
    g = Graph()
    g.parse(IMAGES, format="turtle")
    before = len(g)

    changed = 0
    for s, p, o in list(g.triples((None, None, None))):
        ns, no = remap(s), remap(o)   # predicados nunca são IRIs de mídia
        if ns is s and no is o:
            continue
        g.remove((s, p, o))
        g.add((ns, p, no))
        changed += 1

    # Rebinda prefixos pra saída legível.
    g.bind("med", MED)
    g.bind("env", ENV)

    n_media = sum(1 for s in set(g.subjects()) if str(s).startswith(MED))
    n_env = sum(1 for s in set(g.subjects()) if str(s).startswith(ENV))
    print(f"triples reescritas: {changed} | sujeitos med:*={n_media} env:*={n_env}")
    # Sanidade: nenhum image_/video_/upload_ sobrando no host antigo.
    leftover = [str(x) for x in set(g.all_nodes())
                if any(str(x).startswith(OLD + p) for p in ("image_", "video_", "upload_"))]
    if leftover:
        print(f"  ⚠ RESTARAM {len(leftover)} no host antigo: {leftover[:3]}")
    if changed == 0:
        print("nada a fazer — já migrado.")
        return 0
    g.serialize(destination=IMAGES, format="turtle")
    print(f"images.ttl: {before} → {len(g)} triples")
    return 0 if not leftover else 1


if __name__ == "__main__":
    sys.exit(main())
