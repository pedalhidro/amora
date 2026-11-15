#!/usr/bin/env python3
"""Trilha em camadas feita com o SOM DOS PRÓPRIOS VÍDEOS — versão ESCURA (ré menor, tudo grave e abafado; a clara está em musica3-claro.py).
Contemplativa: nada rítmico além do
clique do metrônomo, nada que suba ou comemore. Mesma estrutura das outras:
  trem      o ronco do trem afinado na nota do baixo, contínuo: parado no ré durante o mapa, depois DESCE um grau por trimestre até o ré do mural;
            respira a cada passeio que entra (um seno discreto por baixo garante a nota)
  agua      córregos passados por ressonadores afinados no acorde: a água "canta" a harmonia
  passeios  uma gota afinada por passeio (estalo de água num ressonador; pedal mais longo = nota mais grave), com eco
  multidao  o ato/protesto: 3, 2, 1 golpes na virada de cada ano (contagem regressiva) e a chegada no mural
  vento     o vento cresce antes de cada trimestre (mais antes de cada ano e do mural)
  A cada ano a textura esvazia; no mural volta tudo.
  musica3.py <draft_info.json> <routes.json> <pasta de saída> [metronomo.wav]"""
import sys, json, os, re, wave, math, subprocess, collections, numpy as np
from scipy.signal import fftconvolve, lfilter, butter, sosfilt, iirpeak
SR = 48000; rng = np.random.default_rng(1929)
MIDIA = os.path.expanduser("~/Downloads/1110-midia/AmoraVideos/")
FONTES = dict(
    agua=["PH-075_2026-01-28_a3043805_360p.webm", "BT-002_2025-01-19_c882a0c0_360p.webm", "PH-028_2025-03-11_a409c810_360p.webm",
          "PH-S-004_2025-06-01_1516_fda7d966_720p.mp4", "PH-065_2025-11-11_93667899_360p.webm", "PH-008_2024-10-24_2030_f199c7cc_360p.webm"],
    vento=["PH-043_2025-07-01_2129_d01772c1_720p.mp4", "PH-024_2025-01-28_2042_d880a001_360p.webm", "PH-113_2026-09-25_2229_d4c33cc3_720p.webm",
           "PH-005_2024-10-08_2114_822a0da6_360p.webm", "PH-015_2024-11-23_1134_d38124c0_360p.webm"],
    trem=["PH-113_2026-09-25_2150_e6b811f3_360p.webm"], multidao=["Pedalula-002_2026-10-24_c288d4b6_360p.webm"])
D2 = 73.416; DOR = [0, 2, 3, 5, 7, 8, 10]                                # ré menor natural (eólio)
ACORDE = {0: [0, 3, 7], 1: [2, 7, 0], 2: [3, 7, 0], 3: [5, 8, 0], 4: [7, 10, 2], 5: [8, 0, 5], 6: [10, 2, 7]}   # menores (ou quartas) sobre cada grau do baixo
grau_hz = lambda p: D2 * 2 ** ((12 * (p // 7) + DOR[p % 7]) / 12)

# ---------- linha do tempo (igual às outras) ----------
d = json.load(open(sys.argv[1])); V = {m["id"]: m for m in d["materials"]["videos"]}
tours, INTRO, MURAL, passos = {}, None, None, []
NUM, passos_num, clipes = None, [], []
for t in d["tracks"]:
    if t["type"] != "video": continue
    for s in t["segments"]:
        a = s["target_timerange"]["start"] / 1e6; b = a + s["target_timerange"]["duration"] / 1e6; nm = os.path.basename(V[s["material_id"]]["path"])
        clipes.append((a, b))
        if nm.startswith("1110-intro"): INTRO = (a, b)
        if nm.startswith("1110-numeros-10s"):
            s0n = s["source_timerange"]["start"] / 1e6; NUM = (a, b)
            passos_num = [a + (q - s0n) / s["speed"] for q in ((3, 4, 5, 6, 7, 8) if "-4x5" in nm else (4, 7)) if a <= a + (q - s0n) / s["speed"] < b]
        if nm.startswith("1110-mural-10s-60bpm"):
            s0 = s["source_timerange"]["start"] / 1e6; MURAL = (a, b)
            passos = [a + (q - s0) / s["speed"] for q in (range(1, 10) if "-4x5" in nm else (1, 3, 5, 7, 9)) if a <= a + (q - s0) / s["speed"] < b]
        m = re.match(r"(.+?)_(\d{4})-(\d\d)-\d\d", nm)
        if m:
            k = m.group(1); y, mo = int(m.group(2)), int(m.group(3))
            tours[k] = (min(a, tours.get(k, (1e9,))[0]), (y, (mo - 1) // 3 + 1))
FIM = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"] for t in d["tracks"] if t["type"] != "audio" for s in t["segments"]) / 1e6
assert INTRO and MURAL
N_MURAL = len(passos)                                                  # os passos do mural de artes; o resto é a coda
if NUM: passos += [NUM[0]] + passos_num + sorted({a for a, b in clipes if a >= NUM[1] - 1e-6})   # mural de números (entrada + passos) e o logo final
entradas = collections.defaultdict(list)
for k, (a, q) in tours.items(): entradas[round(a, 3)].append(k)
tempos = sorted(entradas)
trims = sorted({q for a, q in tours.values()}, reverse=True)
lim = [INTRO[1]]
for i in range(1, len(trims)):
    ant = [a for a, q in tours.values() if q == trims[i - 1]]; nov = [a for a, q in tours.values() if q == trims[i]]
    cands = [t for t in tempos if t > lim[-1]]
    lim.append(min(cands, key=lambda b: (sum(a >= b for a in ant) + sum(a < b for a in nov), -b)))
anos = sorted({q[0] for q in trims}, reverse=True); lim_ano = [lim[[q[0] for q in trims].index(y)] for y in anos]
N = int(SR * FIM)
def acha_lista(o):
    if isinstance(o, list) and o and isinstance(o[0], dict) and "latlngs" in o[0]: return o
    for v in (o.values() if isinstance(o, dict) else o if isinstance(o, list) else []):
        r = acha_lista(v)
        if r: return r
km = {}
try:
    for e in acha_lista(json.load(open(sys.argv[2]))) or []:
        ll = e.get("latlngs") or []
        if len(ll) < 2: continue
        a = np.radians(np.array(ll, float)[:, :2]); dl = np.diff(a, axis=0)
        h = np.sin(dl[:, 0] / 2) ** 2 + np.cos(a[:-1, 0]) * np.cos(a[1:, 0]) * np.sin(dl[:, 1] / 2) ** 2
        L = float((2 * 6371 * np.arcsin(np.sqrt(h))).sum())
        for n in (e.get("numbers") or [e.get("number")]):
            if isinstance(n, dict) and str(n.get("value")).isdigit(): km[f"{n.get('source')}-{int(n.get('value')):03d}"] = L
except Exception as ex: print("rotas não lidas:", ex)
def comprimento(k): return next((km[p] for p in k.split("+") if p in km), None)
comps = sorted(v for v in (comprimento(k) for k in tours) if v); med = comps[len(comps) // 2] if comps else 30.0
pct = lambda k: (np.searchsorted(comps, comprimento(k) or med) / max(1, len(comps) - 1)) if comps else 0.5
SEG = []; qi = (INTRO[1] - INTRO[0]) / 4
SEG.append((INTRO[0], INTRO[1], 7, ACORDE[0], "mapa"))                # o mapa fica parado no ré: não sobe
nq = len(trims)
for i in range(nq):
    p = nq - i; SEG.append((lim[i], lim[i + 1] if i + 1 < nq else MURAL[0], p, ACORDE[p % 7], anos.index(trims[i][0])))
SEG.append((MURAL[0], FIM, 0, [0, 3, 7], "mural"))
def seg_em(t): return next(s for s in SEG if s[0] - 1e-6 <= t < s[1] + 1e-6)
def notas(ac, lo, hi): return sorted({round(D2 * 2 ** (o + c / 12), 3) for o in range(8) for c in ac if lo <= D2 * 2 ** (o + c / 12) <= hi})

# ---------- fontes: o som dos vídeos ----------
def le(nome):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", MIDIA + nome, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32).astype(float); assert len(x) > SR, f"sem áudio: {nome}"
    x = sosfilt(butter(2, 45, btype="high", fs=SR, output="sos"), x); return x / (np.sqrt((x ** 2).mean()) + 1e-9)
SRC = {k: [le(n) for n in v] for k, v in FONTES.items()}
def laco(x, n, ini=None):
    """n amostras de x em laço (emenda com crossfade de 0,4 s), começando num ponto ao acaso."""
    xf = int(min(0.4 * SR, len(x) // 4)); corpo = x[:len(x) - xf].copy()
    w = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2; corpo[:xf] = corpo[:xf] * w + x[len(x) - xf:] * (1 - w)
    i0 = rng.integers(0, len(corpo)) if ini is None else ini
    return np.take(corpo, (i0 + np.arange(n)) % len(corpo))
def rms(x): return float(np.sqrt((x ** 2).mean()) + 1e-12)
def ressoa(x, freqs, Q, pesos=None):
    y = np.zeros_like(x)
    for j, f in enumerate(freqs):
        if f >= SR * 0.45: continue
        b, a = iirpeak(f, Q(f) if callable(Q) else Q, fs=SR); y += lfilter(b, a, x, axis=0) * (1.0 if pesos is None else pesos[j])
    return y
def buf(): return np.zeros((N + SR * 6, 2))
def poe(b, t0, sig, pan=0.0, g=1.0):
    i = int(round(t0 * SR))
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), len(b) - i)
    if n <= 0: return
    if sig.ndim == 1:
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        b[i:i + n, 0] += sig[:n] * l * g; b[i:i + n, 1] += sig[:n] * r * g
    else: b[i:i + n] += sig[:n] * g
def bordas(n, a, r):
    e = np.ones(n); na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na: e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    if nr: e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e
def eco(b, atraso=0.375, fb=0.4, taps=5, molhado=0.4):
    out = b.copy(); D = int(atraso * SR)
    for i in range(1, taps + 1):
        src = b[:, ::-1] if i % 2 else b; out[i * D:] += molhado * fb ** (i - 1) * src[:len(b) - i * D]
    return out

trem, agua, pas, mult, vento = buf(), buf(), buf(), buf(), buf()
PARES = {2: 1.0, 3: 0.7, 6: 0.85, 7: 0.6}                              # semicolcheias em que a roda bate: ta-tam … ta-tam (o tempo fica pro clique)
for si, (t0, t1, p, ac, era) in enumerate(SEG):
    f = grau_hz(p)
    # ---- trem afinado no baixo
    n = int((t1 - t0 + 0.4) * SR); tg = t0 + np.arange(n) / SR; t = np.arange(n) / SR
    h = [f * k for k in range(1, 7)] + [f * k * 1.006 for k in range(1, 4)]   # 2ª fileira 10 cents acima: bate devagar
    r = np.stack([ressoa(laco(SRC["trem"][0], n), h, lambda fq: 30 + fq / 12, [1, 0.6, 0.35, 0.2, 0.12, 0.08, 0.7, 0.4, 0.2]) for _ in (0, 1)], axis=1); r /= rms(r)
    seno = (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t) + (0.5 * np.sin(np.pi * f * t) if f >= 110 else 0))[:, None] * 0.5
    y = r * 0.8 + seno
    if era == "mapa":
        u = np.clip((tg - INTRO[0]) / (INTRO[1] - INTRO[0]), 0, 1); g = 0.2 + 0.8 * u
    elif era in (0, 1, "mural"):
        g = np.full(n, 0.55)                                           # contínuo; respira a cada passeio (ou passo do mural) que entra
        for tp in [x for x in tempos + passos if t0 - 1e-6 <= x < t1]:
            i0 = int((tp - t0) * SR); uu = t[i0:] - t[i0]
            g[i0:] = np.maximum(g[i0:], 0.55 + 0.4 * np.exp(-uu / 1.3) * np.minimum(1, uu / 0.08))
    else: g = 0.55 + 0.25 * np.sin(2 * np.pi * 0.09 * t - 1.3)         # último ano: o trem só passa, sem pulsar
    poe(trem, t0, y * (g * bordas(n, 0.15, 0.4))[:, None] * 0.3)
    # ---- água que canta o acorde
    lo, hi = {"mapa": (98, 420), 0: (98, 620), 1: (98, 440), "mural": (73, 620)}.get(era, (98, 300))
    fq = notas(ac, lo, hi)
    if era not in ("mapa", "mural", 0, 1): fq = fq[:2]
    n = int((t1 - t0 + 2.4) * SR); fonte = SRC["agua"][si % len(SRC["agua"])]
    st = np.stack([ressoa(laco(fonte, n), fq, lambda q: 20 + q / 25, [(150 / q) ** 0.9 for q in fq]) for _ in (0, 1)], axis=1); st /= rms(st)
    seco = np.stack([laco(fonte, n) for _ in (0, 1)], axis=1); seco = sosfilt(butter(2, 900, btype="high", fs=SR, output="sos"), seco, axis=0); seco /= rms(seco)
    e = bordas(n, 1.0, 2.2) * (np.linspace(0.2, 1.0, n) if era == "mapa" else 1.0)
    ganho = {"mapa": 0.55, "mural": 1.0, 0: 1.0, 1: 0.75}.get(era, 0.5); umido = 0.0
    poe(agua, t0 - 0.4, (st + umido * seco) * e[:, None] * ganho * 0.22)
agua = 0.35 * np.tanh(agua / 0.35)                                     # doma os estalos da gravação
# ---- passeios: gota afinada
def gota(f, dur=1.1, brilho=1.0):
    n = int(dur * SR); x = np.zeros(n); m = int(0.03 * SR)
    fonte = SRC["agua"][rng.integers(len(SRC["agua"]))]; x[:m] = laco(fonte, m) * np.exp(-np.arange(m) / SR / 0.008)
    hs = [f, 2 * f, 3.01 * f, 4.03 * f]; taus = [0.5, 0.2, 0.08, 0.04]
    y = sum(lfilter(*iirpeak(h, max(8, math.pi * h * tau), fs=SR), x) * w for h, tau, w in zip(hs, taus, [1, 0.55 * brilho, 0.35 * brilho, 0.25 * brilho]) if h < SR * 0.45)
    return y / (np.abs(y).max() + 1e-9)
for tp in tempos:
    _, _, p, ac, era = seg_em(tp); cand = notas(ac, 146, 600); usados = []
    for j, k in enumerate(sorted(entradas[tp], key=pct, reverse=True)):
        idx = int(round((1 - pct(k)) * (len(cand) - 1)))
        while idx in usados: idx = (idx + 1) % len(cand)
        usados.append(idx); poe(pas, tp + 0.03 * j, gota(cand[idx], brilho={0: 0.35, 1: 0.3}.get(era, 0.25)), pan=rng.uniform(-0.4, 0.4), g=0.8)
arp = notas([0, 7], 100, 320)
for j, tp in enumerate(passos):
    for q, fq in enumerate(arp[:3]): poe(pas, tp + 0.025 * q, gota(fq, 1.8, 0.3), pan=-0.4 + 0.4 * q, g=0.6)   # o mesmo acorde aberto a cada passo: chega, não comemora
pas = eco(pas, molhado=0.25)
# ---- multidão: golpes em contagem regressiva + chegada no mural
M = sosfilt(butter(2, [150, 1600], btype="band", fs=SR, output="sos"), SRC["multidao"][0]); M /= rms(M)
jan = int(0.4 * SR); en = np.convolve(M ** 2, np.ones(jan) / jan, mode="valid"); ordem = np.argsort(-en); picos = []
for i in ordem:                                                        # os 3 trechos mais fortes, sem sobreposição
    if all(abs(i - q) > jan for q in picos): picos.append(int(i))
    if len(picos) == 3: break
def golpe(i):
    n = int(0.36 * SR); x = M[i:i + n].copy(); x *= bordas(len(x), 0.008, 0.09); return x / (np.abs(x).max() + 1e-9)
for i, b in enumerate(lim_ano):
    for q in range(len(anos) - i): poe(mult, b + 0.5 * q, golpe(picos[q % len(picos)]), pan=(-0.3, 0.3, 0.0)[q % 3], g=0.18)
nw = int((FIM - MURAL[0] + 5.0) * SR); w = np.stack([laco(M, nw), laco(M, nw)], axis=1); tw = np.arange(nw) / SR
ew = np.where(tw < 5.0, (tw / 5.0) ** 2.5, 1.0 - 0.45 * np.clip((tw - 5.0) / max(1e-6, FIM - MURAL[0]), 0, 1))
poe(mult, MURAL[0] - 5.0, w * ew[:, None] * 0.075)
# ---- vento antes de cada fronteira
hp = butter(2, 220, btype="high", fs=SR, output="sos")
for i, b in enumerate(lim + [MURAL[0]]):
    grande = b in lim_ano or i == len(lim); dur = 6.0 if i == len(lim) else 4.5 if grande else 2.5
    n = int(dur * SR); fonte = SRC["vento"][i % len(SRC["vento"])]
    x = np.stack([laco(fonte, n), laco(fonte, n)], axis=1); ar = sosfilt(hp, x, axis=0); ar /= rms(ar)
    u = np.arange(n) / n; e = u ** 2.3; nf = int(0.02 * SR); e[-nf:] *= np.linspace(1, 0, nf)
    poe(vento, b - dur, (1.0 * x + 0.3 * ar) * e[:, None] * (0.15 if grande else 0.085))

# ---------- sala curta e saída ----------
nir = int(2.6 * SR); tir = np.arange(nir) / SR
ir = rng.standard_normal((nir, 2)) * np.exp(-tir / 0.6)[:, None]; ir = lfilter([0.1], [1, -0.9], lfilter([0.1], [1, -0.9], ir, axis=0), axis=0); ir /= np.sqrt((ir ** 2).sum(axis=0))
def sala(b, molhado): return b + molhado * np.stack([fftconvolve(b[:, c], ir[:, c])[:len(b)] for c in (0, 1)], axis=1)
abafa = lambda b, fc: sosfilt(butter(2, fc, btype="low", fs=SR, output="sos"), b, axis=0)
stems = {"trem": abafa(trem, 1200), "agua": sala(abafa(agua, 1400), 0.25), "passeios": sala(abafa(pas, 1600), 0.22), "multidao": sala(mult, 0.6), "vento": sala(vento, 0.1)}
fade = np.ones(N); nf = int(0.8 * SR); fade[-nf:] = np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
stems = {k: v[:N] * fade[:, None] for k, v in stems.items()}
assert all(np.isfinite(v).all() for v in stems.values())
mix = sum(stems.values()); g = 0.7 / np.abs(mix).max()
out = sys.argv[3]; os.makedirs(out, exist_ok=True)
def grava(nome, x):
    w = wave.open(f"{out}/{nome}.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
for j, (k, v) in enumerate(stems.items()): grava(f"campo-{j + 1}-{k}", v * g)
grava("campo-mix", mix * g)
if len(sys.argv) > 4:
    w = wave.open(sys.argv[4]); c = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767; w.close()
    c = np.pad(c, (0, max(0, N - len(c))))[:N]; grava("campo-mix-com-cliques", mix * g + 0.55 * c[:, None])
print(f"fim {FIM:g} s; {len(tempos)} entradas; anos {list(zip(anos, lim_ano))}; fontes: " + ", ".join(f"{k} {len(v)}" for k, v in SRC.items()))
print("pico de cada camada:", {k: round(float(np.abs(v).max() * g), 3) for k, v in stems.items()})
