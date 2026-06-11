"""
rwgps.py — lógica compartilhada de busca de geometria de rotas no RideWithGPS
e montagem de entradas de `routes.json`.

Fonte única de verdade para dois consumidores:
  • `scripts/build-routes.py` — rebuild completo de `web/routes.json` a partir
    de todo o `tours.ttl`.
  • `backend/pi/main.py` — atualização incremental de uma entrada quando um
    tour é criado/editado/apagado (POST /upload-tour, /delete-tour).

Mantendo o fetch + parsing + shape da entrada aqui, os dois caminhos produzem
entradas idênticas (mesmos campos, mesmo downsample), evitando que o app
renderize rotas vindas do rebuild diferente das vindas do upload.

Credenciais lidas de `os.environ` no momento da chamada (cada consumidor as
carrega do seu jeito — build-routes via python-dotenv, o backend via env do
serviço):
  RWGPS_API_KEY
  RWGPS_AUTH_TOKEN
  RWGPS_COLLECTION_PRIVACY_CODE  (opcional)
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
MAX_POINTS_PER_ROUTE = 400   # downsample pra manter o JSON enxuto
COORD_PRECISION      = 5     # ~1 m de precisão

# Prioridade pra escolher qual sigla mostrar quando o passeio é vinculado a
# várias séries (ex.: PH 10 + BT 1 → usa PH). Match a `number.source` que
# o sidebar exibe.
SERIES_PRIORITY = ["PH", "BT", "BP", "S"]
# Override de exibição: o série "S" aparece como "PH-S" pra ficar coerente
# com a convenção do popup de foto.
SERIES_LABEL_OVERRIDE = {"S": "PH-S"}


def _creds() -> tuple[str, str, str]:
    """(api_key, auth_token, privacy_code) lidos do ambiente na hora da chamada."""
    return (
        os.environ.get("RWGPS_API_KEY", ""),
        os.environ.get("RWGPS_AUTH_TOKEN", ""),
        os.environ.get("RWGPS_COLLECTION_PRIVACY_CODE", ""),
    )


def has_credentials() -> bool:
    api_key, auth_token, _ = _creds()
    return bool(api_key and auth_token)


# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def http_get(url: str, accept: str | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url)
    if accept:
        req.add_header("Accept", accept)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, body
    except urllib.error.URLError as e:
        # Falha de rede/DNS/timeout (a parente de HTTPError). Antes escapava
        # como exceção e matava a cadeia de fallback GPX→JSON; devolvemos um
        # status sentinela 0 pra que o caller tente o próximo endpoint.
        return 0, str(getattr(e, "reason", e))


# ─── Extração de id / séries ──────────────────────────────────────────────────
def extract_rwgps_id(url: str) -> str | None:
    if not url:
        return None
    m = re.search(r"ridewithgps\.com/routes/(\d+)", url, re.IGNORECASE)
    return m.group(1) if m else None


def series_slug(iri: str) -> str:
    """`https://pedalhidrografi.co/data/PH` → `PH`."""
    return iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def series_label(iri: str) -> str:
    slug = series_slug(iri)
    return SERIES_LABEL_OVERRIDE.get(slug, slug)


def order_numbers(assocs: list[dict]) -> list[dict]:
    """Retorna [{source, value}, …] ordenados por SERIES_PRIORITY.
    Tours pertencendo a múltiplas séries (ex.: PH 79 + BP 4) preservam todas
    as associações para a UI exibir."""
    if not assocs:
        return []
    ordered: list[dict] = []
    seen_iris: set[str] = set()
    for s in SERIES_PRIORITY:
        for a in assocs:
            if a["series_iri"] in seen_iris:
                continue
            if series_slug(a["series_iri"]) == s:
                ordered.append({"source": series_label(a["series_iri"]), "value": str(a["seq"])})
                seen_iris.add(a["series_iri"])
    # Séries fora da priority list ficam no final, ordem de aparição.
    for a in assocs:
        if a["series_iri"] in seen_iris:
            continue
        ordered.append({"source": series_label(a["series_iri"]), "value": str(a["seq"])})
        seen_iris.add(a["series_iri"])
    return ordered


def parse_iso_date_ms(s: str) -> int | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


# ─── Tour (RDF) → entrada (metadados, sem geometria) ──────────────────────────
def tour_entry_from_graph(g, tour) -> dict | None:
    """Monta a entrada de metadados de UM `ph:Tour` (sem `latlngs`/`pois`).

    Retorna `None` se o tour não tiver `ph:linkRoute` apontando pra uma URL
    do RideWithGPS — esses passeios ficam fora do routes.json.

    `g` é um `rdflib.Graph`; `tour` é o `rdflib.URIRef` do passeio. rdflib é
    importado aqui (lazy) pra que `import rwgps` permaneça leve quando só o
    fetch de geometria é necessário.
    """
    from rdflib import Namespace, RDF
    from rdflib.namespace import DCTERMS

    PH     = Namespace("https://pedalhidrografi.co/terms#")
    SCHEMA = Namespace("https://schema.org/")

    # Rota (RWGPS) — sem ela, o passeio fica fora do routes.json.
    rwgps_url = None
    for ref in g.objects(tour, PH.linkRoute):
        for url in g.objects(ref, SCHEMA.url):
            rwgps_url = str(url)
            break
        if rwgps_url:
            break
    rid = extract_rwgps_id(rwgps_url)
    if not rid:
        return None

    title = next(iter(g.objects(tour, DCTERMS.title)), None)
    title = str(title) if title else ""

    date_lit = next(iter(g.objects(tour, DCTERMS.date)), None)
    date_str = str(date_lit) if date_lit else ""
    date_ms = parse_iso_date_ms(date_str)
    # `date` exibido: só a parte AAAA-MM-DD pra ficar igual ao que o app já
    # consome historicamente.
    date_disp = date_str[:10] if date_str else ""

    ig = next(iter(g.objects(tour, PH.linkInstagram)), None)
    ig = str(ig) if ig else ""

    assocs = []
    for a in g.objects(tour, PH.inSeriesEdition):
        seriesIri = next(iter(g.objects(a, PH.inEventSeries)), None)
        seqLit    = next(iter(g.objects(a, PH.sequenceInSeries)), None)
        if seriesIri is None or seqLit is None:
            continue
        try:
            seq = int(str(seqLit))
        except ValueError:
            continue
        assocs.append({"series_iri": str(seriesIri), "seq": seq})

    nums = order_numbers(assocs)
    return {
        "id":      rid,
        "tourIri": str(tour),
        "date":    date_disp,
        "dateMs":  date_ms,
        "name":    title,
        "igPost":  ig,
        "number":  nums[0] if nums else {"source": "", "value": ""},
        "numbers": nums,
    }


# ─── RideWithGPS fetch ────────────────────────────────────────────────────────
def decorate_rwgps(url: str) -> str:
    api_key, auth_token, privacy_code = _creds()
    parts = urllib.parse.urlparse(url)
    q = dict(urllib.parse.parse_qsl(parts.query))
    if api_key:      q["apikey"] = api_key
    if auth_token:   q["auth_token"] = auth_token
    q["version"] = "2"
    if privacy_code: q["privacy_code"] = privacy_code
    return urllib.parse.urlunparse(parts._replace(query=urllib.parse.urlencode(q)))


def fetch_route_data(route_id: str) -> dict:
    # Tentativa 1: .gpx nativo com auth — traz <wpt> (cues) e <ele> por trkpt.
    gpx_url = decorate_rwgps(f"https://ridewithgps.com/routes/{route_id}.gpx")
    gpx_status, gpx_text = http_get(gpx_url)
    if gpx_status == 200:
        points = parse_gpx_points(gpx_text)
        pois   = parse_gpx_pois(gpx_text)
        if points:
            latlngs = [[p["lat"], p["lon"]] for p in points]
            return {"latlngs": latlngs, "pois": pois, "stats": compute_route_stats(points)}

    # Tentativa 2: endpoint JSON → track_points + course_points.
    json_url = decorate_rwgps(f"https://ridewithgps.com/routes/{route_id}.json")
    json_status, json_text = http_get(json_url, accept="application/json")
    if json_status != 200:
        snippet = (json_text or "")[:200]
        raise RuntimeError(
            f"gpx {gpx_status}, json {json_status} ({snippet or 'empty'})"
        )
    data = json.loads(json_text)
    pts = (data.get("route") or {}).get("track_points") or data.get("track_points") or []
    if not isinstance(pts, list) or not pts:
        raise RuntimeError("json had no track_points")
    points = []
    for p in pts:
        lat = p.get("y", p.get("lat"))
        lon = p.get("x", p.get("lon"))
        ele = p.get("e")
        if ele is None or not isinstance(ele, (int, float)):
            ele = p.get("elevation")
        if not isinstance(ele, (int, float)) or not math.isfinite(ele):
            ele = None
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and \
           math.isfinite(lat) and math.isfinite(lon):
            points.append({"lat": float(lat), "lon": float(lon), "ele": ele})

    latlngs = [[p["lat"], p["lon"]] for p in points]
    stats   = compute_route_stats(points)

    raw_pois = (data.get("route") or {}).get("points_of_interest") or \
               data.get("points_of_interest") or []
    pois = []
    for p in raw_pois:
        lat, lng = p.get("lat"), p.get("lng")
        if not (isinstance(lat, (int, float)) and isinstance(lng, (int, float))):
            continue
        pois.append({
            "lat":  lat,
            "lng":  lng,
            "name": p.get("n") or p.get("name") or "",
            "sym":  p.get("t") or p.get("poi_type") or "",
            "type": p.get("t") or p.get("poi_type") or "",
        })

    return {"latlngs": latlngs, "pois": pois, "stats": stats}


# ─── GPX parsing ──────────────────────────────────────────────────────────────
_TRKPT_RE = re.compile(
    r"<(trkpt|rtept)\s+([^>]*?)(?:/>|>([\s\S]*?)</\1\s*>)",
    re.IGNORECASE,
)
_WPT_RE  = re.compile(r"<wpt\s+([^>]*)>([\s\S]*?)</wpt>", re.IGNORECASE)
_ATTR_LAT = re.compile(r'\blat\s*=\s*"([^"]+)"', re.IGNORECASE)
_ATTR_LON = re.compile(r'\blon\s*=\s*"([^"]+)"', re.IGNORECASE)
_ELE_RE   = re.compile(r"<ele>([^<]+)</ele>", re.IGNORECASE)
_NAME_RE  = re.compile(r"<name>([\s\S]*?)</name>", re.IGNORECASE)
_SYM_RE   = re.compile(r"<sym>([\s\S]*?)</sym>", re.IGNORECASE)
_TYPE_RE  = re.compile(r"<type>([\s\S]*?)</type>", re.IGNORECASE)


def parse_gpx_points(gpx_text: str) -> list[dict]:
    out = []
    for m in _TRKPT_RE.finditer(gpx_text):
        attrs, body = m.group(2), m.group(3) or ""
        lat_m = _ATTR_LAT.search(attrs)
        lon_m = _ATTR_LON.search(attrs)
        if not lat_m or not lon_m:
            continue
        try:
            la, lo = float(lat_m.group(1)), float(lon_m.group(1))
        except ValueError:
            continue
        if not (math.isfinite(la) and math.isfinite(lo)):
            continue
        ele = None
        ele_m = _ELE_RE.search(body)
        if ele_m:
            try:
                e = float(ele_m.group(1))
                if math.isfinite(e):
                    ele = e
            except ValueError:
                pass
        out.append({"lat": la, "lon": lo, "ele": ele})
    return out


def parse_gpx_pois(gpx_text: str) -> list[dict]:
    out = []
    for m in _WPT_RE.finditer(gpx_text):
        attrs, body = m.group(1), m.group(2)
        lat_m = _ATTR_LAT.search(attrs)
        lon_m = _ATTR_LON.search(attrs)
        if not lat_m or not lon_m:
            continue
        try:
            la, lo = float(lat_m.group(1)), float(lon_m.group(1))
        except ValueError:
            continue
        if not (math.isfinite(la) and math.isfinite(lo)):
            continue
        name_m = _NAME_RE.search(body)
        sym_m  = _SYM_RE.search(body)
        typ_m  = _TYPE_RE.search(body)
        name = name_m.group(1) if name_m else ""
        sym  = sym_m.group(1)  if sym_m  else ""
        typ  = typ_m.group(1)  if typ_m  else ""
        out.append({
            "lat":  round(la, COORD_PRECISION),
            "lng":  round(lo, COORD_PRECISION),
            "name": decode_xml(name).strip(),
            "sym":  decode_xml(sym).strip(),
            "type": decode_xml(typ).strip(),
        })
    return out


def decode_xml(s: str) -> str:
    return (str(s)
            .replace("&amp;",  "&")
            .replace("&lt;",   "<")
            .replace("&gt;",   ">")
            .replace("&quot;", '"')
            .replace("&apos;", "'"))


# ─── Geometria / stats ────────────────────────────────────────────────────────
def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    rad = math.radians
    d_lat = rad(lat2 - lat1)
    d_lon = rad(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(d_lon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def compute_route_stats(points: list[dict]) -> dict:
    dist = ascent = descent = 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        dist += haversine_meters(a["lat"], a["lon"], b["lat"], b["lon"])
        if a["ele"] is not None and b["ele"] is not None:
            dh = b["ele"] - a["ele"]
            if dh > 0:
                ascent += dh
            else:
                descent += -dh
    return {
        "distMeters":    round(dist),
        "ascentMeters":  round(ascent),
        "descentMeters": round(descent),
    }


def downsample_and_round(points):
    if not points:
        return points
    out = points
    if len(out) > MAX_POINTS_PER_ROUTE:
        stride = math.ceil(len(out) / MAX_POINTS_PER_ROUTE)
        sampled = [out[i] for i in range(0, len(out), stride)]
        if sampled[-1] is not out[-1]:
            sampled.append(out[-1])
        out = sampled
    f = 10 ** COORD_PRECISION
    return [[round(la * f) / f, round(lo * f) / f] for la, lo in out]


def build_route_entry(meta: dict) -> dict:
    """Dado o dict de metadados de `tour_entry_from_graph`, busca a geometria
    no RideWithGPS e devolve a entrada completa de routes.json.

    Em caso de falha de fetch, devolve a entrada com `latlngs: null`, `pois: []`
    e um campo `error` — mesma convenção do build-routes.py, pra que o app
    ainda exiba os metadados do passeio.
    """
    try:
        data = fetch_route_data(meta["id"])
        return {
            **meta,
            "latlngs": downsample_and_round(data["latlngs"]),
            "pois":    data["pois"],
        }
    except Exception as e:  # noqa: BLE001
        return {**meta, "latlngs": None, "pois": [], "error": str(e)}
