#!/usr/bin/env python3
"""Tira os espaços em branco das cenas do projeto deitado SEM refazer a composição: cada clipe cresce (mantendo a proporção) só na
direção do vazio mais próximo dele, até a tela ficar coberta. Quem está por baixo na pilha cresce primeiro (não tampa ninguém).
  preenche.py <projeto> [--previa pasta] [--apply] [--teto 1.6]
Sem --apply só mede e (com --previa) grava um rascunho pra folha de contato. Clipes compostos não mudam."""
import copy, json, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut_layout import tamanho
args = [a for a in sys.argv[1:] if not a.startswith("--")]; proj = args[0]
opt = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PREVIA, TETO = opt("--previa"), float(opt("--teto", 1.6))
T = [p for p in sorted(os.listdir(proj + "/Timelines")) if os.path.isfile(f"{proj}/Timelines/{p}/draft_info.json") and open(f"{proj}/Timelines/{p}/draft_info.json", "rb").read() == open(proj + "/draft_info.json", "rb").read()]
assert len(T) == 1; T = f"{proj}/Timelines/{T[0]}"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig); CW, CH = d["canvas_config"]["width"], d["canvas_config"]["height"]
V = {m["id"]: m for m in d["materials"]["videos"]}
GX, GY = 192, round(192 * CH / CW); gx = (np.arange(GX) + 0.5) * CW / GX; gy = (np.arange(GY) + 0.5) * CH / GY
clipes = []
for ti, t in enumerate(d["tracks"]):
    if t["type"] != "video": continue
    for s in t["segments"]:
        m = V[s["material_id"]]; nm = os.path.basename(m["path"])
        if not re.match(r".+?_\d{4}-\d\d-\d\d", nm): continue               # só mídia de passeio (mapa, murais, logo e compostos ficam)
        c = s["clip"]; Wc, Hc = tamanho(m); fit = min(CW / Wc, CH / Hc); rot = round(c.get("rotation") or 0) % 180
        w, h = Wc * fit * c["scale"]["x"], Hc * fit * c["scale"]["y"]
        if rot: w, h = h, w
        a = s["target_timerange"]["start"]; clipes.append(dict(s=s, z=ti, a=a, b=a + s["target_timerange"]["duration"], cx=CW / 2 * (1 + c["transform"]["x"]), cy=CH / 2 * (1 - c["transform"]["y"]), w=w, h=h, w0=w, h0=h))
fixos = []                                                                 # o que cobre a tela mas não muda (compostos etc.): conta como coberto inteiro
for ti, t in enumerate(d["tracks"]):
    if t["type"] != "video": continue
    for s in t["segments"]:
        if not any(s is c["s"] for c in clipes): a = s["target_timerange"]["start"]; fixos.append((a, a + s["target_timerange"]["duration"]))
clipes.sort(key=lambda c: (c["a"], c["b"])); cenas, fim = [], -1
for c in clipes:
    if c["a"] >= fim: cenas.append([c]); fim = c["b"]
    else: cenas[-1].append(c); fim = max(fim, c["b"])
def vazio(ativos):
    cob = np.zeros((GY, GX), bool)
    for c in ativos:
        cob |= ((gx >= c["cx"] - c["w"] / 2) & (gx <= c["cx"] + c["w"] / 2))[None, :] & ((gy >= c["cy"] - c["h"] / 2) & (gy <= c["cy"] + c["h"] / 2))[:, None]
    return ~cob
def instantes(cena):
    ts = sorted({c["a"] for c in cena} | {c["b"] for c in cena}); return [(x + y) / 2 for x, y in zip(ts, ts[1:]) if y - x > 200000]
antes, depois, mexidos, tem_fixo = [], [], 0, 0
for cena in cenas:
    a0, b0 = cena[0]["a"], max(c["b"] for c in cena)
    if any(fa < b0 and a0 < fb for fa, fb in fixos): tem_fixo += 1; continue    # cena com clipe composto: o modelo não enxerga a tela toda
    ts = instantes(cena); dur = lambda t: 1.0
    med = lambda: float(np.mean([vazio([c for c in cena if c["a"] <= t < c["b"]]).mean() for t in ts])) if ts else 0.0
    antes.append((med(), a0 / 1e6))
    for _ in range(30):
        pede = {}
        for t in ts:
            at = [c for c in cena if c["a"] <= t < c["b"]]; vz = vazio(at)
            if not at or vz.mean() < 0.002: continue
            ys, xs = np.nonzero(vz); px, py = gx[xs], gy[ys]
            dist = np.stack([np.hypot(np.maximum(np.abs(px - c["cx"]) - c["w"] / 2, 0), np.maximum(np.abs(py - c["cy"]) - c["h"] / 2, 0)) + 0.015 * CW * k for k, c in enumerate(sorted(at, key=lambda c: c["z"]))])
            dono = dist.argmin(axis=0); ordenados = sorted(at, key=lambda c: c["z"])
            for k, c in enumerate(ordenados):
                m = dono == k
                if not m.any(): continue
                r = pede.setdefault(id(c), [c, c["cx"] - c["w"] / 2, c["cy"] - c["h"] / 2, c["cx"] + c["w"] / 2, c["cy"] + c["h"] / 2])
                r[1] = min(r[1], px[m].min() - CW / GX); r[2] = min(r[2], py[m].min() - CH / GY); r[3] = max(r[3], px[m].max() + CW / GX); r[4] = max(r[4], py[m].max() + CH / GY)
        if not pede: break
        mudou = False
        for c, x0, y0, x1, y1 in pede.values():
            s = max((x1 - x0) / c["w"], (y1 - y0) / c["h"]); s = min(s, 1.12, TETO * c["w0"] / c["w"])        # no máx. 12 % por volta, e o teto no total
            if s <= 1.001: continue
            nw, nh = c["w"] * s, c["h"] * s                                  # cresce cobrindo o alvo; onde sobra, fica centrado no alvo
            c["cx"] = min(max((x0 + x1) / 2, x1 - nw / 2), x0 + nw / 2) if nw >= x1 - x0 else c["cx"]
            c["cy"] = min(max((y0 + y1) / 2, y1 - nh / 2), y0 + nh / 2) if nh >= y1 - y0 else c["cy"]
            c["w"], c["h"] = nw, nh; mudou = True
        if not mudou: break
    depois.append((med(), a0 / 1e6))
    for c in cena:
        k = c["w"] / c["w0"]
        if k > 1.001 or abs(c["cx"] - CW / 2 * (1 + c["s"]["clip"]["transform"]["x"])) > 0.5 or abs(c["cy"] - CH / 2 * (1 - c["s"]["clip"]["transform"]["y"])) > 0.5:
            cl = c["s"]["clip"]; cl["scale"] = dict(x=cl["scale"]["x"] * k, y=cl["scale"]["y"] * k); cl["transform"] = dict(x=(c["cx"] - CW / 2) / (CW / 2), y=-(c["cy"] - CH / 2) / (CH / 2)); mexidos += 1
A = np.array([x[0] for x in antes]); D = np.array([x[0] for x in depois]); cresc = np.array([c["w"] / c["w0"] for c in clipes])
print(f"{len(cenas)} cenas ({tem_fixo} com clipe composto, não mexidas); tela em branco: média {A.mean():.1%} → {D.mean():.1%}; pior cena {A.max():.1%} → {D.max():.1%}; cenas com mais de 2 % em branco: {(A > 0.02).sum()} → {(D > 0.02).sum()}")
print(f"clipes mexidos: {mexidos} de {len(clipes)}; crescimento mediano dos mexidos {np.median(cresc[cresc > 1.001]) if (cresc > 1.001).any() else 1:.2f}×, máximo {cresc.max():.2f}× (teto {TETO}×)")
print("piores antes:", [f"{t:.0f}s {v:.0%}" for v, t in sorted(antes, reverse=True)[:10]]); print("piores depois:", [f"{t:.0f}s {v:.0%}" for v, t in sorted(depois, reverse=True)[:6]])
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
chk = json.loads(out); OS = {s["id"]: s for t in orig["tracks"] for s in t["segments"]}
for t in chk["tracks"]:
    for s in t["segments"]:
        if t["type"] == "video": s["clip"]["scale"] = OS[s["id"]]["clip"]["scale"]; s["clip"]["transform"] = OS[s["id"]]["clip"]["transform"]
assert chk == orig, "mudou mais do que devia"
if PREVIA: os.makedirs(PREVIA, exist_ok=True); open(PREVIA + "/draft_info.json", "wb").write(out)
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw
    for p in alvos: open(p, "wb").write(out)
    print("gravado em", len(alvos), "arquivos")
