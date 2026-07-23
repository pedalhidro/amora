#!/usr/bin/env python3
"""Backfill do pós-passeio a partir da GRAVAÇÃO GPS (RideWithGPS trips).

O catálogo tem a rota PLANEJADA de quase todo passeio (`ph:linkRoute`), mas
não tem a GRAVAÇÃO do que foi de fato pedalado (`ph:linkActivity`) — está em
0 de 109. Sem ela, os campos do pós-passeio não têm de onde ser reconstruídos:
saída, chegada, tempo em movimento e energia MEDIDA só entram na mão.

Este script casa cada passeio com a atividade (trip) correspondente na conta
do RideWithGPS e grava, via backend:

    ph:linkActivity     ← a URL do trip (SEMPRE que casar — é o ponto)
    ph:departedAt       ← só quando ausente
    ph:arrivedAt        ← só quando ausente
    ph:movingDuration   ← só quando ausente
    ph:measuredEnergy   ← só quando ausente

Gravar o `ph:linkActivity` é o objetivo real: ele torna o casamento DURÁVEL.
A heurística abaixo é cara e imperfeita; depois que a URL está no catálogo,
ninguém precisa rodá-la de novo — qualquer script futuro lê o trip direto.

COMO CASA (data sozinha colide — dois pedais no mesmo dia é rotina):
  data (±12 h do horário marcado) ∧ início E fim da rota dentro do bbox do
  trip ∧ distância do trip ≥ distância da rota. Empate → desempata pela
  proximidade real do traço ao início/fim da rota.

A JANELA (o pulo do gato): a gravação inclui o trajeto de casa até o ponto de
encontro e a volta pra casa. O passeio é um SUBCONJUNTO do trip. Integrar o
trip inteiro superestima a energia em ~70%. Então:

    saída   = o movimento retomando depois da parada de encontro,
              perto do início da rota
    chegada = a parada geograficamente mais próxima do fim da rota
    energia e movimento = integrados SÓ nessa janela

O campo `work` do trip É trabalho mecânico em kJ (= ∫potência·dt), mas vale
pro TRIP INTEIRO — por isso a energia é reintegrada ponto a ponto (`p` = W)
dentro da janela. Quando o passeio JÁ tem saída/chegada humanas, a janela é
a HUMANA (isso reproduziu os valores de energia já existentes em 23 de 24
casos, dentro de 10%).

PRECISÃO HONESTA — medida, não prometida. `--validar` recalcula a janela do
zero nos passeios que JÁ têm campo humano e compara (n=61 saídas/chegadas,
60 energias):

    saída    mediana 2 min   82% dentro de 10 min, 90% dentro de 30
    chegada  mediana 5 min   62% dentro de 10 min, 80% dentro de 30
    energia  mediana 3%      82% dentro de 10%,    90% dentro de 20%

A chegada é o campo RUIDOSO: é sugestão, não verdade. Um em cada cinco erra
por mais de meia hora. O relatório marca com `!` tudo que merece olho humano,
e uma chegada que o rastro não sustenta (a parada mais próxima do fim da rota
está a mais de 500 m dele) NÃO é gravada — nem ela, nem o movimento e a
energia, que são integrais até ela.

Uso:
    backfill-activities.py                    # dry-run (default), tudo
    backfill-activities.py --slug 05cr6685    # um passeio só
    backfill-activities.py --apply            # grava de verdade
    backfill-activities.py --apply --force    # sobrescreve valor humano (!)
    backfill-activities.py --json relatorio.json

O dry-run é o DEFAULT: escrever exige `--apply` explícito. A escrita é
sempre `POST /upload-tour` com `mode=patch` — o backend é o único escritor
legítimo dos catálogos.

REDE: a listagem dos trips baixa ~2,5 mil registros (paginado, alguns MB) e
cada trip detalhado baixa seus track_points (~1–5 MB cada, ~13 mil pontos).
Rodar em cima dos 109 passeios puxa algumas centenas de MB na primeira vez —
por isso os detalhes ficam em cache (`ignore/rwgps-trips/`, `--sem-cache`
para ignorar). Nada é escrito no RideWithGPS: só GET.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    import rdflib
except ImportError:
    sys.exit("falta rdflib: pip install rdflib")
try:
    import certifi
except ImportError:
    sys.exit("falta certifi: pip install certifi")

# Reusa a fonte única de verdade do RideWithGPS (credenciais + assinatura da
# URL + haversine). Nada de reimplementar o que backend/rwgps.py já faz.
from backend import rwgps  # noqa: E402

DATA = REPO / "web" / "data"

PH      = rdflib.Namespace("https://id.pedalhidrografi.co/terms#")
DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")

TZ_SP = timezone(timedelta(hours=-3))

SERVIDOR_PADRAO = "https://amora.pedalhidrografi.co"
USUARIO_PADRAO  = "2112645"          # conta do Danilo no RideWithGPS
CACHE_PADRAO    = REPO / "ignore" / "rwgps-trips"

# ── Parâmetros da heurística (todos medidos, nenhum sagrado) ─────────────
# A data do passeio NÃO é um instante confiável: 40% dos `dcterms:date` são
# meia-noite (só o dia foi anotado). Por isso a janela de data é o DIA LOCAL
# do passeio — não ±N h em torno do horário marcado, que jogaria o pedal das
# 20 h fora quando a data é 00:00.
MADRUGADA_H     = 4       # trip que partiu até as 4 h do dia seguinte ainda conta
MARGEM_BBOX     = 0.003   # ~330 m de folga no bbox do trip (GPS + downsample)
FRACAO_DIST     = 0.90    # trip ≥ 90% da distância da rota (a rota vem
                          # downsampleada em routes.json → subestima um pouco)
RAIO_INICIO     = 250.0   # "perto do início da rota", em metros
VEL_PARADO      = 0.5     # m/s — abaixo disso é parada (1,8 km/h)
PARADA_MIN      = 90      # s — parada curta demais não é encontro nem chegada
GAP_PARADA      = 60      # s — buraco no rastro (auto-pause) também é parada
FRACAO_PERCURSO = 0.70    # a chegada só é procurada depois que o rastro já
                          # cobriu 70% da rota — senão, em rota circular, a
                          # "parada mais próxima do fim" é a do PRÓPRIO encontro
BOM_CASAMENTO   = 150.0   # m — traço passou a ≤ isso do início: casou bem
MAX_CASAMENTO   = 400.0   # m — acima disso, o casamento é suspeito
BOA_CHEGADA     = 200.0   # m — parada de chegada a ≤ isso do fim da rota
MAX_CHEGADA     = 500.0   # m — acima disso a chegada é chute: NÃO se grava
                          # chegada/movimento/energia (todos dependem dela)
JANELA_MIN      = 900     # s — passeio do coletivo NUNCA durou 15 min. Janela
                          # mais curta que isso não é um passeio: é um trip que
                          # só passou raspando pelo início da rota. Nada derivado
                          # se grava (só o linkActivity, pra revisão humana)

_CTX = ssl.create_default_context(cafile=certifi.where())


# ═════════════════════════════════════════════════════════════════════════
# 1. HTTP (RideWithGPS)
# ═════════════════════════════════════════════════════════════════════════

def _get_json(url: str) -> dict:
    """GET assinado + JSON. O ssl context é explícito porque o Python do
    sistema (macOS) não tem bundle de CA e falha o handshake sem certifi."""
    req = urllib.request.Request(rwgps.decorate_rwgps(url),
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120, context=_CTX) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def listar_trips(usuario: str, desde: datetime, quieto: bool = False) -> list[dict]:
    """Todos os trips do usuário até `desde` (a API devolve do mais novo pro
    mais velho; para de paginar quando passa da data do passeio mais antigo).

    Traz só a listagem — bbox, data, distância — que é o bastante pra filtrar.
    O detalhe (track_points, caro) só é baixado pros candidatos que sobram.
    """
    trips: list[dict] = []
    offset, pagina = 0, 200
    while True:
        d = _get_json(f"https://ridewithgps.com/users/{usuario}/trips.json"
                      f"?limit={pagina}&offset={offset}")
        lote = d.get("results") or []
        if not lote:
            break
        trips += lote
        mais_velho = min((t.get("departed_at") or "9999") for t in lote)
        if not quieto:
            print(f"  … {len(trips)} trips (até {mais_velho[:10]})", file=sys.stderr)
        if mais_velho[:10] < desde.date().isoformat():
            break
        offset += pagina
        if offset >= (d.get("results_count") or 0):
            break
    return trips


def detalhe_trip(trip_id: int, cache: Path | None) -> dict:
    """O trip com track_points. Cacheia em disco: são ~13 mil pontos por
    gravação, e reprocessar 109 passeios sem cache repuxaria centenas de MB."""
    if cache:
        f = cache / f"{trip_id}.json"
        if f.exists() and f.stat().st_size > 0:
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    d = _get_json(f"https://ridewithgps.com/trips/{trip_id}.json")
    trip = d.get("trip") or d
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / f"{trip_id}.json").write_text(
            json.dumps(trip, ensure_ascii=False), encoding="utf-8")
    return trip


# ═════════════════════════════════════════════════════════════════════════
# 2. O catálogo + a geometria da rota
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class Passeio:
    iri: str
    slug: str
    titulo: str
    data: datetime
    edicao: str
    atividades: list[str] = field(default_factory=list)   # ph:linkActivity já gravados
    saida: datetime | None = None                         # ph:departedAt humano
    chegada: datetime | None = None                       # ph:arrivedAt humano
    movimento: str | None = None                          # ph:movingDuration
    energia: float | None = None                          # ph:measuredEnergy
    latlngs: list[list[float]] = field(default_factory=list)
    dist_rota: float = 0.0                                # m


def carregar_passeios(servidor: str) -> list[Passeio]:
    """O catálogo vem DO SERVIDOR em que vamos escrever, não do disco.

    O `web/data/tours.ttl` local é uma cópia que envelhece (o backend é o
    escritor); decidir "este campo está ausente" a partir dele gravaria por
    cima de valor que já existe lá, e reescreveria o linkActivity a cada
    rodada. Lê-se a verdade de quem manda. Sem rede, cai pro disco.
    """
    g = rdflib.Graph()
    ttl = _baixar(f"{servidor}/data/tours.ttl")
    if ttl:
        g.parse(data=ttl, format="turtle")
    else:
        print(f"  ⚠ {servidor} fora do ar — lendo o tours.ttl local (pode estar velho)",
              file=sys.stderr)
        g.parse(DATA / "tours.ttl", format="turtle")

    rotas = {}
    bruto = _baixar(f"{servidor}/routes.json")
    if bruto is None:
        rj = REPO / "web" / "routes.json"
        bruto = rj.read_text(encoding="utf-8") if rj.exists() else "{}"
    for e in (json.loads(bruto).get("routes") or []):
        if e.get("tourIri") and e.get("latlngs"):
            rotas[e["tourIri"]] = e["latlngs"]

    passeios: list[Passeio] = []
    for t in g.subjects(rdflib.RDF.type, PH.Tour):
        data = g.value(t, DCTERMS.date)
        if data is None:
            continue
        serie = seq = None
        ed = g.value(t, PH.inSeriesEdition)
        if ed is not None:
            s = g.value(ed, PH.inEventSeries)
            serie = str(s).rsplit("/", 1)[-1] if s else None
            q = g.value(ed, PH.sequenceInSeries)
            seq = int(q) if q is not None else None

        dt = data.toPython()
        if isinstance(dt, datetime) and dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_SP)

        e = g.value(t, PH.measuredEnergy)
        p = Passeio(
            iri=str(t),
            slug=str(t).rsplit("/", 1)[-1],
            titulo=str(g.value(t, DCTERMS.title) or "—"),
            data=dt,
            edicao=f"{serie}/{seq}" if serie and seq is not None else "—",
            atividades=sorted(str(a) for a in g.objects(t, PH.linkActivity)),
            saida=_dt(g.value(t, PH.departedAt)),
            chegada=_dt(g.value(t, PH.arrivedAt)),
            movimento=str(g.value(t, PH.movingDuration)) if g.value(t, PH.movingDuration) else None,
            energia=float(e) if e is not None else None,
            latlngs=rotas.get(str(t), []),
        )
        p.dist_rota = _comprimento(p.latlngs)
        passeios.append(p)

    passeios.sort(key=lambda x: x.data, reverse=True)
    return passeios


def _baixar(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=60, context=_CTX) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return None


def _dt(lit) -> datetime | None:
    if lit is None:
        return None
    v = lit.toPython()
    if not isinstance(v, datetime):
        return None
    return v.replace(tzinfo=TZ_SP) if v.tzinfo is None else v


def _comprimento(latlngs) -> float:
    return sum(rwgps.haversine_meters(a[0], a[1], b[0], b[1])
               for a, b in zip(latlngs, latlngs[1:]))


# ═════════════════════════════════════════════════════════════════════════
# 3. Casamento passeio ↔ trip
# ═════════════════════════════════════════════════════════════════════════

def candidatos(p: Passeio, trips: list[dict]) -> list[dict]:
    """Filtro barato, só com a listagem: dia + bbox + distância.

    A data sozinha colide (pedal de manhã + pedal do coletivo à noite no mesmo
    dia — acontece toda semana). A geometria é quem decide: o bbox do trip tem
    que conter o INÍCIO da rota, e o trip tem que ter pedalado pelo menos o
    tanto da rota (ele pedala MAIS — vai de casa e volta pra casa).

    O fim da rota NÃO entra aqui: gravação que morre de bateria no meio ainda
    é a gravação certa. Quem cobra a proximidade do fim é o estágio do detalhe,
    onde ela vira confiança (e trava a escrita da chegada), não um veto mudo.
    """
    if not p.latlngs:
        return []
    dia = p.data.astimezone(TZ_SP).date()

    out = []
    for t in trips:
        dep = _iso(t.get("departed_at"))
        if dep is None:
            continue
        dep = dep.astimezone(TZ_SP)
        if not (dep.date() == dia
                or (dep.date() == dia + timedelta(days=1) and dep.hour < MADRUGADA_H)):
            continue
        if not _no_bbox(t, p.latlngs[0]):
            continue
        if (t.get("distance") or 0) < FRACAO_DIST * p.dist_rota:
            continue
        out.append(t)
    return out


def _no_bbox(t: dict, ponto) -> bool:
    """O ponto cabe no bbox do trip? Bbox AUSENTE ou degenerado (a API devolve
    sw=(90,180)/ne=(-90,-180) em alguns trips) não reprova ninguém: o filtro é
    um atalho barato, e o veto de verdade é a proximidade do rastro, medida no
    detalhe. Reprovar por bbox quebrado perdia gravações reais em silêncio."""
    la, lo = ponto
    try:
        sw_la, sw_lo, ne_la, ne_lo = (t["sw_lat"], t["sw_lng"], t["ne_lat"], t["ne_lng"])
        if sw_la > ne_la or sw_lo > ne_lo:
            return True
        return (sw_la - MARGEM_BBOX <= la <= ne_la + MARGEM_BBOX
                and sw_lo - MARGEM_BBOX <= lo <= ne_lo + MARGEM_BBOX)
    except (KeyError, TypeError):
        return True


def _iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ═════════════════════════════════════════════════════════════════════════
# 4. O trip: pontos, paradas, janela do passeio
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class Ponto:
    t: int
    lat: float
    lng: float
    vel: float      # m/s
    pot: float      # W


def pontos(trip: dict) -> list[Ponto]:
    """track_points → pontos com coordenada. Os primeiros registros de um
    Garmin costumam vir SEM x/y (o GPS ainda não fixou): a coordenada é
    arrastada do último fix conhecido, e o que vier antes do primeiro fix é
    descartado."""
    out: list[Ponto] = []
    lat = lng = None
    for q in trip.get("track_points") or []:
        ts = q.get("t")
        if ts is None:
            continue
        if isinstance(q.get("y"), (int, float)) and isinstance(q.get("x"), (int, float)):
            lat, lng = float(q["y"]), float(q["x"])
        if lat is None:
            continue
        v = q.get("s")
        w = q.get("p")
        out.append(Ponto(int(ts), lat, lng,
                         float(v) if isinstance(v, (int, float)) else 0.0,
                         float(w) if isinstance(w, (int, float)) else 0.0))
    return out


@dataclass
class Parada:
    ini: int
    fim: int
    lat: float
    lng: float

    @property
    def dur(self) -> int:
        return self.fim - self.ini


def paradas(pts: list[Ponto]) -> list[Parada]:
    """Trechos parados: velocidade abaixo do limiar por ≥ PARADA_MIN, OU um
    buraco no rastro (o Garmin com auto-pause simplesmente para de gravar —
    um gap de 20 min é a parada mais eloquente que existe)."""
    out: list[Parada] = []
    ini = None
    ancora: Ponto | None = None
    ant: Ponto | None = None
    for q in pts:
        if ant is not None and q.t - ant.t >= GAP_PARADA:
            out.append(Parada(ant.t, q.t, ant.lat, ant.lng))
            ini, ancora = None, None
        if q.vel <= VEL_PARADO:
            if ini is None:
                ini, ancora = q.t, q
        else:
            if ini is not None and ant is not None and ant.t - ini >= PARADA_MIN:
                out.append(Parada(ini, ant.t, ancora.lat, ancora.lng))
            ini, ancora = None, None
        ant = q
    if ini is not None and ant is not None and ant.t - ini >= PARADA_MIN:
        out.append(Parada(ini, ant.t, ancora.lat, ancora.lng))
    return out


def _dist(a, lat: float, lng: float) -> float:
    return rwgps.haversine_meters(a.lat, a.lng, lat, lng)


@dataclass
class Janela:
    saida: int
    chegada: int
    kj: float
    movimento: int          # s
    d_inicio: float         # m — o quanto o traço chegou perto do início da rota
    d_fim: float            # m — o quanto o traço chegou perto do FIM da rota
    d_chegada: float        # m — o quanto a parada de chegada está do fim da rota
    saida_por_parada: bool  # True = achou a parada do encontro; False = fallback
    fonte: str              # 'heuristica' | 'humana' | 'mista'

    @property
    def chegada_confiavel(self) -> bool:
        return self.d_chegada <= MAX_CHEGADA

    @property
    def plausivel(self) -> bool:
        """A janela tem cara de passeio? Uma de 3 min só pode ser um trip que
        raspou o ponto de encontro — nada dela vale como dado."""
        return self.chegada - self.saida >= JANELA_MIN


def janela(pts: list[Ponto], rota, dist_rota: float, saida_h: datetime | None,
           chegada_h: datetime | None) -> Janela | None:
    """A janela do passeio dentro do trip.

    Quando o passeio já tem saída/chegada HUMANAS, elas mandam — só integramos
    a energia dentro delas (foi assim que os valores existentes de
    ph:measuredEnergy foram reproduzidos, em 23 de 24 casos, dentro de 10%).
    """
    if not pts or not rota:
        return None
    r_ini, r_fim = rota[0], rota[-1]
    ps = paradas(pts)

    d_inicio = min(_dist(q, *r_ini) for q in pts)

    # ── saída ────────────────────────────────────────────────────────────
    por_parada = False
    if saida_h is not None:
        saida = int(saida_h.timestamp())
    else:
        vis = _visitas(pts, r_ini)
        if not vis:
            return None     # o rastro nem passa perto do início: não é este trip
        # Qual das visitas ao ponto de encontro é a que ABRE o passeio? A
        # PRIMEIRA que ainda tem a ROTA INTEIRA pela frente. Passar perto do
        # início não basta: o rastro encosta ali de novo na volta pra casa e,
        # em rota circular, no fim do próprio passeio — visitas que não têm
        # mais rota pela frente e por isso caem fora. (Medido contra os 61
        # passeios com saída anotada à mão: a primeira-com-rota acerta 81%
        # dentro de 10 min; "a última", "a de maior parada" e "a de maior
        # espera" todas pioram. A regra simples ganhou.)
        resta = _restante(pts)
        alvo = dist_rota * FRACAO_PERCURSO
        i0, i1 = next((v for v in vis if resta[v[1]] >= alvo),
                      max(vis, key=lambda v: resta[v[1]]))
        # A parada de encontro é a ÚLTIMA parada dentro dessa visita; a saída é
        # o FIM dela — o movimento retomando.
        dentro = [q for q in ps
                  if q.fim >= pts[i0].t - 600 and q.ini <= pts[i1].t + 60
                  and _dist(q, *r_ini) <= RAIO_INICIO * 2]
        if dentro:
            saida = max(dentro, key=lambda q: q.fim).fim
            por_parada = True
        else:
            # Ninguém parou (chegou e saiu na hora): a saída é o instante em
            # que o rastro deixa a bolha do início. Erra pra tarde em até
            # ~1 min (o raio dividido pela velocidade). Aceitável.
            saida = pts[i1].t

    # ── chegada ──────────────────────────────────────────────────────────
    # Onde o rastro encosta no fim da rota — procurado SÓ depois que o grupo
    # já pedalou FRACAO_PERCURSO da rota. Sem essa âncora, numa rota que volta
    # pro ponto de partida o "mais próximo do fim" seria a parada do encontro,
    # e a janela sairia com 5 minutos e 0 kJ.
    adiante = _apos_percurso(pts, saida, dist_rota * FRACAO_PERCURSO)
    if not adiante:
        adiante = [q for q in pts if q.t > saida] or pts
    perto_fim = min(adiante, key=lambda q: _dist(q, *r_fim))
    d_fim = _dist(perto_fim, *r_fim)

    if chegada_h is not None:
        chegada = int(chegada_h.timestamp())
        d_chegada = d_fim
    else:
        # A parada geograficamente mais próxima do fim da rota — mas SÓ se ela
        # for mesmo no fim da rota. O fim do trip entra como pseudo-parada:
        # quem encerra a gravação no destino não gera parada nenhuma.
        ult = pts[-1]
        cands = [q for q in ps if q.ini >= perto_fim.t - 300]
        cands.append(Parada(ult.t, ult.t, ult.lat, ult.lng))
        melhor = min(cands, key=lambda q: _dist(q, *r_fim))
        d_parada = _dist(melhor, *r_fim)
        if d_parada <= BOA_CHEGADA:
            chegada, d_chegada = melhor.ini, d_parada
        else:
            # Ninguém parou no destino (o grupo se dispersa pedalando, e quem
            # gravou seguiu direto pra casa): a chegada é o instante em que o
            # rastro passa mais perto do fim da rota. Medido contra as 61
            # chegadas anotadas à mão, essa regra tira a mediana do erro de
            # 6,7 → 4,7 min e resgata 15 passeios que a regra da parada vetava.
            chegada, d_chegada = perto_fim.t, d_fim

    if chegada <= saida:
        return None

    kj, mov = integrar(pts, saida, chegada)
    fonte = ("humana" if saida_h and chegada_h
             else "heuristica" if not saida_h and not chegada_h else "mista")
    return Janela(saida, chegada, kj, mov, d_inicio, d_fim, d_chegada, por_parada, fonte)


def _visitas(pts: list[Ponto], r_ini) -> list[tuple[int, int]]:
    """Os trechos contíguos em que o rastro está dentro do raio do início da
    rota. Um rastro típico visita o ponto de encontro mais de uma vez: chegando
    de casa, e de novo na volta (ou, em rota circular, no fim do passeio)."""
    vis: list[tuple[int, int]] = []
    cur: list[int] | None = None
    for i, q in enumerate(pts):
        if _dist(q, *r_ini) <= RAIO_INICIO:
            if cur is None:
                cur = [i, i]
            else:
                cur[1] = i
        elif cur is not None and q.t - pts[cur[1]].t > GAP_PARADA:
            vis.append((cur[0], cur[1]))
            cur = None
    if cur is not None:
        vis.append((cur[0], cur[1]))
    return vis


def _restante(pts: list[Ponto]) -> list[float]:
    """resta[i] = metros que o rastro ainda percorre a partir do ponto i."""
    n = len(pts)
    resta = [0.0] * n
    for i in range(n - 2, -1, -1):
        resta[i] = resta[i + 1] + rwgps.haversine_meters(
            pts[i].lat, pts[i].lng, pts[i + 1].lat, pts[i + 1].lng)
    return resta


def _apos_percurso(pts: list[Ponto], saida: int, alvo: float) -> list[Ponto]:
    """Os pontos depois que o rastro já andou `alvo` metros desde a saída."""
    if alvo <= 0:
        return [q for q in pts if q.t > saida]
    acum = 0.0
    ant: Ponto | None = None
    for i, q in enumerate(pts):
        if q.t < saida:
            ant = q
            continue
        if ant is not None:
            acum += rwgps.haversine_meters(ant.lat, ant.lng, q.lat, q.lng)
        ant = q
        if acum >= alvo:
            return pts[i:]
    return []


def integrar(pts: list[Ponto], t0: int, t1: int) -> tuple[float, int]:
    """∫potência·dt (kJ) e tempo em movimento (s) DENTRO da janela.

    É exatamente o que o campo `work` do trip faz — só que ele integra o trip
    INTEIRO, casa-a-casa. Aqui o intervalo é o do passeio.
    """
    j = 0.0
    mov = 0
    ant: Ponto | None = None
    for q in pts:
        if q.t < t0:
            ant = q
            continue
        if q.t > t1:
            break
        if ant is not None:
            dt = q.t - ant.t
            if 0 < dt <= 30:        # gap maior = parada/auto-pause, não integra
                j += q.pot * dt
                if q.vel > VEL_PARADO:
                    mov += dt
        ant = q
    return j / 1000.0, mov


# ═════════════════════════════════════════════════════════════════════════
# 5. O casamento, com confiança
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class Casamento:
    passeio: Passeio
    trip: dict | None = None
    jan: Janela | None = None
    confianca: str = "nenhuma"      # alta | media | baixa | nenhuma
    motivo: str = ""
    n_candidatos: int = 0

    @property
    def url(self) -> str:
        return f"https://ridewithgps.com/trips/{self.trip['id']}" if self.trip else ""

    def escreveria(self, force: bool) -> dict:
        """Os campos que este casamento gravaria. `ph:linkActivity` SEMPRE
        (é o ponto do script); os derivados só quando ausentes — valor humano
        não se sobrescreve sem --force.

        Chegada não confiável (a parada mais próxima do fim da rota está a mais
        de MAX_CHEGADA dela) trava a chegada E o que depende dela: movimento e
        energia são integrais ATÉ a chegada, e uma chegada errada envenena as
        três. Nesses casos sai só linkActivity + saída.
        """
        p, j = self.passeio, self.jan
        campos: dict = {}
        if self.trip and self.url not in p.atividades:
            campos["ph:linkActivity"] = self.url
        if not j or not j.plausivel:
            return campos       # a URL fica (é revisável); o resto seria lixo
        if p.saida is None or force:
            campos["ph:departedAt"] = _iso_sp(j.saida)
        if not j.chegada_confiavel and p.chegada is None:
            return campos
        if p.chegada is None or force:
            campos["ph:arrivedAt"] = _iso_sp(j.chegada)
        if (p.movimento is None or force) and j.movimento > 0:
            campos["ph:movingDuration"] = _iso_dur(j.movimento)
        if (p.energia is None or force) and j.kj > 0:
            campos["ph:measuredEnergy"] = round(j.kj, 1)
        return campos


def _iso_sp(ts: int) -> str:
    """Epoch → ISO no fuso de SP, arredondado pro minuto. A precisão do método
    é de MINUTOS (±10 no pior caso); cravar o segundo seria precisão falsa."""
    d = datetime.fromtimestamp(ts, TZ_SP)
    if d.second >= 30:
        d += timedelta(minutes=1)
    return d.replace(second=0, microsecond=0).isoformat()


def _iso_dur(seg: int) -> str:
    h, m = divmod(round(seg / 60), 60)
    return "PT" + (f"{h}H" if h else "") + f"{m}M"


def casar(p: Passeio, trips: list[dict], cache: Path | None,
          force: bool = False) -> Casamento:
    """`force` recalcula a janela DO ZERO, ignorando saída/chegada humanas —
    é o que "sobrescrever valor humano" quer dizer. Sem ele, a janela humana é
    soberana e serve de âncora pra integrar energia e movimento."""
    c = Casamento(passeio=p)
    if not p.latlngs:
        c.motivo = "sem rota no routes.json — não há geometria pra casar"
        return c
    saida_h = None if force else p.saida
    chegada_h = None if force else p.chegada

    cands = candidatos(p, trips)
    c.n_candidatos = len(cands)
    if not cands:
        c.motivo = "nenhum trip na data com a rota dentro do bbox"
        return c

    # Só agora baixa o detalhe (caro). Com >1 candidato, quem passa mais perto
    # do início E do fim da rota ganha — a data já provou que não basta.
    avaliados = []
    for t in cands:
        try:
            det = detalhe_trip(t["id"], cache)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"    ✗ trip {t['id']}: {e}", file=sys.stderr)
            continue
        pts = pontos(det)
        if not pts:
            continue
        j = janela(pts, p.latlngs, p.dist_rota, saida_h, chegada_h)
        if j is None or j.d_inicio > MAX_CASAMENTO:
            continue
        avaliados.append((j.d_inicio + j.d_fim, t, j))
    if not avaliados:
        c.motivo = (f"{len(cands)} candidato(s) na data, mas nenhum passa a menos de "
                    f"{MAX_CASAMENTO:.0f} m do início da rota")
        return c

    avaliados.sort(key=lambda a: a[0])
    _, c.trip, c.jan = avaliados[0]
    j = c.jan

    # Confiança do CASAMENTO. A chegada tem confiança PRÓPRIA (ver revisar()):
    # um casamento pode ser certíssimo e a chegada, um chute.
    if len(avaliados) > 1 and avaliados[1][0] < avaliados[0][0] * 2 + 100:
        c.confianca = "baixa"
        c.motivo = f"{len(avaliados)} trips igualmente plausíveis no dia"
    elif j.d_fim > MAX_CASAMENTO:
        c.confianca = "baixa"
        c.motivo = (f"o rastro nunca chega perto do fim da rota ({j.d_fim:.0f} m) — "
                    f"gravação interrompida? grupo encurtou o percurso?")
    elif j.d_inicio <= BOM_CASAMENTO and j.d_fim <= BOM_CASAMENTO:
        c.confianca = "alta"
    else:
        c.confianca = "media"
        c.motivo = f"{j.d_inicio:.0f} m do início, {j.d_fim:.0f} m do fim da rota"
    return c


def revisar(c: Casamento) -> list[str]:
    """O que este casamento pede de olho humano. A chegada é o campo ruidoso
    do método (~2/3 de acerto) — quando ela é gravada, avisa."""
    if not c.trip or not c.jan:
        return []
    r = []
    if c.confianca == "baixa":
        r.append(f"casamento fraco: {c.motivo}")
    if not c.jan.plausivel:
        r.append(f"janela de só {(c.jan.chegada - c.jan.saida) // 60} min — curta demais "
                 f"pra ser o passeio; provavelmente é o trip errado. NADA derivado será "
                 f"gravado, só a URL, pra você conferir")
        return r
    if c.passeio.chegada is None:
        if not c.jan.chegada_confiavel:
            r.append(f"parada de chegada a {c.jan.d_chegada:.0f} m do fim da rota — "
                     f"chegada/movimento/energia NÃO serão gravados")
        elif c.jan.d_chegada > BOA_CHEGADA:
            r.append(f"chegada a {c.jan.d_chegada:.0f} m do fim da rota — confira")
    if c.passeio.saida is None and not c.jan.saida_por_parada:
        r.append("saída sem parada de encontro no rastro (estimada pela saída do raio)")
    return r


# ═════════════════════════════════════════════════════════════════════════
# 6. Escrita (POST /upload-tour mode=patch)
# ═════════════════════════════════════════════════════════════════════════

def ttl_do_patch(c: Casamento, campos: dict) -> str:
    """O fragmento do patch. `mode=patch` substitui, por predicado, tudo que o
    fragmento afirma — então o ph:linkActivity (que é REPETÍVEL) reafirma
    junto os que já existiam, senão o patch os apagaria."""
    linhas = []
    urls = sorted(set(c.passeio.atividades) | ({campos["ph:linkActivity"]}
                                               if "ph:linkActivity" in campos else set()))
    if "ph:linkActivity" in campos:
        linhas.append("    ph:linkActivity " + ",\n        ".join(
            f'"{u}"^^xsd:anyURI' for u in urls))
    for k in ("ph:departedAt", "ph:arrivedAt"):
        if k in campos:
            linhas.append(f'    {k} "{campos[k]}"^^xsd:dateTime')
    if "ph:movingDuration" in campos:
        linhas.append(f'    ph:movingDuration "{campos["ph:movingDuration"]}"^^xsd:duration')
    if "ph:measuredEnergy" in campos:
        linhas.append(f'    ph:measuredEnergy {campos["ph:measuredEnergy"]:.1f}')
    return ("@prefix ph: <https://id.pedalhidrografi.co/terms#> .\n"
            "@prefix pas: <https://id.pedalhidrografi.co/passeio/> .\n"
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
            f"pas:{c.passeio.slug} a ph:Tour ;\n"
            + " ;\n".join(linhas) + " .\n")


def _multipart(campos: dict[str, str]) -> tuple[bytes, dict]:
    bnd = "----phidrobackfill" + os.urandom(8).hex()
    partes = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
              for k, v in campos.items()]
    partes.append(f"--{bnd}--\r\n")
    return "".join(partes).encode("utf-8"), {
        "Content-Type": f"multipart/form-data; boundary={bnd}"}


def gravar(c: Casamento, campos: dict, servidor: str) -> bool:
    body, headers = _multipart({"ttl": ttl_do_patch(c, campos), "mode": "patch"})
    req = urllib.request.Request(f"{servidor}/upload-tour", data=body,
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180, context=_CTX) as r:
            if r.status != 200:
                print(f"        ✗ HTTP {r.status}")
                return False
        return True
    except urllib.error.HTTPError as e:
        print(f"        ✗ HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"        ✗ {e}")
    return False


# ═════════════════════════════════════════════════════════════════════════
# 7. Relatório
# ═════════════════════════════════════════════════════════════════════════

def relatorio(cas: list[Casamento], force: bool, aplicar: bool, servidor: str) -> None:
    n = len(cas)
    casados = [c for c in cas if c.trip]
    print("═" * 78)
    print(f"  BACKFILL DE ATIVIDADES — {n} passeios, {len(casados)} casados com um trip")
    print("═" * 78)
    print("  conf: ✓ alta · ~ média · ! baixa      campos: A=linkActivity D=saída"
          " C=chegada M=movimento E=energia")
    print()

    escritas = {"ph:linkActivity": 0, "ph:departedAt": 0, "ph:arrivedAt": 0,
                "ph:movingDuration": 0, "ph:measuredEnergy": 0}
    pra_revisar: list[tuple[Casamento, list[str]]] = []
    falhas = 0

    for c in cas:
        p = c.passeio
        if not c.trip:
            print(f"  ·  {p.data.date()}  {p.edicao:7} {p.titulo[:34]:34}  — {c.motivo}")
            continue
        campos = c.escreveria(force)
        for k in campos:
            escritas[k] += 1
        j = c.jan
        marca = {"alta": "✓", "media": "~", "baixa": "!"}[c.confianca]
        letras = "".join(l for k, l in (("ph:linkActivity", "A"), ("ph:departedAt", "D"),
                                        ("ph:arrivedAt", "C"), ("ph:movingDuration", "M"),
                                        ("ph:measuredEnergy", "E")) if k in campos) or "—"
        print(f"  {marca}  {p.data.date()}  {p.edicao:7} {p.titulo[:34]:34}  "
              f"trip {c.trip['id']}  {j.kj:5.0f} kJ  {_iso_dur(j.movimento):>7}  "
              f"{_iso_sp(j.saida)[11:16]}→{_iso_sp(j.chegada)[11:16]}  "
              f"[{j.fonte[:4]}]  grava: {letras}")
        rev = revisar(c)
        if rev:
            pra_revisar.append((c, rev))
        if aplicar and campos:
            if not gravar(c, campos, servidor):
                falhas += 1

    print("\nGRAVARIA" if not aplicar else "\nGRAVOU")
    for k, v in escritas.items():
        print(f"  {v:3} × {k}")
    if falhas:
        print(f"  ✗ {falhas} falharam")

    if pra_revisar:
        print(f"\nREVISÃO HUMANA — {len(pra_revisar)} passeios")
        print("  (a chegada é o campo ruidoso do método: 62% dentro de 10 min — "
              "veja --validar)")
        for c, rev in pra_revisar:
            print(f"    {c.passeio.data.date()}  {c.passeio.edicao:7} "
                  f"{c.passeio.titulo[:30]:30} {c.url}")
            for r in rev:
                print(f"        · {r}")

    if not aplicar:
        print(f"\n(dry-run: nada foi enviado. --apply grava em {servidor})")
    print()


def validar(cas: list[Casamento], cache: Path | None) -> None:
    """Mede o método contra os campos HUMANOS que já existem.

    Recalcula a janela do zero (ignorando saída/chegada anotadas) nos passeios
    que as têm, e compara. É a única aferição honesta possível: não há verdade
    fundamental além do que uma pessoa anotou na hora.
    """
    print("═" * 78)
    print("  VALIDAÇÃO — heurística cega vs. o que a mão anotou")
    print("═" * 78)
    linhas, e_saida, e_chegada, e_energia = [], [], [], []
    for c in cas:
        p = c.passeio
        if not c.trip or (p.saida is None and p.chegada is None):
            continue
        try:
            pts = pontos(detalhe_trip(c.trip["id"], cache))
        except Exception:  # noqa: BLE001
            continue
        j = janela(pts, p.latlngs, p.dist_rota, None, None)   # cego
        if not j:
            continue
        ds = dc = de = None
        if p.saida is not None:
            ds = (j.saida - p.saida.timestamp()) / 60
            e_saida.append(abs(ds))
        if p.chegada is not None:
            dc = (j.chegada - p.chegada.timestamp()) / 60
            e_chegada.append(abs(dc))
        if p.energia and j.kj > 0:
            de = 100 * (j.kj - float(p.energia)) / float(p.energia)
            e_energia.append(abs(de))
        linhas.append((p, ds, dc, de, j))

    for p, ds, dc, de, j in linhas:
        f = lambda v, u: "   —   " if v is None else f"{v:+6.0f}{u}"  # noqa: E731
        print(f"  {p.data.date()}  {p.edicao:7} saída {f(ds,'m')}  chegada {f(dc,'m')}  "
              f"energia {f(de,'%')}  {p.titulo[:28]}")

    def resumo(nome, xs, un, limites):
        if not xs:
            return
        xs = sorted(xs)
        med = xs[len(xs) // 2]
        print(f"\n  {nome} (n={len(xs)}): mediana {med:.0f}{un}")
        for lim in limites:
            ok = sum(1 for x in xs if x <= lim)
            print(f"      {ok:3}/{len(xs)} ({100*ok/len(xs):3.0f}%) dentro de {lim}{un}")

    resumo("SAÍDA", e_saida, " min", [5, 10, 30])
    resumo("CHEGADA", e_chegada, " min", [5, 10, 30])
    resumo("ENERGIA", e_energia, "%", [10, 20])
    print("\n  (a chegada é, e continua sendo, o campo ruidoso do método.)\n")


def como_json(cas: list[Casamento], force: bool, destino: Path) -> None:
    destino.write_text(json.dumps({
        "gerado": datetime.now(TZ_SP).isoformat(timespec="seconds"),
        "passeios": [{
            "iri": c.passeio.iri, "slug": c.passeio.slug,
            "data": c.passeio.data.isoformat(), "edicao": c.passeio.edicao,
            "titulo": c.passeio.titulo,
            "trip": c.url or None,
            "confianca": c.confianca, "motivo": c.motivo or None,
            "candidatos": c.n_candidatos,
            "janela": None if not c.jan else {
                "saida": _iso_sp(c.jan.saida), "chegada": _iso_sp(c.jan.chegada),
                "kj": round(c.jan.kj, 1), "movimento": _iso_dur(c.jan.movimento),
                "fonte": c.jan.fonte,
                "metros_do_inicio": round(c.jan.d_inicio),
                "metros_do_fim": round(c.jan.d_chegada),
            },
            "gravaria": c.escreveria(force),
            "revisar": revisar(c),
        } for c in cas],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {destino}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="grava de verdade (default é dry-run)")
    ap.add_argument("--force", action="store_true",
                    help="recalcula a janela do zero (ignora saída/chegada humanas) e "
                         "sobrescreve os campos já preenchidos — por padrão, valor "
                         "humano é intocável e serve de âncora pra energia")
    ap.add_argument("--slug", action="append",
                    help="só este(s) passeio(s) (repetível)")
    ap.add_argument("--limite", type=int, help="processa só os N passeios mais recentes")
    ap.add_argument("--usuario", default=USUARIO_PADRAO,
                    help=f"id do usuário no RideWithGPS (default: {USUARIO_PADRAO})")
    ap.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", SERVIDOR_PADRAO))
    ap.add_argument("--cache", type=Path, default=CACHE_PADRAO,
                    help="cache dos trips detalhados")
    ap.add_argument("--sem-cache", action="store_true", help="ignora e não escreve o cache")
    ap.add_argument("--json", type=Path, help="grava o relatório cru")
    ap.add_argument("--validar", action="store_true",
                    help="mede a heurística contra os campos humanos existentes "
                         "(recalcula a janela do zero e compara) — não grava nada")
    a = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
    except ImportError:
        pass
    if not rwgps.has_credentials():
        sys.exit("faltam RWGPS_API_KEY / RWGPS_AUTH_TOKEN (ponha no .env do repo)")

    servidor = a.servidor.rstrip("/")
    passeios = carregar_passeios(servidor)
    if a.slug:
        passeios = [p for p in passeios if p.slug in set(a.slug)]
    if a.limite:
        passeios = passeios[:a.limite]
    if not passeios:
        sys.exit("nenhum passeio selecionado")

    mais_antigo = min(p.data for p in passeios) - timedelta(days=2)
    print(f"listando trips de {a.usuario} desde {mais_antigo.date()}…", file=sys.stderr)
    trips = listar_trips(a.usuario, mais_antigo)
    print(f"{len(trips)} trips; casando {len(passeios)} passeios…\n", file=sys.stderr)

    cache = None if a.sem_cache else a.cache
    cas = [casar(p, trips, cache, a.force) for p in passeios]

    if a.validar:
        validar(cas, cache)
        return

    relatorio(cas, a.force, a.apply, servidor)
    if a.json:
        como_json(cas, a.force, a.json)


if __name__ == "__main__":
    main()
