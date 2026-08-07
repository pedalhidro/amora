#!/usr/bin/env python
"""Constrói os FlatGeobuf (FGB) do viário da América do Sul a partir do
extrato Geofabrik, próprios pra leitura por RANGE REQUEST no navegador
("Menor energia pelo viário" / modo terreno).

Antes este script enxugava um gpkg local de SP (~152 MB → ~125 MB) que o app
baixava INTEIRO e consultava via sql.js. A migração pra FlatGeobuf muda tudo:
o índice espacial (packed Hilbert R-tree) do FGB permite ao cliente buscar só
os BYTES da bbox visível via HTTP Range — o tamanho do arquivo deixa de
importar pro usuário, o que viabiliza cobrir a América do Sul inteira.

Pipeline (fonte = south-america-latest.osm.pbf, ~4 GB, cacheado em ignore/):

  - `osmium tags-filter w/highway` pré-filtra o pbf (load-bearing: sem isso o
    driver OSM do ogr2ogr varre o continente inteiro por camada);
  - ogr2ogr → `south-america-viario.fgb` com geometria + 3 colunas finas
    (`bridge`, `tunnel`, `layer`) promovidas a campo via um osmconf.ini
    mínimo escrito pelo script (substitui o antigo instr/substr no hstore
    `other_tags`). Valores CRUS do OSM — o cliente já trata
    (`bridge && bridge !== 'no'`, `tunnel === 'yes'`, `parseInt(layer)`);
  - `--water`: `osmium tags-filter` de água → dois FGBs (FGB é mono-camada):
    `south-america-water-areas.fgb` (polígonos: natural=water /
    landuse=reservoir / waterway=riverbank) e
    `south-america-water-rivers.fgb` (linhas: waterway=river);
  - EPSG:4326 nativo do pbf — nada de reprojeção; índice espacial é o
    default do driver FlatGeobuf.

Depois de gerar, suba pro mesmo host dos DEMs. ATENÇÃO: **SEM -Z nos .fgb** —
`Content-Encoding: gzip` no GCS quebra os range requests que o cliente usa
(o transcoding decompressivo ignora Range):

    gcloud storage cp --cache-control="public,max-age=86400" \\
        ignore/south-america-viario.fgb \\
        ignore/south-america-water-areas.fgb \\
        ignore/south-america-water-rivers.fgb \\
        gs://telhas/viario/

(servidos em https://telhas.pedalhidrografi.co/viario/<nome>.fgb — ver
VIARIO_FGB_URL / WATER_*_FGB_URL em web/app.js). Verificação pós-upload:

    curl -sI -H 'Range: bytes=0-15' \\
        https://telhas.pedalhidrografi.co/viario/south-america-viario.fgb
    # esperar: 206 + Content-Range, sem Content-Encoding

Requisitos: ogr2ogr (GDAL ≥ 3.1, driver FlatGeobuf) e osmium no PATH;
`--graph` requer também os bindings Python do GDAL (`from osgeo import ogr` —
brew install gdal / apt install python3-gdal).

Roda:
    python scripts/build-viario.py                # só o viário
    python scripts/build-viario.py --water        # viário + água
    python scripts/build-viario.py --water --graph
    # teste rápido com um extrato pequeno (mesmos nomes de saída!):
    python scripts/build-viario.py --extract \\
        https://download.geofabrik.de/south-america/ecuador-latest.osm.pbf

Além dos FGBs, `--graph` (ou `--graph-only`, se o FGB do viário já existe)
cozinha o GRAFO BINÁRIO pré-pronto `ignore/sampa-viario-graph.bin` — nós com
elevação já amostrada (DEM de SP + FABDEM via /vsicurl) e tabuleiros
achatados — que é o que o "Menor energia pelo viário" baixa em vez de montar
o grafo por sessão. O grafo segue RECORTADO à região de SP (GRAPH_BBOX — a
cobertura dos DEMs manda; fora dela o roteamento cai pro FGB/Overpass).
Ver o bloco "Grafo pré-cozido" abaixo. Sobe com (-Z ok: é baixado inteiro):

    gcloud storage cp -Z ignore/sampa-viario-graph.bin gs://telhas/viario/
"""
from __future__ import annotations
import argparse
import gzip
import math
import os
import shutil
import struct
import subprocess
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORE = ROOT / "ignore"

# Fonte: extrato Geofabrik da América do Sul (~4 GB). Cacheado em ignore/ e
# MANTIDO por padrão (re-baixar dói) — `--drop-pbf` apaga ao final.
GEOFABRIK_URL = "https://download.geofabrik.de/south-america-latest.osm.pbf"

OUT_VIARIO = IGNORE / "south-america-viario.fgb"
OUT_WATER_AREAS = IGNORE / "south-america-water-areas.fgb"
OUT_WATER_RIVERS = IGNORE / "south-america-water-rivers.fgb"

# osmconf.ini mínimo pro driver OSM do GDAL: só a camada `lines` interessa e
# só bridge/tunnel/layer viram campo (highway fica implícito no pré-filtro,
# mas entra como campo pra permitir -where "highway IS NOT NULL" — proteção
# contra um pbf não pré-filtrado). `other_tags=no` mantém o FGB fino.
OSMCONF = """\
closed_ways_are_polygons=aeroway,amenity,boundary,building,craft,geological,historic,landuse,leisure,military,natural,office,place,shop,sport,tourism,highway=platform,public_transport=platform

[points]
osm_id=no
attributes=name
other_tags=no

[lines]
osm_id=no
attributes=highway,bridge,tunnel,layer,waterway
other_tags=no

[multipolygons]
osm_id=no
osm_way_id=no
attributes=natural,landuse,waterway
other_tags=no

[multilinestrings]
osm_id=no
attributes=type
other_tags=no

[other_relations]
osm_id=no
attributes=type
other_tags=no
"""


def _run(cmd: list[str]) -> None:
    print("$ " + " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def download_pbf(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"→ reusando {dest.name} ({dest.stat().st_size / 1e6:.0f} MB) — apague pra re-baixar")
        return
    print(f"→ baixando extrato Geofabrik → {dest.name}")
    _run(["curl", "-fL", "--retry", "4", "-C", "-", "-o", dest, url])


def build_viario_fgb(pbf: Path, out: Path) -> None:
    """south-america-viario.fgb: linhas highway com bridge/tunnel/layer."""
    hw_pbf = IGNORE / (pbf.stem + "-highways.osm.pbf")
    conf = IGNORE / "osmconf-viario.ini"
    conf.write_text(OSMCONF)
    if hw_pbf.exists() and hw_pbf.stat().st_mtime >= pbf.stat().st_mtime:
        print(f"→ reusando {hw_pbf.name} (apague pra re-filtrar)")
    else:
        _run(["osmium", "tags-filter", pbf, "w/highway", "-o", hw_pbf, "--overwrite"])
    out.unlink(missing_ok=True)
    # OSM_MAX_TMPFILE_SIZE (MB): cache de nós do driver OSM num tempfile só.
    # TEMPORARY_DIR: o sort Hilbert do driver FGB escreve temporários grandes —
    # aponta pra ignore/ (o /tmp do sandbox/laptop pode ser pequeno).
    _run(["ogr2ogr", "-f", "FlatGeobuf", out, hw_pbf, "lines",
          "-oo", f"CONFIG_FILE={conf}",
          "-select", "bridge,tunnel,layer",
          "-where", "highway IS NOT NULL",
          "-nlt", "LINESTRING",
          "-lco", f"TEMPORARY_DIR={IGNORE}",
          "--config", "OSM_MAX_TMPFILE_SIZE", "4000"])
    print(f"→ {out.name}: {out.stat().st_size / 1e6:.0f} MB")


def build_water_fgbs(pbf: Path) -> None:
    """Água em DOIS FGBs (FGB é mono-camada; polígono e linha separados —
    mesma razão dos dois pipelines osmium antigos: o contorno do polígono não
    pode duplicar como linha). O app rasteriza: polígono→preenche, linha→barreira."""
    ar_pbf = IGNORE / "water-area.osm.pbf"
    rv_pbf = IGNORE / "water-river.osm.pbf"
    _run(["osmium", "tags-filter", pbf, "-o", ar_pbf, "--overwrite",
          "nwr/natural=water", "nwr/landuse=reservoir", "nwr/waterway=riverbank"])
    _run(["osmium", "tags-filter", pbf, "-o", rv_pbf, "--overwrite", "w/waterway=river"])
    conf = IGNORE / "osmconf-viario.ini"
    conf.write_text(OSMCONF)
    OUT_WATER_AREAS.unlink(missing_ok=True)
    _run(["ogr2ogr", "-f", "FlatGeobuf", OUT_WATER_AREAS, ar_pbf, "multipolygons",
          "-oo", f"CONFIG_FILE={conf}",
          "-select", "natural",
          "-nlt", "MULTIPOLYGON",
          "-lco", f"TEMPORARY_DIR={IGNORE}",
          "--config", "OSM_MAX_TMPFILE_SIZE", "4000"])
    OUT_WATER_RIVERS.unlink(missing_ok=True)
    _run(["ogr2ogr", "-f", "FlatGeobuf", OUT_WATER_RIVERS, rv_pbf, "lines",
          "-oo", f"CONFIG_FILE={conf}",
          "-select", "waterway",
          "-nlt", "LINESTRING",
          "-lco", f"TEMPORARY_DIR={IGNORE}",
          "--config", "OSM_MAX_TMPFILE_SIZE", "4000"])
    for tmp in (ar_pbf, rv_pbf):
        tmp.unlink(missing_ok=True)
    print(f"→ {OUT_WATER_AREAS.name}: {OUT_WATER_AREAS.stat().st_size / 1e6:.0f} MB · "
          f"{OUT_WATER_RIVERS.name}: {OUT_WATER_RIVERS.stat().st_size / 1e6:.0f} MB")


# ─── Grafo pré-cozido (--graph) ───────────────────────────────────────────────
# Em vez de o navegador consultar o FGB + amostrar o DEM + montar o grafo A
# CADA sessão, o bake produz `sampa-viario-graph.bin`: um grafo binário
# compacto com as ELEVAÇÕES JÁ AMOSTRADAS por nó (DEM de SP ~5 m onde cobre,
# FABDEM no resto — mesma prioridade do runtime) e os tabuleiros (ponte/túnel)
# já achatados em rampa entre os apoios. O app decodifica com typed arrays
# (zero parse pesado) e roteia direto — ver ensureViarioGraph /
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
DEFAULT_GRAPH_OUT = IGNORE / "sampa-viario-graph.bin"
GRAPH_TMP = IGNORE / "graph-tmp"

# Recorte do grafo: a extensão do antigo gpkg de SP (a cobertura DEM manda —
# fora dela não há elevação boa pra assar). O FGB continental é filtrado a
# esta bbox via SetSpatialFilterRect. Sobrepõe com --graph-bbox W,S,E,N.
GRAPH_BBOX = (-47.419098, -24.041109, -45.807267, -23.088709)


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


def _seg_len_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Mesma equiretangular do app.js (M_DEG e cos da latitude média)."""
    d_lat = (b[1] - a[1]) * M_DEG
    d_lng = (b[0] - a[0]) * M_DEG * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot(d_lat, d_lng)


def _iter_fgb_lines(fgb: Path, bbox: tuple[float, float, float, float]):
    """Itera (pts, bridge, tunnel) das linhas do FGB que tocam a bbox, via
    bindings Python do GDAL (o índice espacial do FGB serve o filtro).
    pts = [(lng, lat), …]. Substitui o antigo leitor sqlite3+WKB do gpkg."""
    try:
        from osgeo import ogr
    except ImportError as e:
        raise RuntimeError(
            "bindings Python do GDAL ausentes (from osgeo import ogr) — "
            "brew install gdal / apt install python3-gdal") from e
    ogr.UseExceptions()
    ds = ogr.Open(str(fgb))
    if ds is None:
        raise RuntimeError(f"não consegui abrir {fgb}")
    lyr = ds.GetLayer(0)
    w, s, e, n = bbox
    lyr.SetSpatialFilterRect(w, s, e, n)
    defn = lyr.GetLayerDefn()
    i_bridge = defn.GetFieldIndex("bridge")
    i_tunnel = defn.GetFieldIndex("tunnel")
    for feat in lyr:
        g = feat.GetGeometryRef()
        if g is None:
            continue
        bridge = feat.GetField(i_bridge) if i_bridge >= 0 else None
        tunnel = feat.GetField(i_tunnel) if i_tunnel >= 0 else None
        t = g.GetGeometryType()
        flat = ogr.GT_Flatten(t)
        if flat == ogr.wkbLineString:
            parts = [g]
        elif flat == ogr.wkbMultiLineString:
            parts = [g.GetGeometryRef(k) for k in range(g.GetGeometryCount())]
        else:
            continue
        for part in parts:
            pts = [(p[0], p[1]) for p in part.GetPoints()]
            if len(pts) >= 2:
                yield pts, bridge, tunnel


def bake_graph(fgb: Path, out: Path, graph_bbox: tuple[float, float, float, float]) -> None:
    pad = 0.01
    bbox = (math.floor((graph_bbox[0] - pad) / ARCSEC) * ARCSEC,
            math.floor((graph_bbox[1] - pad) / ARCSEC) * ARCSEC,
            math.ceil((graph_bbox[2] + pad) / ARCSEC) * ARCSEC,
            math.ceil((graph_bbox[3] + pad) / ARCSEC) * ARCSEC)
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

    n_feat = n_deck = 0
    for pts, bridge, tunnel in _iter_fgb_lines(fgb, graph_bbox):
        is_deck = bool(bridge and bridge != "no") or tunnel == "yes"
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


def _print_upload_help() -> None:
    print("\nsuba pro bucket (SEM -Z nos .fgb — gzip quebraria os range requests):\n"
          "    gcloud storage cp --cache-control=\"public,max-age=86400\" \\\n"
          f"        {OUT_VIARIO} \\\n"
          f"        {OUT_WATER_AREAS} \\\n"
          f"        {OUT_WATER_RIVERS} \\\n"
          "        gs://telhas/viario/\n"
          "e confira VIARIO_FGB_URL / WATER_*_FGB_URL em web/app.js.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Constrói os FGBs do viário/água da América do Sul (+ grafo de SP).")
    ap.add_argument("--extract", metavar="URL", default=GEOFABRIK_URL,
                    help="URL de extrato Geofabrik alternativo (teste rápido; "
                         "MESMOS nomes de saída)")
    ap.add_argument("--out", dest="dst", type=Path, default=OUT_VIARIO,
                    help=f"FGB de saída do viário (default: {OUT_VIARIO.relative_to(ROOT)})")
    ap.add_argument("--water", action="store_true",
                    help="também gera os dois FGBs de água (áreas + rios)")
    ap.add_argument("--drop-pbf", action="store_true",
                    help="apaga o .pbf do Geofabrik ao final (default: mantém — é caro re-baixar)")
    ap.add_argument("--graph", action="store_true",
                    help="depois dos FGBs, também cozinha o grafo binário (sampa-viario-graph.bin)")
    ap.add_argument("--graph-only", action="store_true",
                    help="só cozinha o grafo a partir do FGB de --out (que já deve existir)")
    ap.add_argument("--graph-out", type=Path, default=DEFAULT_GRAPH_OUT,
                    help=f"saída do grafo binário (default: {DEFAULT_GRAPH_OUT.relative_to(ROOT)})")
    ap.add_argument("--graph-bbox", metavar="W,S,E,N",
                    help="recorte do grafo (default: extensão SP do antigo gpkg)")
    args = ap.parse_args()

    graph_bbox = GRAPH_BBOX
    if args.graph_bbox:
        parts = [float(x) for x in args.graph_bbox.split(",")]
        if len(parts) != 4:
            print("erro: --graph-bbox precisa de W,S,E,N", file=sys.stderr)
            return 1
        graph_bbox = (parts[0], parts[1], parts[2], parts[3])

    if not shutil.which("ogr2ogr"):
        print("erro: ogr2ogr (GDAL) não está no PATH "
              "(brew install gdal / apt install gdal-bin).", file=sys.stderr)
        return 1

    if args.graph_only:
        if not args.dst.exists():
            print(f"erro: --graph-only precisa do FGB já gerado em {args.dst}", file=sys.stderr)
            return 1
        try:
            bake_graph(args.dst, args.graph_out, graph_bbox)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"erro: bake do grafo falhou: {e}", file=sys.stderr)
            return 1
        return 0

    if not shutil.which("osmium"):
        print("erro: osmium não está no PATH (brew install osmium-tool / "
              "apt install osmium-tool).", file=sys.stderr)
        return 1

    IGNORE.mkdir(exist_ok=True)
    pbf = IGNORE / Path(args.extract).name
    try:
        download_pbf(args.extract, pbf)
        build_viario_fgb(pbf, args.dst)
        if args.water:
            build_water_fgbs(pbf)
        if args.graph:
            bake_graph(args.dst, args.graph_out, graph_bbox)
    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1

    if args.drop_pbf:
        pbf.unlink(missing_ok=True)
    _print_upload_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
