"""Renderizador de mapa 1-bit pro navegador e-ink de guidão (DIY).

Filosofia: dispositivos e-ink DIY (ESP32 + Waveshare/LilyGO) são péssimos em
rodar mapas mas ótimos em desenhar um framebuffer pronto. Então o SERVIDOR
renderiza o quadro (tiles OSM ditherizados + hidrografia + rotas + pessoas ao
vivo + HUD) e o dispositivo só faz GET e blita. O telefone da ciclista é o GPS:
ela liga o "Localização ao vivo" no amora (funciona com a tela apagada via
shell nativo) e o dispositivo pede o mapa com `?follow=<apelido>` — zero
hardware de GPS no guidão.

Este módulo é PURO desenho: server.py coleta rotas (routes.json) + posições ao
vivo e chama render_map(). Nada aqui toca catálogo/estado — só uma cache
in-process de tiles (read-only, com lock próprio).

Ver eink/README.md pro guia completo (hardware, API, sketch ESP32).
"""

from __future__ import annotations

import io
import math
import threading
import urllib.request
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

TILE_SIZE = 256
OSM_TILE = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
HYDRO_TILE = "https://telhas.pedalhidrografi.co/rmsampa-v2/{z}/{x}/{y}.png"
USER_AGENT = "amora-eink/1.0 (+https://amora.pedalhidrografi.co/eink.html)"
LOCAL_TZ = timezone(timedelta(hours=-3))   # São Paulo, sem DST desde 2019

# Limites defensivos (sem auth por design — só sanidade de parâmetros).
MAX_W, MAX_H = 1600, 1600
MIN_Z, MAX_Z = 3, 19
MAX_TILES_PER_RENDER = 80

# Cache LRU de tiles (bytes PNG) — e-ink pede o mesmo enquadramento a cada
# 30-60 s, então a taxa de acerto é alta. ~256 tiles ≈ poucos MB.
_tile_cache: OrderedDict[str, bytes | None] = OrderedDict()
_tile_cache_lock = threading.Lock()
TILE_CACHE_MAX = 256


def _merc_px(lat, lng, z):
    """(lat, lng) → pixel global Web-Mercator no zoom z (tiles de 256 px)."""
    lat = max(-85.05112878, min(85.05112878, lat))
    n = 2.0 ** z * TILE_SIZE
    x = (lng + 180.0) / 360.0 * n
    sin = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin) / (1 - sin)) / (4 * math.pi)) * n
    return x, y


def _meters_per_px(lat, z):
    return 156543.03392 * math.cos(math.radians(lat)) / (2.0 ** z)


def _ssl_context():
    """Contexto TLS: sistema primeiro; se o trust store local estiver quebrado
    (Python de macOS sem 'Install Certificates.command'), cai pro certifi."""
    import ssl
    ctx = ssl.create_default_context()
    try:
        if ctx.cert_store_stats().get("x509_ca", 0) == 0:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        pass
    return ctx


_SSL_CTX = None


def _fetch_tile_bytes(url):
    """GET de um tile com cache LRU. Falha (timeout/404) cacheia None — não
    martela o servidor de tiles a cada refresh do e-ink."""
    global _SSL_CTX
    with _tile_cache_lock:
        if url in _tile_cache:
            _tile_cache.move_to_end(url)
            return _tile_cache[url]
    if _SSL_CTX is None:
        _SSL_CTX = _ssl_context()
    data = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4, context=_SSL_CTX) as resp:
            data = resp.read()
    except Exception:  # noqa: BLE001 — tile ausente/offline → fundo branco
        data = None
    with _tile_cache_lock:
        _tile_cache[url] = data
        while len(_tile_cache) > TILE_CACHE_MAX:
            _tile_cache.popitem(last=False)
    return data


def _load_font(size):
    """DejaVu se existir no sistema; senão o bitmap embutido do Pillow
    (load_default aceita `size` no Pillow ≥ 10.1; fallback pro fixo)."""
    from PIL import ImageFont
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fit_zoom(bbox, w, h, pad_px=24):
    """Zoom inteiro que enquadra o bbox (latmin,lngmin,latmax,lngmax)."""
    latmin, lngmin, latmax, lngmax = bbox
    for z in range(MAX_Z, MIN_Z - 1, -1):
        x0, y1 = _merc_px(latmin, lngmin, z)
        x1, y0 = _merc_px(latmax, lngmax, z)
        if abs(x1 - x0) <= w - 2 * pad_px and abs(y1 - y0) <= h - 2 * pad_px:
            return z
    return MIN_Z


def _nice_scale(meters_max):
    """Maior distância "redonda" que cabe (p/ a barra de escala)."""
    for m in (50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10):
        if m <= meters_max:
            return m
    return 10


def render_map(*, lat, lng, z, w, h, routes, peers,
               route_slug=None, follow_id=None,
               base="osm", invert=False, heading=None,
               pan_x=0, pan_y=0):
    """Renderiza o quadro 1-bit. Retorna PIL.Image mode '1'.

    routes: lista de entradas do routes.json ({tourIri, name, latlngs, pois}).
    peers:  lista de posições ao vivo ({id, name, lat, lng, heading?, trail}).
    base:   'osm' (ruas) | 'hydro' (o raster de hidrografia do telhas — que é
            um BASEMAP opaco, como no seletor de camadas do app, não um
            overlay) | 'none' (fundo branco, só vetores — render instantâneo).
    pan_x/pan_y: desloca o viewport em PIXELS (direita/baixo positivos) DEPOIS
            do centro resolvido — funciona em qualquer modo. Ex.: follow com
            pan_y=-h*0.3 = "look-ahead" (mais mapa à frente do que atrás).
    """
    from PIL import Image, ImageDraw

    w = max(64, min(MAX_W, int(w)))
    h = max(64, min(MAX_H, int(h)))
    z = max(MIN_Z, min(MAX_Z, int(z)))

    # Canto superior-esquerdo do viewport em pixels globais (+ pan, limitado a
    # ±2 viewports pra URL não conseguir pedir tile do outro lado do mundo).
    cx, cy = _merc_px(lat, lng, z)
    pan_x = max(-2 * w, min(2 * w, int(pan_x or 0)))
    pan_y = max(-2 * h, min(2 * h, int(pan_y or 0)))
    ox, oy = cx - w / 2 + pan_x, cy - h / 2 + pan_y

    def to_px(la, ln):
        x, y = _merc_px(la, ln, z)
        return x - ox, y - oy

    # ── Base raster em cinza, ditherizada pra 1-bit ───────────────────────
    img_l = Image.new("L", (w, h), 255)
    tx0, ty0 = int(ox // TILE_SIZE), int(oy // TILE_SIZE)
    tx1, ty1 = int((ox + w) // TILE_SIZE), int((oy + h) // TILE_SIZE)
    n_tiles = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    max_tile = 2 ** z - 1
    if base in ("osm", "hydro") and n_tiles <= MAX_TILES_PER_RENDER:
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                if not (0 <= tx <= max_tile and 0 <= ty <= max_tile):
                    continue
                if base == "hydro":
                    url = HYDRO_TILE.format(z=z, x=tx, y=ty)
                else:
                    sub = "abc"[(tx + ty) % 3]
                    url = OSM_TILE.format(s=sub, z=z, x=tx, y=ty)
                data = _fetch_tile_bytes(url)
                if not data:
                    continue
                try:
                    tile = Image.open(io.BytesIO(data))
                    if tile.mode in ("RGBA", "LA", "P"):
                        # Achata alpha sobre branco antes do grayscale.
                        rgba = tile.convert("RGBA")
                        flat = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        flat.alpha_composite(rgba)
                        tile = flat
                    tile = tile.convert("L")
                except Exception:  # noqa: BLE001
                    continue
                img_l.paste(tile, (int(tx * TILE_SIZE - ox),
                                   int(ty * TILE_SIZE - oy)))
        # Clareia o fundo antes do dither: basemaps têm muito cinza-claro que
        # vira ruído no e-ink; um ponto de gama derruba isso e mantém o traço.
        img_l = img_l.point(lambda v: min(255, int((v / 255) ** 0.32 * 255)))

    if min(w, h) < 180:
        # Painel minúsculo (2.9"/2.13"): dither vira sopa de ruído nessa
        # densidade — limiar duro preserva só o traço (ruas/rotulagem escura).
        img = img_l.point(lambda v: 255 if v > 140 else 0).convert("1")
    else:
        img = img_l.convert("1")       # Floyd–Steinberg (default do Pillow)
    draw = ImageDraw.Draw(img)

    # Fator de escala dos elementos vetoriais: os tamanhos abaixo foram
    # afinados pra 400×300; em painéis maiores (T5 960×540) um marcador de
    # 13 px some, e em menores (2.9" 296×128) sobra. Escala pelo lado menor.
    s = max(0.75, min(w, h) / 300.0)

    # ── Rotas (vetor puro, DEPOIS do dither → preto sólido) ──────────────
    def draw_polyline(latlngs, width, halo=True):
        pts = [to_px(p[0], p[1]) for p in latlngs]
        pts = [(x, y) for (x, y) in pts
               if -50 <= x <= w + 50 and -50 <= y <= h + 50] or None
        if not pts or len(pts) < 2:
            return
        width = max(1, round(width * s))
        if halo:
            draw.line(pts, fill=1, width=width + max(2, round(4 * s)), joint="curve")
        draw.line(pts, fill=0, width=width, joint="curve")

    # Com route= o quadro é DAQUELA rota: as outras somem (num overview de 1-bit
    # o acervo inteiro vira espaguete). Sem route=, desenha todas (contexto).
    focused = None
    for r in routes:
        if not r.get("latlngs"):
            continue
        slug = (r.get("tourIri") or "").rsplit("/", 1)[-1]
        if route_slug:
            if slug == route_slug:
                focused = r
        else:
            draw_polyline(r["latlngs"], 2, halo=False)
    if focused:
        draw_polyline(focused["latlngs"], 5)
        # POIs da rota focada: losango.
        d5 = 5 * s
        for poi in (focused.get("pois") or []):
            x, y = to_px(poi["lat"], poi["lng"])
            if not (0 <= x <= w and 0 <= y <= h):
                continue
            draw.polygon([(x, y - d5), (x + d5, y), (x, y + d5), (x - d5, y)],
                         fill=1, outline=0)

    # ── Pessoas ao vivo ───────────────────────────────────────────────────
    f_peer = _load_font(max(9, round(13 * s)))
    followed = None
    for p in peers:
        if follow_id and (p.get("id") == follow_id
                          or (p.get("name") or "").casefold() == follow_id.casefold()):
            followed = p
            continue
        x, y = to_px(p["lat"], p["lng"])
        if not (-10 <= x <= w + 10 and -10 <= y <= h + 10):
            continue
        r8 = 8 * s
        draw.ellipse([x - r8, y - r8, x + r8, y + r8], fill=1, outline=0,
                     width=max(2, round(2 * s)))
        initial = ((p.get("name") or "?")[:1] or "?").upper()
        draw.text((x, y - 1), initial, fill=0, font=f_peer, anchor="mm")

    # A pessoa seguida: rastro pontilhado + seta de rumo (por último, por cima).
    if followed:
        trail = followed.get("trail") or []
        r_dot = 2.5 * s
        for pt in trail[-200::2]:      # pontilhado barato: 1 a cada 2 pontos
            x, y = to_px(pt[0], pt[1])
            if 0 <= x <= w and 0 <= y <= h:
                draw.ellipse([x - r_dot, y - r_dot, x + r_dot, y + r_dot],
                             fill=0, outline=1)
        x, y = to_px(followed["lat"], followed["lng"])
        hd = followed.get("heading", heading)
        if hd is not None and math.isfinite(float(hd)):
            a = math.radians(float(hd))

            def _tri(rt, rw):
                tip = (x + rt * math.sin(a), y - rt * math.cos(a))
                left = (x + rw * math.sin(a + 2.5), y - rw * math.cos(a + 2.5))
                right = (x + rw * math.sin(a - 2.5), y - rw * math.cos(a - 2.5))
                return [tip, left, (x, y), right]
            # Halo: um triângulo branco MAIOR por baixo (outline com width
            # comeria o preenchimento numa seta pequena), seta preta sólida
            # por cima.
            pad = 4 * s
            draw.polygon(_tri(13 * s + pad, 9 * s + pad), fill=1)
            draw.polygon(_tri(13 * s, 9 * s), fill=0)
        else:
            r9, r4 = 9 * s, 4 * s
            draw.ellipse([x - r9, y - r9, x + r9, y + r9], fill=0)
            draw.ellipse([x - r4, y - r4, x + r4, y + r4], fill=1)

    # ── HUD: barra inferior com hora, escala e norte ──────────────────────
    hud_h = max(18, h // 18)
    f_hud = _load_font(max(11, hud_h - 6))
    draw.rectangle([0, h - hud_h, w, h], fill=1)
    draw.line([(0, h - hud_h), (w, h - hud_h)], fill=0, width=1)
    now_txt = datetime.now(LOCAL_TZ).strftime("%H:%M")
    label = f"amora · {now_txt}"
    if followed:
        label += f" · {followed.get('name') or 'ao vivo'}"
    n_peers = len(peers)
    if n_peers:
        label += f" · {n_peers} ao vivo"
    draw.text((4, h - hud_h / 2), label, fill=0, font=f_hud, anchor="lm")
    # Barra de escala (direita).
    mpp = _meters_per_px(lat, z)
    scale_m = _nice_scale(mpp * w / 4)
    bar_px = scale_m / mpp
    bx1 = w - 6
    bx0 = bx1 - bar_px
    by = h - hud_h / 2 + 3
    draw.line([(bx0, by), (bx1, by)], fill=0, width=2)
    draw.line([(bx0, by - 4), (bx0, by)], fill=0, width=2)
    draw.line([(bx1, by - 4), (bx1, by)], fill=0, width=2)
    stxt = f"{scale_m} m" if scale_m < 1000 else f"{scale_m // 1000} km"
    draw.text(((bx0 + bx1) / 2, by - 6), stxt, fill=0, font=f_hud, anchor="mb")
    # Atribuição OSM (obrigatória quando usamos os tiles).
    if base == "osm":
        f_attr = _load_font(9)
        draw.text((w - 3, h - hud_h - 2), "© OpenStreetMap", fill=0,
                  font=f_attr, anchor="rb")

    if invert:
        from PIL import ImageOps
        img = ImageOps.invert(img.convert("L")).convert("1")
    return img


def image_to_response_bytes(img, fmt):
    """PNG (qualquer cliente) ou framebuffer cru (ESP32 blita direto).

    fmt='raw': linhas MSB-first, cada linha ceil(w/8) bytes, bit 1 = branco —
    o layout dos buffers Waveshare/GxEPD2. Sem header; dimensões vão em
    headers HTTP (X-EPD-Width/Height).
    """
    if fmt == "raw":
        return img.tobytes(), "application/octet-stream"
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), "image/png"


def route_bbox(latlngs):
    lats = [p[0] for p in latlngs]
    lngs = [p[1] for p in latlngs]
    return min(lats), min(lngs), max(lats), max(lngs)


def fit_route(latlngs, w, h):
    """(lat, lng, z) que enquadra a rota no viewport."""
    latmin, lngmin, latmax, lngmax = route_bbox(latlngs)
    return ((latmin + latmax) / 2, (lngmin + lngmax) / 2,
            _fit_zoom((latmin, lngmin, latmax, lngmax), w, h))
