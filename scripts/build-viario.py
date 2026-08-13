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
  - `--layers`: os dois FGBs das CAMADAS DE MAPA (o que antes vinha do
    Overpass ao vivo) + o GeoJSON da rede cicloviária do coletivo:
    `south-america-hidro.fgb` (linhas: `waterway=*` + `natural=ridge`, com
    `tunnel`/`name` — a camada "Morros e Águas"),
    `south-america-cicloinfra.fgb` (linhas: ciclovias, caminhos compartilhados
    e vias com ciclofaixa — a camada "Cicloinfra OSM") e
    `ph-cycle-network.geojson` (as relations `cycle_network=BR:PedalHidrografico`,
    minúsculo, baixado inteiro pelo cliente);
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
    # o que o job semanal roda (pula o viário, que é o build caro):
    python scripts/build-viario.py --no-viario --water --layers
    # teste rápido com um extrato pequeno (mesmos nomes de saída!):
    python scripts/build-viario.py --extract \\
        https://download.geofabrik.de/south-america/ecuador-latest.osm.pbf

Além dos FGBs, `--graph` (ou `--graph-only`, se o FGB do viário já existe)
cozinha o GRAFO BINÁRIO pré-pronto `ignore/sampa-viario-graph.bin` — nós com
elevação já amostrada (DEM de SP + FABDEM via /vsicurl) e tabuleiros
achatados — que é o que o "Menor energia pelo viário" baixa em vez de montar
o grafo por sessão. O grafo segue RECORTADO à região de SP (GRAPH_BBOX — a
cobertura dos DEMs manda; fora dela o roteamento cai pro FGB/Overpass).

As elevações levam o TRATAMENTO σ do mapa (`--graph-sigma`, default 30 m =
o demSmoothSigmaM do app.js) sobre o mosaico fundido, ANTES de amostrar por
nó — senão o grafo pré-cozido seria o único consumidor de roteamento lendo
relevo cru, e o ruído sub-célula inflaria h₊ (medido num trecho plano de
5,5 km: 110 kJ com elevação crua contra 79 kJ tratada, pra uma estimativa
route-level de 66 kJ). `--graph-src` aceita um `/vsicurl/https://…`, então
dá pra assar sem baixar os ~4,5 GB do FGB (o índice serve só a bbox).

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
import time
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
# Camadas de mapa (--layers): o que a "Morros e Águas" e a "Cicloinfra OSM"
# liam do Overpass ao vivo, agora assadas pro mesmo host dos outros FGBs.
OUT_HIDRO = IGNORE / "south-america-hidro.fgb"
OUT_CICLOINFRA = IGNORE / "south-america-cicloinfra.fgb"
OUT_PH_NETWORK = IGNORE / "ph-cycle-network.geojson"

# Valores de `cycleway[:left|:right|:both]` que contam como ciclofaixa — os
# MESMOS do regex que a consulta Overpass usava, agora como lista SQL (o
# -where do OGR não tem regex portátil).
CYCLEWAY_LANE_VALUES = ("lane", "track", "opposite_lane", "opposite_track",
                        "shared_lane", "share_busway")

# A rede cicloviária do coletivo no OSM: relations com esta tag. São poucas e
# locais — viram um GeoJSON minúsculo (uma MultiLineString por relation, com
# name/ref) que o cliente baixa INTEIRO, em vez de um FGB por range request.
PH_CYCLE_NETWORK = "BR:PedalHidrografico"

# osmconf.ini mínimo pro driver OSM do GDAL. `attributes=` é a UNIÃO do que
# todas as saídas precisam (highway fica implícito no pré-filtro, mas entra
# como campo pra permitir -where "highway IS NOT NULL" — proteção contra um
# pbf não pré-filtrado). Listar demais NÃO engorda saída nenhuma: cada build
# fixa o próprio schema com `-select`, e `other_tags=no` mantém os FGBs finos.
#
# ATENÇÃO ao `:` — o GDAL aceita a chave crua do OSM aqui (`cycleway:left`)
# mas SANEIA o nome do campo pra `cycleway_left`. É esse nome saneado que vale
# no `-select`, no `-where` e do lado do cliente (`props.cycleway_left` em
# web/app.js); usar `cycleway:left` ali dá
# `ERROR 1: "cycleway:left" not recognised as an available field`.
OSMCONF = """\
closed_ways_are_polygons=aeroway,amenity,boundary,building,craft,geological,historic,landuse,leisure,military,natural,office,place,shop,sport,tourism,highway=platform,public_transport=platform

[points]
osm_id=no
attributes=name
other_tags=no

[lines]
osm_id=no
attributes=highway,bridge,tunnel,layer,waterway,natural,name,bicycle,surface,cycleway,cycleway:left,cycleway:right,cycleway:both
other_tags=no

[multipolygons]
osm_id=no
osm_way_id=no
attributes=natural,landuse,waterway
other_tags=no

[multilinestrings]
osm_id=no
attributes=type,name,ref,cycle_network
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


# ─── Camadas de mapa (--layers) ───────────────────────────────────────────────
# "Morros e Águas" e "Cicloinfra OSM" liam o Overpass a cada pan/zoom: lento,
# sujeito ao rate limit do servidor do OSM e sem funcionar offline. Agora saem
# daqui, pros MESMOS range requests que o viário já usa — o cliente busca só os
# bytes da bbox visível (ver web/app.js §"Camadas OSM por FlatGeobuf").


def _write_osmconf() -> Path:
    """Escreve (idempotente) o osmconf.ini compartilhado e devolve o caminho."""
    conf = IGNORE / "osmconf-viario.ini"
    conf.write_text(OSMCONF)
    return conf


def _write_hidro_osmconf() -> Path:
    """osmconf só do hidro, com `natural` FORA de closed_ways_are_polygons.

    `natural` está na lista compartilhada por causa do build de água, que lê
    `natural=water` da camada multipolygons. Mas a lista é global por arquivo de
    config: com ela, uma way FECHADA de `natural=ridge` (uma crista em laço) é
    roteada pro multipolygons e some da camada `lines` — some, portanto, da
    "Morros e Águas", que a consulta Overpass (`way["natural"="ridge"]`, sem
    distinguir aberta de fechada) trazia. Tirar `natural` daqui devolve as
    cristas fechadas pras linhas; `natural=water` fechado continua irrelevante
    porque o -where do hidro só aceita waterway=* ou natural=ridge.
    """
    conf = IGNORE / "osmconf-hidro.ini"
    head, _, rest = OSMCONF.partition("\n")
    kept = ",".join(k for k in head.split("=", 1)[1].split(",") if k != "natural")
    conf.write_text(f"closed_ways_are_polygons={kept}\n{rest}")
    return conf


def build_hidro_fgb(pbf: Path) -> None:
    """south-america-hidro.fgb: linhas de água + cristas ("Morros e Águas").

    Mesmo conjunto que a consulta Overpass trazia (`way["waterway"]` +
    `way["natural"="ridge"]`), mais `tunnel` (o traço pontilhado dos trechos
    canalizados) e `name` (o tooltip). Sem filtrar valor de `waterway`: a
    camada desenha rio (verde, grosso) e todo o resto (ocre, fino), igual antes.
    """
    hi_pbf = IGNORE / (pbf.stem + "-hidro.osm.pbf")
    _run(["osmium", "tags-filter", pbf, "-o", hi_pbf, "--overwrite",
          "w/waterway", "w/natural=ridge"])
    conf = _write_hidro_osmconf()
    OUT_HIDRO.unlink(missing_ok=True)
    # "natural" precisa de aspas — é palavra reservada de SQL (NATURAL JOIN).
    _run(["ogr2ogr", "-f", "FlatGeobuf", OUT_HIDRO, hi_pbf, "lines",
          "-oo", f"CONFIG_FILE={conf}",
          "-select", "waterway,natural,tunnel,name",
          "-where", "waterway IS NOT NULL OR \"natural\" = 'ridge'",
          "-nlt", "LINESTRING",
          "-lco", f"TEMPORARY_DIR={IGNORE}",
          "--config", "OSM_MAX_TMPFILE_SIZE", "4000"])
    hi_pbf.unlink(missing_ok=True)
    print(f"→ {OUT_HIDRO.name}: {OUT_HIDRO.stat().st_size / 1e6:.0f} MB")


def build_cicloinfra_fgb(pbf: Path) -> None:
    """south-america-cicloinfra.fgb: ciclovias, caminhos compartilhados e vias
    com ciclofaixa ("Cicloinfra OSM")."""
    ci_pbf = IGNORE / (pbf.stem + "-cicloinfra.osm.pbf")
    # `tags-filter` é UNIÃO de expressões e não casa valor por regex, então não
    # dá pra exprimir "highway=* E cycleway~lane|track|…" nele. Pré-filtra um
    # SUPERCONJUNTO barato (qualquer via com uma dessas chaves) e deixa o
    # -where do OGR fechar a conta exata — que é o mesmo predicado da consulta
    # Overpass antiga.
    _run(["osmium", "tags-filter", pbf, "-o", ci_pbf, "--overwrite",
          "w/highway=cycleway", "w/cycleway", "w/cycleway:left",
          "w/cycleway:right", "w/cycleway:both", "w/bicycle"])
    conf = _write_osmconf()
    vals = ",".join(f"'{v}'" for v in CYCLEWAY_LANE_VALUES)
    # Nomes SANEADOS pelo GDAL (`cycleway:left` → `cycleway_left`) — ver OSMCONF.
    lane = " OR ".join(f"{c} IN ({vals})" for c in
                       ("cycleway", "cycleway_left", "cycleway_right", "cycleway_both"))
    where = ("highway = 'cycleway'"
             " OR (highway = 'path' AND bicycle IN ('yes','designated'))"
             f" OR (highway IS NOT NULL AND ({lane}))")
    OUT_CICLOINFRA.unlink(missing_ok=True)
    _run(["ogr2ogr", "-f", "FlatGeobuf", OUT_CICLOINFRA, ci_pbf, "lines",
          "-oo", f"CONFIG_FILE={conf}",
          "-select", "highway,bicycle,cycleway,cycleway_left,cycleway_right,"
                     "cycleway_both,surface,name",
          "-where", where,
          "-nlt", "LINESTRING",
          "-lco", f"TEMPORARY_DIR={IGNORE}",
          "--config", "OSM_MAX_TMPFILE_SIZE", "4000"])
    ci_pbf.unlink(missing_ok=True)
    print(f"→ {OUT_CICLOINFRA.name}: {OUT_CICLOINFRA.stat().st_size / 1e6:.0f} MB")


def build_ph_network_geojson(pbf: Path) -> None:
    """ph-cycle-network.geojson: as relations da rede do coletivo.

    Uma MultiLineString por relation (o driver OSM já costura os membros), com
    `name`/`ref` pro tooltip. São poucas — o cliente baixa o arquivo inteiro.
    Não é fatal se não houver nenhuma (extrato de teste, tag ainda não mapeada).
    """
    rel_pbf = IGNORE / (pbf.stem + "-phnet.osm.pbf")
    _run(["osmium", "tags-filter", pbf, "-o", rel_pbf, "--overwrite",
          f"r/cycle_network={PH_CYCLE_NETWORK}"])
    conf = _write_osmconf()
    OUT_PH_NETWORK.unlink(missing_ok=True)
    try:
        # Sem -where: o osmium já deixou só as relations certas, e um -where
        # sobre um campo que não materializou abortaria o build à toa.
        _run(["ogr2ogr", "-f", "GeoJSON", OUT_PH_NETWORK, rel_pbf,
              "multilinestrings", "-oo", f"CONFIG_FILE={conf}",
              "-select", "name,ref"])
    except subprocess.CalledProcessError:
        # O driver GeoJSON cria o arquivo ao ABRIR o dataset, então um ogr2ogr
        # que falha deixa um .geojson de 0 byte pra trás. Sem este unlink ele
        # passaria no `exists()` do main() e seria publicado por cima do bom.
        print(f"  (ogr2ogr falhou em {OUT_PH_NETWORK.name} — descartado)")
        OUT_PH_NETWORK.unlink(missing_ok=True)
        rel_pbf.unlink(missing_ok=True)
        return
    rel_pbf.unlink(missing_ok=True)
    n = OUT_PH_NETWORK.read_text().count('"type": "Feature"')
    # ZERO relations NÃO é um sucesso silencioso. O driver OSM declara a camada
    # `multilinestrings` a partir do osmconf mesmo sem nenhuma feição, então o
    # ogr2ogr acima sai com 0 e grava um FeatureCollection vazio — o `except`
    # não pega este caso. Publicar isso apagaria a rede do coletivo do mapa,
    # num bucket SEM Object Versioning. Some com o arquivo: aí ele fica fora do
    # `built` e o job não sobe nada.
    if n == 0:
        OUT_PH_NETWORK.unlink(missing_ok=True)
        print(f"  AVISO: nenhuma relation cycle_network={PH_CYCLE_NETWORK} no "
              f"extrato — {OUT_PH_NETWORK.name} NÃO gerado (nada a publicar). "
              f"Se isso for inesperado, confira a tag no OSM antes de subir.")
        return
    print(f"→ {OUT_PH_NETWORK.name}: {n} relation(s), "
          f"{OUT_PH_NETWORK.stat().st_size / 1e3:.0f} kB")


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
EARTH_R = 6378137.0              # mesma constante do energyRoute (app.js)
# Tratamento σ do mapa aplicado ao mosaico ANTES de amostrar as elevações por
# nó — espelha o DEFAULT_PARAMS.demSmoothSigmaM do app.js (Entry 74). Manter
# os dois em sincronia: é o mesmo relevo que o roteamento por energia lê.
DEFAULT_GRAPH_SIGMA_M = 30.0
# Guarda de sanidade entre as duas fontes de DEM ao fundir o mosaico do bake:
# acima disto o valor do DEM de SP é considerado buraco/artefato e fica o
# FABDEM. Ver o comentário em DemSampler.__init__.
SRC_DISAGREE_MAX_M = 100.0
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


def _smooth_heights_in_place(height, mask, H: int, W: int,
                             dx_m: float, dy_m: float, sigma_m: float):
    """Tratamento σ do mapa (bicycling-energy-model, Entry 74) — PORTE FIEL do
    smoothHeightsInPlace do app.js (que por sua vez é cópia à mão do sampasimu,
    travada pelo test-dem-smoothing.mjs de lá).

    Gaussiana SEPARÁVEL (horizontal e depois vertical), NORMALIZADA PELA
    MÁSCARA (num/den só soma vizinhos válidos e dentro da grade), truncada em
    3σ, com σ_px por eixo derivado do passo em metros. Escreve só onde a
    máscara vale. NÃO trocar por um blur genérico: os σ do estudo só valem
    pra ESTA transformação.

    Sem isto, o grafo pré-cozido saía com elevação CRUA enquanto todo o resto
    do roteamento por energia lia o mosaico tratado — o ruído sub-célula
    fabricava micro-subidas e inflava h₊ (e portanto o custo v2).

    Recebe/devolve um array 1-D (H·W) float32 do numpy.
    """
    try:
        import numpy as np
    except ImportError as e:                                  # pragma: no cover
        raise RuntimeError("numpy ausente — necessário pro tratamento σ do bake "
                           "(pip install numpy, ou use --graph-sigma 0)") from e
    if not (sigma_m > 0):
        return np.asarray(height, dtype=np.float32).ravel()

    h = np.asarray(height, dtype=np.float64).reshape(H, W)
    m = np.asarray(mask, dtype=bool).reshape(H, W)
    mf = m.astype(np.float64)

    for sig_px, horizontal in ((sigma_m / dx_m, True), (sigma_m / dy_m, False)):
        R = math.ceil(3 * sig_px)
        if R < 1:
            continue
        w = [math.exp(-(k * k) / (2 * sig_px * sig_px)) for k in range(R + 1)]
        v = np.where(m, h, 0.0)
        num = w[0] * v
        den = w[0] * mf
        for k in range(1, R + 1):
            wk = w[k]
            # `k >= W` (ou `>= H`): não existe vizinho a essa distância na
            # linha/coluna — pular. Sem a guarda, `W - k` fica negativo e o
            # slice devolve uma fatia deslocada em vez de vazia.
            if horizontal:
                if k >= W:
                    continue
                # vizinho em c+k contribui pra saída em c, e vice-versa.
                num[:, :W - k] += wk * v[:, k:];  den[:, :W - k] += wk * mf[:, k:]
                num[:, k:]     += wk * v[:, :W - k]; den[:, k:]  += wk * mf[:, :W - k]
            else:
                if k >= H:
                    continue
                num[:H - k, :] += wk * v[k:, :];  den[:H - k, :] += wk * mf[k:, :]
                num[k:, :]     += wk * v[:H - k, :]; den[k:, :]  += wk * mf[:H - k, :]
        safe = den > 0
        h = np.where(m & safe, num / np.where(safe, den, 1.0), h)

    return h.astype(np.float32).ravel()


class DemSampler:
    """Elevação por lat/lng na grade do bake: DEM de SP (5 m, reamostrado) onde
    cobre, FABDEM no resto, 0.0 onde nenhum cobre (igual ao sampleElev do
    runtime, que devolve 0 fora da máscara).

    As duas fontes são FUNDIDAS num mosaico único (SP onde vale, FABDEM no
    resto) e esse mosaico leva o TRATAMENTO σ do mapa antes de qualquer
    amostragem — o mesmo que o runtime aplica em energyRoute. Antes as
    elevações eram assadas cruas, e o grafo pré-cozido (fonte PRIMÁRIA do
    "menor energia pelo viário" em SP) era o único consumidor de roteamento
    lendo relevo não-tratado."""

    def __init__(self, bbox: tuple[float, float, float, float],
                 sigma_m: float = DEFAULT_GRAPH_SIGMA_M) -> None:
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

        # Funde as duas fontes num mosaico único (SP onde vale, FABDEM no
        # resto) e aplica o tratamento σ — o runtime suaviza o mosaico, não
        # cada fonte separada, então a fusão vem ANTES da suavização.
        try:
            import numpy as np
        except ImportError as e:                              # pragma: no cover
            raise RuntimeError("numpy ausente — necessário pro bake do grafo "
                               "(pip install numpy)") from e
        fab = np.asarray(self._read_grid(GRAPH_TMP / "fabdem-grid"), dtype=np.float32)
        sampa = np.asarray(self._read_grid(GRAPH_TMP / "sampa-grid"), dtype=np.float32)
        ok_s = (sampa != -9999.0) & np.isfinite(sampa)
        ok_f = (fab != -9999.0) & np.isfinite(fab)
        # O DEM municipal de SP tem BURACOS gravados como ~0 m em vez de
        # nodata — ~91 mil células marcando nível do mar no meio da cidade,
        # espalhadas pelo INTERIOR da extensão dele (não só na borda). O bake
        # antigo amostrava esses 0 direto (o grafo em produção tem nó a 0,2 m
        # em plena SP) e, com o tratamento σ, cada buraco desses passaria a
        # contaminar a vizinhança inteira. Onde as duas fontes discordam
        # MUITO, fica o FABDEM (global e consistente): a discordância real
        # entre um DEM de 5 m e um de 30 m fica uma ordem de grandeza abaixo
        # deste limiar (medido: 2,9% das células > 20 m, e quase todas elas
        # > 400 m — ou seja, os dois regimes são bem separados).
        bad_s = ok_s & ok_f & (np.abs(sampa - fab) > SRC_DISAGREE_MAX_M)
        n_bad = int(bad_s.sum())
        if n_bad:
            print(f"→ DEM de SP: {n_bad} células descartadas por discordarem "
                  f">{SRC_DISAGREE_MAX_M:g} m do FABDEM (buracos gravados como 0 m)")
        ok_s = ok_s & ~bad_s
        self.mask = (ok_s | ok_f)
        self.h = np.where(ok_s, sampa, np.where(ok_f, fab, 0.0)).astype(np.float32)
        del fab, sampa, ok_s, ok_f
        cover = int(self.mask.sum())
        print(f"→ mosaico fundido: {cover}/{self.W * self.H} células com cobertura "
              f"({100.0 * cover / (self.W * self.H):.1f}%)")

        # Passo da célula em metros na latitude média — MESMA fórmula do
        # energyRoute (EARTH_R e cos da latitude média da bbox).
        mid_lat = (s + n) / 2.0
        dy = ARCSEC * math.pi / 180.0 * EARTH_R
        dx = dy * math.cos(math.radians(mid_lat))
        self.sigma_m = sigma_m
        if sigma_m > 0:
            t0 = time.time()
            self.h = _smooth_heights_in_place(self.h, self.mask, self.H, self.W,
                                              dx, dy, sigma_m)
            print(f"→ tratamento σ={sigma_m:g} m aplicado ao mosaico "
                  f"(dx={dx:.2f} m, dy={dy:.2f} m) em {time.time() - t0:.1f} s")
        else:
            print("→ tratamento σ DESLIGADO (--graph-sigma 0) — elevação crua")

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
        return float(self.h[i]) if self.mask[i] else 0.0


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
    if str(fgb).startswith("/vsi"):
        # A Cloudflare que fronteia o bucket às vezes responde o HEAD de sonda
        # do GDAL sem `Accept-Ranges`, e ele desiste com "Range downloading not
        # supported by this server!" — mesmo com o GET ranged funcionando
        # (206). Sem o HEAD, o driver vai direto no range e o índice do FGB
        # baixa só a faixa da bbox.
        from osgeo import gdal
        gdal.SetConfigOption("CPL_VSIL_CURL_USE_HEAD", "NO")
        gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "YES")
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


def bake_graph(fgb: Path | str, out: Path, graph_bbox: tuple[float, float, float, float],
               sigma_m: float = DEFAULT_GRAPH_SIGMA_M) -> None:
    pad = 0.01
    bbox = (math.floor((graph_bbox[0] - pad) / ARCSEC) * ARCSEC,
            math.floor((graph_bbox[1] - pad) / ARCSEC) * ARCSEC,
            math.ceil((graph_bbox[2] + pad) / ARCSEC) * ARCSEC,
            math.ceil((graph_bbox[3] + pad) / ARCSEC) * ARCSEC)
    print(f"→ bbox do grafo: {bbox}")
    dem = DemSampler(bbox, sigma_m)
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


def _print_upload_help(built: list[Path]) -> None:
    fgbs = [p for p in built if p.suffix == ".fgb"]
    others = [p for p in built if p.suffix != ".fgb"]
    if fgbs:
        print("\nsuba pro bucket (SEM -Z nos .fgb — gzip quebraria os range requests):\n"
              "    gcloud storage cp --cache-control=\"public,max-age=86400\" \\\n"
              + "".join(f"        {p} \\\n" for p in fgbs)
              + "        gs://telhas/viario/")
    if others:
        # GeoJSON é baixado INTEIRO (não por Range) — aí o -Z vale a pena.
        print("\ne o GeoJSON, esse sim com -Z (baixado inteiro, não por Range):\n"
              "    gcloud storage cp -Z --cache-control=\"public,max-age=86400\" \\\n"
              + "".join(f"        {p} \\\n" for p in others)
              + "        gs://telhas/viario/")
    print("\ne confira VIARIO_FGB_URL / WATER_*_FGB_URL / OSM_FGB_* em web/app.js.")


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
    ap.add_argument("--layers", action="store_true",
                    help="também gera as camadas de mapa: hidro + cicloinfra "
                         "(FGB) e a rede do coletivo (GeoJSON)")
    ap.add_argument("--no-viario", action="store_true",
                    help="pula o FGB do viário (~4,5 GB, o build mais caro) — "
                         "é o modo do job semanal, que só refaz água + camadas")
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
    ap.add_argument("--graph-src", metavar="SRC",
                    help="fonte OGR do viário pro bake do grafo — aceita um "
                         "caminho local OU um /vsicurl/https://… (o filtro "
                         "espacial do FGB só baixa a faixa da bbox por range "
                         "request, em vez dos ~4,5 GB). Default: --out")
    ap.add_argument("--graph-sigma", type=float, default=DEFAULT_GRAPH_SIGMA_M,
                    metavar="M",
                    help=f"σ (m) do tratamento do mapa aplicado ao mosaico DEM "
                         f"antes de amostrar as elevações por nó "
                         f"(default: {DEFAULT_GRAPH_SIGMA_M:g}, igual ao "
                         f"demSmoothSigmaM do app.js; 0 = cru)")
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
        # `--graph-src` pode ser um /vsicurl/… (remoto): aí não há arquivo local
        # pra checar — o OGR resolve, e o índice do FGB baixa só a bbox.
        graph_src = args.graph_src or str(args.dst)
        is_remote = graph_src.startswith(("/vsicurl/", "/vsi"))
        if not is_remote and not Path(graph_src).exists():
            print(f"erro: --graph-only precisa do FGB já gerado em {graph_src}", file=sys.stderr)
            return 1
        try:
            bake_graph(graph_src, args.graph_out, graph_bbox, args.graph_sigma)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"erro: bake do grafo falhou: {e}", file=sys.stderr)
            return 1
        return 0

    if not shutil.which("osmium"):
        print("erro: osmium não está no PATH (brew install osmium-tool / "
              "apt install osmium-tool).", file=sys.stderr)
        return 1

    if args.no_viario and not (args.water or args.layers or args.graph):
        print("erro: --no-viario sem --water/--layers/--graph não faria nada.",
              file=sys.stderr)
        return 1

    IGNORE.mkdir(exist_ok=True)
    pbf = IGNORE / Path(args.extract).name
    built: list[Path] = []
    try:
        download_pbf(args.extract, pbf)
        if not args.no_viario:
            build_viario_fgb(pbf, args.dst)
            built.append(args.dst)
        if args.water:
            build_water_fgbs(pbf)
            built += [OUT_WATER_AREAS, OUT_WATER_RIVERS]
        if args.layers:
            build_hidro_fgb(pbf)
            build_cicloinfra_fgb(pbf)
            build_ph_network_geojson(pbf)
            built += [OUT_HIDRO, OUT_CICLOINFRA]
            if OUT_PH_NETWORK.exists():
                built.append(OUT_PH_NETWORK)
        if args.graph:
            bake_graph(args.graph_src or args.dst, args.graph_out, graph_bbox,
                       args.graph_sigma)
    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1

    if args.drop_pbf:
        pbf.unlink(missing_ok=True)
    _print_upload_help(built)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
