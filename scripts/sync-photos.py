#!/usr/bin/env python3
"""Fotos da Apple → amora: achar candidatas, revisar, (depois) enviar.

O acervo pessoal fica no app Fotos, não no Drive. Diferente do acervo do
Drive — onde estar na pasta do passeio JÁ é a curadoria —, a biblioteca do
Fotos tem de tudo: a vida inteira de quem a mantém, fotos de outras pessoas
salvas pelo WhatsApp, capturas de tela. Por isso aqui NADA sobe sem um "sim"
explícito, dado numa folha de contato local:

    sync-photos.py candidatas                 # por passeio: quantas, de que tipo
    sync-photos.py candidatas --passeio PH/56 # o detalhe de um passeio
    sync-photos.py revisar --passeio PH/56    # folha de contato em 127.0.0.1
    sync-photos.py enviar                     # o que subiria (dry-run)
    sync-photos.py enviar --apply             # baixa do iCloud e sobe o aprovado

Como uma foto vira candidata de um passeio:

  1. Caiu na JANELA do passeio (saída −1 h … chegada +1 h). Passeio sem hora
     conhecida (gravado às 00:00) usa o dia inteiro, e aí só o GPS desempata.
  2. Tem câmera no EXIF. Sem câmera = print, imagem salva do zap, download —
     não é registro do pedal (e a cópia do zap já vem pelo acervo do Drive).
  3. Vai pra um de três grupos pela distância à ROTA do passeio (routes.json):
     "na rota" (≤ 400 m), "longe da rota" (tem GPS, mas em outro lugar — pode
     ser o caminho de casa) e "sem GPS" (câmera sem GPS: só a hora sustenta).

Cada candidata é comparada com o amora pelo pHash da PRÉVIA local (os
originais moram no iCloud; baixar 4 mil pra só então descobrir que metade já
está lá não faz sentido): nova · substitui a cópia pior que já está lá · já
está · parece mídia apagada no amora. O hash que vale na hora de enviar é o do
original.

As decisões da revisão vão pra `.sync-state/photos-review.jsonl` (fora do
git, como o livro-razão): "aprovar" entra na fila de envio, "rejeitar" faz a
foto nunca mais ser proposta. A folha de contato só existe em 127.0.0.1 —
nunca é publicada em lugar nenhum.

Somente leitura no Fotos: nada é alterado, movido nem apagado na biblioteca.
"""
from __future__ import annotations

import argparse
import bisect
import html
import shutil
import tempfile
import urllib.error
import importlib.util
import json
import math
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _importa(mod: str, arquivo: str):
    if mod in sys.modules:
        return sys.modules[mod]
    spec = importlib.util.spec_from_file_location(mod, REPO / "scripts" / arquivo)
    m = importlib.util.module_from_spec(spec)
    sys.modules[mod] = m
    spec.loader.exec_module(m)
    return m


I = _importa("ingest_drive", "ingest-drive.py")   # pHash, dedup, substituição
W = _importa("ingest_whatsapp", "ingest-whatsapp.py")   # o caminho de vídeo (vhash, transcode)
A = I.A                                            # catálogos, passeios
L = I.L                                            # livro-razão

import rdflib  # noqa: E402

BIBLIOTECA_PADRAO = str(Path.home() / "Pictures" / "Local Photos Library.photoslibrary")
REVISAO = L.STATE_DIR / "photos-review.jsonl"
CACHE_HASH = L.STATE_DIR / "photos-preview-hash.json"
# De quem é cada câmera — a biblioteca tem fotos de mais de uma pessoa, e a
# autoria NÃO pode cair toda em quem mantém a biblioteca. Local e fora do git
# (como o livro-razão): { "padrao": "<slug da pessoa>", "cameras": { "<fabricante
# modelo, minúsculo>": "<slug>" } }. Sem o arquivo, ninguém é creditado.
CAMERAS = L.STATE_DIR / "photos-cameras.json"
# Álbuns do Fotos cujo conteúdo JÁ É a aprovação (estar no álbum = "sobe"), sem
# passar pela folha de contato: { "aprovados": ["Amora", "PH 56 …"] }. Uma
# decisão explícita na revisão ("não sobe") ainda ganha do álbum.
ALBUNS = L.STATE_DIR / "photos-albums.json"

TZ_SP = timezone(timedelta(hours=-3))
FOLGA = timedelta(hours=1)          # antes da saída / depois da chegada
DURACAO_PADRAO = timedelta(hours=6)  # passeio com saída mas sem chegada
ROTA_PERTO_M = 400

PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#")


# ═════════════════════════════════════════════════════════════════════════
# 1. Janelas e rotas dos passeios
# ═════════════════════════════════════════════════════════════════════════

def janela(g, p) -> tuple[datetime, datetime, str]:
    """(início, fim, confiança) — 'hora' quando o passeio tem horário, 'dia'
    quando só se sabe o dia (gravado às 00:00)."""
    t = rdflib.URIRef(p.iri)
    dep, arr = g.value(t, PH.departedAt), g.value(t, PH.arrivedAt)
    ini = dep.toPython() if dep is not None else p.data
    if ini.tzinfo is None:
        ini = ini.replace(tzinfo=TZ_SP)
    if dep is None and ini.hour == 0 and ini.minute == 0:
        return ini, ini + timedelta(hours=28), "dia"
    fim = arr.toPython() if arr is not None else ini + DURACAO_PADRAO
    if fim.tzinfo is None:
        fim = fim.replace(tzinfo=TZ_SP)
    return ini - FOLGA, fim + FOLGA, "hora"


def rotas(servidor: str) -> dict[str, list]:
    req = urllib.request.Request(f"{servidor}/routes.json", headers={"User-Agent": A.USER_AGENT})
    with urllib.request.urlopen(req, timeout=120, context=A._contexto_ssl()) as r:
        d = json.loads(r.read().decode("utf-8"))
    return {e["tourIri"]: e["latlngs"] for e in d.get("routes", [])
            if e.get("tourIri") and e.get("latlngs")}


def dist_rota_m(lat: float, lon: float, latlngs: list) -> float:
    """Distância (m) do ponto à polilinha — projeção equirretangular local,
    mais que suficiente pra separar "na rota" de "em casa"."""
    kx = 111_320 * math.cos(math.radians(lat))
    ky = 110_540
    melhor = float("inf")
    ax = ay = None
    for la, lo in latlngs:
        bx, by = (lo - lon) * kx, (la - lat) * ky
        if ax is not None:
            dx, dy = bx - ax, by - ay
            den = dx * dx + dy * dy
            t = 0.0 if den == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / den))
            d = math.hypot(ax + t * dx, ay + t * dy)
        else:
            d = math.hypot(bx, by)
        melhor = min(melhor, d)
        ax, ay = bx, by
    return melhor


# ═════════════════════════════════════════════════════════════════════════
# 2. A revisão (decisões humanas)
# ═════════════════════════════════════════════════════════════════════════

def le_revisao() -> dict[str, dict]:
    """uuid → última decisão ({'decisao': 'aprovar'|'rejeitar', 'tour', 'at'})."""
    out: dict[str, dict] = {}
    if REVISAO.exists():
        for linha in REVISAO.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            r = json.loads(linha)
            if r.get("decisao"):
                out[r["uuid"]] = r
            else:
                out.pop(r["uuid"], None)        # decisão desfeita
    return out


def grava_revisao(decisoes: dict[str, str | None], tour: str) -> int:
    REVISAO.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with REVISAO.open("a", encoding="utf-8") as f:
        for uuid, dec in decisoes.items():
            if dec not in ("aprovar", "rejeitar", None):
                continue
            f.write(json.dumps({"uuid": uuid, "decisao": dec, "tour": tour, "at": L.agora()},
                               ensure_ascii=False) + "\n")
            n += 1
        f.flush()
        os.fsync(f.fileno())
    return n


def le_cameras() -> dict:
    if CAMERAS.exists():
        d = json.loads(CAMERAS.read_text(encoding="utf-8"))
        return {"padrao": d.get("padrao"),
                "cameras": {k.lower(): v for k, v in (d.get("cameras") or {}).items()}}
    return {"padrao": None, "cameras": {}}


def le_albuns_aprovados() -> set[str]:
    if ALBUNS.exists():
        return set(json.loads(ALBUNS.read_text(encoding="utf-8")).get("aprovados") or [])
    return set()


def autora_da_camera(mapa: dict, camera: str) -> str | None:
    """Slug da pessoa (pes:<slug>) que fotografou com esta câmera, ou None."""
    return mapa["cameras"].get(camera.lower(), mapa["padrao"])


# ═════════════════════════════════════════════════════════════════════════
# 3. Candidatas
# ═════════════════════════════════════════════════════════════════════════

class Contexto:
    """Tudo que é caro de montar, uma vez só: biblioteca, catálogos, rotas."""

    def __init__(self, biblioteca: str, servidor: str):
        try:
            import osxphotos
        except ImportError:
            sys.exit("falta osxphotos (≥ 0.78): pip install -U osxphotos")
        print("abrindo a biblioteca do Fotos (só leitura)…", file=sys.stderr, flush=True)
        self.db = osxphotos.PhotosDB(biblioteca)
        self.fotos = sorted((f for f in self.db.photos(images=True, movies=True)
                             if f.date is not None and f.date.tzinfo is not None),
                            key=lambda f: f.date)
        self.datas = [f.date for f in self.fotos]
        self.servidor = servidor
        self.passeios, self.g = A.carregar_catalogos(servidor)
        self.rotas = rotas(servidor)
        self.por_classe = I.hashes_no_servidor(servidor)
        try:
            self.livro = L.Livro()
        except L.LivroAusente:
            self.livro = None
        self.lapides = L.prepara(self.por_classe, grava=False, livro=self.livro)
        self.revisao = le_revisao()
        self.cameras = le_cameras()
        self.albuns_ok = le_albuns_aprovados()
        PES = "https://id.pedalhidrografi.co/pessoas/"
        SN = rdflib.Namespace("https://schema.org/")
        self.nomes = {str(s)[len(PES):]: str(self.g.value(s, SN.alternateName) or self.g.value(s, SN.name) or "")
                      for s in self.g.subjects(rdflib.RDF.type, SN.Person) if str(s).startswith(PES)}
        self._hash: dict[str, str] = {}
        if CACHE_HASH.exists():
            self._hash = json.loads(CACHE_HASH.read_text(encoding="utf-8"))
        self._hash_sujo = False

    def passeio(self, chave: str):
        k = chave.strip().lower()
        for p in self.passeios:
            if p.edicao.lower() == k or p.slug.lower() == k:
                return p
        sys.exit(f"passeio não encontrado: {chave} (use a edição, ex.: PH/56, ou o slug)")

    def hash_previa(self, f) -> str | None:
        """pHash da maior prévia LOCAL (o original costuma estar só no iCloud)."""
        if f.uuid in self._hash:
            return self._hash[f.uuid] or None
        h = None
        for d in (f.path_derivatives or []):
            try:
                img, icc = I._abre(Path(d))
                h = I.phash(img, icc)
                break
            except Exception:  # noqa: BLE001
                continue
        self._hash[f.uuid] = h or ""
        self._hash_sujo = True
        return h

    def salva_cache(self) -> None:
        if self._hash_sujo:
            CACHE_HASH.parent.mkdir(parents=True, exist_ok=True)
            tmp = CACHE_HASH.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._hash), encoding="utf-8")
            os.replace(tmp, CACHE_HASH)
            self._hash_sujo = False

    def na_janela(self, ini: datetime, fim: datetime) -> list:
        return self.fotos[bisect.bisect_left(self.datas, ini):bisect.bisect_right(self.datas, fim)]


def candidatas(ctx: Contexto, p, com_hash: bool = True) -> tuple[list[dict], Counter]:
    """As candidatas de um passeio + o que foi deixado de fora (e por quê)."""
    ini, fim, conf = janela(ctx.g, p)
    rota = ctx.rotas.get(p.iri)
    fora = Counter()
    out = []
    for f in ctx.na_janela(ini, fim):
        if f.screenshot:
            fora["captura de tela"] += 1
            continue
        if f.hidden:
            fora["oculta"] += 1
            continue
        if f.shared:
            fora["de álbum compartilhado"] += 1
            continue
        ex = f.exif_info
        album_ok = sorted(ctx.albuns_ok.intersection(f.albums or []))
        tem_camera = bool(ex and ex.camera_make)
        if not tem_camera and not album_ok:
            fora["sem câmera no EXIF (zap / download)"] += 1
            continue
        src = L.chave_photos(f.uuid)
        if ctx.livro and src in ctx.livro.terminal:
            fora["já resolvida no livro-razão"] += 1
            continue
        gps = (f.latitude, f.longitude) if f.latitude is not None and f.longitude is not None else None
        dist = dist_rota_m(gps[0], gps[1], rota) if (gps and rota) else None
        if gps is None:
            grupo = "sem-gps"
        elif dist is None:
            grupo = "sem-rota"
        elif dist <= ROTA_PERTO_M:
            grupo = "na-rota"
        else:
            grupo = "longe"
        previas = f.path_derivatives or []
        estado, alvo = "video" if f.ismovie else "sem-previa", None
        if com_hash and not f.ismovie and previas:
            h = ctx.hash_previa(f)
            if h:
                antigo = I.ja_existe(h, ctx.por_classe["StillImage"])
                if antigo:
                    mot = I.motivo_substituir(I.herdado(ctx.g, antigo), gps is not None, True)
                    estado, alvo = ("substitui" if mot else "ja-esta"), antigo
                elif L.lapide_proxima(h, "image", ctx.lapides):
                    estado, alvo = "lapide", L.lapide_proxima(h, "image", ctx.lapides)[0]
                else:
                    estado = "nova"
        dec = ctx.revisao.get(f.uuid)
        # Sem câmera no EXIF não dá pra saber quem fez (costuma ser foto de
        # outra pessoa, salva do zap): entra SEM autoria, nunca no "padrão".
        camera = f"{ex.camera_make} {ex.camera_model or ''}".strip() if tem_camera else "(sem câmera)"
        autora = autora_da_camera(ctx.cameras, camera) if tem_camera else None
        out.append({
            "uuid": f.uuid, "nome": f.original_filename, "data": f.date.isoformat(),
            "hora": f.date.astimezone(TZ_SP).strftime("%H:%M:%S"),
            "kind": "video" if f.ismovie else "image",
            "camera": camera, "autora": autora,
            "autora_nome": (ctx.nomes.get(autora) or autora) if autora else None,
            "gps": gps, "dist_m": round(dist) if dist is not None else None,
            "grupo": grupo, "estado": estado, "alvo": alvo,
            "editada": bool(f.hasadjustments), "local": bool(f.path),
            "previa": previas[0] if previas else None,
            # Decisão: a da revisão, se houver; senão o álbum aprovado vale "sobe"
            # — MENOS pra foto com GPS LONGE da rota: ela pode ser de casa, do
            # caminho, e sobe com o EXIF inteiro. Essa só com um "sim" explícito
            # na folha de contato, mesmo estando no álbum.
            "decisao": dec["decisao"] if dec else ("aprovar" if (album_ok and grupo != "longe") else None),
            "via": "revisão" if dec else ("álbum" if (album_ok and grupo != "longe") else None),
            "albuns": album_ok, "confianca": conf,
            # Bandeira na folha de contato: está num álbum aprovado, mas o GPS
            # cai longe da rota — pode ser de casa ou do caminho.
            "alerta": "do álbum, mas LONGE da rota — confira" if (album_ok and grupo == "longe") else None,
        })
    ctx.salva_cache()
    return out, fora


def candidatas_sem_passeio(ctx: Contexto, com_hash: bool = True) -> list[dict]:
    """As de álbum aprovado que NÃO caem na janela de nenhum passeio. Não há
    rota contra a qual conferir, e a coordenada (se houver) pode ser de
    qualquer lugar — então o álbum NÃO as aprova sozinho: cada uma pede um
    "sim" na folha de contato (`revisar --sem-passeio`). Sobem sem passeio."""
    em_janela = set()
    for p in ctx.passeios:
        ini, fim, _ = janela(ctx.g, p)
        em_janela.update(f.uuid for f in ctx.na_janela(ini, fim))
    out = []
    for f in ctx.fotos:
        if f.uuid in em_janela:
            continue
        album_ok = sorted(ctx.albuns_ok.intersection(f.albums or []))
        if not album_ok or f.screenshot or f.hidden or f.shared:
            continue
        if ctx.livro and L.chave_photos(f.uuid) in ctx.livro.terminal:
            continue
        ex = f.exif_info
        tem_camera = bool(ex and ex.camera_make)
        camera = f"{ex.camera_make} {ex.camera_model or ''}".strip() if tem_camera else "(sem câmera)"
        autora = autora_da_camera(ctx.cameras, camera) if tem_camera else None
        gps = (f.latitude, f.longitude) if f.latitude is not None and f.longitude is not None else None
        previas = f.path_derivatives or []
        estado, alvo = "video" if f.ismovie else "sem-previa", None
        if com_hash and not f.ismovie and previas:
            h = ctx.hash_previa(f)
            if h:
                antigo = I.ja_existe(h, ctx.por_classe["StillImage"])
                if antigo:
                    mot = I.motivo_substituir(I.herdado(ctx.g, antigo), gps is not None, True)
                    estado, alvo = ("substitui" if mot else "ja-esta"), antigo
                elif L.lapide_proxima(h, "image", ctx.lapides):
                    estado, alvo = "lapide", L.lapide_proxima(h, "image", ctx.lapides)[0]
                else:
                    estado = "nova"
        dec = ctx.revisao.get(f.uuid)
        out.append({
            "uuid": f.uuid, "nome": f.original_filename, "data": f.date.isoformat(),
            "hora": f.date.astimezone(TZ_SP).strftime("%d/%m/%Y %H:%M"),
            "kind": "video" if f.ismovie else "image", "camera": camera, "autora": autora,
            "autora_nome": (ctx.nomes.get(autora) or autora) if autora else None,
            "gps": gps, "dist_m": None, "grupo": "fora-de-janela", "estado": estado, "alvo": alvo,
            "editada": bool(f.hasadjustments), "local": bool(f.path),
            "previa": previas[0] if previas else None,
            "decisao": dec["decisao"] if dec else None, "via": "revisão" if dec else None,
            "albuns": album_ok, "confianca": None,
            "alerta": "fora da janela de qualquer passeio" + (" · tem GPS" if gps else ""),
        })
    ctx.salva_cache()
    return out


GRUPOS = [("na-rota", "Na rota do passeio"), ("sem-rota", "Com GPS (passeio sem rota)"),
          ("longe", "Com GPS, longe da rota"), ("sem-gps", "Sem GPS (só a hora sustenta)"),
          ("fora-de-janela", "De álbum aprovado, fora da janela de qualquer passeio (sobem sem passeio)")]
ESTADOS = {"nova": "nova", "substitui": "substitui a cópia do amora", "ja-esta": "já está no amora",
           "lapide": "parece mídia apagada", "video": "vídeo", "sem-previa": "sem prévia local"}


def cmd_candidatas(a) -> None:
    ctx = Contexto(a.biblioteca, a.servidor.rstrip("/"))
    if a.passeio:
        p = ctx.passeio(a.passeio)
        cs, fora = candidatas(ctx, p)
        ini, fim, conf = janela(ctx.g, p)
        print(f"\n{p.edicao} — {p.titulo}")
        print(f"janela: {ini.astimezone(TZ_SP):%d/%m/%Y %H:%M} – {fim.astimezone(TZ_SP):%d/%m %H:%M}"
              f"{'  (só o DIA é conhecido)' if conf == 'dia' else ''}")
        print(f"{len(cs)} candidatas")
        for chave, rot in GRUPOS:
            g = [c for c in cs if c["grupo"] == chave]
            if g:
                est = Counter(ESTADOS[c["estado"]] for c in g)
                print(f"  {len(g):5}  {rot}: " + ", ".join(f"{v} {k}" for k, v in est.most_common()))
        print("  câmeras (→ autoria): " + ", ".join(
            f"{v} {k} → {a or 'SEM AUTORIA'}" for (k, a), v in
            Counter((c["camera"], c["autora_nome"]) for c in cs).most_common()))
        dec = Counter((c["decisao"] or "sem decisão") + (f" (via {c['via']})" if c["via"] else "") for c in cs)
        print("  decisão: " + ", ".join(f"{v} {k}" for k, v in dec.most_common()))
        print(f"  editadas: {sum(1 for c in cs if c['editada'])} (sobe a versão EDITADA)")
        if fora:
            print("  fora: " + ", ".join(f"{v} {k}" for k, v in fora.most_common()))
        if a.json:
            a.json.write_text(json.dumps(cs, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"→ {a.json}")
        return

    linhas, tot = [], Counter()
    for p in ctx.passeios:
        cs, _ = candidatas(ctx, p, com_hash=False)     # visão geral: sem hashear 4 mil prévias
        if not cs:
            continue
        c = Counter(x["grupo"] for x in cs)
        tot.update(c)
        linhas.append((p, len(cs), c, janela(ctx.g, p)[2]))
    print(f"\n{sum(n for _, n, _, _ in linhas)} candidatas em {len(linhas)} passeios "
          f"({tot['na-rota']} na rota, {tot['longe']} longe, {tot['sem-gps']} sem GPS, "
          f"{tot['sem-rota']} sem rota)\n")
    print(f"  {'data':10} {'passeio':13} {'total':>5} {'rota':>5} {'longe':>5} {'s/gps':>5}  título")
    for p, n, c, conf in linhas:
        print(f"  {p.data.date()} {p.edicao:13} {n:5} {c['na-rota']:5} {c['longe']:5} {c['sem-gps']:5}  "
              f"{p.titulo[:34]}{'  [só o dia]' if conf == 'dia' else ''}")


# ═════════════════════════════════════════════════════════════════════════
# 4. Folha de contato (só em 127.0.0.1)
# ═════════════════════════════════════════════════════════════════════════

PAGINA = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisão — __TITULO__</title>
<style>
  :root { color-scheme: light dark; --ok: #1a7f4b; --no: #b3261e; --bd: #8884; }
  body { font: 14px/1.4 system-ui, sans-serif; margin: 0; padding: 12px 16px 90px; }
  h1 { font-size: 18px; margin: 0 0 4px; } h2 { font-size: 15px; margin: 22px 0 8px; }
  .sub { opacity: .75; margin: 0 0 10px; }
  .barra { position: fixed; left: 0; right: 0; bottom: 0; padding: 10px 16px; display: flex; gap: 10px;
           align-items: center; flex-wrap: wrap; background: Canvas; border-top: 1px solid var(--bd); }
  button { font: inherit; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--bd); background: ButtonFace; cursor: pointer; }
  button.pri { background: var(--ok); color: #fff; border-color: var(--ok); }
  .filtros { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0 2px; }
  .filtros label { border: 1px solid var(--bd); border-radius: 999px; padding: 2px 10px; cursor: pointer; }
  .grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; }
  .t { border: 3px solid transparent; border-radius: 8px; overflow: hidden; cursor: pointer; background: #8881; position: relative; }
  .t img { width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; }
  .t .leg { padding: 4px 6px; font-size: 12px; }
  .t .est { font-size: 11px; opacity: .8; }
  .t[data-d="aprovar"] { border-color: var(--ok); } .t[data-d="rejeitar"] { border-color: var(--no); opacity: .45; }
  .t[data-d="aprovar"]::after { content: "✓ sobe"; position: absolute; top: 6px; left: 6px; background: var(--ok); color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 12px; }
  .t[data-d="rejeitar"]::after { content: "✕ não"; position: absolute; top: 6px; left: 6px; background: var(--no); color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 12px; }
  .t.oculta { display: none; }
  .tag { display: inline-block; border: 1px solid var(--bd); border-radius: 4px; padding: 0 4px; font-size: 11px; }
  .tag.sub { border-color: var(--ok); } .tag.lap { border-color: var(--no); }
  .alerta { display: block; margin-top: 2px; font-size: 11px; font-weight: 600; color: #b45309; }
  .t.com-alerta { outline: 2px dashed #d97706; outline-offset: -2px; }
</style>
<h1>__TITULO__</h1>
<p class="sub">__SUB__ · Clique na foto: <b>sobe</b> → <b>não sobe</b> → sem decisão. Nada sai desta máquina aqui:
"Salvar" só grava a sua escolha; o envio é outro passo.</p>
<div class="filtros" id="cams"></div>
<div id="grupos"></div>
<div class="barra">
  <button class="pri" id="salvar">Salvar decisões</button>
  <span id="conta"></span><span id="msg"></span>
</div>
<script>
const DADOS = __DADOS__, GRUPOS = __GRUPOS__, ESTADOS = __ESTADOS__;
const dec = Object.fromEntries(DADOS.map((c) => [c.uuid, c.decisao]));
const cams = [...new Set(DADOS.map((c) => c.camera))];
const camOn = new Set(cams);
const $ = (s) => document.querySelector(s);
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch])); }
$('#cams').innerHTML = cams.map((c, i) => { const ds = DADOS.filter((d) => d.camera === c); return `<label><input type="checkbox" data-cam="${i}" checked> ${esc(c)} — de ${esc(ds[0].autora_nome || 'SEM AUTORIA')} (${ds.length})</label>`; }).join('');
$('#cams').addEventListener('change', (e) => { const c = cams[e.target.dataset.cam]; e.target.checked ? camOn.add(c) : camOn.delete(c); pinta(); });
function tile(c) {
  const tag = c.estado === 'substitui' ? '<span class="tag sub">substitui a cópia do amora</span>'
    : c.estado === 'lapide' ? '<span class="tag lap">parece mídia apagada</span>'
    : c.estado === 'nova' ? '' : `<span class="tag">${esc(ESTADOS[c.estado])}</span>`;
  return `<div class="t${c.alerta ? ' com-alerta' : ''}" data-u="${c.uuid}" data-cam="${esc(c.camera)}" title="${esc(c.nome)}">` +
    `<img loading="lazy" src="/previa/${c.uuid}" alt="">` +
    `<div class="leg">${c.hora}${c.kind === 'video' ? ' ▶' : ''}${c.editada ? ' ✎' : ''} · ${esc(c.camera)}` +
    `<div class="est">${c.dist_m != null ? c.dist_m + ' m da rota · ' : ''}${tag}</div>` +
    (c.alerta ? `<span class="alerta">⚠ ${esc(c.alerta)}</span>` : '') + `</div></div>`;
}
$('#grupos').innerHTML = GRUPOS.map(([k, rot]) => {
  const g = DADOS.filter((c) => c.grupo === k);
  return g.length ? `<h2>${rot} — ${g.length} <button data-todas="${k}">marcar as novas como "sobe" (menos as ⚠)</button> <button data-limpa="${k}">limpar</button></h2><div class="grade">${g.map(tile).join('')}</div>` : '';
}).join('');
function pinta() {
  for (const el of document.querySelectorAll('.t')) {
    el.dataset.d = dec[el.dataset.u] || '';
    el.classList.toggle('oculta', !camOn.has(el.dataset.cam));
  }
  const v = Object.values(dec);
  $('#conta').textContent = `${v.filter((x) => x === 'aprovar').length} sobem · ${v.filter((x) => x === 'rejeitar').length} não sobem · ${v.filter((x) => !x).length} sem decisão`;
}
document.addEventListener('click', (e) => {
  const t = e.target.closest('.t');
  if (t) { const u = t.dataset.u; dec[u] = dec[u] === 'aprovar' ? 'rejeitar' : dec[u] === 'rejeitar' ? null : 'aprovar'; pinta(); return; }
  const b = e.target.closest('button');
  if (!b) return;
  const k = b.dataset.todas || b.dataset.limpa;
  if (k) {
    for (const c of DADOS) {
      if (c.grupo !== k || !camOn.has(c.camera)) continue;
      if (b.dataset.limpa) dec[c.uuid] = null;
      // As com bandeira (⚠) nunca entram no "marcar todas": pedem um clique próprio.
      else if (!c.alerta && !dec[c.uuid] && (c.estado === 'nova' || c.estado === 'substitui' || c.estado === 'video')) dec[c.uuid] = 'aprovar';
    }
    pinta();
  }
});
$('#salvar').addEventListener('click', async () => {
  $('#msg').textContent = 'salvando…';
  const mudou = Object.fromEntries(DADOS.filter((c) => (dec[c.uuid] || null) !== (c.decisao || null)).map((c) => [c.uuid, dec[c.uuid] || null]));
  const r = await fetch('/salvar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mudou) });
  const j = await r.json();
  if (r.ok) { for (const c of DADOS) c.decisao = dec[c.uuid] || null; $('#msg').textContent = `✓ ${j.gravadas} decisões gravadas`; }
  else $('#msg').textContent = 'erro: ' + (j.erro || r.status);
});
pinta();
</script></html>"""


def cmd_revisar(a) -> None:
    if bool(a.passeio) == bool(a.sem_passeio):
        sys.exit("escolha UM: --passeio <edição> ou --sem-passeio.")
    ctx = Contexto(a.biblioteca, a.servidor.rstrip("/"))
    print("calculando as candidatas (hash das prévias)…", file=sys.stderr, flush=True)
    if a.sem_passeio:
        p, fora = None, Counter()
        cs = candidatas_sem_passeio(ctx)
        if not cs:
            sys.exit("nenhuma foto de álbum aprovado fora da janela dos passeios.")
        titulo = "Álbuns aprovados — fora da janela de qualquer passeio"
        sub = f"{len(cs)} itens · sobem SEM passeio, só os que você marcar"
    else:
        p = ctx.passeio(a.passeio)
        cs, fora = candidatas(ctx, p)
        if not cs:
            sys.exit(f"nenhuma candidata pro {p.edicao}.")
        ini, fim, conf = janela(ctx.g, p)
        titulo = f"{p.edicao} — {p.titulo}"
        sub = (f"{len(cs)} candidatas · janela {ini.astimezone(TZ_SP):%d/%m/%Y %H:%M}–"
               f"{fim.astimezone(TZ_SP):%H:%M}" + (" (só o dia é conhecido)" if conf == "dia" else ""))
    previas = {c["uuid"]: c["previa"] for c in cs if c["previa"]}
    dados = [{k: c[k] for k in ("uuid", "nome", "hora", "kind", "camera", "autora_nome", "dist_m",
                                "grupo", "estado", "editada", "decisao", "alerta")} for c in cs]
    pagina = (PAGINA.replace("__TITULO__", html.escape(titulo))
              .replace("__SUB__", html.escape(sub))
              .replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"))
              .replace("__GRUPOS__", json.dumps(GRUPOS, ensure_ascii=False))
              .replace("__ESTADOS__", json.dumps(ESTADOS, ensure_ascii=False))).encode("utf-8")
    tour_slug = p.slug if p else ""

    class H(BaseHTTPRequestHandler):
        def log_message(self, *_):       # silencioso
            pass

        def _manda(self, code, corpo: bytes, tipo: str):
            self.send_response(code)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            if self.path == "/":
                return self._manda(200, pagina, "text/html; charset=utf-8")
            if self.path.startswith("/previa/"):
                # Só serve prévia de candidata DESTA página (o uuid é a chave
                # de um dicionário — nenhum caminho vem da URL).
                arq = previas.get(self.path[len("/previa/"):])
                if arq and os.path.isfile(arq):
                    with open(arq, "rb") as f:
                        return self._manda(200, f.read(), "image/jpeg")
            self._manda(404, b"", "text/plain")

        def do_POST(self):
            if self.path != "/salvar":
                return self._manda(404, b"", "text/plain")
            try:
                n = int(self.headers.get("Content-Length") or 0)
                d = json.loads(self.rfile.read(n).decode("utf-8"))
                d = {u: v for u, v in d.items() if u in previas or any(c["uuid"] == u for c in cs)}
                g = grava_revisao(d, tour_slug)
                self._manda(200, json.dumps({"gravadas": g}).encode(), "application/json")
            except Exception as e:  # noqa: BLE001
                self._manda(400, json.dumps({"erro": str(e)}).encode(), "application/json")

    srv = ThreadingHTTPServer(("127.0.0.1", a.porta), H)      # SÓ loopback
    print(f"\nfolha de contato ({titulo}): http://127.0.0.1:{a.porta}/   (Ctrl-C pra fechar)")
    print(f"decisões → {REVISAO}")
    if fora:
        print("fora da folha: " + ", ".join(f"{v} {k}" for k, v in fora.most_common()))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nfechado.")


# ═════════════════════════════════════════════════════════════════════════
# 5. Enviar o que foi aprovado
# ═════════════════════════════════════════════════════════════════════════
# Um por vez: baixa do iCloud (pelo app Fotos) → EXIF → pHash do ARQUIVO → a
# mesma decisão das ingestões do Drive (duplicata / substitui a cópia pior /
# lápide / nova) → sobe → registra no livro-razão → apaga o temporário.

LIMITE_REQ = 31 * 1024 * 1024       # o Cloud Run recusa corpo > 32 MiB


def fila(ctx: Contexto, so_passeio=None) -> tuple[list[tuple], Counter]:
    """[(foto do Fotos, candidata, passeio | None)] do que está aprovado (pela
    revisão ou por álbum) e ainda sem desfecho no livro. Foto de álbum aprovado
    que não cai na janela de passeio nenhum entra SEM passeio."""
    por_uuid = {f.uuid: f for f in ctx.fotos}
    out, vistos, resumo = [], set(), Counter()
    passeios = [so_passeio] if so_passeio else ctx.passeios
    for p in passeios:
        cs, _ = candidatas(ctx, p, com_hash=False)
        for c in cs:
            if c["uuid"] in vistos:
                continue
            if c["decisao"] == "rejeitar":
                resumo["rejeitadas na revisão"] += 1
                vistos.add(c["uuid"])
            elif c["decisao"] == "aprovar":
                vistos.add(c["uuid"])
                out.append((por_uuid[c["uuid"]], c, p))
            elif c.get("albuns") and c["grupo"] == "longe":
                resumo["de álbum aprovado, mas com GPS LONGE da rota (pedem um sim na folha de contato)"] += 1
            else:
                resumo["sem decisão (não sobem)"] += 1
    if not so_passeio and ctx.albuns_ok:
        for c in candidatas_sem_passeio(ctx, com_hash=False):
            if c["uuid"] in vistos:
                continue
            if c["decisao"] == "aprovar":
                out.append((por_uuid[c["uuid"]], c, None))
                resumo["de álbum aprovado, fora de qualquer passeio, com SIM na revisão (sobem sem passeio)"] += 1
            elif c["decisao"] == "rejeitar":
                resumo["rejeitadas na revisão"] += 1
            else:
                resumo["de álbum aprovado, fora da janela de qualquer passeio (pedem um sim: revisar --sem-passeio)"] += 1
    return out, resumo


def baixa(f, destino: Path) -> Path:
    """O arquivo que sobe: a versão EDITADA quando a foto foi editada no Fotos
    (decisão do coletivo: vale o que a pessoa escolheu mostrar), senão o
    original. Usa o arquivo local se ele existir; senão pede ao app Fotos, que
    baixa do iCloud."""
    editada = bool(f.hasadjustments)
    local = f.path_edited if editada else f.path
    if local and os.path.isfile(local):
        alvo = destino / os.path.basename(local)
        shutil.copyfile(local, alvo)
        return alvo
    out = f.export(str(destino), edited=editada, use_photos_export=True, timeout=180, overwrite=True)
    if not out:
        raise RuntimeError("o Fotos não exportou o arquivo (iCloud fora do ar? app Fotos travado?)")
    return Path(out[0])


def monta_ttl_foto(alvo: str, *, data, gps, bearing, focal, mime, tour_slug, autora, provedor,
                   herda: dict | None) -> str:
    """TTL de uma foto vinda do Fotos. `alvo` = o hash que vira o IRI (o da
    própria foto, ou o da mídia que ela SUBSTITUI — aí `herda` traz o que a
    antiga tinha). Autora = dona da câmera; quem subiu = dona da biblioteca."""
    ident = f"med:{alvo}"
    fonte = ""
    if gps is None and herda and herda["geo"]:
        gps = herda["geo"]                    # a antiga tinha coordenada: não se perde
        fonte = I.linha_fonte_geo(herda)      # …e segue marcada, se era aproximada
    props = ["a ph:StillImage" + (", ph:GeoreferencedImage" if gps else ""),
             f"nfo:hasHash {ident}_hash"]
    if data:
        props.append(f'dcterms:date "{data}"^^xsd:dateTime')
    elif herda and herda["data"]:
        props.append(f"dcterms:date {herda['data']}")
    if gps:
        props.append(f"schema:locationCreated {ident}_geo")
    if bearing is not None:
        props.append(f'exif:gpsImgDirection "{I._dec(bearing)}"^^xsd:decimal')
    if focal is not None:
        props.append(f'exif:focalLengthIn35mmFilm "{I._dec(focal)}"^^xsd:decimal')
    pes = "https://id.pedalhidrografi.co/pessoas/"
    if herda is not None:
        if herda["do_zap"] and autora:
            # A cópia do zap foi creditada a quem a COMPARTILHOU no grupo; o
            # original diz de quem é a câmera. Vale a câmera — quem
            # compartilhou segue no schema:creditText e em pav:providedBy.
            herda = {**herda, "autores": []}
        props += I.props_herdados(herda, autora, tour_slug, None)
        if provedor and pes + provedor not in herda["provedores"]:
            props.append(f"pav:providedBy <{pes}{provedor}>")
    else:
        props.append(f"dcterms:license <{I.LICENCA_PADRAO}>")
        if tour_slug:
            props.append(f"ph:capturedDuring pas:{tour_slug}")
        if autora:
            props.append(f"prov:wasAttributedTo pes:{autora}")
        if provedor:
            props.append(f"pav:providedBy pes:{provedor}")
    if mime != "image/jpeg":
        props.append(f'schema:encodingFormat "{mime}"')
    corpo = " ;\n".join(f"    {x}" for x in props)
    derivados = (f"{ident}_hash a nfo:FileHash ;\n"
                 f'    nfo:hashAlgorithm "pHash" ;\n'
                 f'    nfo:hashValue "{alvo}" .')
    if gps:
        derivados += (f"\n\n{ident}_geo a schema:GeoCoordinates ;\n"
                      f'    schema:latitude "{gps[0]:.6f}"^^xsd:decimal ;\n'
                      f'    schema:longitude "{gps[1]:.6f}"^^xsd:decimal{fonte} .')
    return f"{I.PREFIXOS}\n{ident}\n{corpo} .\n\n{derivados}\n"


def posta(servidor: str, ttl: str, variantes: dict) -> tuple[bool, str]:
    body, headers = I._multipart({"ttl": ttl}, variantes)
    if len(body) > LIMITE_REQ:
        return False, f"requisição de {len(body) / 2**20:.0f} MiB passa do limite de 31 MiB"
    headers["User-Agent"] = A.USER_AGENT
    req = urllib.request.Request(f"{servidor}/upload-image", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300, context=A._contexto_ssl()) as r:
            j = json.loads(r.read().decode("utf-8"))
            return True, f"phash={j.get('phash')}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}"
    except Exception as e:                  # noqa: BLE001
        return False, str(e)


def cmd_enviar(a) -> None:
    ctx = Contexto(a.biblioteca, a.servidor.rstrip("/"))
    servidor = ctx.servidor
    so = ctx.passeio(a.passeio) if a.passeio else None
    itens, resumo = fila(ctx, so)
    if a.sem_videos:
        itens = [x for x in itens if x[1]["kind"] == "image"]
    if a.uuid:
        itens = [x for x in itens if x[0].uuid in set(a.uuid)]
    if a.limite:
        itens = itens[:a.limite]

    print("═" * 72)
    n_vid = sum(1 for x in itens if x[1]["kind"] == "video")
    print(f"  FOTOS → AMORA   {len(itens) - n_vid} fotos + {n_vid} vídeos aprovados na fila"
          + (f" ({so.edicao})" if so else ""))
    print("═" * 72)
    for k, v in resumo.most_common():
        print(f"  {v:5}  {k}")
    por_autora = Counter((ctx.nomes.get(c["autora"]) or c["autora"] or "SEM AUTORIA") for _, c, _ in itens)
    print("  autoria: " + ", ".join(f"{v} {k}" for k, v in por_autora.most_common()))
    print(f"  editadas (sobe a versão editada): {sum(1 for _, c, _ in itens if c['editada'])}")
    por_passeio = Counter((p.edicao if p else "(sem passeio)") for _, _, p in itens)
    print("  passeios: " + ", ".join(f"{v} {k}" for k, v in por_passeio.most_common(12))
          + ("…" if len(por_passeio) > 12 else ""))
    if not itens:
        return
    if not a.apply:
        print("\n(dry-run: nada foi baixado nem enviado. Use --apply.)")
        return

    # ── pra valer: livro (trava de escritor único), lápides, catálogo ──────
    livro = L.abre_livro(True, a.iniciar_livro)
    lapides = L.prepara(ctx.por_classe, grava=True, livro=livro)
    fotos_cat = ctx.por_classe["StillImage"]
    videos_cat = ctx.por_classe["MotionImage"]
    dur_cat = W.duracoes_dos_videos(ctx.g)
    vivos = set().union(*ctx.por_classe.values())
    provedor = ctx.cameras["padrao"]            # quem mantém a biblioteca é quem sobe

    # Rejeições da revisão viram "excluded" no livro: nunca mais propostas.
    for uuid, dec in ctx.revisao.items():
        src = L.chave_photos(uuid)
        if dec["decisao"] == "rejeitar" and src not in livro.terminal:
            livro.registra(src, "excluded", fase="photos", reason="rejeitada na revisão",
                           tour=dec.get("tour"))

    cont = Counter()
    substituidas: set[str] = set()
    erros = []

    class RelerFalhou(Exception):
        pass

    def herdado_do_alvo(alvo: str):
        # O estado de AGORA da mídia que seria substituída (não o do começo da
        # rodada): o /upload-* é purge-and-replace, e uma coordenada colocada
        # à mão ou um álbum editado no meio do caminho se perderiam.
        try:
            return I.herdado_agora(servidor, alvo)
        except Exception as e:                  # noqa: BLE001
            raise RelerFalhou(str(e))
    for i, (f, c, p) in enumerate(itens, 1):
        src = L.chave_photos(f.uuid)
        est, _ = L.estado_da_origem(src, livro, vivos)
        if est in ("subiu", "duplicata", "excluida", "apagada-no-amora"):
            cont[f"já no livro ({est})"] += 1
            continue
        tour_slug = p.slug if p else None

        def anota(outcome, **kw):
            livro.registra(src, outcome, fase="photos", kind=c["kind"], path=f.original_filename,
                           tour=tour_slug, camera=c["camera"], **kw)

        if shutil.disk_usage(tempfile.gettempdir()).free < 2 * 1024**3:
            sys.exit("menos de 2 GiB livres no disco temporário — parei antes de baixar mais.")
        tmp = Path(tempfile.mkdtemp(prefix="amora-fotos-"))
        rot = f"  [{i}/{len(itens)}] {{}} {f.original_filename[:34]:36}"
        try:
            try:
                caminho = baixa(f, tmp)
            except Exception as e:              # noqa: BLE001
                erros.append((f, f"download: {e}"))
                anota("error", reason=f"download: {e}"[:120])
                print(rot.format("✗") + f" download: {str(e)[:70]}")
                continue
            if c["kind"] == "video":
                # ── vídeo: o mesmo caminho da ingestão do Drive (vhash, 360p) ──
                try:
                    info = W.ffprobe(caminho)
                    dur = float(info.get("format", {}).get("duration") or 0)
                    it = W.Item(caminho=caminho, pasta="", kind="video", original=True)
                    it.hash, it.duracao = W.vhash(caminho, dur), dur
                except Exception as e:          # noqa: BLE001
                    erros.append((f, f"hash: {e}"))
                    anota("error", reason=f"hash: {e}"[:120])
                    print(rot.format("✗") + f" hash do vídeo: {str(e)[:60]}")
                    continue
                mv = W.le_meta_video([caminho]).get(str(caminho), {})
                it.data = W.data_do_video(mv, p.data if p else None) \
                    or f.date.replace(microsecond=0).isoformat()
                lat, lon = mv.get("GPSLatitude"), mv.get("GPSLongitude")
                if not I.gps_valido(lat, lon):
                    lat, lon = f.latitude, f.longitude
                it.gps = (float(lat), float(lon)) if I.gps_valido(lat, lon) else None
                it.tour_slug, it.pessoa_slug = tour_slug, c["autora"]
                antigo = I.ja_existe(it.hash, videos_cat) \
                    or W.gemeo_de_video(it.hash, dur, dur_cat, videos_cat)
                herda = None
                if antigo:
                    herda = None if antigo in substituidas else herdado_do_alvo(antigo)
                    mot = I.motivo_substituir(herda, it.gps is not None, True)
                    if not mot:
                        cont["já estava no amora (duplicata)"] += 1
                        anota("duplicate", media=antigo, hash=it.hash,
                              dist=I.hamming(it.hash, antigo), src_gps=it.gps is not None)
                        print(rot.format("=") + f" já está: med:{antigo}")
                        continue
                    alvo = antigo
                else:
                    if src not in livro.liberados:
                        lp = L.lapide_proxima(it.hash, "video", lapides)
                        if lp:
                            cont["RETIDAS (parecem mídia apagada)"] += 1
                            anota("held", reason="lapide", media=lp[0], dist=lp[1], hash=it.hash)
                            print(rot.format("!") + f" retido ~ lápide {lp[0]} ({lp[1]} bits)")
                            continue
                    alvo, mot = it.hash, None
                try:
                    variantes, it.duracao = W.transcoda_video(caminho, info)
                    ttl = W.monta_ttl_video(it, alvo=alvo if mot else None, herda=herda if mot else None)
                    if not mot and c["autora"] and provedor:
                        # autora = dona da câmera; quem subiu = dona da biblioteca
                        ttl = ttl.replace(f"pav:providedBy pes:{c['autora']}", f"pav:providedBy pes:{provedor}")
                    ok, msg = W.envia(servidor, "/upload-video", {"ttl": ttl, "id": alvo}, variantes)
                except Exception as e:          # noqa: BLE001
                    ok, msg = False, f"transcode: {str(e)[:160]}"
                if not ok:
                    erros.append((f, msg))
                    anota("error", reason=str(msg)[:120])
                    print(rot.format("✗") + f" {msg[:80]}")
                    continue
                anota("ingested", media=alvo, hash=it.hash, src_gps=it.gps is not None, replaced=mot,
                      dist=I.hamming(it.hash, alvo) if mot else None)
                videos_cat.add(alvo)
                if mot:
                    substituidas.add(alvo)
                    cont[f"SUBSTITUÍRAM a cópia do amora ({mot})"] += 1
                    print(rot.format("⇄") + f" ▶ substitui med:{alvo} ({mot})")
                else:
                    cont["NOVAS"] += 1
                    print(rot.format("✓") + f" ▶ med:{alvo}{'' if it.gps else '  (sem GPS)'}")
                continue

            ext = I.ext_original(caminho)
            if ext not in I.EXT_ORIGINAL_OK or (ext in ("heic", "heif") and not I.TEM_HEIC):
                erros.append((f, f"formato .{ext}"))
                anota("error", reason=f"formato .{ext}")
                print(rot.format("✗") + f" formato .{ext} não suportado")
                continue
            try:
                img, icc = I._abre(caminho)
                h = I.phash(img, icc)
            except Exception as e:              # noqa: BLE001
                erros.append((f, f"decode: {e}"))
                anota("error", reason=f"decode: {e}"[:120])
                print(rot.format("✗") + f" decode: {str(e)[:70]}")
                continue
            meta = I.le_exif([caminho]).get(str(caminho), {})
            lat, lon = meta.get("GPSLatitude"), meta.get("GPSLongitude")
            if not I.gps_valido(lat, lon):          # sem GPS no arquivo: vale o do Fotos, se houver
                lat, lon = f.latitude, f.longitude
            gps = (float(lat), float(lon)) if I.gps_valido(lat, lon) else None
            data = I.data_xsd(meta) or f.date.replace(microsecond=0).isoformat()
            _, mime = I.formato_original(caminho)
            comum = dict(data=data, gps=gps, bearing=meta.get("GPSImgDirection"),
                         focal=meta.get("FocalLengthIn35mmFormat"), mime=mime,
                         tour_slug=tour_slug, autora=c["autora"], provedor=provedor)

            antigo = I.ja_existe(h, fotos_cat)
            herda = None
            if antigo:
                herda = None if antigo in substituidas else herdado_do_alvo(antigo)
                mot = I.motivo_substituir(herda, gps is not None, True)
                if not mot:
                    cont["já estava no amora (duplicata)"] += 1
                    anota("duplicate", media=antigo, hash=h, dist=I.hamming(h, antigo),
                          src_gps=gps is not None)
                    print(rot.format("=") + f" já está: med:{antigo}")
                    continue
                alvo = antigo
            else:
                if src not in livro.liberados:
                    lp = L.lapide_proxima(h, "image", lapides)
                    if lp:
                        cont["RETIDAS (parecem mídia apagada)"] += 1
                        anota("held", reason="lapide", media=lp[0], dist=lp[1], hash=h)
                        print(rot.format("!") + f" retida ~ lápide {lp[0]} ({lp[1]} bits)")
                        continue
                alvo, mot = h, None
            try:
                variantes = I.monta_variantes(caminho, img, icc)
            except Exception as e:              # noqa: BLE001
                erros.append((f, f"variantes: {e}"))
                anota("error", reason=f"variantes: {e}"[:120])
                print(rot.format("✗") + f" variantes: {str(e)[:70]}")
                continue
            ok, msg = posta(servidor, monta_ttl_foto(alvo, herda=herda if mot else None, **comum),
                            variantes)
            if not ok:
                erros.append((f, msg))
                anota("error", reason=str(msg)[:120])
                print(rot.format("✗") + f" {msg[:80]}")
                continue
            anota("ingested", media=alvo, hash=h, src_gps=gps is not None, replaced=mot,
                  dist=I.hamming(h, alvo) if mot else None, editada=c["editada"] or None)
            fotos_cat.add(alvo)
            if mot:
                substituidas.add(alvo)
                cont[f"SUBSTITUÍRAM a cópia do amora ({mot})"] += 1
                print(rot.format("⇄") + f" substitui med:{alvo} ({mot})")
            else:
                cont["NOVAS"] += 1
                print(rot.format("✓") + f" med:{alvo}{'' if gps else '  (sem GPS)'}")
        except RelerFalhou as e:
            erros.append((f, f"relendo a mídia antes de substituir: {e}"))
            anota("error", reason=f"reler alvo: {e}"[:120])
            print(rot.format("✗") + f" não consegui reler a mídia a substituir: {str(e)[:50]}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "─" * 72)
    for k, v in cont.most_common():
        print(f"  {v:5}  {k}")
    if erros:
        print(f"  {len(erros):5}  ERROS")
        for f, msg in erros[:10]:
            print(f"         {f.original_filename[:36]:38} {msg[:80]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("enviar")
    s.add_argument("--biblioteca", default=os.environ.get("PHIDRO_PHOTOS_LIB", BIBLIOTECA_PADRAO))
    s.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", A.SERVIDOR_PADRAO))
    s.add_argument("--passeio", help="só o que foi aprovado deste passeio (edição ou slug)")
    s.add_argument("--limite", type=int, help="no máximo N fotos")
    s.add_argument("--uuid", action="append", help="só esta(s) foto(s) da fila (repetível)")
    s.add_argument("--sem-videos", action="store_true", help="só as fotos")
    s.add_argument("--apply", action="store_true", help="baixa e envia pra valer (default: dry-run)")
    s.add_argument("--iniciar-livro", action="store_true",
                   help="com --apply: cria o livro-razão se ele ainda não existe nesta máquina")
    for nome in ("candidatas", "revisar"):
        s = sub.add_parser(nome)
        s.add_argument("--biblioteca", default=os.environ.get("PHIDRO_PHOTOS_LIB", BIBLIOTECA_PADRAO))
        s.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", A.SERVIDOR_PADRAO))
        s.add_argument("--passeio", help="edição (PH/56) ou slug do passeio")
        if nome == "candidatas":
            s.add_argument("--json", type=Path)
        else:
            s.add_argument("--sem-passeio", action="store_true",
                           help="as de álbum aprovado que não caem na janela de nenhum passeio")
            s.add_argument("--porta", type=int, default=8791)
    a = ap.parse_args()
    {"candidatas": cmd_candidatas, "revisar": cmd_revisar, "enviar": cmd_enviar}[a.cmd](a)


if __name__ == "__main__":
    main()
