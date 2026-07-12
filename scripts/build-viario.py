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

Além do gpkg, `--graph` (ou `--graph-only`, se o gpkg de --out já existe)
cozinha o GRAFO BINÁRIO pré-pronto `ignore/sampa-viario-graph.bin` — nós com
elevação já amostrada (DEM de SP + FABDEM via /vsicurl) e tabuleiros
achatados — que é o que o "Menor energia pelo viário" baixa hoje em vez do
gpkg inteiro (o gpkg segue servido pro modo terreno: camada water/portais).
Ver o bloco "Grafo pré-cozido" abaixo. Sobe com:

    gcloud storage cp -Z ignore/sampa-viario-graph.bin gs://telhas/viario/
"""
from __future__ import annotations
import argparse
import gzip
import math
import os
import shutil
import sqlite3
import struct
import subprocess
import sys
from array import array
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


# ─── Grafo pré-cozido (--graph) ───────────────────────────────────────────────
# Em vez de o navegador baixar o gpkg inteiro (~125 MB) + amostrar o DEM +
# montar o grafo A CADA sessão, o bake produz `sampa-viario-graph.bin`: um
# grafo binário compacto com as ELEVAÇÕES JÁ AMOSTRADAS por nó (DEM de SP ~5 m
# onde cobre, FABDEM no resto — mesma prioridade do runtime) e os tabuleiros
# (ponte/túnel) já achatados em rampa entre os apoios. O app decodifica com
# typed arrays (zero parse pesado) e roteia direto — ver ensureViarioGraph /
# bakedViarioRoute em web/app.js.
#
# Fidelidade com o viarioGraphRoute do app: mesma quantização de junção
# (1e-6 grau), mesma fórmula de distância (equiretangular · cos da latitude
# média) e arestas longas DENSIFICADAS a ~1 célula do FABDEM (30,9 m) — os
# substeps do profile-sampling do runtime viram nós de grau 2, o que dá o
# MESMO custo total por aresta (o custo v2 é aditivo ao longo da cadeia) sem
# precisar do DEM no cliente.
#
# Formato (little-endian; seções alinhadas a 4 bytes — pad entre elas):
#   header: magic 'PHVG' (4 bytes), u32 version=1, u32 N, u32 NESC, u32 EX,
#           u32 reserved
#   dLat  i16[N]   delta em µgrau do nó anterior na ordem de emissão
#   dLng  i16[N]   (sentinela dLat=-32768 → coords absolutas na lista esc)
#   elev  i16[N]   elevação em decímetros (nodata → 0, igual ao runtime)
#   flags u8[N]    bit0 = interior de tabuleiro (deck), bit1 = aresta de
#                  cadeia pro nó i+1 (dist em chainDist[i])
#   chainDist u16[N]  comprimento da aresta de cadeia em dm (0 se sem bit1)
#   escIdx u32[NESC], escLat i32[NESC], escLng i32[NESC]  escapes (µgrau abs)
#   exU u32[EX], exV u32[EX], exDist u16[EX]  arestas explícitas (junções)
#
# O JS reconstrói o CSR (indptr/targets) num passe — ver decodeViarioGraph.

FABDEM_BASE = "https://telhas.pedalhidrografi.co/fabdem/"
SAMPA_DEM_URL = "https://telhas.pedalhidrografi.co/dem/sampa_geral.tif"
ARCSEC = 1.0 / 3600.0            # célula do FABDEM (~30,9 m) — grade do bake
M_DEG = 111320.0                 # mesma constante do app.js
DENSIFY_M = ARCSEC * M_DEG       # ~30,92 m — casa com o cellM do runtime
DECK_MAX_SEG_M = 600.0           # só pra caber em u16 dm; rampa é linear mesmo
DEFAULT_GRAPH_OUT = ROOT / "ignore" / "sampa-viario-graph.bin"
GRAPH_TMP = ROOT / "ignore" / "graph-tmp"


def fabdem_tile_name(lat: int, lon: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}_FABDEM_V1-2.tif"


def _url_exists(url: str) -> bool:
    # curl em vez de urllib: o Python do python.org no macOS vem sem os
    # certificados TLS do sistema (CERTIFICATE_VERIFY_FAILED); o curl usa os
    # do SO — e o script já depende dele pro download do Geofabrik.
    r = subprocess.run(["curl", "-sIf", "-o", os.devnull, "--max-time", "30", url])
    return r.returncode == 0


def _parse_envi_hdr(hdr: Path) -> tuple[int, int]:
    """(samples, lines) do header ENVI."""
    samples = lines = None
    for ln in hdr.read_text().splitlines():
        k, _, v = ln.partition("=")
        k = k.strip().lower()
        if k == "samples":
            samples = int(v.strip())
        elif k == "lines":
            lines = int(v.strip())
    if not samples or not lines:
        raise RuntimeError(f"header ENVI sem samples/lines: {hdr}")
    return samples, lines


def _warp_to_grid(src: str, dst: Path, bbox: tuple[float, float, float, float],
                  nodata: str | None) -> None:
    """gdalwarp da fonte pra grade global do FABDEM (ARCSEC) recortada à bbox.
    -r near = mesmo vizinho-mais-próximo do runtime. Reusa o artefato se já
    existe (apague ignore/graph-tmp/ pra forçar re-warp)."""
    if dst.with_suffix(".bin").exists():
        print(f"→ reusando {dst.with_suffix('.bin').name} (apague ignore/graph-tmp/ pra re-warpar)")
        return
    w, s, e, n = bbox
    cmd = ["gdalwarp", "-of", "ENVI", "-ot", "Float32", "-r", "near",
           "-te", f"{w:.10f}", f"{s:.10f}", f"{e:.10f}", f"{n:.10f}",
           "-tr", f"{ARCSEC:.12f}", f"{ARCSEC:.12f}",
           "-multi", "-wo", "NUM_THREADS=ALL_CPUS",
           "-dstnodata", "-9999"]
    if nodata is not None:
        cmd += ["-srcnodata", nodata]
    cmd += [src, str(dst.with_suffix(".bin"))]
    _run(cmd)


class DemSampler:
    """Elevação por lat/lng na grade do bake: DEM de SP (5 m, reamostrado) onde
    cobre, FABDEM no resto, 0.0 onde nenhum cobre (igual ao sampleElev do
    runtime, que devolve 0 fora da máscara)."""

    def __init__(self, bbox: tuple[float, float, float, float]) -> None:
        GRAPH_TMP.mkdir(parents=True, exist_ok=True)
        w, s, e, n = bbox
        self.west, self.north = w, n
        self.W = round((e - w) / ARCSEC)
        self.H = round((n - s) / ARCSEC)

        # FABDEM: VRT dos tiles 1°×1° que existem no bucket.
        tiles = []
        for lat in range(math.floor(s), math.floor(n - 1e-9) + 1):
            for lon in range(math.floor(w), math.floor(e - 1e-9) + 1):
                url = FABDEM_BASE + fabdem_tile_name(lat, lon)
                if _url_exists(url):
                    tiles.append("/vsicurl/" + url)
                else:
                    print(f"  (FABDEM ausente: {fabdem_tile_name(lat, lon)} — pulando)")
        if not tiles:
            raise RuntimeError("nenhum tile FABDEM encontrado pra bbox")
        vrt = GRAPH_TMP / "fabdem.vrt"
        if not vrt.exists():
            _run(["gdalbuildvrt", str(vrt)] + tiles)
        _warp_to_grid(str(vrt), GRAPH_TMP / "fabdem-grid", bbox, nodata="-9999")
        _warp_to_grid("/vsicurl/" + SAMPA_DEM_URL, GRAPH_TMP / "sampa-grid", bbox, nodata=None)

        self.fab = self._read_grid(GRAPH_TMP / "fabdem-grid")
        self.sampa = self._read_grid(GRAPH_TMP / "sampa-grid")

    def _read_grid(self, base: Path) -> array:
        samples, lines = _parse_envi_hdr(base.with_suffix(".hdr"))
        if (samples, lines) != (self.W, self.H):
            raise RuntimeError(f"{base.name}: grade {samples}×{lines} ≠ esperada {self.W}×{self.H}")
        a = array("f")
        with open(base.with_suffix(".bin"), "rb") as f:
            a.fromfile(f, self.W * self.H)
        if sys.byteorder != "little":
            a.byteswap()
        return a

    def elev(self, lat: float, lng: float) -> float:
        r = round((self.north - lat) / ARCSEC)
        c = round((lng - self.west) / ARCSEC)
        if r < 0 or r >= self.H or c < 0 or c >= self.W:
            return 0.0
        i = r * self.W + c
        v = self.sampa[i]
        if v != -9999.0 and v == v:      # != nodata e != NaN
            return v
        v = self.fab[i]
        if v != -9999.0 and v == v:
            return v
        return 0.0


def _parse_gpkg_lines(blob: bytes) -> list[list[tuple[float, float]]] | None:
    """GPKG StandardGeoPackageBinary → [[(lng,lat),…],…] ((Multi)LineString,
    2-D/Z/M nas codificações ISO e EWKB — port do parseGpkgGeom do app.js)."""
    if len(blob) < 8 or blob[:2] != b"GP":
        return None
    env = (blob[3] >> 1) & 7
    off = 8 + [0, 32, 48, 48, 64, 0, 0, 0][env]

    def wkb_line(off: int) -> tuple[list[tuple[float, float]] | None, int]:
        le = blob[off] == 1
        fmt = "<" if le else ">"
        t = struct.unpack_from(fmt + "I", blob, off + 1)[0]
        code = t & 0x0FFFFFFF
        base, isodim = code % 1000, code // 1000
        has_z = bool(t & 0x80000000) or isodim in (1, 3)
        has_m = bool(t & 0x40000000) or isodim in (2, 3)
        stride = 16 + (8 if has_z else 0) + (8 if has_m else 0)
        if base != 2:
            return None, base
        n = struct.unpack_from(fmt + "I", blob, off + 5)[0]
        p = off + 9
        pts = [struct.unpack_from(fmt + "dd", blob, p + i * stride) for i in range(n)]
        return pts, p + n * stride

    le = blob[off] == 1
    fmt = "<" if le else ">"
    t = struct.unpack_from(fmt + "I", blob, off + 1)[0]
    base = (t & 0x0FFFFFFF) % 1000
    if base == 2:
        pts, _ = wkb_line(off)
        return [pts] if pts else None
    if base == 5:  # MultiLineString — cada filho repete o header WKB
        k = struct.unpack_from(fmt + "I", blob, off + 5)[0]
        p = off + 9
        out = []
        for _ in range(k):
            pts, p = wkb_line(p)
            if pts is None:
                return None
            out.append(pts)
        return out
    return None


def _seg_len_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Mesma equiretangular do app.js (M_DEG e cos da latitude média)."""
    d_lat = (b[1] - a[1]) * M_DEG
    d_lng = (b[0] - a[0]) * M_DEG * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot(d_lat, d_lng)


def bake_graph(gpkg: Path, out: Path) -> None:
    db = sqlite3.connect(str(gpkg))
    row = db.execute(
        "SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name = ?",
        (TABLE,)).fetchone()
    if not row:
        raise RuntimeError(f"camada {TABLE!r} não está em gpkg_contents de {gpkg}")
    pad = 0.01
    bbox = (math.floor((row[0] - pad) / ARCSEC) * ARCSEC,
            math.floor((row[1] - pad) / ARCSEC) * ARCSEC,
            math.ceil((row[2] + pad) / ARCSEC) * ARCSEC,
            math.ceil((row[3] + pad) / ARCSEC) * ARCSEC)
    print(f"→ bbox do grafo: {bbox}")
    dem = DemSampler(bbox)
    print(f"→ DEM {dem.W}×{dem.H} pronto")

    # Nós — mesma identidade de junção do runtime: round(coord · 1e6).
    key2id: dict[tuple[int, int], int] = {}
    lat_us = array("i"); lng_us = array("i")     # µgrau absoluto
    elev_dm = array("h"); flags = array("B"); chain_dm = array("H")
    ex_u = array("I"); ex_v = array("I"); ex_dm = array("H")

    def get_node(lng: float, lat: float, elev_m: float | None, deck: bool) -> int:
        k = (round(lat * 1e6), round(lng * 1e6))
        nid = key2id.get(k)
        if nid is not None:
            return nid                      # primeiro registro vence (como no app)
        nid = len(lat_us)
        key2id[k] = nid
        lat_us.append(k[0]); lng_us.append(k[1])
        h = dem.elev(lat, lng) if elev_m is None else elev_m
        elev_dm.append(max(-32767, min(32767, round(h * 10))))
        flags.append(1 if deck else 0)
        chain_dm.append(0)
        return nid

    def add_edge(a: int, b: int, dist_m: float) -> None:
        if a == b:
            return
        dm = min(65535, round(dist_m * 10))
        if b == a + 1 and (flags[a] & 2) == 0:
            flags[a] |= 2
            chain_dm[a] = dm
        else:
            ex_u.append(a); ex_v.append(b); ex_dm.append(dm)

    cur = db.execute(f'SELECT "{GEOM}", bridge, tunnel FROM "{TABLE}"')
    n_feat = n_deck = 0
    for geom_blob, bridge, tunnel in cur:
        lines = _parse_gpkg_lines(geom_blob)
        if not lines:
            continue
        is_deck = bool(bridge and bridge != "no") or tunnel == "yes"
        for pts in lines:
            if len(pts) < 2:
                continue
            n_feat += 1
            if is_deck:
                n_deck += 1
            # Rampa do tabuleiro: elevação linear (por comprimento de arco)
            # entre os apoios NO SOLO — igual ao `flat` do viarioGraphRoute.
            ramp = None
            if is_deck:
                h0 = dem.elev(pts[0][1], pts[0][0])
                h1 = dem.elev(pts[-1][1], pts[-1][0])
                arc = [0.0]
                for i in range(1, len(pts)):
                    arc.append(arc[-1] + _seg_len_m(pts[i - 1], pts[i]))
                total = arc[-1]
                ramp = [h0 + (h1 - h0) * (a / total) if total > 0 else h0 for a in arc]
            prev_id = -1
            for i, (lng, lat) in enumerate(pts):
                interior = is_deck and 0 < i < len(pts) - 1
                nid = get_node(lng, lat, ramp[i] if interior else None, interior)
                if prev_id >= 0 and nid != prev_id:
                    d = _seg_len_m(pts[i - 1], pts[i])
                    step = DECK_MAX_SEG_M if is_deck else DENSIFY_M
                    nsub = max(1, math.ceil(d / step))
                    if nsub == 1:
                        add_edge(prev_id, nid, d)
                    else:
                        # Densifica: os substeps do profile-sampling do runtime
                        # viram nós de grau 2 (custo aditivo → total idêntico).
                        # Num tabuleiro, os pontos intermediários seguem a rampa.
                        la0, lg0 = pts[i - 1][1], pts[i - 1][0]
                        la1, lg1 = lat, lng
                        pid = prev_id
                        for sct in range(1, nsub):
                            tt = sct / nsub
                            slat = la0 + (la1 - la0) * tt
                            slng = lg0 + (lg1 - lg0) * tt
                            selev = None
                            if is_deck:
                                selev = ramp[i - 1] + (ramp[i] - ramp[i - 1]) * tt
                            sid = get_node(slng, slat, selev, is_deck)
                            add_edge(pid, sid, d / nsub)
                            pid = sid
                        add_edge(pid, nid, d / nsub)
                prev_id = nid
    db.close()

    n = len(lat_us)
    n_chain = sum(1 for f in flags if f & 2)
    print(f"→ grafo: {n} nós · {n_chain} arestas de cadeia · {len(ex_u)} explícitas · "
          f"{n_feat} linhas ({n_deck} tabuleiros)")

    # Deltas µgrau (i16) na ordem de emissão; overflow → escape absoluto.
    d_lat = array("h"); d_lng = array("h")
    esc_idx = array("I"); esc_lat = array("i"); esc_lng = array("i")
    p_lat = p_lng = 0
    for i in range(n):
        dla = lat_us[i] - p_lat
        dlg = lng_us[i] - p_lng
        if -32767 <= dla <= 32767 and -32767 <= dlg <= 32767:
            d_lat.append(dla); d_lng.append(dlg)
        else:
            d_lat.append(-32768); d_lng.append(0)
            esc_idx.append(i); esc_lat.append(lat_us[i]); esc_lng.append(lng_us[i])
        p_lat, p_lng = lat_us[i], lng_us[i]

    def pad4(f) -> None:
        f.write(b"\0" * ((4 - f.tell() % 4) % 4))

    with open(out, "wb") as f:
        f.write(b"PHVG")
        f.write(struct.pack("<IIIII", 1, n, len(esc_idx), len(ex_u), 0))
        for arr in (d_lat, d_lng, elev_dm, flags, chain_dm,
                    esc_idx, esc_lat, esc_lng, ex_u, ex_v, ex_dm):
            pad4(f)
            if sys.byteorder != "little":
                arr = array(arr.typecode, arr); arr.byteswap()
            arr.tofile(f)
    raw_mb = out.stat().st_size / 1e6
    with open(out, "rb") as f:
        gz = len(gzip.compress(f.read(), 6)) / 1e6
    print(f"\nok: {out.name} — {raw_mb:.0f} MB raw, ~{gz:.0f} MB gzip. Suba com:\n"
          f"    gcloud storage cp -Z {out} gs://telhas/viario/sampa-viario-graph.bin\n"
          f"(o -Z guarda gzip + Content-Encoding; ver VIARIO_GRAPH_URL em web/app.js)")


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
    ap.add_argument("--graph", action="store_true",
                    help="depois do gpkg, também cozinha o grafo binário (sampa-viario-graph.bin)")
    ap.add_argument("--graph-only", action="store_true",
                    help="só cozinha o grafo a partir do gpkg de --out (que já deve existir)")
    ap.add_argument("--graph-out", type=Path, default=DEFAULT_GRAPH_OUT,
                    help="saída do grafo binário (default: ignore/sampa-viario-graph.bin)")
    args = ap.parse_args()

    if not shutil.which("ogr2ogr"):
        print("erro: ogr2ogr (GDAL) não está no PATH "
              "(brew install gdal / apt install gdal-bin).", file=sys.stderr)
        return 1
    if args.graph_only:
        if not args.dst.exists():
            print(f"erro: --graph-only precisa do gpkg já gerado em {args.dst}", file=sys.stderr)
            return 1
        try:
            bake_graph(args.dst, args.graph_out)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"erro: bake do grafo falhou: {e}", file=sys.stderr)
            return 1
        return 0
    if not args.src.exists():
        print(f"erro: fonte não encontrada: {args.src}", file=sys.stderr)
        return 1
    if args.dst.exists():
        args.dst.unlink()  # ogr2ogr não sobrescreve gpkg existente

    # Geometria + bridge/tunnel/layer extraídos do hstore other_tags; só ruas;
    # reprojetado pra WGS84; R-tree reconstruído pelo driver de saída.
    # other_tags tem o formato `"chave"=>"valor",…` — extraímos os 3 campos com
    # instr/substr (sem precisar de extensão). `"layer"=>"` tem 10 caracteres.
    # NULLIF(...,0) protege contra hstore malformado sem aspas de fechamento:
    # sem o guard, instr()=0 vira length=-1 e o SQLite conta pra trás,
    # produzindo um "layer" bogus em vez de degradar pra NULL.
    sql = f"""SELECT {GEOM},
      CASE WHEN instr(other_tags,'"bridge"=>')>0 AND instr(other_tags,'"bridge"=>"no"')=0 THEN 'yes' END AS bridge,
      CASE WHEN instr(other_tags,'"tunnel"=>"yes"')>0 THEN 'yes' END AS tunnel,
      CASE WHEN instr(other_tags,'"layer"=>"')>0 THEN CAST(substr(
        other_tags, instr(other_tags,'"layer"=>"')+10,
        NULLIF(instr(substr(other_tags, instr(other_tags,'"layer"=>"')+10),'"'), 0)-1) AS INTEGER) END AS layer
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

    if args.graph:
        try:
            bake_graph(args.dst, args.graph_out)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"erro: bake do grafo falhou: {e}", file=sys.stderr)
            return 1

    src_mb = args.src.stat().st_size / 1e6
    dst_mb = args.dst.stat().st_size / 1e6
    print(f"\nok: {args.src.name} ({src_mb:.0f} MB) → "
          f"{args.dst.name} ({dst_mb:.0f} MB){' + camada water' if args.water else ''}")
    print("suba pro bucket telhas/viario/ e confira VIARIO_GPKG_URL em web/app.js.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
