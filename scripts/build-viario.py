#!/usr/bin/env python
"""Enxuga o gpkg do viário de SP pra um arquivo leve, próprio pra baixar
no navegador e rasterizar como máscara de rede ("Menor energia pelo viário").

A fonte (`ignore/sampa-viario.gpkg`, ~152 MB) traz a tabela `viario`
(LINESTRING, EPSG:31983 — SIRGAS 2000 / UTM 23S) com 440 k+ feições e um
monte de colunas de atributo (osm_id, name, other_tags, waterway, railway…)
que não servem pra rasterização. Este script:

  - mantém a geometria (`geom`) + 3 colunas finas extraídas do hstore
    `other_tags` pro achatamento de tabuleiro no "Menor energia pelo viário":
    `bridge` ('yes' p/ ponte/viaduto, i.e. bridge!=no), `tunnel` ('yes') e
    `layer` (int). Sem elas o app teria que puxar pontes do Overpass por trecho;
    com elas a flag vem do próprio gpkg (offline, rápido);
  - filtra `highway IS NOT NULL` — mesma semântica do antigo Overpass
    (`way["highway"]`): ruas pedaláveis, não rios/ferrovias;
  - reconstrói o índice R-tree (SPATIAL_INDEX=YES, padrão do driver GPKG)
    pra consulta por bbox continuar rápida no navegador;
  - reprojeta pra EPSG:4326 (WGS84). Assim o app NÃO precisa do proj4 nem
    reprojeta vértice a vértice na rasterização — era o gargalo que deixava
    a rota lenta/travada. A bbox e os vértices já saem em lat/lng.

Alvo: ~30–50 MB. Depois de gerar, suba o arquivo pro mesmo host dos DEMs:

    gcloud storage cp ignore/sampa-viario-slim.gpkg \\
        gs://telhas/viario/sampa-viario.gpkg

(servido em https://telhas.pedalhidrografi.co/viario/sampa-viario.gpkg —
ver VIARIO_GPKG_URL em web/app.js).

Requisitos: ogr2ogr (GDAL) no PATH.

Roda:
    python scripts/build-viario.py
    python scripts/build-viario.py --in ignore/sampa-viario.gpkg --out ignore/sampa-viario-slim.gpkg
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = ROOT / "ignore" / "sampa-viario.gpkg"
DEFAULT_OUT = ROOT / "ignore" / "sampa-viario-slim.gpkg"

# Tabela/coluna esperadas na fonte (ver `gpkg_geometry_columns`).
TABLE = "viario"
GEOM = "geom"

# Camada de água (`--water`): não está na fonte do viário (é um export só de
# ruas), então puxa do OSM via um extrato Geofabrik + osmium. SP é interior (sem
# litoral) → água = áreas (natural=water / waterway=riverbank / landuse=reservoir)
# + rios (waterway=river). Vira a camada `water` no gpkg, lida pela máscara de
# barreira do "Menor energia pelo terreno". O .pbf (~800 MB) é cacheado em ignore/.
GEOFABRIK_URL = "https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf"
PBF = ROOT / "ignore" / "sudeste-latest.osm.pbf"


def _run(cmd: list[str]) -> None:
    print("$ " + " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def extent_4326(gpkg: Path, layer: str) -> tuple[float, float, float, float]:
    """(W, S, E, N) da camada via ogrinfo. O gpkg já é 4326."""
    out = subprocess.run(["ogrinfo", "-so", str(gpkg), layer],
                         capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        if line.strip().startswith("Extent:"):
            nums = [float(x) for x in __import__("re").findall(r"-?\d+\.\d+", line)]
            if len(nums) == 4:
                return nums[0], nums[1], nums[2], nums[3]  # W, S, E, N
    raise RuntimeError("não achei Extent na saída do ogrinfo")


def build_water_layer(dst: Path, keep_pbf: bool) -> None:
    """Adiciona a camada `water` (áreas + rios) ao gpkg, recortada à extensão do
    viário, a partir de um extrato Geofabrik via osmium. Idempotente."""
    for tool in ("osmium",):
        if not shutil.which(tool):
            raise RuntimeError(f"{tool} não está no PATH (brew install osmium-tool).")
    w, s, e, n = extent_4326(dst, TABLE)
    pad = 0.02
    bbox = f"{w - pad},{s - pad},{e + pad},{n + pad}"  # left,bottom,right,top
    ig = dst.parent
    sp_pbf = ig / "water-sp.osm.pbf"
    ar_pbf, ar_gj = ig / "water-area.osm.pbf", ig / "water_areas.geojson"
    rv_pbf, rv_gj = ig / "water-river.osm.pbf", ig / "water_rivers.geojson"

    if not PBF.exists():
        print(f"→ baixando extrato Geofabrik (~800 MB) → {PBF.name}")
        _run(["curl", "-fL", "--retry", "3", "-C", "-", "-o", PBF, GEOFABRIK_URL])
    # Recorta à bbox do viário (rápido). Depois DOIS pipelines separados pra que o
    # osmium NÃO emita o contorno do polígono também como linha (que duplicaria a
    # área): áreas → só polígonos; rios → só linhas. (`--geometry-types`.)
    _run(["osmium", "extract", "-b", bbox, PBF, "-o", sp_pbf, "--overwrite"])
    _run(["osmium", "tags-filter", sp_pbf, "-o", ar_pbf, "--overwrite",
          "nwr/natural=water", "nwr/landuse=reservoir", "nwr/waterway=riverbank"])
    _run(["osmium", "export", ar_pbf, "-o", ar_gj, "--overwrite", "-f", "geojson", "--geometry-types=polygon"])
    _run(["osmium", "tags-filter", sp_pbf, "-o", rv_pbf, "--overwrite", "w/waterway=river"])
    _run(["osmium", "export", rv_pbf, "-o", rv_gj, "--overwrite", "-f", "geojson", "--geometry-types=linestring"])
    # Camada `water` no gpkg: áreas (polígono) + rios (linha) numa camada
    # GEOMETRY. O app rasteriza por tipo: polígono→preenche, linha→barreira.
    _run(["ogr2ogr", "-f", "GPKG", "-update", "-nln", "water", "-nlt", "GEOMETRY",
          "-t_srs", "EPSG:4326", "-lco", "SPATIAL_INDEX=YES", str(dst), str(ar_gj)])
    _run(["ogr2ogr", "-f", "GPKG", "-update", "-append", "-nln", "water",
          "-t_srs", "EPSG:4326", str(dst), str(rv_gj)])
    for tmp in (sp_pbf, ar_pbf, ar_gj, rv_pbf, rv_gj):
        tmp.unlink(missing_ok=True)
    if not keep_pbf:
        PBF.unlink(missing_ok=True)  # libera ~800 MB; re-baixa no próximo --water


def main() -> int:
    ap = argparse.ArgumentParser(description="Enxuga o gpkg do viário de SP.")
    ap.add_argument("--in", dest="src", type=Path, default=DEFAULT_IN,
                    help="gpkg de origem (default: ignore/sampa-viario.gpkg)")
    ap.add_argument("--out", dest="dst", type=Path, default=DEFAULT_OUT,
                    help="gpkg de saída (default: ignore/sampa-viario-slim.gpkg)")
    ap.add_argument("--water", action="store_true",
                    help="também adiciona a camada `water` (baixa ~800 MB do Geofabrik via osmium)")
    ap.add_argument("--keep-pbf", action="store_true",
                    help="mantém o .pbf do Geofabrik em ignore/ (default: apaga após usar)")
    args = ap.parse_args()

    if not shutil.which("ogr2ogr"):
        print("erro: ogr2ogr (GDAL) não está no PATH "
              "(brew install gdal / apt install gdal-bin).", file=sys.stderr)
        return 1
    if not args.src.exists():
        print(f"erro: fonte não encontrada: {args.src}", file=sys.stderr)
        return 1
    if args.dst.exists():
        args.dst.unlink()  # ogr2ogr não sobrescreve gpkg existente

    # Geometria + bridge/tunnel/layer extraídos do hstore other_tags; só ruas;
    # reprojetado pra WGS84; R-tree reconstruído pelo driver de saída.
    # other_tags tem o formato `"chave"=>"valor",…` — extraímos os 3 campos com
    # instr/substr (sem precisar de extensão). `"layer"=>"` tem 10 caracteres.
    sql = f"""SELECT {GEOM},
      CASE WHEN instr(other_tags,'"bridge"=>')>0 AND instr(other_tags,'"bridge"=>"no"')=0 THEN 'yes' END AS bridge,
      CASE WHEN instr(other_tags,'"tunnel"=>"yes"')>0 THEN 'yes' END AS tunnel,
      CASE WHEN instr(other_tags,'"layer"=>"')>0 THEN CAST(substr(
        other_tags, instr(other_tags,'"layer"=>"')+10,
        instr(substr(other_tags, instr(other_tags,'"layer"=>"')+10),'"')-1) AS INTEGER) END AS layer
      FROM {TABLE} WHERE highway IS NOT NULL"""
    cmd = [
        "ogr2ogr", "-f", "GPKG", str(args.dst), str(args.src),
        "-dialect", "SQLITE", "-sql", sql,
        "-t_srs", "EPSG:4326",
        "-nln", TABLE, "-nlt", "LINESTRING",
        "-lco", "SPATIAL_INDEX=YES",
    ]
    print("$ " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"erro: ogr2ogr falhou (código {e.returncode}).", file=sys.stderr)
        return e.returncode

    if args.water:
        try:
            build_water_layer(args.dst, args.keep_pbf)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"erro: camada de água falhou: {e}", file=sys.stderr)
            return 1

    src_mb = args.src.stat().st_size / 1e6
    dst_mb = args.dst.stat().st_size / 1e6
    print(f"\nok: {args.src.name} ({src_mb:.0f} MB) → "
          f"{args.dst.name} ({dst_mb:.0f} MB){' + camada water' if args.water else ''}")
    print("suba pro bucket telhas/viario/ e confira VIARIO_GPKG_URL em web/app.js.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
