#!/usr/bin/env python3
"""PoC: vídeo do mapa (Topografia Colorida) destacando a rota de cada passeio no tempo em que
ele aparece no projeto do CapCut. Lê schedule.json (feito por schedule.py) + routes.json.

  render.py <dir> --still 5.0 12.0 …   → PNGs de conferência
  render.py <dir> --out mapa.mp4       → o vídeo inteiro
"""
import argparse, io, json, math, os, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, SS = 1920, 1080, 2            # quadro final e superamostragem
ZOOM = 12.1                          # zoom do quadro final (fracionário)
UA = "Mozilla/5.0 (map-render-poc)"
TOPO = "https://telhas.pedalhidrografi.co/rmsampa-v2/{z}/{x}/{y}.png"
OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TOPO_OPACITY = 0.85                  # como no amora
DRAW_FRAC = 0.7                      # a rota termina de ser desenhada em 70 % do tempo dela
FADE = 0.2                           # s de fade de entrada/saída do destaque


def merc(lat, lon, z):
    s = 256 * 2 ** z
    x = (lon + 180) / 360 * s
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * s
    return x, y


def tile(url, z, x, y, cache):
    p = f"{cache}/{'topo' if 'telhas' in url else 'osm'}-{z}-{x}-{y}.png"
    if os.path.exists(p):
        return Image.open(p).convert("RGBA") if os.path.getsize(p) else None
    try:
        req = urllib.request.Request(url.format(z=z, x=x, y=y), headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=30).read()
        open(p, "wb").write(data)
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        if getattr(e, "code", None) == 404:
            open(p, "wb").close()
        else:
            print("tile falhou", z, x, y, e, file=sys.stderr)
        return None


def mosaic(url, tz, cx, cy, zview, cache, mode):
    """Mosaico dos tiles do zoom inteiro `tz` cobrindo a vista (centro cx,cy em px do zview), já
    reamostrado pro tamanho superamostrado."""
    f = 2 ** (tz - zview)            # px do zview → px do tz
    ww, hh = W * SS, H * SS
    x0, y0 = (cx - ww / 2) * f, (cy - hh / 2) * f
    x1, y1 = (cx + ww / 2) * f, (cy + hh / 2) * f
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    big = Image.new(mode, ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (0, 0, 0, 0))
    jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
    with ThreadPoolExecutor(8 if "telhas" in url else 2) as ex:
        for (x, y), im in zip(jobs, ex.map(lambda j: tile(url, tz, j[0], j[1], cache), jobs)):
            if im:
                big.paste(im, ((x - tx0) * 256, (y - ty0) * 256))
    box = (x0 - tx0 * 256, y0 - ty0 * 256, x1 - tx0 * 256, y1 - ty0 * 256)
    return big.resize((ww, hh), Image.LANCZOS, box=box)


def stroke(d, pts, fill, width):
    if len(pts) < 2:
        return
    d.line(pts, fill=fill, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def partial(pts, cum, frac):
    """Prefixo da polilinha até a fração `frac` do comprimento; devolve (pontos, ponta)."""
    if frac >= 1:
        return pts, pts[-1]
    alvo = cum[-1] * frac
    out = [pts[0]]
    for i in range(1, len(pts)):
        if cum[i] >= alvo:
            seg = cum[i] - cum[i - 1]
            u = (alvo - cum[i - 1]) / seg if seg else 0
            p = (pts[i - 1][0] + u * (pts[i][0] - pts[i - 1][0]), pts[i - 1][1] + u * (pts[i][1] - pts[i - 1][1]))
            out.append(p)
            return out, p
        out.append(pts[i])
    return out, out[-1]


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--still", nargs="*", type=float)
    ap.add_argument("--out")
    a = ap.parse_args()
    S = a.dir
    cache = f"{S}/tiles"
    os.makedirs(cache, exist_ok=True)
    sc = json.load(open(f"{S}/schedule.json"))
    todas = json.load(open(f"{S}/../routes.json"))["routes"]
    fps = sc["fps"]
    nframes = round(sc["duration"] * fps / 1e6)

    # vista fixa: caixa de todas as rotas do vídeo
    lats = [p[0] for t in sc["tours"] for p in t["latlngs"]]
    lons = [p[1] for t in sc["tours"] for p in t["latlngs"]]
    zv = ZOOM + math.log2(SS)
    ax, ay = merc(max(lats), min(lons), zv)
    bx, by = merc(min(lats), max(lons), zv)
    cx, cy = (ax + bx) / 2, (ay + by) / 2
    ox, oy = cx - W * SS / 2, cy - H * SS / 2

    def proj(latlngs):
        return [(merc(la, lo, zv)[0] - ox, merc(la, lo, zv)[1] - oy) for la, lo in latlngs]

    # ── base: OSM + topografia a 85 % + todas as rotas do coletivo, fininhas ──
    basep = f"{S}/base.png"
    if os.path.exists(basep):
        base = Image.open(basep).convert("RGB")
    else:
        osm = mosaic(OSM, 12, cx, cy, zv, cache, "RGBA")
        topo = mosaic(TOPO, 13, cx, cy, zv, cache, "RGBA")
        fundo = Image.new("RGBA", osm.size, (40, 40, 40, 255))
        fundo.alpha_composite(osm)
        topo.putalpha(topo.getchannel("A").point(lambda v: int(v * TOPO_OPACITY)))
        fundo.alpha_composite(topo)
        base = fundo.convert("RGB").point(lambda v: int(v * 0.8))      # escurece 20 %: o destaque salta
        lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for r in todas:
            if r.get("latlngs"):
                stroke(d, proj(r["latlngs"]), (255, 255, 255, 90), 2 * SS)
        base = Image.alpha_composite(base.convert("RGBA"), lay).convert("RGB")
        base.save(basep)

    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 26 * SS, index=1)
    tours = []
    for t in sc["tours"]:
        pts = proj(t["latlngs"])
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + math.dist(pts[i], pts[i - 1]))
        a0, b0 = min(s[0] for s in t["spans"]), max(s[1] for s in t["spans"])
        serie, num = t["label"].split("/")
        tours.append(dict(pts=pts, cum=cum, a=a0 / 1e6, b=b0 / 1e6, label=f"{serie} {num}"))

    done = {"n": -1, "img": None}

    def visited(t):
        """base + rotas dos passeios que já passaram (acesas, sem destaque); cacheada por conjunto."""
        fim = [T for T in tours if T["b"] <= t]
        if len(fim) != done["n"]:
            lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            for T in fim:
                stroke(d, T["pts"], (255, 255, 255, 215), 3 * SS)
            done["img"] = Image.alpha_composite(base.convert("RGBA"), lay)
            done["n"] = len(fim)
        return done["img"]

    def frame(i):
        t = i / fps
        im = visited(t).copy()
        ativos = [T for T in tours if T["a"] <= t < T["b"]]
        if ativos:
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            pontas = []
            for T in ativos:
                dur = T["b"] - T["a"]
                alpha = min(1.0, (t - T["a"] + 1 / fps) / FADE, max(0.0, (T["b"] - t)) / FADE + 0.35)
                A = int(255 * alpha)
                # o traçado inteiro, fraco, pra rota já "existir"; por cima, o trecho percorrido
                stroke(d, T["pts"], (0, 0, 0, int(A * 0.45)), 7 * SS)
                stroke(d, T["pts"], (255, 255, 255, int(A * 0.45)), 3 * SS)
                sub, ponta = partial(T["pts"], T["cum"], ease((t - T["a"]) / (dur * DRAW_FRAC)))
                stroke(d, sub, (0, 0, 0, A), 13 * SS)
                stroke(d, sub, (255, 240, 60, A), 7 * SS)
                pontas.append((T, ponta, A))
            for T, (px, py), A in pontas:
                r = 9 * SS
                d.ellipse((px - r, py - r, px + r, py + r), fill=(255, 255, 255, A), outline=(0, 0, 0, A), width=3 * SS)
                # rótulo: acima do ponto mais alto da rota, preso ao quadro
                top = min(T["pts"], key=lambda p: p[1])
                tw = d.textlength(T["label"], font=font)
                lx = min(max(top[0] - tw / 2, 12 * SS), W * SS - tw - 12 * SS)
                ly = max(top[1] - 44 * SS, 8 * SS)
                d.text((lx, ly), T["label"], font=font, fill=(255, 255, 255, A), stroke_width=4 * SS, stroke_fill=(0, 0, 0, A))
            im.alpha_composite(lay)
        return im.convert("RGB").resize((W, H), Image.LANCZOS)

    if a.still is not None:
        for t in a.still:
            frame(round(t * fps)).save(f"{S}/still-{t:05.2f}.jpg", quality=88)
        return
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(int(fps)), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for i in range(nframes):
        ff.stdin.write(frame(i).tobytes())
        if i % 150 == 0:
            print(f"quadro {i}/{nframes}", flush=True)
    ff.stdin.close()
    sys.exit(ff.wait())


if __name__ == "__main__":
    main()
