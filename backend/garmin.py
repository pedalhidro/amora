"""Endpoints dos apps Garmin (Connect IQ) — ver garmin/README.md.

Tudo sob `/garmin/…`, registrado por `register(app, main)` no fim do main.py.
`main` é o próprio módulo do backend: os helpers dele (`_tours_sorted`,
`_read_saved_routes`, `_live_positions`…) são lidos por atributo NA HORA da
requisição, então este arquivo não importa o main (sem import circular) e
não duplica nenhuma leitura de catálogo.

Quem consome:
  • app "Amora" do relógio/ciclocomputador (garmin/amora): lista de passeios e
    rotas, ficha de um item, download do percurso em FIT, fila "enviadas por
    você" (pareamento por código);
  • campo de dados "Pessoas ao vivo" (garmin/pessoas): leitura enxuta das
    posições ao vivo;
  • o site: "Enviar pro Garmin" (POST /garmin/send) e "Exportar .fit".

As respostas são PEQUENAS de propósito: um campo de dados do Edge 1040 tem
128 KB de memória pra código + dados, e o JSON chega pelo Bluetooth do
celular. Chaves curtas (k/id/n/s) pelo mesmo motivo.

Sem auth, como o resto do backend. O código de pareamento é um token
pseudônimo gerado NO APARELHO (6 caracteres Crockford); quem o conhece só
consegue pôr uma rota na lista daquele aparelho.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from datetime import datetime, timedelta, timezone

from flask import Response, abort, jsonify, request

import fit_course

KEY_QUEUE = "garmin_queue.json"
QUEUE_MAX_CODES = 2000          # aparelhos pareados lembrados (LRU por uso)
QUEUE_MAX_ITEMS = 10            # itens enviados por aparelho (os mais novos)
QUEUE_ITEM_TTL_S = 30 * 86400   # um envio some da lista depois de 30 dias
LIST_NEXT, LIST_RECENT, LIST_ROUTES = 6, 6, 10
PREVIEW_PTS = 60                # pontos do traçado na ficha (MapView do relógio)
LIVE_MAX_PEERS = 30             # pessoas por resposta do /garmin/live
GEOM_TTL_S = 6 * 3600           # cache da geometria cheia buscada no RideWithGPS
UPCOMING_GRACE_S = 6 * 3600     # passeio que saiu há < 6 h ainda é "próximo"

# São Paulo não tem horário de verão desde 2019: UTC−3 fixo.
SP_TZ = timezone(timedelta(hours=-3))
_WEEKDAYS = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")
_CODE_RE = re.compile(r"[0-9a-hjkmnp-tv-z]{6}")
_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]{0,80}")

_queue_lock = threading.Lock()
_geom_lock = threading.Lock()
_geom_cache = {}                # (provider, id) -> (instante, dict geometria)
GEOM_CACHE_MAX = 256            # > nº de passeios: um crawl do /garmin/course
                                # não fica rebuscando o RideWithGPS
# O /garmin/course é público e sem auth, e a geometria cheia de um passeio do
# RideWithGPS é buscada LÁ com as credenciais do coletivo. O cache acima some
# a cada cold start do Cloud Run, então sem um freio um crawler varrendo os
# passeios viraria uma rajada de fetches autenticados a cada instância nova.
RWGPS_MIN_GAP_S = 5             # no máx. 1 fetch a cada 5 s (o resto: traçado grosso)
GEOM_FAIL_TTL_S = 600           # rota que falhou: não insiste por 10 min
_rwgps_gate = [0.0]             # instante do último fetch iniciado


def norm_code(code):
    """Código de pareamento digitado → forma canônica, ou None. Crockford
    base32 em minúsculas; O→0 e I/L→1 (o que a pessoa lê na tela do relógio
    e digita no celular), espaços e hífens ignorados."""
    s = re.sub(r"[\s\-]", "", str(code or "")).lower()
    s = s.replace("o", "0").replace("i", "1").replace("l", "1")
    return s if _CODE_RE.fullmatch(s) else None


def _km_label(meters):
    if not meters:
        return None
    km = meters / 1000.0
    return (f"{km:.1f}".replace(".", ",") if km < 20 else f"{km:.0f}") + " km"


def _sub_label(bits):
    return " · ".join(b for b in bits if b)


def _polyline_dist(latlngs):
    from rwgps import haversine_meters
    d = 0.0
    for i in range(1, len(latlngs)):
        a, b = latlngs[i - 1], latlngs[i]
        d += haversine_meters(a[0], a[1], b[0], b[1])
    return d


def _resample(latlngs, max_pts, digits=5):
    pts = latlngs
    if len(pts) > max_pts:
        stride = (len(pts) - 1) / (max_pts - 1)
        pts = [pts[round(i * stride)] for i in range(max_pts)]
    return [[round(p[0], digits), round(p[1], digits)] for p in pts]


def register(app, m):
    """Liga os endpoints /garmin/… ao app Flask. `m` = módulo main."""

    # ── Passeios e rotas → itens ────────────────────────────────────────
    def _local(dt):
        if dt is None:
            return None
        return dt.astimezone(SP_TZ) if dt.tzinfo else dt.replace(tzinfo=SP_TZ)

    def _when_label(dt):
        d = _local(dt)
        if d is None:
            return None
        s = f"{_WEEKDAYS[d.weekday()]} {d.day}/{d.month}"
        if d.hour or d.minute:
            s += f" · {d.hour}h" + (f"{d.minute:02d}" if d.minute else "")
        return s

    def _routes_by_tour():
        try:
            routes = m._load_routes_payload().get("routes") or []
        except Exception as e:  # noqa: BLE001
            print(f"[garmin] routes.json ilegível: {e}")
            routes = []
        return {r.get("tourIri"): r for r in routes
                if isinstance(r, dict) and r.get("tourIri")}

    def _tour_items():
        """Passeios COM traçado, como dicts internos (mais recentes primeiro).
        Barato: _tours_sorted lê o grafo cacheado por digest."""
        by_tour = _routes_by_tour()
        out = []
        for d in m._tours_sorted():
            r = by_tour.get(d["iri"])
            if not r or not r.get("latlngs"):
                continue
            out.append({
                "k": "t", "id": d["pretty"] or d["id"], "alt": d["id"],
                "n": d["title"], "dt": d["dt"], "kj": d["energy"],
                "iri": d["iri"], "route": r,
            })
        return out

    def _tour_public(it, with_date=True):
        km = _km_label(_polyline_dist(it["route"]["latlngs"]))
        kj = f"{it['kj']:.0f} kJ" if it["kj"] is not None else None
        when = _when_label(it["dt"]) if with_date else None
        return {"k": "t", "id": it["id"], "n": it["n"],
                "s": _sub_label([when, km, kj])}

    def _route_items():
        """Rotas salvas, mais novas primeiro."""
        out = []
        for rid, r in (m._read_saved_routes().get("routes") or {}).items():
            if not isinstance(r, dict) or not isinstance(r.get("state"), dict):
                continue
            out.append({"k": "r", "id": m._entry_slug(r), "rid": rid,
                        "n": r.get("name") or "", "entry": r,
                        "stamp": r.get("updated") or r.get("created") or ""})
        out.sort(key=lambda x: x["stamp"], reverse=True)
        return out

    def _route_stats(entry):
        st = entry.get("stats") if isinstance(entry.get("stats"), dict) else {}

        def num(key):
            v = st.get(key)
            return float(v) if isinstance(v, (int, float)) and math.isfinite(v) else None
        return num("energyKj"), num("ascentM")

    def _route_public(it):
        _, dist = m._route_preview_and_dist(it["entry"]["state"])
        kj, _asc = _route_stats(it["entry"])
        return {"k": "r", "id": it["id"], "n": it["n"],
                "s": _sub_label([_km_label(dist),
                                 f"{kj:.0f} kJ" if kj is not None else None])}

    def _find(kind, ref):
        """(kind, ref) → item interno, ou None."""
        if not _REF_RE.fullmatch(ref or ""):
            return None
        if kind == "t":
            for it in _tour_items():
                if ref in (it["id"], it["alt"]):
                    return it
            return None
        if kind == "r":
            rid, r = m._find_saved_route(ref)
            if isinstance(r, dict) and isinstance(r.get("state"), dict):
                return {"k": "r", "id": m._entry_slug(r), "rid": rid,
                        "n": r.get("name") or "", "entry": r}
        return None

    # ── Fila "enviadas por você" (persistida no store) ──────────────────
    def _read_queue():
        try:
            obj = json.loads(m.STORE.read_text(KEY_QUEUE) or "{}")
        except (ValueError, TypeError):
            obj = {}
        if not isinstance(obj, dict) or not isinstance(obj.get("codes"), dict):
            obj = {"codes": {}}
        return obj

    def _write_queue(q):
        codes = q["codes"]
        if len(codes) > QUEUE_MAX_CODES:      # esquece os aparelhos mais parados
            keep = sorted(codes, key=lambda c: codes[c].get("seen") or 0,
                          reverse=True)[:QUEUE_MAX_CODES]
            q["codes"] = {c: codes[c] for c in keep}
        m.STORE.write_text(KEY_QUEUE, json.dumps(q, ensure_ascii=False),
                           content_type="application/json")

    def _queue_items(entry, now):
        return [i for i in (entry.get("items") or [])
                if isinstance(i, dict) and now - (i.get("t") or 0) < QUEUE_ITEM_TTL_S]

    def _sent_for(code, register, tours, routes):
        """Itens enviados pro aparelho `code` (mais novos primeiro), resolvidos
        contra as listas JÁ carregadas nesta requisição (`tours`, `routes`) —
        nada de reler routes.json/saved_routes.json do bucket por item.

        `register` (só no POST do aparelho): na primeira vez que o código
        aparece, marca-o como visto — é o que deixa o site avisar "esse código
        ainda não abriu o app" em vez de aceitar um erro de digitação em
        silêncio. Um GET nunca grava no store."""
        now = time.time()
        with _queue_lock:
            q = _read_queue()
            entry = q["codes"].get(code)
            if register and (entry is None or not entry.get("seen")):
                if entry is None:
                    entry = q["codes"][code] = {"items": []}
                entry["seen"] = round(now)
                try:
                    _write_queue(q)
                except Exception as e:  # noqa: BLE001
                    print(f"[garmin] não registrou o código: {e}")
            raw = _queue_items(entry, now) if entry else []
        by_tour = {}
        for it in tours:
            by_tour[it["id"]] = it
            by_tour.setdefault(it["alt"], it)
        by_route = {it["id"]: it for it in reversed(routes)}   # empate: a mais nova
        out = []
        for i in reversed(raw):        # a lista é gravada em ordem de envio
            it = (by_tour if i.get("k") == "t" else by_route).get(i.get("id"))
            if it:   # rota apagada/renomeada depois do envio some da lista
                out.append(_tour_public(it) if it["k"] == "t" else _route_public(it))
        return out

    # ── Geometria cheia (percurso) ──────────────────────────────────────
    def _tour_geometry(it):
        """{latlngs, pois, eles?} do traçado de um passeio, na melhor
        resolução disponível. routes.json guarda ≤ 400 pontos por rota (um
        ponto a cada ~100 m num pedal de 40 km) — grosso demais pra navegar
        esquina a esquina —, então: rota do amora → o estado salvo (geometria
        cheia); RideWithGPS → rebusca o GPX (com altitude), cacheado e com
        freio (RWGPS_MIN_GAP_S); se a rede falhar ou o freio segurar, cai no
        traçado do routes.json."""
        import rwgps
        r = it["route"]
        key = (r.get("provider") or "rwgps", str(r.get("id") or ""))
        if key[0] == "amora":
            _rid, entry = m._find_saved_route(key[1])
            if isinstance(entry, dict) and isinstance(entry.get("state"), dict):
                try:
                    return rwgps.amora_route_geometry(entry["state"])
                except Exception as e:  # noqa: BLE001
                    print(f"[garmin] rota amora {key[1]} não decodifica: {e}")
            return {"latlngs": r["latlngs"], "pois": r.get("pois") or []}
        coarse = {"latlngs": r["latlngs"], "pois": r.get("pois") or []}
        now = time.time()
        with _geom_lock:
            hit = _geom_cache.get(key)
            if hit is not None:
                age = now - hit[0]
                if hit[1] is not None and age < GEOM_TTL_S:
                    return hit[1]
                if hit[1] is None and age < GEOM_FAIL_TTL_S:
                    return coarse           # falhou há pouco: não insiste
            if now - _rwgps_gate[0] < RWGPS_MIN_GAP_S:
                return coarse               # freio: fica o traçado do routes.json
            _rwgps_gate[0] = now
        geom = None
        try:
            status, text = rwgps.http_get(rwgps.decorate_rwgps(
                f"https://ridewithgps.com/routes/{key[1]}.gpx"))
            pts = rwgps.parse_gpx_points(text) if status == 200 else []
            if len(pts) >= 2:
                eles = [p.get("ele") for p in pts]
                geom = {"latlngs": [[p["lat"], p["lon"]] for p in pts],
                        "pois": rwgps.parse_gpx_pois(text),
                        "eles": eles if all(isinstance(e, (int, float)) for e in eles) else None}
        except Exception as e:  # noqa: BLE001
            print(f"[garmin] GPX do RideWithGPS {key[1]} falhou: {e}")
        with _geom_lock:
            _geom_cache.pop(key, None)          # reinsere no fim (mais novo)
            _geom_cache[key] = (now, geom)      # None = falha (GEOM_FAIL_TTL_S)
            while len(_geom_cache) > GEOM_CACHE_MAX:
                _geom_cache.pop(next(iter(_geom_cache)))   # o mais antigo
        return geom if geom is not None else coarse

    def _geometry(it):
        if it["k"] == "t":
            return _tour_geometry(it)
        import rwgps
        return rwgps.amora_route_geometry(it["entry"]["state"])

    def _no_store(payload, status=200):
        return Response(json.dumps(payload, ensure_ascii=False,
                                   separators=(",", ":")),
                        status=status, mimetype="application/json",
                        headers={"Cache-Control": "no-store"})

    # ── Endpoints ───────────────────────────────────────────────────────
    @app.route("/garmin/list", methods=["GET", "POST"])
    def garmin_list():
        """Lista pro app do relógio: `sent` (enviadas pro código), `next`
        (próximos passeios, o mais próximo primeiro), `recent` (últimos
        passeios) e `routes` (rotas salvas mais novas). Só entra passeio que
        tem traçado. `?glance=1` devolve só `next[0]` — é o que o glance
        (64 KB de memória) pede.

        O código de pareamento vem em `?code=` (GET — só lê) ou no corpo
        JSON `{code}` de um POST: é o que o app do aparelho usa, e o que
        REGISTRA o código como visto (um GET nunca grava no store)."""
        tours = _tour_items()
        now = datetime.now(timezone.utc).timestamp()

        def stamp(it):
            d = _local(it["dt"])
            return d.timestamp() if d else None
        upcoming = [it for it in tours
                    if stamp(it) is not None and stamp(it) >= now - UPCOMING_GRACE_S]
        upcoming.sort(key=stamp)
        if request.args.get("glance"):
            nxt = _tour_public(upcoming[0]) if upcoming else None
            return _no_store({"v": 1, "next": nxt})
        ids = {id(it) for it in upcoming}
        recent = [it for it in tours if id(it) not in ids][:LIST_RECENT]
        routes = _route_items()
        body = {
            "v": 1,
            "next": [_tour_public(it) for it in upcoming[:LIST_NEXT]],
            "recent": [_tour_public(it) for it in recent],
            "routes": [_route_public(it) for it in routes[:LIST_ROUTES]],
        }
        posted = request.method == "POST"
        raw_code = ((request.get_json(silent=True) or {}).get("code") if posted
                    else request.args.get("code"))
        code = norm_code(raw_code)
        if code:
            body["sent"] = _sent_for(code, posted, tours, routes)
        return _no_store(body)

    @app.get("/garmin/item/<kind>/<ref>")
    def garmin_item(kind, ref):
        """Ficha de um passeio (`t`) ou rota salva (`r`): nome, quando, de
        onde sai, km, subida, kJ + faixa do censo e o traçado reamostrado a
        ≤ 60 pontos pra pré-visualização no mapa do aparelho."""
        it = _find(kind, ref)
        if it is None:
            abort(404)
        out = {"v": 1, "k": it["k"], "id": it["id"], "n": it["n"],
               "fit": f"/garmin/course/{it['k']}/{it['id']}.fit"}
        if it["k"] == "t":
            latlngs = it["route"]["latlngs"]
            kj, asc = it["kj"], None
            out["when"] = _when_label(it["dt"])
            try:
                from rdflib import Namespace, URIRef
                place = m._tours_graph().value(
                    URIRef(it["iri"]), Namespace(m.PH_NS).departureLocation)
                if place:
                    out["place"] = str(place)[:60]
            except Exception:  # noqa: BLE001
                pass
        else:
            import rwgps
            latlngs = rwgps.amora_route_geometry(it["entry"]["state"])["latlngs"]
            kj, asc = _route_stats(it["entry"])
        out["km"] = round(_polyline_dist(latlngs) / 1000.0, 1)
        if asc is not None:
            out["up"] = round(asc)
        if kj is not None:
            out["kj"] = round(kj)
            out["band"] = m._intensity_for(kj)
        out["pts"] = _resample(latlngs, PREVIEW_PTS)
        return _no_store(out)

    @app.get("/garmin/course/<kind>/<ref>.fit")
    def garmin_course(kind, ref):
        """O percurso em FIT (Garmin): o app do aparelho baixa e entrega à
        navegação nativa; o site usa o mesmo arquivo no "Exportar pro
        Garmin". POIs viram pontos de percurso."""
        it = _find(kind, ref)
        if it is None:
            abort(404)
        try:
            geom = _geometry(it)
            data = fit_course.encode_course(it["n"] or it["id"], geom["latlngs"],
                                            geom.get("pois"), geom.get("eles"))
        except Exception as e:  # noqa: BLE001
            print(f"[garmin] percurso {kind}/{ref} falhou: {e}")
            abort(404)
        resp = Response(data, mimetype="application/vnd.ant.fit")
        resp.headers["Content-Disposition"] = f'attachment; filename="{it["id"]}.fit"'
        resp.headers["Cache-Control"] = "no-cache"
        return m._conditional(resp)

    @app.post("/garmin/send")
    def garmin_send():
        """"Enviar pro Garmin" do site: põe um passeio/rota na lista do
        aparelho pareado. Body JSON {code, k, id}. `seen: false` na resposta =
        nenhum aparelho abriu o app com esse código ainda (provável erro de
        digitação) — o envio fica guardado mesmo assim."""
        data = request.get_json(silent=True) or {}
        code = norm_code(data.get("code"))
        if not code:
            return jsonify(error="código inválido"), 400
        it = _find(str(data.get("k") or ""), str(data.get("id") or ""))
        if it is None:
            return jsonify(error="rota não encontrada"), 404
        now = time.time()
        with _queue_lock:
            q = _read_queue()
            entry = q["codes"].get(code)
            seen = entry is not None and bool(entry.get("seen"))
            if entry is None:
                entry = q["codes"][code] = {"seen": 0, "items": []}
            items = [i for i in _queue_items(entry, now)
                     if not (i.get("k") == it["k"] and i.get("id") == it["id"])]
            items.append({"k": it["k"], "id": it["id"], "t": round(now)})
            entry["items"] = items[-QUEUE_MAX_ITEMS:]
            _write_queue(q)
        return jsonify(ok=True, seen=seen, name=it["n"])

    @app.post("/garmin/live")
    def garmin_live():
        """Posições ao vivo, enxutas, pro campo de dados "Pessoas ao vivo":
        {n, p: [[nome, lat, lng, idade_s], …]} — sem rastro e SEM os tokens
        (o /live-locations do site devolve os dois). Body JSON opcional
        {id}: o token do próprio aparelho, pra ele não aparecer na própria
        lista; vai no corpo, não na URL, pra não cair em log de acesso. O
        aparelho calcula distância e rumo — a posição dele só sobe se a
        pessoa ligou a transmissão (POST /live-location)."""
        own = str((request.get_json(silent=True) or {}).get("id") or "")
        with m._live_positions_lock:
            now = m._live_now()
            m._prune_live(now)
            rows = [(p["ts"], p.get("name") or "", p["lat"], p["lng"])
                    for t, p in m._live_positions.items() if t != own]
        rows.sort(reverse=True)
        return _no_store({
            "n": len(rows),
            "p": [[name[:16], round(lat, 5), round(lng, 5), max(0, round(now - ts))]
                  for ts, name, lat, lng in rows[:LIVE_MAX_PEERS]],
        })
