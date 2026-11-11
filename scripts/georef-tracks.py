#!/usr/bin/env python3
"""Posicionar pela HORA: mídia com hora de verdade e sem coordenada, sobre a
gravação GPS do passeio.

Uma câmera sem GPS (Fuji, Nikon, Sony…) grava QUANDO a foto foi tirada, mas
não ONDE. Se existe uma gravação GPS do passeio com carimbo de tempo, o "onde"
sai dela: a posição da gravação no instante da foto. A coordenada entra
marcada — `ph:coordinateSource ph:interpolatedFromTrack` no nó `_geo` — e o
mapa diz "aproximada — calculada pela hora, sobre o rastro do passeio".

    georef-tracks.py                      # o que seria posicionado (dry-run)
    georef-tracks.py --passeio PH/56      # só um passeio
    georef-tracks.py --apply              # grava (patch em /update-image, /update-video)
    georef-tracks.py --desfazer --passeio PH/56 --apply   # tira as interpoladas
    georef-tracks.py --hora               # o caminho INVERSO (dry-run): ver abaixo
    georef-tracks.py --hora --apply

O caminho inverso (`--hora`): a mídia do zap não tem hora, mas depois de
POSICIONADA À MÃO sobre a rota (georef.html) ela tem um lugar — e a gravação
diz a que horas o pedal passou por ali. Essa hora entra como
`ph:estimatedCaptureTime`, NUNCA no `dcterms:date`: é uma estimativa (o mapa e
a galeria mostram com ≈), e um xsd:dateTime no dcterms:date segue querendo
dizer "hora de verdade". Só vale quando a gravação passa por ali UMA vez: em
trecho de ida e volta, ou no ponto de encontro de um pedal circular, não dá
pra saber em qual das passagens a foto foi tirada — e aí não se estima.

O que é (e o que não é) a gravação:

  · É a gravação de UMA pessoa (os trips do RideWithGPS de quem mantém o
    acervo), não do grupo. Dentro do pedal isso basta — o grupo anda junto —,
    mas a gravação também tem o caminho de casa até o ponto de encontro. Por
    isso ela é CORTADA na janela saída…chegada do passeio (± FOLGA): fora
    dela, a posição de quem gravou não diz nada sobre onde os outros estavam.
  · Fica só nesta máquina (`ignore/tracks/`, gitignored). Nada dela é
    publicado; o que sobe é a coordenada de cada foto.

Limites, ditos com todas as letras:

  · O relógio da câmera não é o do GPS. Um relógio 5 min adiantado põe a foto
    ~1 km adiante no pedal. `--ajuste SEG` soma um desvio às horas das mídias
    (use com --passeio, depois de conferir no mapa); se o relógio estiver
    errado por HORAS, a mídia cai fora da janela e simplesmente não é
    posicionada.
  · Só preenche o que está VAZIO: mídia com coordenada (do arquivo, ou colocada
    à mão) nunca é tocada.
  · Um buraco na gravação (pausa > BURACO_S) não é atravessado: a foto tirada
    ali fica sem posição.
"""
from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
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


A = _importa("audit_captura", "audit-captura.py")
BK = _importa("backfill_activities", "backfill-activities.py")   # trips do RideWithGPS (com cache)

import rdflib  # noqa: E402

TRACKS = REPO / "ignore" / "tracks"
PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#")
SCHEMA = rdflib.Namespace("https://schema.org/")
DCT = rdflib.Namespace("http://purl.org/dc/terms/")
MED_NS = "https://id.pedalhidrografi.co/midia/"
XSD_DATETIME = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#dateTime")
INTERPOLADA = PH.interpolatedFromTrack
TZ_SP = timezone(timedelta(hours=-3))

FOLGA_S = 10 * 60          # antes da saída / depois da chegada
COBERTURA_MIN = 0.6        # a gravação tem que cobrir ≥ isto da janela do passeio
BURACO_S = 180             # pausa na gravação maior que isto não é atravessada
RAIO_M = 60                # --hora: a gravação "passa pelo ponto" a até isto dele
PASSAGEM_S = 300           # --hora: mais que isto longe do ponto = OUTRA passagem
ESTIMADA = PH.estimatedCaptureTime
MANUAL = PH.placedManually
RALO_S, RALO_M = 5, 10     # um ponto a cada 5 s OU 10 m (o que vier antes)

PREFIXOS = ("@prefix ph: <https://id.pedalhidrografi.co/terms#> .\n"
            "@prefix med: <https://id.pedalhidrografi.co/midia/> .\n"
            "@prefix schema: <https://schema.org/> .\n"
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")


def _dist_m(a_lat, a_lng, b_lat, b_lng) -> float:
    kx = 111_320 * math.cos(math.radians(a_lat))
    return math.hypot((b_lng - a_lng) * kx, (b_lat - a_lat) * 110_540)


# ═════════════════════════════════════════════════════════════════════════
# 1. O rastro de cada passeio
# ═════════════════════════════════════════════════════════════════════════

def janela(g, p) -> tuple[int, int] | None:
    """(saída, chegada) em epoch — só quando o passeio tem as duas horas."""
    t = rdflib.URIRef(p.iri)
    dep, arr = g.value(t, PH.departedAt), g.value(t, PH.arrivedAt)
    if dep is None or arr is None:
        return None
    a, b = dep.toPython(), arr.toPython()
    if a.tzinfo is None:
        a = a.replace(tzinfo=TZ_SP)
    if b.tzinfo is None:
        b = b.replace(tzinfo=TZ_SP)
    return (int(a.timestamp()), int(b.timestamp())) if b > a else None


def _inicio(trip: dict) -> int | None:
    """Início do trip em epoch. `departed_at` vem como ISO na listagem e, em
    alguns detalhes em cache, já como número."""
    v = trip.get("departed_at")
    if isinstance(v, (int, float)):
        return int(v)
    d = BK._iso(v) if isinstance(v, str) else None
    return int(d.timestamp()) if d else None


def indice_de_trips(usuario: str, desde: datetime, sem_rede: bool) -> dict[int, int]:
    """{trip id: início (epoch)} — do cache e, se der, da listagem da conta."""
    idx: dict[int, int] = {}
    if BK.CACHE_PADRAO.is_dir():
        for f in BK.CACHE_PADRAO.glob("*.json"):
            try:
                t = json.loads(f.read_text(encoding="utf-8"))
                ini = _inicio(t)
                if ini:
                    idx[int(t["id"])] = ini
            except (ValueError, KeyError, TypeError):
                continue
    if not sem_rede:
        try:
            # A listagem hoje devolve a conta INTEIRA numa lista só (ignora
            # limit/offset); a forma antiga era {results: [...]}. Aceita as duas.
            d = BK._get_json(f"https://ridewithgps.com/users/{usuario}/trips.json?limit=5000&offset=0")
            lote = d if isinstance(d, list) else (d.get("results") or [])
            corte = desde.timestamp() - 86400
            for t in lote:
                ini = _inicio(t)
                if ini and t.get("id") and ini >= corte:
                    idx[int(t["id"])] = ini
        except Exception as e:                  # noqa: BLE001
            print(f"  ⚠ não listei os trips do RideWithGPS ({e}); sigo só com o cache", file=sys.stderr)
    return idx


def rastro_do_passeio(p, jan: tuple[int, int], idx: dict[int, int], sem_rede: bool) -> dict | None:
    """O rastro CORTADO na janela do passeio: {'trip', 'cobertura', 'pontos': [[t, lat, lng]…]}.
    Cacheado em ignore/tracks/<slug>.json (chave = a janela: mudou a hora do
    passeio, refaz)."""
    arq = TRACKS / f"{p.slug}.json"
    if arq.exists():
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
            if d.get("janela") == list(jan):
                return d if d.get("pontos") else None
        except ValueError:
            pass
    sai, che = jan
    cands = [i for i, t0 in idx.items() if sai - 8 * 3600 <= t0 <= che]
    melhor = None
    for tid in cands:
        f = BK.CACHE_PADRAO / f"{tid}.json"
        if sem_rede and not f.exists():
            continue
        try:
            pts = BK.pontos(BK.detalhe_trip(tid, BK.CACHE_PADRAO))
        except Exception:                       # noqa: BLE001
            continue
        if len(pts) < 2:
            continue
        cob = max(0, min(che, pts[-1].t) - max(sai, pts[0].t)) / (che - sai)
        if melhor is None or cob > melhor[0]:
            melhor = (cob, tid, pts)
    out = {"janela": list(jan), "trip": None, "cobertura": 0.0, "pontos": []}
    if melhor and melhor[0] >= COBERTURA_MIN:
        cob, tid, pts = melhor
        ralo, ult = [], None
        for q in pts:
            if not (sai - FOLGA_S <= q.t <= che + FOLGA_S):
                continue
            if ult is None or q.t - ult.t >= RALO_S or _dist_m(ult.lat, ult.lng, q.lat, q.lng) >= RALO_M:
                ralo.append([q.t, round(q.lat, 6), round(q.lng, 6)])
                ult = q
        out = {"janela": list(jan), "trip": tid, "cobertura": round(cob, 3), "pontos": ralo}
    TRACKS.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(out), encoding="utf-8")
    return out if out["pontos"] else None


def posicao_em(pontos: list, ts: list[int], t: float) -> tuple[float, float] | str:
    """(lat, lng) da gravação no instante `t`, ou o motivo de não haver."""
    if t < ts[0] or t > ts[-1]:
        return "fora da gravação"
    i = bisect.bisect_right(ts, t)
    if i >= len(ts):
        return pontos[-1][1], pontos[-1][2]
    a, b = pontos[i - 1], pontos[i]
    if b[0] - a[0] > BURACO_S:
        return "buraco na gravação"
    k = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
    return a[1] + k * (b[1] - a[1]), a[2] + k * (b[2] - a[2])


# ═════════════════════════════════════════════════════════════════════════
# 2. As mídias
# ═════════════════════════════════════════════════════════════════════════

def hora_no_ponto(pontos: list, lat: float, lng: float) -> int | str:
    """A que horas a gravação passou pelo ponto — ou por que não dá pra dizer."""
    perto = [(q[0], _dist_m(lat, lng, q[1], q[2])) for q in pontos]
    perto = [(t, d) for t, d in perto if d <= RAIO_M]
    if not perto:
        return "longe da gravação"
    passagens, atual = [], [perto[0]]
    for t, d in perto[1:]:
        if t - atual[-1][0] > PASSAGEM_S:
            passagens.append(atual)
            atual = []
        atual.append((t, d))
    passagens.append(atual)
    if len(passagens) > 1:
        return "ambíguo (a gravação passa mais de uma vez por ali)"
    return min(passagens[0], key=lambda x: x[1])[0]


def midias_para_hora(g, p):
    """Mídias do passeio pro caminho inverso: [(hash, kind, tem_hora_real,
    (lat, lng) se colocada À MÃO senão None, hora estimada já gravada | None)]."""
    out = []
    for m in g.subjects(PH.capturedDuring, rdflib.URIRef(p.iri)):
        if not str(m).startswith(MED_NS):
            continue
        if (m, rdflib.RDF.type, PH.StillImage) in g:
            kind = "image"
        elif (m, rdflib.RDF.type, PH.MotionImage) in g:
            kind = "video"
        else:
            continue
        d = g.value(m, DCT.date)
        real = d is not None and d.datatype == XSD_DATETIME
        geo = g.value(m, SCHEMA.locationCreated)
        pos = None
        if geo is not None and g.value(geo, PH.coordinateSource) == MANUAL:
            la, lo = g.value(geo, SCHEMA.latitude), g.value(geo, SCHEMA.longitude)
            if la is not None and lo is not None:
                pos = (float(la), float(lo))
        est = g.value(m, ESTIMADA)
        ev = est.toPython() if est is not None else None
        out.append((str(m)[len(MED_NS):], kind, real, pos, geo is not None,
                    ev.timestamp() if isinstance(ev, datetime) else None))
    return out


def ttl_hora(h: str, kind: str, tem_geo: bool, t: int) -> str:
    tipo = ("ph:StillImage" if kind == "image" else "ph:MotionImage") + (", ph:GeoreferencedImage" if tem_geo else "")
    iso = datetime.fromtimestamp(t, TZ_SP).replace(microsecond=0).isoformat()
    return (f"{PREFIXOS}\nmed:{h}\n    a {tipo} ;\n"
            f'    ph:estimatedCaptureTime "{iso}"^^xsd:dateTime .\n')


def ttl_tipo(h: str, kind: str, tem_geo: bool) -> str:
    tipo = ("ph:StillImage" if kind == "image" else "ph:MotionImage") + (", ph:GeoreferencedImage" if tem_geo else "")
    return f"{PREFIXOS}\nmed:{h}\n    a {tipo} .\n"


def modo_hora(a, servidor: str, passeios, g) -> None:
    """Hora ESTIMADA pra mídia sem hora que foi posicionada à mão."""
    trabalho = []
    for p in passeios:
        ms = midias_para_hora(g, p)
        # estimar: sem hora real + colocada à mão · limpar: tem estimativa que não vale mais
        if any((not real and pos) or (est is not None and (real or not pos)) for _, _, real, pos, _, est in ms):
            trabalho.append((p, ms))
    if not trabalho:
        print("nenhuma mídia sem hora posicionada à mão (nem estimativa velha pra limpar).")
        return
    idx = indice_de_trips(a.usuario, min(p.data for p, _ in trabalho), a.sem_rede)
    print("═" * 72)
    print("  HORA ESTIMADA — mídia sem hora, posicionada à mão, sobre a gravação")
    print("═" * 72)
    tot, planos = Counter(), []           # planos: (hash, kind, tem_geo, epoch | None=remover)
    for p, ms in sorted(trabalho, key=lambda x: x[0].data, reverse=True):
        jan = janela(g, p)
        r = rastro_do_passeio(p, jan, idx, a.sem_rede) if jan else None
        c = Counter()
        for h, kind, real, pos, tem_geo, est in ms:
            if est is not None and (real or not pos):
                c["estimativa velha (a limpar)"] += 1
                planos.append((h, kind, tem_geo, None))
                continue
            if real or not pos:
                continue
            if r is None:
                c["passeio sem gravação" if jan else "passeio sem saída/chegada"] += 1
                continue
            t = hora_no_ponto(r["pontos"], pos[0], pos[1])
            if isinstance(t, str):
                c[t] += 1
                if est is not None:       # tinha estimativa, o ponto mudou e ficou sem resposta
                    planos.append((h, kind, tem_geo, None))
            elif est is not None and abs(est - t) < 60:
                c["já estimada (igual)"] += 1
            else:
                c["estimáveis"] += 1
                planos.append((h, kind, tem_geo, t))
        tot.update(c)
        print(f"  {p.data.date()} {p.edicao:13} " + ", ".join(f"{v} {k}" for k, v in c.most_common()))
    print("─" * 72)
    for k, v in tot.most_common():
        print(f"  {v:5}  {k}")
    if not planos:
        return
    if not a.apply:
        print("\n(dry-run: nada foi gravado. Use --apply.)")
        return
    ok, falhas = 0, []
    for h, kind, tem_geo, t in planos:
        if t is None:
            bom, msg = _post(servidor, kind, h, ttl_tipo(h, kind, tem_geo), "ph:estimatedCaptureTime")
        else:
            bom, msg = _post(servidor, kind, h, ttl_hora(h, kind, tem_geo, t), "")
        ok += bom
        if not bom:
            falhas.append((h, msg))
    print(f"\n{ok}/{len(planos)} gravadas (ph:estimatedCaptureTime).")
    for h, msg in falhas[:10]:
        print(f"  ✗ {h} {msg}")


def midias_do_passeio(g, p):
    """[(hash, kind, epoch | None, tem_geo, fonte_geo)] das mídias do passeio."""
    out = []
    for m in g.subjects(PH.capturedDuring, rdflib.URIRef(p.iri)):
        if not str(m).startswith(MED_NS):
            continue
        if (m, rdflib.RDF.type, PH.StillImage) in g:
            kind = "image"
        elif (m, rdflib.RDF.type, PH.MotionImage) in g:
            kind = "video"
        else:
            continue
        d = g.value(m, DCT.date)
        t = None
        if d is not None and d.datatype == XSD_DATETIME:
            v = d.toPython()
            if isinstance(v, datetime):
                t = (v if v.tzinfo else v.replace(tzinfo=TZ_SP)).timestamp()
        geo = g.value(m, SCHEMA.locationCreated)
        fonte = g.value(geo, PH.coordinateSource) if geo is not None else None
        out.append((str(m)[len(MED_NS):], kind, t, geo is not None, fonte))
    return out


def _post(servidor: str, kind: str, h: str, ttl: str, remove: str) -> tuple[bool, str]:
    bnd = "----phidrogeoref" + os.urandom(8).hex()
    corpo = (f'--{bnd}\r\nContent-Disposition: form-data; name="ttl"\r\n\r\n{ttl}\r\n'
             f'--{bnd}\r\nContent-Disposition: form-data; name="remove"\r\n\r\n{remove}\r\n'
             f"--{bnd}--\r\n").encode("utf-8")
    req = urllib.request.Request(
        f"{servidor}/update-{'image' if kind == 'image' else 'video'}/{h}", data=corpo, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={bnd}", "User-Agent": A.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120, context=A._contexto_ssl()) as r:
            return r.status == 200, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except Exception as e:                      # noqa: BLE001
        return False, str(e)


def ttl_posicao(h: str, kind: str, lat: float, lng: float) -> str:
    tipo = "ph:StillImage" if kind == "image" else "ph:MotionImage"
    return (f"{PREFIXOS}\nmed:{h}\n    a {tipo}, ph:GeoreferencedImage ;\n"
            f"    schema:locationCreated med:{h}_geo .\n\n"
            f"med:{h}_geo a schema:GeoCoordinates ;\n"
            f'    schema:latitude "{lat:.6f}"^^xsd:decimal ;\n'
            f'    schema:longitude "{lng:.6f}"^^xsd:decimal ;\n'
            f"    ph:coordinateSource ph:interpolatedFromTrack .\n")


def ttl_sem_posicao(h: str, kind: str) -> str:
    return f"{PREFIXOS}\nmed:{h}\n    a {'ph:StillImage' if kind == 'image' else 'ph:MotionImage'} .\n"


# ═════════════════════════════════════════════════════════════════════════
# 3. main
# ═════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", A.SERVIDOR_PADRAO))
    ap.add_argument("--passeio", help="só este passeio (edição, ex.: PH/56, ou slug)")
    ap.add_argument("--apply", action="store_true", help="grava pra valer (default: dry-run)")
    ap.add_argument("--desfazer", action="store_true",
                    help="tira as coordenadas INTERPOLADAS (só elas) — exige --passeio")
    ap.add_argument("--hora", action="store_true",
                    help="o caminho inverso: hora ESTIMADA (ph:estimatedCaptureTime) pra mídia sem "
                         "hora que foi posicionada à mão")
    ap.add_argument("--ajuste", type=float, default=0.0, metavar="SEG",
                    help="soma SEG segundos à hora das mídias (relógio da câmera errado) — exige --passeio")
    ap.add_argument("--usuario", default=BK.USUARIO_PADRAO, help="conta do RideWithGPS dona das gravações")
    ap.add_argument("--sem-rede", action="store_true", help="só os trips já em cache (ignore/rwgps-trips/)")
    a = ap.parse_args()
    if (a.desfazer or a.ajuste) and not a.passeio:
        sys.exit("--desfazer e --ajuste exigem --passeio (são decisões por passeio).")
    servidor = a.servidor.rstrip("/")

    passeios, g = A.carregar_catalogos(servidor)
    if a.passeio:
        k = a.passeio.strip().lower()
        passeios = [p for p in passeios if p.edicao.lower() == k or p.slug.lower() == k]
        if not passeios:
            sys.exit(f"passeio não encontrado: {a.passeio}")

    if a.hora:
        modo_hora(a, servidor, passeios, g)
        return

    if a.desfazer:
        p = passeios[0]
        alvos = [(h, kind) for h, kind, _, tem, fonte in midias_do_passeio(g, p) if tem and fonte == INTERPOLADA]
        print(f"{p.edicao} — {len(alvos)} mídias com coordenada interpolada")
        ok = 0
        for h, kind in alvos:
            if a.apply:
                bom, msg = _post(servidor, kind, h, ttl_sem_posicao(h, kind), "schema:locationCreated")
                ok += bom
                if not bom:
                    print(f"  ✗ {h} {msg}")
        print(f"{ok} desfeitas." if a.apply else "(dry-run: nada foi alterado. Use --apply.)")
        return

    # só passeios com mídia que TEM hora e NÃO tem coordenada
    trabalho = []
    for p in passeios:
        ms = midias_do_passeio(g, p)
        cand = [(h, kind, t) for h, kind, t, tem, _ in ms if t is not None and not tem]
        if cand:
            trabalho.append((p, cand))
    if not trabalho:
        print("nenhuma mídia com hora e sem coordenada.")
        return
    idx = indice_de_trips(a.usuario, min(p.data for p, _ in trabalho), a.sem_rede)

    print("═" * 72)
    print("  POSICIONAR PELA HORA — mídia com hora de verdade e sem coordenada")
    print("═" * 72)
    tot = Counter()
    planos = []
    for p, cand in sorted(trabalho, key=lambda x: x[0].data, reverse=True):
        jan = janela(g, p)
        if jan is None:
            tot["passeio sem saída/chegada"] += len(cand)
            print(f"  {p.data.date()} {p.edicao:13} {len(cand):4} mídias — passeio sem hora de saída/chegada")
            continue
        r = rastro_do_passeio(p, jan, idx, a.sem_rede)
        if r is None:
            tot["passeio sem gravação"] += len(cand)
            print(f"  {p.data.date()} {p.edicao:13} {len(cand):4} mídias — sem gravação que cubra o passeio")
            continue
        pts = r["pontos"]
        ts = [q[0] for q in pts]
        c = Counter()
        for h, kind, t in cand:
            pos = posicao_em(pts, ts, t + a.ajuste)
            if isinstance(pos, str):
                c[pos] += 1
            else:
                c["posicionáveis"] += 1
                planos.append((p, h, kind, pos))
        tot.update(c)
        print(f"  {p.data.date()} {p.edicao:13} {len(cand):4} mídias — "
              + ", ".join(f"{v} {k}" for k, v in c.most_common())
              + f"   [trip {r['trip']}, cobre {r['cobertura']:.0%}]")

    print("─" * 72)
    for k, v in tot.most_common():
        print(f"  {v:5}  {k}")
    if not planos:
        return
    if not a.apply:
        print("\n(dry-run: nada foi gravado. Use --apply.)")
        return
    ok, falhas = 0, []
    for p, h, kind, (lat, lng) in planos:
        bom, msg = _post(servidor, kind, h, ttl_posicao(h, kind, lat, lng), "")
        ok += bom
        if not bom:
            falhas.append((h, msg))
    print(f"\n{ok}/{len(planos)} posicionadas (ph:interpolatedFromTrack).")
    for h, msg in falhas[:10]:
        print(f"  ✗ {h} {msg}")


if __name__ == "__main__":
    main()
