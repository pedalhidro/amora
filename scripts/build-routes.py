#!/usr/bin/env python
"""
build-routes.py — REBUILD COMPLETO de `web/routes.json` a partir de
`web/data/tours.ttl`, buscando cada GPX no RideWithGPS.

NÃO faz parte do fluxo normal: o backend já mantém routes.json
INCREMENTALMENTE — faz upsert/remove da rota de 1 passeio a cada
/upload-tour e /delete-tour, via `backend/rwgps.py` (mesma lógica de
fetch/parse). Rode este script só pra:
  - bake inicial (primeira geração do routes.json), ou
  - recuperação / re-fetch em massa (geometria mudou no RWGPS, JSON corrompeu).
Pra obter a versão vigente do servidor use `scripts/pull-cloudrun.sh`; depois
de um rebuild empurre com `scripts/deploy-cloudrun.sh --state` (sync-guarded —
não clobbera o que o servidor escreveu nesse meio-tempo).

Fonte de verdade: o catálogo RDF `web/data/tours.ttl`. Cada `ph:Tour` com
`ph:linkRoute` apontando pra uma URL do RideWithGPS vira uma entrada em
routes.json. Passeios sem `linkRoute` (ex.: registros antigos sem GPX) ficam
fora — o sidebar do app pode listá-los à parte, lendo o mesmo TTL.

Uso:  python scripts/build-routes.py   (rebuild completo — ver acima)

Lê do .env (carregado via python-dotenv):
  RWGPS_API_KEY
  RWGPS_AUTH_TOKEN
  RWGPS_COLLECTION_PRIVACY_CODE  (opcional)

Rotas que falham mantêm-se no JSON com `latlngs: null` e um campo `error`,
para que a página ainda possa exibir o metadado.

Dependências:
  pip install python-dotenv rdflib
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rdflib import Graph, Namespace, RDF

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

# A lógica de fetch/parsing/montagem de entrada vive em `backend/rwgps.py`
# (fonte única compartilhada com o backend, que faz a atualização incremental
# por upload/delete de tour). Adicionamos o dir ao path pra importar.
sys.path.insert(0, str(REPO_ROOT / "backend"))
from rwgps import (  # noqa: E402
    downsample_and_round,
    fetch_route_data,
    has_credentials,
    tour_entry_from_graph,
)

# ─── Config ───────────────────────────────────────────────────────────────────
TOURS_TTL    = REPO_ROOT / "web" / "data" / "tours.ttl"
OUTPUT_PATH  = REPO_ROOT / "web" / "routes.json"
CONCURRENCY  = 4     # paralelismo de fetches no RWGPS

PH = Namespace("https://pedalhidrografi.co/terms#")


# ─── Leitura do tours.ttl ─────────────────────────────────────────────────────
def parse_tours(ttl_path: Path) -> list[dict]:
    g = Graph()
    g.parse(ttl_path, format="turtle")

    entries: list[dict] = []
    for tour in g.subjects(RDF.type, PH.Tour):
        entry = tour_entry_from_graph(g, tour)
        if entry is not None:   # None = passeio sem linkRoute do RideWithGPS
            entries.append(entry)

    # Cada passeio (tour) é um evento distinto, mesmo quando dois passeios
    # reaproveitam a mesma rota do RideWithGPS (ex.: aniversários). Mantemos
    # uma entrada por tour; o fetch da GPX é deduplicado no main().
    entries.sort(key=lambda e: e["dateMs"] or 0, reverse=True)
    return entries


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("[build-routes] NOTA: rebuild COMPLETO do routes.json. Em operação "
          "normal o backend o mantém incrementalmente (a cada upload/delete de "
          "tour). Use só pra bake inicial/recuperação e empurre com "
          "deploy-cloudrun.sh --state (sync-guarded).", file=sys.stderr)
    if not has_credentials():
        print("Warning: RWGPS_API_KEY/RWGPS_AUTH_TOKEN are not set. "
              "Public routes may still work; private/unlisted ones will return 401.",
              file=sys.stderr)

    if not TOURS_TTL.exists():
        raise RuntimeError(f"tours.ttl não encontrado em {TOURS_TTL}")
    print(f'Reading {TOURS_TTL.relative_to(REPO_ROOT)}…')
    entries = parse_tours(TOURS_TTL)
    print(f"  {len(entries)} passeio(s) com linkRoute do RideWithGPS")
    if not entries:
        raise RuntimeError("nenhum passeio com `ph:linkRoute` encontrado")

    # Fetch each unique RWGPS id once; passeios diferentes podem compartilhar
    # uma rota (aniversários, rerides). Cada entry permanece como evento próprio.
    unique_ids = sorted({e["id"] for e in entries})
    print(f"Fetching {len(unique_ids)} GPX único(s) (concurrency={CONCURRENCY})…")
    counter = {"done": 0}
    total_ids = len(unique_ids)

    def fetch_worker(rid: str):
        try:
            data = fetch_route_data(rid)
            pts_tag = f'{len(data["latlngs"])}pts' if data["latlngs"] else "FAIL"
            poi_tag = f', {len(data["pois"])} POIs' if data["pois"] else ""
            tag = f"ok ({pts_tag}{poi_tag})"
            err = None
        except Exception as e:
            data, err, tag = None, str(e), f"FAIL ({e})"
        counter["done"] += 1
        print(f"  [{counter['done']}/{total_ids}] {rid} — {tag}", flush=True)
        return rid, data, err

    fetched: dict[str, tuple[dict | None, str | None]] = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        for rid, data, err in pool.map(fetch_worker, unique_ids):
            fetched[rid] = (data, err)

    results = []
    for entry in entries:
        data, err = fetched[entry["id"]]
        if data:
            results.append({
                **entry,
                "latlngs": downsample_and_round(data["latlngs"]),
                "pois":    data["pois"],
            })
        else:
            results.append({**entry, "latlngs": None, "pois": [], "error": err})

    ok = sum(1 for r in results if r.get("latlngs"))
    print(f"Done: {ok} ok, {len(results) - ok} failed")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"file": str(TOURS_TTL.relative_to(REPO_ROOT))},
        "routes": results,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
