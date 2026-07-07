"""Servidor standalone do navegador e-ink de guidão (projeto paralelo).

DELIBERADAMENTE FORA do backend do amora: fala com o amora só pelos endpoints
PÚBLICOS que qualquer cliente usa (routes.json + GET /live-locations), então
roda em qualquer lugar — laptop em casa, Raspberry Pi, ou um Cloud Run próprio
se um dia ficar sério. Nada aqui toca catálogo/estado do amora.

    pip install -r eink/requirements.txt
    python eink/server.py                      # http://127.0.0.1:8300
    AMORA_URL=http://127.0.0.1:8000 python eink/server.py   # amora local

Endpoints:
    GET /            simulador no navegador (+ ?kiosk=1 pro Kindle)
    GET /map.png     o quadro 1-bit (mesmos parâmetros de render.py)
    GET /routes.json proxy do routes.json do amora (o simulador precisa
                     same-origin; o amora não manda CORS nesse arquivo)

Ver eink/README.md pro guia completo (hardware, API, sketch ESP32).
"""

import json
import math
import os
import threading
import time
import urllib.request
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

import render

HERE = Path(__file__).resolve().parent
AMORA_URL = (os.environ.get("AMORA_URL") or "https://amora.pedalhidrografi.co").rstrip("/")
PORT = int(os.environ.get("PORT") or 8300)

app = Flask(__name__)

# Cache curtinho do routes.json (muda raramente; não martelar o amora a cada
# refresh de 30 s do e-ink). Posições ao vivo NÃO são cacheadas (mudam sempre).
_routes_cache = {"ts": 0.0, "routes": []}
_routes_lock = threading.Lock()
ROUTES_TTL_S = 300


def _amora_get_json(path, timeout=6):
    req = urllib.request.Request(
        AMORA_URL + path, headers={"User-Agent": render.USER_AGENT})
    ctx = render._ssl_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_routes():
    with _routes_lock:
        if time.time() - _routes_cache["ts"] < ROUTES_TTL_S:
            return _routes_cache["routes"]
    try:
        routes = _amora_get_json("/routes.json").get("routes") or []
    except Exception:  # noqa: BLE001 — amora fora do ar → mapa sem rotas
        routes = _routes_cache["routes"]
    with _routes_lock:
        _routes_cache.update(ts=time.time(), routes=routes)
    return routes


def _get_peers():
    """Posições ao vivo do amora. Formato público: {positions:[{id, name,
    lat, lng, heading?, trail:[[lat,lng,acc,age],...]}]} — o renderizador só
    lê trail[i][0]/[1], então o layout público serve direto."""
    try:
        return _amora_get_json("/live-locations").get("positions") or []
    except Exception:  # noqa: BLE001
        return []


@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.get("/routes.json")
def routes_proxy():
    return jsonify(routes=_get_routes())


@app.get("/map.png")
def map_png():
    def fnum(name):
        v = request.args.get(name)
        try:
            f = float(v)
            return f if math.isfinite(f) else None
        except (TypeError, ValueError):
            return None

    w = int(fnum("w") or 400)
    h = int(fnum("h") or 300)
    lat, lng, z = fnum("lat"), fnum("lng"), fnum("z")
    route_slug = (request.args.get("route") or "").strip() or None
    follow_id = (request.args.get("follow") or "").strip() or None

    routes = _get_routes()
    peers = _get_peers()

    # Centro: follow > lat/lng explícito > enquadramento da rota.
    if follow_id:
        fl = follow_id.casefold()
        hit = next((p for p in peers
                    if p.get("id") == follow_id
                    or (p.get("name") or "").casefold() == fl), None)
        if hit:
            lat, lng = hit["lat"], hit["lng"]
            if z is None:
                z = 16
        elif lat is None and not route_slug:
            return jsonify(error=f"ninguém ao vivo como '{follow_id}'"), 404
    if (lat is None or lng is None) and route_slug:
        r = next((r for r in routes
                  if (r.get("tourIri") or "").rsplit("/", 1)[-1] == route_slug
                  and r.get("latlngs")), None)
        if r is None:
            return jsonify(error=f"rota '{route_slug}' não encontrada"), 404
        lat, lng, zfit = render.fit_route(
            r["latlngs"], min(w, render.MAX_W), min(h, render.MAX_H))
        if z is None:
            z = zfit
    if lat is None or lng is None:
        return jsonify(error="faltam lat/lng (ou route= ou follow=)"), 400

    base = request.args.get("base") or "osm"
    if base not in ("osm", "hydro", "none"):
        base = "osm"
    img = render.render_map(
        lat=lat, lng=lng, z=int(z if z is not None else 15), w=w, h=h,
        routes=routes, peers=peers,
        route_slug=route_slug, follow_id=follow_id,
        base=base,
        invert=request.args.get("invert") == "1",
        heading=fnum("heading"))
    fmt = "raw" if request.args.get("fmt") == "raw" else "png"
    body, mime = render.image_to_response_bytes(img, fmt)
    return Response(body, mimetype=mime, headers={
        "Cache-Control": "no-store",           # posições mudam toda hora
        "X-EPD-Width": str(img.width),
        "X-EPD-Height": str(img.height),
    })


if __name__ == "__main__":
    print(f"[eink] amora: {AMORA_URL}  ·  simulador: http://127.0.0.1:{PORT}/")
    app.run(host="0.0.0.0", port=PORT)
