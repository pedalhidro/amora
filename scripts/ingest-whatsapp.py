#!/usr/bin/env python3
"""FASE 2 da ingestão do acervo: os arquivos do WHATSAPP (sem EXIF).

A fase 1 (ingest-drive.py) sobe os originais com EXIF/GPS — mídia de primeira
classe, com marcador no mapa. Esta sobe o resto: os ~6.400 JPEGs e ~1.300 MP4s
que passaram pelo WhatsApp, que remove TODO o EXIF ao enviar. Sem GPS não há
marcador (o mixin ph:GeoreferencedImage NÃO é emitido; o mapa os ignora
sozinho), mas eles entram como MEMÓRIA do passeio: ph:capturedDuring, quem
compartilhou, navegáveis na galeria e no modal do passeio.

O que se sabe de verdade sobre cada arquivo, e é só isso que vai pro TTL:
  · o passeio ......... a pasta do acervo casa com o tours.ttl (audit-captura)
  · quando ............ dcterms:date = o DIA do passeio, como xsd:date — só o
                        dia, sem hora inventada (os leitores tratam como 23:59
                        daquele dia). O carimbo no nome do arquivo é a hora do
                        COMPARTILHAMENTO, não da captura, e vai pra
                        schema:datePublished, que é o que ele é.
  · quem compartilhou . o slug do acervo vai SEMPRE como literal em
                        schema:creditText (é o join com identities.ttl via
                        schema:alternateName, como o ph:sweepContributor do
                        passe); quando o whatsapp-slug-map.json resolve a
                        pessoa, também pav:providedBy + prov:wasAttributedTo.
Nada de coordenada inventada, nada de hora inventada.

RODE A FASE 1 ANTES. Como o pHash é o IRI e o WhatsApp só recomprime, uma
cópia de zap e o original colidem no mesmo IRI (Hamming ≤ 5) — com os
originais já lá, as cópias deduplicam contra eles e a versão COM GPS vence.

    ingest-whatsapp.py                          # dry-run: só imagens
    ingest-whatsapp.py --pasta "Água Preta" --apply
    ingest-whatsapp.py --so-resolvidos --apply  # só quem já tem pessoa no mapa
    ingest-whatsapp.py --videos --pasta X --apply   # inclui os MP4 (ffmpeg)

┌─ BAIXA BYTES DO DRIVE ──────────────────────────────────────────────────────┐
│ Os arquivos são stubs: calcular o pHash exige os bytes, então mesmo o       │
│ --dry-run BAIXA (imagens ≈ 4 GiB; vídeos ≈ 5,5 GiB). Rode por pasta.        │
│ O acervo é SOMENTE-LEITURA: nada é escrito, movido ou apagado lá.           │
└─────────────────────────────────────────────────────────────────────────────┘
Vídeos: vhash (8 quadros, voto por bit — como o form), audio.webm (opus 192k),
360p.webm (vp9 700k + opus 128k, 30 fps) e thumb.jpg via ffmpeg; sem 720p (o
mapa só o usa com "HD" ligado). MP4 sem trilha de áudio ganha silêncio
(anullsrc) — o /upload-video exige ph:audio.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]


def _importa(nome_mod: str, arquivo: str):
    caminho = REPO / "scripts" / arquivo
    spec = importlib.util.spec_from_file_location(nome_mod, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome_mod] = mod
    spec.loader.exec_module(mod)
    return mod


# ingest-drive.py é a fonte do pHash, das variantes e do catálogo remoto; ele
# por sua vez importa o audit-captura (varredura, casamento pasta→passeio).
I = _importa("ingest_drive", "ingest-drive.py")
A = I.A
L = I.L          # livro-razão (scripts/media_ledger.py)

import rdflib  # noqa: E402  (depois dos imports dinâmicos, como o ingest-drive)

PH = rdflib.Namespace(I.PH_NS)
DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")
TZ_SP = timezone(timedelta(hours=-3))

# "dandanlessa WhatsApp Image 2025-09-10 at 00.46.14.jpeg" → 2025-09-10T00:46:14-03:00
RE_CARIMBO = re.compile(
    r"WhatsApp\s+(?:Image|Video|Audio|Ptt)\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2})\.(\d{2})\.(\d{2})",
    re.I)

PREFIXOS = I.PREFIXOS          # (o pav: já vem de lá)

VIDEO_BITRATE_360 = "700k"
AUDIO_BITRATE_CLIP = "128k"
AUDIO_BITRATE_ONLY = "192k"


@dataclass
class Item:
    caminho: Path
    pasta: str
    kind: str                       # 'image' | 'video'
    hash: str = ""
    tour_slug: str | None = None
    tour_iri: str | None = None
    data: str | None = None         # dcterms:date (do passeio)
    publicado: str | None = None    # schema:datePublished (carimbo do arquivo)
    slug_bruto: str | None = None
    pessoa_slug: str | None = None
    duracao: float = 0.0
    original: bool = False          # original sem GPS (fase 1 pulou) — data vem do EXIF
    variantes: dict = field(default_factory=dict)
    src: str | None = None          # chave no livro-razão (drive:<item-id>)
    gps: tuple | None = None        # (lat, lon) — só vídeo ORIGINAL com GPS no arquivo
    tour_data: datetime | None = None   # a data do passeio (pra conferir a data do vídeo)


# ═════════════════════════════════════════════════════════════════════════
# 1. Datas
# ═════════════════════════════════════════════════════════════════════════

def carimbo_compartilhamento(nome: str) -> str | None:
    m = RE_CARIMBO.search(nome)
    if not m:
        return None
    d, hh, mm, ss = m.groups()
    return f"{d}T{hh}:{mm}:{ss}-03:00"


def data_do_passeio(g: rdflib.Graph, tour_iri: str) -> str | None:
    """O DIA-calendário do passeio (AAAA-MM-DD), que vira um xsd:date na mídia.

    Só o dia: do arquivo do zap a gente sabe em que passeio foi, não a que
    horas. Antes isto devolvia a data E A HORA da saída — uma hora inventada,
    indistinguível de um EXIF de verdade. Os leitores (effectiveDate em
    web/lib/media-query.js) tratam o dia sozinho como 23:59 daquele dia."""
    t = rdflib.URIRef(tour_iri)
    v = g.value(t, DCTERMS.date) or g.value(t, PH.departedAt)
    m = re.match(r"\d{4}-\d{2}-\d{2}", str(v or ""))
    return m.group(0) if m else None


# ═════════════════════════════════════════════════════════════════════════
# 2. Vídeo — vhash, transcode e thumb via ffmpeg (o form faz no navegador)
# ═════════════════════════════════════════════════════════════════════════

def ffprobe(caminho: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format",
         str(caminho)], capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout:
        raise RuntimeError(f"ffprobe: {out.stderr.strip()[:120]}")
    return json.loads(out.stdout)


def _quadro(caminho: Path, t: float) -> Image.Image:
    """Um quadro em t (s), já com a rotação do container aplicada (ffmpeg
    autorotate) — o mesmo que o <video> entrega ao canvas."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(caminho), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=False)
    if out.returncode != 0 or not out.stdout:
        raise RuntimeError("ffmpeg quadro")
    return Image.open(io.BytesIO(out.stdout)).convert("RGB")


def vhash(caminho: Path, dur: float, n: int = 8) -> str:
    """computeVideoPHash() do form: N quadros uniformes, pHash de cada, voto
    majoritário por bit. Quadro sem ICC (o <video> entrega sRGB ao canvas)."""
    hist = np.zeros(64, dtype=int)
    got = 0
    for i in range(n):
        t = min(max(0.05, ((i + 0.5) / n) * dur), max(0.05, dur - 0.05))
        try:
            h = I.phash(_quadro(caminho, t), None)
        except Exception:                   # noqa: BLE001 — seek falhou: pula o quadro
            continue
        bits = bin(int(h, 16))[2:].zfill(64)
        hist += np.array([int(b) for b in bits])
        got += 1
    if got == 0:
        raise RuntimeError("nenhum quadro decodificou")
    out = "".join("1" if c > got / 2 else "0" for c in hist)
    hx = f"{int(out, 2):016x}"
    if re.fullmatch(r"(.)\1{15}", hx):     # quadro uniforme → hash degenerado
        raise RuntimeError("vhash uniforme (quadros pretos?)")
    return hx


def _dims_360(w: int, h: int) -> tuple[int, int]:
    if w >= h:
        oh, ow = 360, round(360 * w / h)
    else:
        ow, oh = 360, round(360 * h / w)
    return ow - ow % 2, oh - oh % 2


def transcoda_video(caminho: Path, info: dict) -> tuple[dict[str, tuple[str, bytes]], float]:
    """audio.webm + 360p.webm + thumb.jpg, como o transcodeClip() do form
    (sem 720p). Devolve (variantes, duração)."""
    vs = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    aus = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    if not vs:
        raise RuntimeError("sem trilha de vídeo")
    dur = float(info.get("format", {}).get("duration") or vs.get("duration") or 0)
    if dur <= 0.1:
        raise RuntimeError("duração inválida")
    if dur > 600.5:
        raise RuntimeError("vídeo > 10 min")
    w, h = int(vs["width"]), int(vs["height"])
    rot = 0
    for sd in vs.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if rot % 180:
        w, h = h, w
    ow, oh = _dims_360(w, h)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        entrada = ["-i", str(caminho)]
        # Sem áudio: silêncio da mesma duração — o catálogo exige ph:audio.
        mapa_a = ["-map", "0:a:0"] if aus else ["-f", "lavfi", "-t", f"{dur:.3f}",
                                                 "-i", "anullsrc=r=48000:cl=stereo"]
        if not aus:
            entrada = entrada + mapa_a
            mapa_a = ["-map", "1:a:0"]
        base = ["ffmpeg", "-v", "error", "-y", *entrada]
        subprocess.run([*base, *mapa_a, "-vn", "-c:a", "libopus", "-b:a", AUDIO_BITRATE_ONLY,
                        str(td / "audio.webm")], check=True, capture_output=True)
        subprocess.run([*base, "-map", "0:v:0", *mapa_a,
                        "-vf", f"scale={ow}:{oh}", "-r", "30",
                        "-c:v", "libvpx-vp9", "-b:v", VIDEO_BITRATE_360,
                        "-deadline", "realtime", "-cpu-used", "5", "-row-mt", "1",
                        "-c:a", "libopus", "-b:a", AUDIO_BITRATE_CLIP,
                        str(td / "360p.webm")], check=True, capture_output=True)
        t_thumb = min(0.5, dur * 0.05)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t_thumb:.3f}", "-i", str(caminho),
                        "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "4",
                        str(td / "thumb.jpg")], check=True, capture_output=True)
        return {
            "audio": ("audio.webm", (td / "audio.webm").read_bytes()),
            "video360": ("360p.webm", (td / "360p.webm").read_bytes()),
            "thumb": ("thumb.jpg", (td / "thumb.jpg").read_bytes()),
        }, dur


# ═════════════════════════════════════════════════════════════════════════
# 3. TTL — contratos do /upload-image e do /upload-video
# ═════════════════════════════════════════════════════════════════════════

def _turtle_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _props_comuns(it: Item) -> list[str]:
    props = [f"dcterms:license <{I.LICENCA_PADRAO}>"]
    if it.data:
        # "AAAA-MM-DD" = só o dia do passeio (xsd:date); com 'T' = instante
        # real do EXIF de um original sem GPS (xsd:dateTime).
        tipo = "dateTime" if "T" in it.data else "date"
        props.append(f'dcterms:date "{it.data}"^^xsd:{tipo}')
    if it.publicado:
        props.append(f'schema:datePublished "{it.publicado}"^^xsd:dateTime')
    if it.tour_slug:
        props.append(f"ph:capturedDuring pas:{it.tour_slug}")
    if it.pessoa_slug:
        props.append(f"prov:wasAttributedTo pes:{it.pessoa_slug}")
        props.append(f"pav:providedBy pes:{it.pessoa_slug}")
    if it.slug_bruto:
        props.append(f'schema:creditText "{_turtle_str(it.slug_bruto)}"')
    return props


def monta_ttl_imagem(it: Item, alvo: str | None = None, herda: dict | None = None) -> str:
    """Com `alvo` + `herda` é uma SUBSTITUIÇÃO (ver ingest-drive.py: "Original
    é sempre melhor"): o IRI é o da mídia que já está no amora; data-hora do
    EXIF entra, a parte social e a coordenada (se a antiga tinha) são herdadas."""
    h = alvo or it.hash
    ident = f"med:{h}"
    geo = herda["geo"] if herda else None
    if herda is None:
        props = ["a ph:StillImage",          # SEM ph:GeoreferencedImage: não há GPS
                 f"nfo:hasHash {ident}_hash",
                 *_props_comuns(it)]
    else:
        props = ["a ph:StillImage" + (", ph:GeoreferencedImage" if geo else ""),
                 f"nfo:hasHash {ident}_hash"]
        if it.data and "T" in it.data:       # data-hora REAL do EXIF
            props.append(f'dcterms:date "{it.data}"^^xsd:dateTime')
        elif herda["data"]:
            props.append(f"dcterms:date {herda['data']}")
        elif it.data:
            props.append(f'dcterms:date "{it.data}"^^xsd:date')
        if geo:
            props.append(f"schema:locationCreated {ident}_geo")
        props += I.props_herdados(herda, it.pessoa_slug, it.tour_slug, it.slug_bruto)
    if it.original:
        _, mime = I.formato_original(it.caminho)
        if mime != "image/jpeg":
            props.append(f'schema:encodingFormat "{mime}"')
    corpo = " ;\n".join(f"    {p}" for p in props)
    derivados = (f"{ident}_hash a nfo:FileHash ;\n"
                 f'    nfo:hashAlgorithm "pHash" ;\n'
                 f'    nfo:hashValue "{h}" .')
    if geo:
        derivados += (f"\n\n{ident}_geo a schema:GeoCoordinates ;\n"
                      f'    schema:latitude "{geo[0]:.6f}"^^xsd:decimal ;\n'
                      f'    schema:longitude "{geo[1]:.6f}"^^xsd:decimal'
                      f"{I.linha_fonte_geo(herda)} .")
    return f"{PREFIXOS}\n{ident}\n{corpo} .\n\n{derivados}\n"


# ── Metadados de vídeo ORIGINAL ──────────────────────────────────────────────
# Vídeo de celular/câmera traz a hora da gravação e, no iPhone, a coordenada.
# Dois campos de data, e eles NÃO valem o mesmo:
#   CreationDate (Apple, com fuso) — a hora da GRAVAÇÃO. Confiável.
#   CreateDate (mvhd)              — em câmera é a gravação; em arquivo que
#     passou por app/edição é a hora em que foi SALVO (um vídeo de 10/2024
#     aparecia como 04/2025). Só vale se cair perto do dia do passeio.
RE_DATA_QT = re.compile(r"^(\d{4}):(\d{2}):(\d{2}) (\d{2}:\d{2}:\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})?$")


def le_meta_video(caminhos: list[Path]) -> dict[str, dict]:
    if not caminhos:
        return {}
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("\n".join(str(c) for c in caminhos))
        arglist = fh.name
    try:
        out = subprocess.run(
            ["exiftool", "-n", "-json", "-api", "QuickTimeUTC=1", "-CreationDate", "-CreateDate",
             "-GPSLatitude", "-GPSLongitude", "-@", arglist],
            capture_output=True, text=True, check=False)
        return {j["SourceFile"]: j for j in json.loads(out.stdout)} if out.stdout.strip() else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    finally:
        os.unlink(arglist)


def _data_qt(v) -> str | None:
    m = RE_DATA_QT.match(str(v or ""))
    if not m or m.group(1) == "0000":
        return None
    off = m.group(5) or "-03:00"
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}{'+00:00' if off == 'Z' else off}"


def data_do_video(meta: dict, tour_data: datetime | None) -> str | None:
    """xsd:dateTime da gravação, ou None (aí vale só o dia do passeio)."""
    d = _data_qt(meta.get("CreationDate"))
    if d:
        return d
    d = _data_qt(meta.get("CreateDate"))
    if d and tour_data is not None:
        try:
            quando = datetime.fromisoformat(d)
            ref = tour_data if tour_data.tzinfo else tour_data.replace(tzinfo=quando.tzinfo)
            if abs((quando - ref).total_seconds()) <= 36 * 3600:
                return d
        except ValueError:
            pass
    return None


# ── O gêmeo de um vídeo original ─────────────────────────────────────────────
# O vhash separa mal: vídeos DIFERENTES do acervo ficam a 13–20 bits um do
# outro, e a cópia do zap de um vídeo fica a ~11 do original (a recompressão
# desloca os quadros amostrados). Então a régua da dedup (≤ 5) não acha a
# cópia, e alargá-la sozinha casaria vídeos diferentes. Pra SUBSTITUIÇÃO vale
# um critério composto: mesma duração (a recompressão não a muda) E hash perto.
GEMEO_HAMMING = 12
GEMEO_DUR_S = 0.25
_RE_DUR = re.compile(r"^PT(?:(\d+)M)?([\d.]+)S$")


def duracoes_dos_videos(g) -> dict[str, float]:
    out = {}
    for m, d in g.subject_objects(rdflib.URIRef("https://schema.org/duration")):
        mm = _RE_DUR.match(str(d))
        if mm and str(m).startswith(I.MED_NS):
            out[str(m)[len(I.MED_NS):]] = int(mm.group(1) or 0) * 60 + float(mm.group(2))
    return out


def gemeo_de_video(vh: str, dur: float, duracoes: dict[str, float], videos: set[str]) -> str | None:
    """O vídeo do catálogo que é a mesma gravação (cópia recomprimida), ou None."""
    melhor = None
    for h, d in duracoes.items():
        if h in videos and abs(d - dur) <= GEMEO_DUR_S:
            dist = I.hamming(vh, h)
            if dist <= GEMEO_HAMMING and (melhor is None or dist < melhor[1]):
                melhor = (h, dist)
    return melhor[0] if melhor else None


def monta_ttl_video(it: Item, alvo: str | None = None, herda: dict | None = None) -> str:
    """Com `alvo` + `herda` é uma SUBSTITUIÇÃO (o original no lugar da cópia do
    zap): IRI, id e nomes dos blobs são os da mídia que já está no amora."""
    h = alvo or it.hash
    ident = f"med:{h}"
    gps = it.gps or (herda["geo"] if herda else None)
    iso = f"PT{round(it.duracao * 100) / 100}S"
    props = ["a ph:MotionImage" + (", ph:GeoreferencedImage" if gps else ""),
             f'schema:duration "{iso}"^^xsd:duration',
             f'ph:audio "{h}.audio.webm"',
             f'schema:thumbnail "{h}.thumb.jpg"',
             f'ph:video360p "{h}.360p.webm"',
             'ph:availableResolution "audio", "360p"']
    if herda is None:
        props += _props_comuns(it)
    else:
        if it.data and "T" in it.data:
            props.append(f'dcterms:date "{it.data}"^^xsd:dateTime')
        elif herda["data"]:
            props.append(f"dcterms:date {herda['data']}")
        elif it.data:
            props.append(f'dcterms:date "{it.data}"^^xsd:date')
        props += I.props_herdados(herda, it.pessoa_slug, it.tour_slug, it.slug_bruto)
    derivados = ""
    if gps:
        props.append(f"schema:locationCreated {ident}_geo")
        derivados = (f"\n{ident}_geo a schema:GeoCoordinates ;\n"
                     f'    schema:latitude "{gps[0]:.6f}"^^xsd:decimal ;\n'
                     f'    schema:longitude "{gps[1]:.6f}"^^xsd:decimal'
                     f"{I.linha_fonte_geo(herda) if not it.gps else ''} .\n")
    corpo = " ;\n".join(f"    {p}" for p in props)
    return f"{PREFIXOS}\n{ident}\n{corpo} .\n{derivados}"


def envia(servidor: str, endpoint: str, campos: dict, arquivos: dict) -> tuple[bool, str]:
    body, headers = I._multipart(campos, arquivos)
    headers["User-Agent"] = A.USER_AGENT
    req = urllib.request.Request(f"{servidor}{endpoint}", data=body, headers=headers,
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=600, context=A._contexto_ssl()) as r:
            j = json.loads(r.read().decode("utf-8"))
            return True, ",".join(j.get("files", [])) or "ok"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except Exception as e:                  # noqa: BLE001
        return False, str(e)


# ═════════════════════════════════════════════════════════════════════════
# 4. O laço
# ═════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--acervo", default=os.environ.get("BIBLIOTECA_DIR", A.ACERVO_PADRAO))
    ap.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", I.SERVIDOR_PADRAO))
    ap.add_argument("--apply", action="store_true", help="envia pra valer (default: dry-run)")
    ap.add_argument("--limit", type=int, help="processa no máximo N arquivos")
    ap.add_argument("--pasta", help="só as pastas do acervo cujo nome contém isto")
    ap.add_argument("--pessoa", help="só arquivos cujo slug (normalizado) é este")
    ap.add_argument("--so-resolvidos", action="store_true",
                    help="só arquivos cujo slug já resolve pra uma pessoa no slug-map")
    ap.add_argument("--videos", action="store_true", help="inclui os MP4 (ffmpeg, lento)")
    ap.add_argument("--originais", action="store_true",
                    help="inclui também os ORIGINAIS que a fase 1 pulou por não terem GPS "
                         "(têm data de captura no EXIF → dcterms:date real; sem marcador)")
    ap.add_argument("--so-videos", action="store_true", help="só os MP4")
    ap.add_argument("--iniciar-livro", action="store_true",
                    help="com --apply: cria o livro-razão se ele ainda não existe nesta máquina")
    ap.add_argument("--sem-substituir", action="store_true",
                    help="não troca a cópia pior que já está no amora pelo original")
    a = ap.parse_args()

    servidor = a.servidor.rstrip("/")
    print("═" * 72)
    print("  INGESTÃO DO ACERVO — FASE 2 (WhatsApp: sem EXIF, sem marcador)")
    print("═" * 72)

    pastas = A.ler_acervo(Path(a.acervo), quieto=True)
    passeios, g = A.carregar_catalogos(servidor)   # do servidor: o repo fica pra trás
    A.casar(passeios, pastas)
    por_pasta = {p.pasta.nome: p for p in passeios if p.pasta}
    pessoas = I.mapa_pessoas()
    quer_img = not a.so_videos
    quer_vid = a.videos or a.so_videos

    cands: list[Item] = []
    sem_passeio: set[str] = set()
    for pa in pastas:
        if a.pasta and a.pasta.lower() not in pa.nome.lower():
            continue
        p = por_pasta.get(pa.nome)
        if p is None and pa.whatsapp_paths:
            sem_passeio.add(pa.nome)
            continue                         # sem passeio não há o que ancorar: fica pra depois
        # ORIGINAIS PRIMEIRO: a dedup é "quem chega primeiro fica", e o original
        # (com data de captura de verdade) tem que ganhar da cópia do zap.
        fontes = []
        if a.originais:
            fontes += [(c, sl, True) for c, sl in pa.originais_paths]
        fontes += [(c, sl, False) for c, sl in pa.whatsapp_paths]
        for caminho, slug, original in fontes:
            ext = caminho.suffix.lower()
            if ext in A.IMAGE_EXT and quer_img:
                kind = "image"
            elif ext in A.VIDEO_EXT and quer_vid:
                kind = "video"
            else:
                continue
            if original and ext not in (".jpg", ".jpeg", ".png", ".heic", ".heif", *A.VIDEO_EXT):
                continue                     # o backend só aceita esses como original
            it = Item(caminho=caminho, pasta=pa.nome, kind=kind, original=original)
            # Originais "dandanlessa DSC09460.JPG": 1º token como slug SÓ se
            # já resolve pra pessoa (mesmo fallback da fase 1).
            if not slug and " " in caminho.name and A.norm(caminho.name.split(" ", 1)[0]) in pessoas:
                slug = caminho.name.split(" ", 1)[0]
            it.slug_bruto = slug
            it.pessoa_slug = pessoas.get(A.norm(slug)) if slug else None
            if a.pessoa and (not slug or A.norm(slug) != A.norm(a.pessoa)):
                continue
            if a.so_resolvidos and not it.pessoa_slug:
                continue
            it.tour_slug, it.tour_iri = p.slug, p.iri
            it.tour_data = p.data
            it.data = data_do_passeio(g, p.iri)
            it.publicado = carimbo_compartilhamento(caminho.name)   # None nos originais
            cands.append(it)
    if a.limit:
        cands = cands[:a.limit]
    if sem_passeio:
        print(f"  ⚠ pastas com zap mas sem passeio casado (puladas): {', '.join(sorted(sem_passeio))}")
    if not cands:
        sys.exit("nenhum arquivo do WhatsApp com esses filtros.")

    # ── Livro-razão: o que já tem desfecho não é nem lido de novo ──────────
    por_classe = I.hashes_no_servidor(servidor)
    fotos, videos = por_classe["StillImage"], por_classe["MotionImage"]
    vivos = fotos | videos
    com_geo = L.hashes_com_geo(g)
    livro = L.abre_livro(a.apply, a.iniciar_livro)
    lapides = L.prepara(por_classe, grava=a.apply, livro=livro)
    acervo_raiz = Path(a.acervo)

    def anota(it, outcome, **kw):
        if livro is not None and a.apply and it.src:
            st = it.caminho.stat()
            livro.registra(it.src, outcome, fase="whatsapp", kind=it.kind,
                           path=os.path.relpath(it.caminho, acervo_raiz),
                           size=st.st_size, mtime=int(st.st_mtime),
                           tour=it.tour_slug, **kw)

    no_livro, sem_id, restam = {}, [], []
    for it in cands:
        it.src = L.chave_drive(it.caminho)
        if it.src is None:
            sem_id.append(it)
            if a.apply:
                continue                    # sem id não dá pra rastrear: não sobe
        est, _ = L.estado_da_origem(it.src, livro, vivos)
        if est in ("subiu", "duplicata", "excluida", "apagada-no-amora"):
            no_livro[est] = no_livro.get(est, 0) + 1
            continue
        restam.append(it)
    n_cands = len(cands)
    cands = restam
    if no_livro:
        print("\njá resolvidos no livro-razão (não relidos): "
              + ", ".join(f"{v} {k}" for k, v in sorted(no_livro.items())))
    if sem_id:
        print(f"⚠ {len(sem_id)} arquivos sem id do Drive"
              + (" — NÃO sobem (não dá pra rastrear)" if a.apply else ""))
    if not cands:
        print("\nnada a fazer: todo candidato já tem desfecho no livro-razão.")
        return

    total_b = sum(c.caminho.stat().st_size for c in cands)
    n_img = sum(1 for c in cands if c.kind == "image")
    n_vid = len(cands) - n_img
    print(f"\n{n_img} imagens + {n_vid} vídeos em {len({c.pasta for c in cands})} pastas"
          + (f" (de {n_cands} candidatos)" if n_cands != len(cands) else ""))
    print(f"BAIXANDO ~{total_b / 1024**3:.2f} GiB do Drive\n")
    print(f"catálogo do amora: {len(fotos)} fotos + {len(videos)} vídeos já lá"
          f" · {len(lapides)} lápides (mídia apagada)\n")

    originais = [c for c in cands if c.original and c.kind == "image"]
    exif = {}
    fase1 = []
    if originais:
        I.prewarm([c.caminho for c in originais])
        exif = I.le_exif([c.caminho for c in originais])
        for it in originais:
            meta = exif.get(str(it.caminho), {})
            if I.gps_valido(meta.get("GPSLatitude"), meta.get("GPSLongitude")):
                fase1.append(it)             # tem GPS: é da fase 1, não daqui
            elif I.data_xsd(meta):
                it.data = I.data_xsd(meta)   # data de captura REAL, do EXIF
        cands = [c for c in cands if c not in fase1]
        if fase1:
            print(f"  {len(fase1)} originais COM GPS pulados (são da fase 1: ingest-drive.py)")

    # Vídeos ORIGINAIS: a hora da gravação e (iPhone) a coordenada vêm do arquivo.
    vids_orig = [c for c in cands if c.original and c.kind == "video"]
    if vids_orig:
        I.prewarm([c.caminho for c in vids_orig])
        mv = le_meta_video([c.caminho for c in vids_orig])
        for it in vids_orig:
            meta = mv.get(str(it.caminho), {})
            real = data_do_video(meta, it.tour_data)
            if real:
                it.data = real
            if I.gps_valido(meta.get("GPSLatitude"), meta.get("GPSLongitude")):
                it.gps = (float(meta["GPSLatitude"]), float(meta["GPSLongitude"]))
        print(f"  {len(vids_orig)} vídeos originais: "
              f"{sum(1 for c in vids_orig if c.data and 'T' in c.data)} com hora de gravação, "
              f"{sum(1 for c in vids_orig if c.gps)} com GPS")

    dur_cat = duracoes_dos_videos(g)        # pra achar a cópia do zap de um vídeo original

    dups, erros, prontos, sem_pessoa, retidos = [], [], [], [], []
    subst, substituidas = [], set()      # originais que tomaram o lugar de uma cópia pior
    LOTE = 256                                  # pré-baixa em lotes (não o acervo inteiro de uma vez)
    for i, it in enumerate(cands, 1):
        if (i - 1) % LOTE == 0:
            I.prewarm([c.caminho for c in cands[i - 1:i - 1 + LOTE] if not c.original])
        conhecidos = fotos if it.kind == "image" else videos
        try:
            if it.kind == "image":
                img, icc = I._abre(it.caminho)
                it.hash = I.phash(img, icc)
            else:
                info = ffprobe(it.caminho)
                it.duracao = float(info.get("format", {}).get("duration") or 0)
                it.hash = vhash(it.caminho, it.duracao)
        except Exception as e:              # noqa: BLE001
            erros.append((it, f"hash: {e}"))
            anota(it, "error", reason=f"hash: {e}"[:120])
            continue
        antigo = I.ja_existe(it.hash, conhecidos)
        if not antigo and it.kind == "video" and it.original and not a.sem_substituir:
            # A dedup não reconhece a cópia do zap de um vídeo (ver gemeo_de_video).
            gem = gemeo_de_video(it.hash, it.duracao, dur_cat, conhecidos)
            if gem and gem not in substituidas \
                    and I.motivo_substituir(I.herdado(g, gem), it.gps is not None,
                                            bool(it.data and "T" in it.data)):
                antigo = gem
        if antigo:
            # ORIGINAL × a cópia pior (do zap) que já está no amora: o original
            # toma o lugar dela — foto (sem GPS, mas com EXIF) ou vídeo.
            h = None
            if it.original and not a.sem_substituir and antigo not in substituidas:
                h = I.herdado(g, antigo)
            mot = I.motivo_substituir(h, it.gps is not None, bool(it.data and "T" in it.data))
            if mot and a.apply:
                try:                            # o estado de AGORA da mídia, não o do começo
                    h = I.herdado_agora(servidor, antigo)
                    mot = I.motivo_substituir(h, it.gps is not None, bool(it.data and "T" in it.data))
                except Exception as e:          # noqa: BLE001
                    erros.append((it, f"relendo a mídia antes de substituir: {e}"))
                    anota(it, "error", reason=f"reler alvo: {e}"[:120])
                    continue
            if mot:
                if a.apply:
                    try:
                        if it.kind == "image":
                            it.variantes = I.monta_variantes(it.caminho, img, icc)
                            ok, msg = envia(servidor, "/upload-image",
                                            {"ttl": monta_ttl_imagem(it, alvo=antigo, herda=h)},
                                            it.variantes)
                        else:
                            it.variantes, it.duracao = transcoda_video(it.caminho, info)
                            ok, msg = envia(servidor, "/upload-video",
                                            {"ttl": monta_ttl_video(it, alvo=antigo, herda=h),
                                             "id": antigo}, it.variantes)
                    except subprocess.CalledProcessError as e:
                        ok, msg = False, f"ffmpeg: {(e.stderr or b'').decode(errors='replace')[:160]}"
                    except Exception as e:      # noqa: BLE001
                        ok, msg = False, f"variantes: {e}"
                    if not ok:
                        erros.append((it, msg))
                        anota(it, "error", reason=str(msg)[:120])
                        continue
                    anota(it, "ingested", media=antigo, hash=it.hash, src_gps=it.gps is not None,
                          replaced=mot, dist=I.hamming(it.hash, antigo))
                substituidas.add(antigo)
                subst.append((it, antigo, mot))
                print(f"  [{i}/{len(cands)}] {'⇄' if a.apply else '~'} {it.caminho.name[:44]:46} "
                      f"substitui med:{antigo} ({mot})")
                continue
            dups.append((it, antigo))
            anota(it, "duplicate", media=antigo, hash=it.hash,
                  dist=I.hamming(it.hash, antigo), src_gps=False,
                  alvo_geo=antigo in com_geo)
            continue
        # Parece uma mídia que foi APAGADA no amora? Então não sobe sozinha.
        if not (livro and it.src in livro.liberados):
            lp = L.lapide_proxima(it.hash, it.kind, lapides)
            if lp:
                retidos.append((it, lp))
                anota(it, "held", reason="lapide", media=lp[0], dist=lp[1], hash=it.hash)
                continue
        if not it.pessoa_slug:
            sem_pessoa.append(it)

        rot = (f"{'pas:' + it.tour_slug if it.tour_slug else '(sem passeio)'} "
               f"{'pes:' + it.pessoa_slug if it.pessoa_slug else '(' + (it.slug_bruto or 'sem slug') + ')'}")
        if a.apply:
            try:
                if it.kind == "image":
                    it.variantes = I.monta_variantes(it.caminho, img, icc)
                    ok, msg = envia(servidor, "/upload-image",
                                    {"ttl": monta_ttl_imagem(it)}, it.variantes)
                else:
                    it.variantes, it.duracao = transcoda_video(it.caminho, info)
                    ok, msg = envia(servidor, "/upload-video",
                                    {"ttl": monta_ttl_video(it), "id": it.hash}, it.variantes)
            except subprocess.CalledProcessError as e:
                ok, msg = False, f"ffmpeg: {(e.stderr or b'').decode(errors='replace')[:160]}"
            except Exception as e:          # noqa: BLE001
                ok, msg = False, f"variantes: {e}"
            if not ok:
                erros.append((it, msg))
                anota(it, "error", reason=str(msg)[:120])
                print(f"  [{i}/{len(cands)}] ✗ {it.caminho.name[:44]:46} {msg[:90]}")
                continue
            anota(it, "ingested", media=it.hash, hash=it.hash, src_gps=it.gps is not None)
            conhecidos.add(it.hash)
            print(f"  [{i}/{len(cands)}] ✓ {it.caminho.name[:44]:46} med:{it.hash} {rot}")
        else:
            conhecidos.add(it.hash)
            print(f"  [{i}/{len(cands)}] · {it.caminho.name[:44]:46} med:{it.hash} {rot}")
        prontos.append(it)

    print("\n" + "─" * 72)
    print(f"  candidatos ……………… {len(cands)}  ({n_img} imagens, {n_vid} vídeos)")
    print(f"  já no amora (dedup) … {len(dups)}")
    if subst:
        print(f"  {'SUBSTITUÍRAM' if a.apply else 'substituiriam'} a cópia … {len(subst)}  "
              f"(original no lugar da versão pior)")
    if retidos:
        print(f"  RETIDOS ……………… {len(retidos)}  (parecem mídia apagada no amora — "
              f"`media_ledger.py retidos`)")
        for it, (lap, d) in retidos[:8]:
            print(f"      {it.caminho.name[:40]:42} ~ {lap} ({d} bits)")
    print(f"  {'ENVIADOS' if a.apply else 'a enviar (dry-run)'} …………… {len(prontos)}")
    if sem_pessoa:
        print(f"  sem pessoa mapeada …… {len(sem_pessoa)}  (entram só com schema:creditText)")
    if erros:
        print(f"  ERROS ………………… {len(erros)}")
        for it, msg in erros[:10]:
            print(f"      {it.caminho.name[:40]:42} {msg[:80]}")
    faltando = sorted({it.slug_bruto for it in sem_pessoa if it.slug_bruto})
    if faltando:
        print(f"\n  slugs sem pessoa: {', '.join(faltando[:15])}{'…' if len(faltando) > 15 else ''}")
        print("  → preencha 'pessoa' em scripts/whatsapp-slug-map.json; um patch posterior atribui")
    if not a.apply:
        print("\n(--dry-run é o default: nada foi enviado. Use --apply.)")


if __name__ == "__main__":
    main()
