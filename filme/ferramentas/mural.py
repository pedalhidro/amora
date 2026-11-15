#!/usr/bin/env python3
"""Mural das artes de anúncio (todas as do catálogo, mais novas à esquerda) em NR fileiras, 10 s a 60 BPM:
parado, com 5 deslizes que começam nos segundos 1, 3, 5, 7 e 9.
  mural.py <pasta de cache> <saida.mp4> [fileiras=3] [s por deslize=0.5]"""
import collections, hashlib, json, os, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
import rdflib
from PIL import Image
C, out = sys.argv[1], sys.argv[2]
NR = int(sys.argv[3]) if len(sys.argv) > 3 else 3
MOVE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
W, H, FPS, TOTAL, GAP = 1920, 1080, 30, 10.0, 6
INICIOS = [1.0, 3.0, 5.0, 7.0, 9.0]
UA = {"User-Agent": "Mozilla/5.0 (art-wall)"}
os.makedirs(f"{C}/art-all", exist_ok=True)
ttl = f"{C}/tours.ttl"
if not os.path.exists(ttl):
    open(ttl, "wb").write(urllib.request.urlopen(urllib.request.Request("https://amora.pedalhidrografi.co/data/tours.ttl", headers=UA), timeout=60).read())
g = rdflib.Graph(); g.parse(ttl, format="turtle")
PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#"); DC = rdflib.URIRef("http://purl.org/dc/terms/date")
rows = []
for t in set(g.subjects(rdflib.RDF.type, PH.Tour)):
    u = [str(o) for p in ("http://schema.org/image", "https://schema.org/image") for o in g.objects(t, rdflib.URIRef(p))]
    if u: rows.append(dict(date=str(next(g.objects(t, DC), "")), url=u[0]))
rows.sort(key=lambda r: r["date"], reverse=True)
def pega(r):
    dst = f"{C}/art-all/{hashlib.md5(r['url'].encode()).hexdigest()[:12]}.img"
    if not os.path.exists(dst):
        for cand in (r["url"].rsplit(".", 1)[0] + ".web.jpg", r["url"]):
            if "storage.googleapis.com/phidro-state/" not in cand and cand != r["url"]: continue
            try:
                open(dst + ".part", "wb").write(urllib.request.urlopen(urllib.request.Request(cand, headers=UA), timeout=60).read()); os.replace(dst + ".part", dst); break
            except Exception as e: r["err"] = f"{cand[-40:]}: {e}"
    try: Image.open(dst).size; r["file"] = dst
    except Exception as e: r["err"] = f"{r.get('err', '')} {e}"
    return r
with ThreadPoolExecutor(8) as ex: rows = list(ex.map(pega, rows))
print(len(rows), "artes no catálogo; falhas:", [(r["date"][:10], r.get("err")) for r in rows if not r.get("file")])
rows = [r for r in rows if r.get("file")]
RH = (H - GAP * (NR - 1)) // NR; top = (H - (RH * NR + GAP * (NR - 1))) // 2
fileiras = [[] for _ in range(NR)]; comp = [0] * NR
for r in rows:                                               # cada arte vai pra fileira mais curta: ordem ~cronológica, fileiras parelhas
    im = Image.open(r["file"]).convert("RGB"); im = im.resize((round(im.width * RH / im.height), RH), Image.LANCZOS)
    k = comp.index(min(comp)); fileiras[k].append((comp[k], im)); comp[k] += im.width + GAP
tw = max(comp) - GAP                                         # todas as fileiras justificadas no comprimento da maior
mural = Image.new("RGB", (tw, H))
for k, f in enumerate(fileiras):
    extra = (tw - (comp[k] - GAP)) / max(1, len(f) - 1)
    for j, (x0, im) in enumerate(f): mural.paste(im, (round(x0 + j * extra), top + k * (RH + GAP)))
n = round(TOTAL * FPS); travel = tw - W; NS = len(INICIOS)
def pos(t):
    k = sum(t >= s + MOVE for s in INICIOS)                  # deslizes já completos
    u = next(((t - s) / MOVE for s in INICIOS if s <= t < s + MOVE), 0.0)
    return travel * (k + u * u * u * (u * (u * 6 - 15) + 10)) / NS     # smootherstep
xs = [pos(i / FPS) for i in range(n)]
d = [b - a for a, b in zip(xs, xs[1:])]
print(f"{len(rows)} artes, {[len(f) for f in fileiras]} por fileira, fileira de {RH} px; mural de {tw} px; {NS} deslizes de {travel / NS:.0f} px em {MOVE} s "
      f"(pico {max(d):.0f} px/quadro); {'toda arte aparece parada' if travel / NS <= W - max(im.width for f in fileiras for _, im in f) else 'ATENÇÃO: alguma arte só aparece em movimento'}")
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for x in xs: ff.stdin.write(mural.transform((W, H), Image.AFFINE, (1, 0, min(x, travel), 0, 1, 0), resample=Image.BICUBIC).tobytes())
ff.stdin.close(); sys.exit(ff.wait())
