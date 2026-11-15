#!/usr/bin/env python3
"""Trilha em camadas, versão ELETRÔNICA (ré dórico, 60 BPM com semicolcheias de 120): mesma estrutura da musica.py, outro timbre.
  baixo     sequenciador de serra filtrada: sobe no mapa (ré mi fá lá, filtro abrindo) e DESCE um grau por trimestre até o ré do mural
  harmonia  supersaw frio em acordes abertos (sem terça: nem alegre nem triste); varreduras de ruído antes de cada trimestre
  passeios  um "pluck" de sintetizador com eco por passeio (pedal mais longo = nota mais grave); os que entram juntos soam em acorde
  sinais    bipes em contagem regressiva dos anos (3, 2, 1); impacto grave na entrada do conteúdo e do mural
  bateria   bumbo a cada segundo + chimbal; some no último ano (breakdown), rufo antes do mural, volta dobrado no mural
  A cada ano a textura esvazia; no mural volta tudo.
  musica2.py <draft_info.json> <routes.json> <pasta de saída> [metronomo.wav]"""
import sys, json, os, re, wave, math, collections, numpy as np
from scipy.signal import fftconvolve, lfilter, butter, sosfilt
SR = 48000; rng = np.random.default_rng(2077)
D2 = 73.416; DOR = [0, 2, 3, 5, 7, 9, 10]
ACORDE = {0: [0, 7, 2], 1: [2, 9, 7], 2: [3, 10, 7], 3: [5, 0, 9], 4: [7, 2, 0], 5: [9, 2, 5], 6: [10, 5, 2]}   # sus2/sus4 sobre cada grau do baixo
grau_hz = lambda p: D2 * 2 ** ((12 * (p // 7) + DOR[p % 7]) / 12)

# ---------- linha do tempo (igual à musica.py) ----------
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
            passos_num = [a + (q - s0n) / s["speed"] for q in (4, 7) if a <= a + (q - s0n) / s["speed"] < b]
        if nm.startswith("1110-mural-10s-60bpm"):
            s0 = s["source_timerange"]["start"] / 1e6; MURAL = (a, b)
            passos = [a + (q - s0) / s["speed"] for q in (1, 3, 5, 7, 9) if a <= a + (q - s0) / s["speed"] < b]
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

# ---------- segmentos harmônicos ----------
SEG = []; qi = (INTRO[1] - INTRO[0]) / 4
for j, (p, ac) in enumerate([(7, ACORDE[0]), (8, ACORDE[1]), (9, ACORDE[2]), (11, ACORDE[4])]):
    SEG.append((INTRO[0] + j * qi, INTRO[0] + (j + 1) * qi, p, ac, "mapa"))
nq = len(trims)
for i in range(nq):
    p = nq - i; SEG.append((lim[i], lim[i + 1] if i + 1 < nq else MURAL[0], p, ACORDE[p % 7], anos.index(trims[i][0])))
SEG.append((MURAL[0], FIM, 0, [0, 7, 2], "mural"))
def seg_em(t): return next(s for s in SEG if s[0] - 1e-6 <= t < s[1] + 1e-6)
def notas(ac, lo, hi): return sorted({round(D2 * 2 ** (o + c / 12), 3) for o in range(7) for c in ac if lo <= D2 * 2 ** (o + c / 12) <= hi})
com_bumbo = lambda era: era in (0, 1, "mural")

# ---------- síntese ----------
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
def serra(f, n, fc, q=0.0, fase=0.0):
    """Serra aditiva com passa-baixas de 12 dB/oitava (e ressonância q) aplicado harmônico a harmônico: sem aliasing, e o corte pode variar no tempo."""
    t = np.arange(n) / SR; fc = np.asarray(fc, float); y = np.zeros(n)
    K = max(1, min(60, int(min(10000.0, float(np.max(fc)) * 3.0) / f)))
    for k in range(1, K + 1):
        fk = k * f; w = 1 / np.sqrt(1 + (fk / fc) ** 4)
        if q: w = w + q * np.exp(-((fk - fc) / (0.25 * fc)) ** 2)
        y += np.sin(2 * np.pi * fk * t + fase * k) * w / k
    return y
def ruido(n, lo, hi, estereo=False):
    w = rng.standard_normal((n, 2) if estereo else n)
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), w, axis=0)
def bumbo(forca=1.0):
    n = int(0.42 * SR); t = np.arange(n) / SR; f = 46 + 110 * np.exp(-t / 0.03)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) + 0.25 * ruido(n, 1500, 6000) * np.exp(-t / 0.004)
    return np.tanh(1.6 * y) * forca
def chimbal(aberto=False):
    n = int((0.16 if aberto else 0.035) * SR); t = np.arange(n) / SR
    return ruido(n, 7000, 14000) * np.exp(-t / (0.055 if aberto else 0.009))
def caixa():
    n = int(0.12 * SR); t = np.arange(n) / SR
    return (ruido(n, 900, 7000) * 0.8 + 0.5 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t / 0.035)
def pluck(f, dur=0.9, brilho=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; fc = np.minimum(9000, f * (1.6 + 9 * brilho * np.exp(-t / 0.07)))
    e = np.exp(-t / 0.2) * np.minimum(1, t / 0.002)
    return np.stack([serra(f * 0.9965, n, fc, 0.5), serra(f * 1.0035, n, fc, 0.5, 0.7)], axis=1) * e[:, None]
def bipe(f=1174.66):                                                   # FM curto: "ping" de console
    n = int(0.7 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t + 2.2 * np.exp(-t / 0.05) * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t / 0.13) * np.minimum(1, t / 0.001)
def impacto(dur=3.2):
    n = int(dur * SR); t = np.arange(n) / SR; f = 38 + 75 * np.exp(-t / 0.18)
    sub = np.tanh(2.0 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9))
    return sub[:, None] * 0.9 + ruido(n, 300, 9000, True) * (np.exp(-t / 0.5) * 0.5)[:, None]
def varredura(dur, forca, tom=False):                                  # ruído que sobe de 300 Hz a 8 kHz (+ um tom subindo, nos grandes)
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur; y = np.zeros((n, 2))
    for j, (lo, hi) in enumerate([(250, 600), (600, 1500), (1500, 3500), (3500, 9000)]):
        y += ruido(n, lo, hi, True) * np.exp(-((u * 3.4 - j) / 0.75) ** 2)[:, None]
    y *= (u ** 2.2)[:, None]
    if tom: y += (0.5 * np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * u)) / SR) * u ** 3)[:, None]
    nf = int(0.01 * SR); y[-nf:] *= np.linspace(1, 0, nf)[:, None]      # corta seco no tempo
    return y * forca
def eco(b, atraso=0.375, fb=0.42, taps=6, molhado=0.5):                # eco pingue-pongue
    out = b.copy(); D = int(atraso * SR)
    for i in range(1, taps + 1):
        src = b[:, ::-1] if i % 2 else b
        out[i * D:] += molhado * fb ** (i - 1) * src[:len(b) - i * D]
    return out

baixo, harm, pas, sinais, bat = buf(), buf(), buf(), buf(), buf()
PADRAO = [0, 1, 1, 2, 0, 1, 2, 1]                                      # por segundo, em semicolcheias: 0 pausa (bumbo), 1 nota, 2 oitava acima com acento
for (t0, t1, p, ac, era) in SEG:
    f = grau_hz(p)
    # ---- baixo
    if era == "mapa":                                                  # nota contínua, filtro abrindo, "gate" de colcheia ficando mais fundo
        n = int((t1 - t0) * SR); tg = t0 + np.arange(n) / SR; u = (tg - INTRO[0]) / (INTRO[1] - INTRO[0])
        gate = 1 - (0.75 * u) * (0.5 - 0.5 * np.cos(2 * np.pi * 4 * tg)) ** 0.6
        e = np.ones(n); nf = int(0.03 * SR); e[:nf] = np.linspace(0, 1, nf); e[-nf:] = np.linspace(1, 0, nf)
        poe(baixo, t0, serra(f, n, 110 + 900 * u ** 2, 0.35) * gate * e * (0.25 + 0.75 * u) * 0.34)
    elif era in (0, 1, "mural"):                                       # sequenciador
        br = {0: 1.0, 1: 0.6, "mural": 1.45}[era]
        for ts in np.arange(math.ceil(t0 * 8 - 1e-6) / 8, t1 - 1e-6, 0.125):
            passo = PADRAO[int(round(ts * 8)) % 8]
            if not passo: continue
            n = int(0.118 * SR); t = np.arange(n) / SR; fn = f * (2 if passo == 2 else 1)
            fc = f * (1.4 + (7.5 if passo == 2 else 4.5) * br * np.exp(-t / 0.035))
            e = np.minimum(1, t / 0.002) * np.exp(-t / 0.09); e[-240:] *= np.linspace(1, 0, 240)
            poe(baixo, ts, serra(fn, n, fc, 0.9) * e * (0.34 if passo == 2 else 0.4))
    else:                                                              # breakdown: nota longa, filtro respirando devagar
        n = int((t1 - t0 + 0.3) * SR); t = np.arange(n) / SR
        e = np.ones(n); e[:int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR)); e[-int(0.3 * SR):] = np.linspace(1, 0, int(0.3 * SR))
        poe(baixo, t0, serra(f, n, f * (2.2 + 1.4 * np.sin(2 * np.pi * 0.11 * t - 1.2)), 0.3) * e * 0.3)
    # ---- harmonia: supersaw frio
    vz = notas(ac, 180, 390)
    if era not in ("mapa", "mural", 0, 1): vz = vz[:2]
    if era == "mural": vz = notas(ac, 180, 800)
    n = int((t1 - t0 + 2.0) * SR); t = np.arange(n) / SR; esc, cla = np.zeros((n, 2)), np.zeros((n, 2))
    for fv in vz:
        for ch, cents in ((0, -11), (0, 5), (1, -5), (1, 11)):
            fd = fv * 2 ** (cents / 1200); ph = rng.uniform(0, 6.28)
            for k in range(1, int(2600 / fd) + 1):
                s = np.sin(2 * np.pi * k * fd * t + ph * k) / k
                esc[:, ch] += s / np.sqrt(1 + (k * fd / 500) ** 4); cla[:, ch] += s / np.sqrt(1 + (k * fd / 1500) ** 4)
    l = (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * (t0 + t)))[:, None] * {"mapa": 0.4, "mural": 1.0, 0: 0.8, 1: 0.5}.get(era, 0.3)
    e = np.ones(n); na, nr = int(0.9 * SR), int(2.0 * SR); e[:na] = np.linspace(0, 1, na) ** 2; e[-nr:] = np.linspace(1, 0, nr) ** 2
    if era == "mapa": e = e * np.linspace(0.2, 1.0, n)
    poe(harm, t0 - 0.3, (esc * (1 - l) + cla * l) * e[:, None] / max(1, len(vz)) * {"mapa": 0.5, "mural": 1.2, 0: 1.0, 1: 0.75}.get(era, 0.5) * 0.3)
# ---- bateria + sidechain
batidas = []
for (t0, t1, p, ac, era) in SEG:
    if not com_bumbo(era): continue
    passo = 0.5 if era == "mural" else 1.0
    for tb in np.arange(math.ceil(t0 / passo - 1e-6) * passo, t1 - 1e-6, passo):
        forte = round(float(tb), 3) in entradas or any(abs(tb - x) < 1e-3 for x in passos) or abs(tb - t0) < 1e-3
        batidas.append(tb); poe(bat, tb, bumbo(1.0 if forte else 0.62), g=1.0)
    for ts in np.arange(math.ceil(t0 * 8 - 1e-6) / 8, t1 - 1e-6, 0.125):
        sl = int(round(ts * 8)) % 8
        if sl == 4: poe(bat, ts, chimbal(True), pan=0.25, g=0.36 if era != 1 else 0.25)
        elif era != 1 and sl in (1, 2, 3, 5, 6, 7): poe(bat, ts, chimbal(), pan=-0.2 if sl % 2 else 0.2, g=0.3 if sl in (2, 6) else 0.15)
def rufo(t_fim, dur, forca):                                           # caixa acelerando até o tempo t_fim
    partes = [(dur * 0.4, 0.25), (dur * 0.35, 0.125), (dur * 0.25, 0.0625)]; ts = t_fim - dur
    for comp, passo in partes:
        for tq in np.arange(ts, ts + comp - 1e-6, passo): poe(bat, tq, caixa(), pan=rng.uniform(-0.2, 0.2), g=forca * (0.25 + 0.75 * ((tq - (t_fim - dur)) / dur) ** 1.5))
        ts += comp
rufo(INTRO[1], 2.0, 0.22); rufo(MURAL[0], min(4.0, MURAL[0] - lim[-1] + 1), 0.4)
duck = np.ones(len(baixo)); tt = np.arange(len(baixo)) / SR
for tb in batidas:
    i0 = int(tb * SR); i1 = min(len(duck), i0 + int(0.5 * SR)); duck[i0:i1] = np.minimum(duck[i0:i1], 1 - 0.6 * np.exp(-(tt[i0:i1] - tb) / 0.13))
baixo *= duck[:, None]; harm *= duck[:, None]
# ---- varreduras: antes de cada trimestre; grandes antes do conteúdo, de cada ano e do mural
for i, b in enumerate(lim + [MURAL[0]]):
    grande = b in lim_ano or i == len(lim)
    if i == len(lim): poe(harm, b - 6.0, varredura(6.0, 0.2, True))
    elif grande: poe(harm, b - 4.0, varredura(4.0, 0.14, True))
    else: poe(harm, b - 2.0, varredura(2.0, 0.07))
# ---- passeios
for tp in tempos:
    _, _, p, ac, era = seg_em(tp); cand = notas(ac, 290, 1180); usados = []
    for j, k in enumerate(sorted(entradas[tp], key=pct, reverse=True)):
        idx = int(round((1 - pct(k)) * (len(cand) - 1)))
        while idx in usados: idx = (idx + 1) % len(cand)
        usados.append(idx); poe(pas, tp + 0.03 * j, pluck(cand[idx], brilho={0: 1.0, 1: 0.8}.get(era, 0.6)), g=0.42)
arp = notas([0, 7, 2], 290, 2400)
for j, tp in enumerate(passos):                                        # no mural: cada passo é um acorde aberto um degrau acima
    jj = j if j < N_MURAL else max(0, 2 * (N_MURAL - 1) - j)
    for q, fq in enumerate(arp[jj:jj + 3]): poe(pas, tp + 0.02 * q, pluck(fq, 1.4, 1.3), g=0.34)
pas = eco(pas)
# ---- sinais
for i, b in enumerate(lim_ano):
    for q in range(len(anos) - i): poe(sinais, b + 0.5 * q, bipe(), pan=(-0.35, 0.35, 0.0)[q % 3], g=0.34)
sinais = eco(sinais, 0.25, 0.35, 4, 0.35)
poe(sinais, INTRO[1], impacto(), g=0.28); poe(sinais, MURAL[0], impacto(4.5), g=0.4)

# ---------- sala curta e saída ----------
nir = int(1.3 * SR); tir = np.arange(nir) / SR
ir = rng.standard_normal((nir, 2)) * np.exp(-tir / 0.3)[:, None]; ir = lfilter([0.35], [1, -0.65], ir, axis=0); ir /= np.sqrt((ir ** 2).sum(axis=0))
def sala(b, molhado): return b + molhado * np.stack([fftconvolve(b[:, c], ir[:, c])[:len(b)] for c in (0, 1)], axis=1)
stems = {"baixo": baixo, "harmonia": sala(harm, 0.18), "passeios": sala(pas, 0.14), "sinais": sala(sinais, 0.18), "bateria": sala(bat, 0.05)}
fade = np.ones(N); nf = int(0.5 * SR); fade[-nf:] = np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
stems = {k: v[:N] * fade[:, None] for k, v in stems.items()}
assert all(np.isfinite(v).all() for v in stems.values())
mix = sum(stems.values()); g = 0.7 / np.abs(mix).max()
out = sys.argv[3]; os.makedirs(out, exist_ok=True)
def grava(nome, x):
    w = wave.open(f"{out}/{nome}.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
for j, (k, v) in enumerate(stems.items()): grava(f"eletro-{j + 1}-{k}", v * g)
grava("eletro-mix", mix * g)
if len(sys.argv) > 4:
    w = wave.open(sys.argv[4]); c = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767; w.close()
    c = np.pad(c, (0, max(0, N - len(c))))[:N]; grava("eletro-mix-com-cliques", mix * g + 0.55 * c[:, None])
nome = ["ré", "mi", "fá", "sol", "lá", "si", "dó"]
print(f"fim {FIM:g} s; {len(tempos)} entradas; {len(batidas)} bumbos; anos {list(zip(anos, lim_ano))}")
for (t0, t1, p, ac, era), q in zip(SEG[4:4 + nq], trims): print(f"  {q[0]} T{q[1]}  {t0:6.1f}–{t1:6.1f} s  baixo {nome[p % 7]} ({grau_hz(p):.0f} Hz)")
print("pico de cada camada:", {k: round(float(np.abs(v).max() * g), 3) for k, v in stems.items()})
