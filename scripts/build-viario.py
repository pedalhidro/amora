#!/usr/bin/env python
"""Enxuga o gpkg do viário de SP pra um arquivo leve, próprio pra baixar
no navegador e rasterizar como máscara de rede ("Menor energia pelo viário").

A fonte (`ignore/sampa-viario.gpkg`, ~152 MB) traz a tabela `viario`
(LINESTRING, EPSG:31983 — SIRGAS 2000 / UTM 23S) com 440 k+ feições e um
monte de colunas de atributo (osm_id, name, other_tags, waterway, railway…)
que não servem pra rasterização. Este script:

  - mantém só a geometria (`geom`);
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Enxuga o gpkg do viário de SP.")
    ap.add_argument("--in", dest="src", type=Path, default=DEFAULT_IN,
                    help="gpkg de origem (default: ignore/sampa-viario.gpkg)")
    ap.add_argument("--out", dest="dst", type=Path, default=DEFAULT_OUT,
                    help="gpkg de saída (default: ignore/sampa-viario-slim.gpkg)")
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

    # Só a geometria, só ruas; reprojetado pra WGS84; R-tree reconstruído
    # pelo driver de saída.
    sql = f'SELECT {GEOM} FROM {TABLE} WHERE highway IS NOT NULL'
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

    src_mb = args.src.stat().st_size / 1e6
    dst_mb = args.dst.stat().st_size / 1e6
    print(f"\nok: {args.src.name} ({src_mb:.0f} MB) → "
          f"{args.dst.name} ({dst_mb:.0f} MB)")
    print("suba pro bucket telhas/viario/ e confira VIARIO_GPKG_URL em web/app.js.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
