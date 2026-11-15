#!/usr/bin/env python3
"""Mural das artes de anúncio em RETRATO (1080×1350): 3 colunas (NC), mais novas em cima, rolando pra CIMA em 19 deslizes, um a cada meio
segundo (10 s, 60 BPM). O metrônomo e as trilhas marcam só os deslizes que caem no segundo inteiro (1…9 s): reconhecem o arquivo pelo "-4x5".
  mural45.py <pasta de cache com art-all/ e tours.ttl> <saida.mp4>"""
import hashlib, os, subprocess, sys
import rdflib
from PIL import Image
C, out = sys.argv[1], sys.argv[2]
import os as _os
W, H, FPS, TOTAL, GAP, NC, MOVE = 1080, 1350, 30, 10.0, 6, int(_os.environ.get("NC", 3)), 0.25     # NC = nº de colunas; 0,25 s de deslize + 0,25 s parado
INICIOS = [k / 2 for k in range(1, 20)]                                 # um deslize a cada MEIO segundo (0,5…9,5 s): passo menor que a tela, nada é pulado
g = rdflib.Graph(); g.parse(f"{C}/tours.ttl", format="turtle")
PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#"); DC = rdflib.URIRef("http://purl.org/dc/terms/date")
rows = []
for t in set(g.subjects(rdflib.RDF.type, PH.Tour)):
    u = [str(o) for p in ("http://schema.org/image", "https://schema.org/image") for o in g.objects(t, rdflib.URIRef(p))]
    f = f"{C}/art-all/{hashlib.md5(u[0].encode()).hexdigest()[:12]}.img" if u else None
    if f and os.path.exists(f): rows.append((str(next(g.objects(t, DC), "")), f))
rows.sort(reverse=True)
LW = (W - GAP * (NC - 1)) // NC; x0 = (W - (LW * NC + GAP * (NC - 1))) // 2
cols = [[] for _ in range(NC)]; alt = [0] * NC
for _, f in rows:                                                       # cada arte vai pra coluna mais curta: ordem ~cronológica de cima pra baixo
    im = Image.open(f).convert("RGB"); im = im.resize((LW, round(im.height * LW / im.width)), Image.LANCZOS)
    k = alt.index(min(alt)); cols[k].append((alt[k], im)); alt[k] += im.height + GAP
th = max(alt) - GAP; mural = Image.new("RGB", (W, th))
for k, c in enumerate(cols):                                            # colunas justificadas na altura da maior
    extra = (th - (alt[k] - GAP)) / max(1, len(c) - 1)
    for j, (y0, im) in enumerate(c): mural.paste(im, (x0 + k * (LW + GAP), round(y0 + j * extra)))
travel = th - H; NS = len(INICIOS)
def pos(t):
    k = sum(t >= s + MOVE for s in INICIOS); u = next(((t - s) / MOVE for s in INICIOS if s <= t < s + MOVE), 0.0)
    return travel * (k + u * u * u * (u * (u * 6 - 15) + 10)) / NS
maior = max(im.height for c in cols for _, im in c)
print(f"{len(rows)} artes em {NC} colunas de {LW} px; mural de {th} px; {NS} deslizes de {travel / NS:.0f} px ({travel / NS / H:.0%} da tela); "
      f"{'toda arte aparece parada' if travel / NS <= H - maior else 'ATENÇÃO: alguma arte só aparece em movimento'}")
paradas = [k * travel / NS for k in range(NS + 1)]                       # quantas artes ficam inteiras na tela em alguma pausa
inteiras = sum(any(p <= round(y0 + j * ((th - (alt[k] - GAP)) / max(1, len(c) - 1))) and round(y0 + j * ((th - (alt[k] - GAP)) / max(1, len(c) - 1))) + im.height <= p + H for p in paradas) for k, c in enumerate(cols) for j, (y0, im) in enumerate(c))
print(f"artes vistas inteiras e paradas: {inteiras} de {len(rows)}")
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
                       "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for i in range(round(TOTAL * FPS)):
    ff.stdin.write(mural.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, min(pos(i / FPS), travel)), resample=Image.BICUBIC).tobytes())
ff.stdin.close(); sys.exit(ff.wait())
