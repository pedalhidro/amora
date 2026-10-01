#!/usr/bin/env python3
"""Assa a mancha da enchente histórica de São Paulo (camada "Enchente de 1922").

Hipótese da camada: tudo o que hoje está a até COTA metros de altitude
(default 724 m) e é ligado aos rios da cidade estava debaixo d'água. É um
modelo de "banheira" — sem hidráulica, sem tempo, sem barragens — e o relevo é
o de HOJE (as várzeas foram aterradas e os rios retificados depois), então a
mancha é uma leitura do relevo, não uma reconstrução do evento.

Por que não basta `elevação <= cota`: o Tietê desce pro interior e a Baixada
Santista está a poucos metros do mar — um limiar puro alagaria o vale a jusante
e o litoral. Então só ficam as componentes conexas (4-vizinhança, a mais
conservadora: não vaza na diagonal) que contêm uma das SEMENTES — pontos nas
calhas do Tietê, Pinheiros e Tamanduateí.

Relevo: o MESMO mosaico do bake do grafo viário (build-viario.py,
DemSampler): DEM de SP (~5 m, lido numa overview via /vsicurl — só os bytes
da resolução pedida) onde vale, FABDEM (30 m, bare-earth) no resto e onde o DEM
de SP discorda dele em mais de SRC_DISAGREE_MAX_M (os buracos que o DEM de SP
grava como 0 m — sem essa guarda cada buraco viraria um lago).

Saída: GeoJSON (FeatureCollection com 1 MultiPolygon) em
web/geo/enchente-1922.geojson, servido pelo container junto do app.

Dependências (só pro bake, não pro backend):
    pip install rasterio numpy scipy shapely
(o wheel do rasterio já traz o GDAL — não precisa do GDAL do sistema).

Uso:
    python scripts/build-enchente.py                 # cota 724 m, ~10 m/célula
    python scripts/build-enchente.py --cota 730 --res-m 20 --out /tmp/x.geojson
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "web" / "geo" / "enchente-1922.geojson"

# Mesmas fontes do build-viario.py (FABDEM_BASE / SAMPA_DEM_URL).
FABDEM_BASE = "https://fabdem.pedalhidrografi.co/"
SAMPA_DEM_URL = "https://telhas.pedalhidrografi.co/dem/sampa_geral.tif"
SRC_DISAGREE_MAX_M = 100.0

# Sementes (lat, lng) nas calhas — a mancha é a união das componentes que as
# contêm. Cada semente é "encaixada" na célula MAIS BAIXA num raio de
# SEED_SNAP_M (a calha tem dezenas de metros; um ponto clicado no mapa cai
# fácil na margem). Várias por rio de propósito: pontes e a média da leitura
# em 10 m podem cortar a calha em trechos desconexos. Uma semente que mesmo
# encaixada fique acima da cota é ignorada, com aviso.
SEED_SNAP_M = 300.0
# Corte a jusante: depois de Barueri o Tietê desce abaixo da cota rumo a
# Santana de Parnaíba/Pirapora e a banheira vira uma fita ao longo do vale —
# ali o modelo deixa de fazer sentido (a água não "sobe" pro planalto a
# montante). A oeste desta longitude nada alaga; a várzea de Barueri/
# Carapicuíba fica dentro.
CLIP_WEST_LNG = -46.88
SEEDS = {
    "Tietê · Penha": (-23.5065, -46.5480),
    "Tietê · Vila Maria": (-23.5135, -46.5900),
    "Tietê · Ponte das Bandeiras": (-23.5185, -46.6330),
    "Tietê · Casa Verde": (-23.5195, -46.6650),
    "Tietê · Limão": (-23.5130, -46.6860),
    "Tietê · Freguesia do Ó": (-23.5180, -46.7100),
    "Tietê · Vila Leopoldina": (-23.5250, -46.7400),
    "Tietê · Osasco": (-23.5150, -46.7900),
    "Pinheiros · Cidade Universitária": (-23.5680, -46.7060),
    "Pinheiros · Cidade Jardim": (-23.5870, -46.6930),
    "Pinheiros · Morumbi": (-23.6150, -46.7000),
    "Tamanduateí · Parque D. Pedro II": (-23.5470, -46.6280),
    "Tamanduateí · Glicério": (-23.5530, -46.6260),
}


def fabdem_tile_name(lat: int, lon: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}_FABDEM_V1-2.tif"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cota", type=float, default=724.0,
                    help="altitude máxima alagada, em m (default 724)")
    ap.add_argument("--res-m", type=float, default=10.0,
                    help="tamanho de célula da leitura do DEM de SP, em m (default 10)")
    ap.add_argument("--min-hole-ha", type=float, default=1.0,
                    help="ilhas secas menores que isto (ha) são engolidas (default 1)")
    ap.add_argument("--west", type=float, default=CLIP_WEST_LNG,
                    help=f"longitude do corte a jusante (default {CLIP_WEST_LNG})")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import shapes
    from rasterio.transform import Affine, rowcol
    from rasterio.warp import reproject
    from scipy import ndimage
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union

    # ── DEM de SP numa overview ────────────────────────────────────────────
    with rasterio.open("/vsicurl/" + SAMPA_DEM_URL) as src:
        bounds = src.bounds
        lat_mid = (bounds.top + bounds.bottom) / 2
        native_m = src.res[0] * 111320.0 * math.cos(math.radians(lat_mid))
        factor = max(1, round(args.res_m / native_m))
        W, H = src.width // factor, src.height // factor
        print(f"→ DEM de SP: {src.width}×{src.height} @ {native_m:.1f} m → "
              f"{W}×{H} @ {native_m * factor:.1f} m")
        sp = src.read(1, out_shape=(H, W), resampling=Resampling.average).astype(np.float32)
        tr = src.transform * Affine.scale(src.width / W, src.height / H)
        crs = src.crs

    # ── FABDEM reprojetado na mesma grade ──────────────────────────────────
    fab = np.full((H, W), np.nan, dtype=np.float32)
    for lat in range(math.floor(bounds.bottom), math.floor(bounds.top - 1e-9) + 1):
        for lon in range(math.floor(bounds.left), math.floor(bounds.right - 1e-9) + 1):
            name = fabdem_tile_name(lat, lon)
            print(f"→ FABDEM {name}")
            part = np.full((H, W), np.nan, dtype=np.float32)
            with rasterio.open("/vsicurl/" + FABDEM_BASE + name) as fsrc:
                reproject(rasterio.band(fsrc, 1), part, dst_transform=tr, dst_crs=crs,
                          dst_nodata=np.nan, resampling=Resampling.bilinear)
            fab = np.where(np.isfinite(part), part, fab)

    # ── Fusão (mesma regra do DemSampler do build-viario.py) ───────────────
    ok_f = np.isfinite(fab) & (fab != -9999.0)
    ok_s = np.isfinite(sp) & (sp != -9999.0)
    bad_s = ok_s & ok_f & (np.abs(sp - fab) > SRC_DISAGREE_MAX_M)
    print(f"→ {int(bad_s.sum())} células do DEM de SP trocadas pelo FABDEM (buracos)")
    ok_s &= ~bad_s
    h = np.where(ok_s, sp, np.where(ok_f, fab, np.nan))

    # ── Banheira conexa às calhas ──────────────────────────────────────────
    wet = np.isfinite(h) & (h <= args.cota)
    _, c_west = rowcol(tr, args.west, lat_mid)
    wet[:, :max(0, c_west)] = False
    labels, n = ndimage.label(wet)                    # 4-vizinhança (default)
    keep = set()
    snap = max(1, round(SEED_SNAP_M / (native_m * factor)))
    for name, (lat, lng) in SEEDS.items():
        r0, c0 = rowcol(tr, lng, lat)
        r_lo, r_hi = max(0, r0 - snap), min(H, r0 + snap + 1)
        c_lo, c_hi = max(0, c0 - snap), min(W, c0 + snap + 1)
        win = h[r_lo:r_hi, c_lo:c_hi]
        if win.size == 0 or not np.isfinite(win).any():
            print(f"  ! semente fora do DEM: {name}")
            continue
        dr, dc = np.unravel_index(np.nanargmin(win), win.shape)
        r, c = r_lo + dr, c_lo + dc
        if labels[r, c] == 0:
            print(f"  ! semente acima da cota: {name} ({h[r, c]:.1f} m)")
            continue
        keep.add(int(labels[r, c]))
    if not keep:
        raise SystemExit("nenhuma semente caiu abaixo da cota — nada a assar")
    flood = np.isin(labels, list(keep))

    # Ilhas secas pequenas (aterros pontuais, viadutos no DEM) viram água;
    # morros de verdade no meio da várzea ficam.
    cell_ha = abs(tr.a * tr.e) * (111320.0 ** 2) * math.cos(math.radians(lat_mid)) / 1e4
    holes, nh = ndimage.label(~flood)
    if nh:
        sizes = ndimage.sum(np.ones_like(holes), holes, index=np.arange(1, nh + 1))
        small = np.flatnonzero(sizes * cell_ha < args.min_hole_ha) + 1
        flood |= np.isin(holes, small)
    area_km2 = flood.sum() * cell_ha / 100
    print(f"→ mancha: {area_km2:.1f} km² em {len(keep)} componente(s)")

    # ── Vetoriza, simplifica, grava ────────────────────────────────────────
    polys = [shape(g) for g, v in shapes(flood.astype(np.uint8), mask=flood, transform=tr) if v]
    geom = unary_union(polys).simplify(abs(tr.a) * 0.75, preserve_topology=True)

    def rnd(o):
        if isinstance(o, (list, tuple)):
            return [rnd(x) for x in o]
        return round(o, 5)  # ~1 m — abaixo da célula

    gj = mapping(geom)
    fc = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "cota_m": args.cota,
                "area_km2": round(area_km2, 1),
                "metodo": "banheira: relevo atual <= cota, conexo às calhas do "
                          "Tietê/Pinheiros/Tamanduateí",
                "fontes": "DEM de SP (GeoSampa) + FABDEM V1-2",
            },
            "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])},
        }],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))
    print(f"→ {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
