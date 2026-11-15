#!/usr/bin/env python3
"""Trilha em camadas pra dar noção de onde o vídeo está e de quanto falta (ré maior, 60 BPM):
  baixo     sobe no mapa de abertura (ré mi fá# lá) e depois DESCE um grau por trimestre, chegando no ré quando entra o mural
  harmonia  o acorde de cada grau; cheia no 1º ano, mais rala a cada ano; volta inteira no mural. Ondas (ruído) anunciam cada trimestre
  passeios  uma nota de kalimba por passeio (pedal mais longo = nota mais grave); passeios que entram juntos soam em acorde
  sinos     campainha: 3 toques no 1º ano, 2 no 2º, 1 no 3º (contagem regressiva); gongo na entrada do conteúdo e do mural
  gotas     gotas d'água só no 1º ano e no mural
  musica.py <draft_info.json> <routes.json> <pasta de saída> [metronomo.wav]"""
import sys, json, os, re, wave, math, collections, numpy as np
from scipy.signal import fftconvolve, lfilter
SR = 48000; rng = np.random.default_rng(118)
D2 = 73.416; MAJ = [0, 2, 4, 5, 7, 9, 11]
ACORDE = {0: [0, 4, 7], 1: [2, 5, 9, 0], 2: [4, 7, 0], 3: [5, 9, 0], 4: [7, 0, 4], 5: [9, 0, 4], 6: [11, 2, 7]}   # por grau do baixo (semitons a partir de ré)
grau_hz = lambda p: D2 * 2 ** ((12 * (p // 7) + MAJ[p % 7]) / 12)

# ---------- linha do tempo ----------
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
trims = sorted({q for a, q in tours.values()}, reverse=True)          # o vídeo anda pra trás no tempo
lim = [INTRO[1]]                                                       # começo de cada trimestre: a fronteira que erra menos passeios
for i in range(1, len(trims)):
    ant = [a for a, q in tours.values() if q == trims[i - 1]]; nov = [a for a, q in tours.values() if q == trims[i]]
    cands = [t for t in tempos if t > lim[-1]]
    lim.append(min(cands, key=lambda b: (sum(a >= b for a in ant) + sum(a < b for a in nov), -b)))
anos = sorted({q[0] for q in trims}, reverse=True); lim_ano = [lim[[q[0] for q in trims].index(y)] for y in anos]
N = int(SR * FIM); tt = np.arange(N) / SR

# ---------- comprimento das rotas (pra altura das notas) ----------
def acha_lista(o):
    if isinstance(o, list) and o and isinstance(o[0], dict) and "latlngs" in o[0]: return o
    if isinstance(o, dict):
        for v in o.values():
            r = acha_lista(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
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
            if isinstance(n, dict): km[f"{n.get('source')}-{int(n.get('value')):03d}" if str(n.get("value")).isdigit() else str(n)] = L
except Exception as ex: print("rotas não lidas:", ex)
def comprimento(k):
    for parte in k.split("+"):
        if parte in km: return km[parte]
    return None
comps = sorted(v for v in (comprimento(k) for k in tours) if v); med = comps[len(comps) // 2] if comps else 30.0
pct = lambda k: (np.searchsorted(comps, comprimento(k) or med) / max(1, len(comps) - 1)) if comps else 0.5

# ---------- segmentos harmônicos ----------
SEG = []                                                               # (t0, t1, posição do baixo, classes do acorde, era)
qi = (INTRO[1] - INTRO[0]) / 4
for j, (p, ac) in enumerate([(7, ACORDE[0]), (8, ACORDE[1]), (9, ACORDE[2]), (11, [7, 0, 2])]):          # ré mi fá# lá(sus4): a subida
    SEG.append((INTRO[0] + j * qi, INTRO[0] + (j + 1) * qi, p, ac, "mapa"))
nq = len(trims)
for i in range(nq):
    p = nq - i; ac = [2, 5, 7, 11] if p == 1 else ACORDE[p % 7]        # último grau: lá7 sobre mi, que pede o ré
    SEG.append((lim[i], lim[i + 1] if i + 1 < nq else MURAL[0], p, ac, anos.index(trims[i][0])))
SEG.append((MURAL[0], FIM, 0, [0, 4, 7, 2], "mural"))                  # ré com nona: a chegada
def seg_em(t): return next(s for s in SEG if s[0] - 1e-6 <= t < s[1] + 1e-6)
def notas(ac, lo, hi):                                                 # tons do acorde entre lo e hi (Hz), do grave pro agudo
    out = []
    for o in range(0, 7):
        for c in ac:
            f = D2 * 2 ** (o + c / 12)
            if lo <= f <= hi: out.append(f)
    return sorted(set(round(f, 3) for f in out))

# ---------- utilidades ----------
def buf(): return np.zeros((N + SR * 6, 2))
def poe(b, t0, sig, pan=0.0, g=1.0):
    i = int(round(t0 * SR));
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), len(b) - i)
    if n <= 0: return
    if sig.ndim == 1:
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        b[i:i + n, 0] += sig[:n] * l * g; b[i:i + n, 1] += sig[:n] * r * g
    else: b[i:i + n] += sig[:n] * g
def env_ar(n, a, r):
    e = np.ones(n); na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na: e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    if nr: e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e
def kalimba(f, dur=2.6):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.75) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.35) + 0.22 * np.sin(2 * np.pi * 5.43 * f * t) * np.exp(-t / 0.06) \
        + 0.08 * np.sin(2 * np.pi * 9.1 * f * t) * np.exp(-t / 0.02)
    y[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR)); return y
def campainha(f=1760.0, dur=3.0):                                      # campainha de bicicleta: parciais de sino, com batimento
    t = np.arange(int(dur * SR)) / SR; y = np.zeros_like(t)
    for r, a, dc in [(1.0, 1.0, 1.1), (1.006, 0.8, 1.0), (2.76, 0.45, 0.5), (2.78, 0.3, 0.45), (5.4, 0.25, 0.22), (8.9, 0.12, 0.1)]:
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / dc)
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR)); return y / 2.5
def gongo(f=146.83, dur=9.0):
    t = np.arange(int(dur * SR)) / SR; y = np.zeros_like(t)
    for j, r in enumerate([0.5, 1.0, 1.48, 2.02, 2.56, 3.01, 3.74, 4.21, 5.43, 6.8]):
        cresce = 1 - np.exp(-t / (0.02 + 0.09 * j))                    # os agudos florescem depois da pancada
        y += (1 / (1 + 0.55 * j)) * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6.28)) * cresce * np.exp(-t / (4.5 / (1 + 0.25 * j)))
    return y / 3.0
def gota(f):                                                           # bolha: assobio curto que sobe
    t = np.arange(int(0.16 * SR)) / SR
    return np.sin(2 * np.pi * (f * t + 0.5 * f * 2.2 * t * t)) * np.exp(-t / 0.035) * np.minimum(1, t / 0.002)
def onda(dur, forca):                                                  # onda chegando: ruído que cresce e quebra
    n = int((dur + 0.9) * SR); w = rng.standard_normal((n, 2))
    b1, a1 = [0.06], [1, -0.94]; w = lfilter(b1, a1, lfilter(b1, a1, w, axis=0), axis=0)      # abafado
    w -= lfilter([0.004], [1, -0.996], w, axis=0)                                            # sem ronco
    t = np.arange(n) / SR; e = np.where(t < dur, (t / dur) ** 2.5, np.exp(-(t - dur) / 0.28))
    return w * e[:, None] * forca * 2.2

# ---------- camadas ----------
baixo, harm, pas, sinos, gotas = buf(), buf(), buf(), buf(), buf()
ganho_harm = lambda era: {"mapa": 0.55, "mural": 1.15, 0: 1.0, 1: 0.7}.get(era, 0.38)
pulsos = np.array(tempos + passos)
for (t0, t1, p, ac, era) in SEG:
    # baixo: nota sustentada que "respira" a cada passeio que entra
    n = int((t1 - t0 + 0.5) * SR); t = np.arange(n) / SR; f = grau_hz(p)
    y = sum(np.sin(2 * np.pi * k * f * t + 0.3 * k) / k ** 1.4 for k in range(1, 8)) + 0.5 * np.sin(2 * np.pi * 0.5 * f * t) * (p <= 3)
    e = env_ar(n, 0.12, 0.5); bomba = np.full(n, 0.55)
    for tp in pulsos[(pulsos >= t0 - 1e-6) & (pulsos < t1)]:
        i0 = int((tp - t0) * SR); u = t[i0:] - t[i0]; bomba[i0:] = np.maximum(bomba[i0:], 0.55 + 0.45 * np.exp(-u / 0.9) * np.minimum(1, u / 0.02))   # sobe em 20 ms: sem estalo
    g = np.linspace(0.35, 0.8, n) if era == "mapa" else 1.0
    poe(baixo, t0, y * e * bomba * g * (1.25 if era == "mural" else 1.0) * 0.3)
    # harmonia: vozes desafinadas à esquerda e à direita; no último ano só o esqueleto (fundamental + quinta mais próxima)
    vz = notas(ac, 185, 400)
    if era not in ("mapa", "mural", 0, 1): vz = vz[:2]
    if era == "mural": vz = notas(ac, 185, 800)
    n = int((t1 - t0 + 3.0) * SR); t = np.arange(n) / SR; st = np.zeros((n, 2))
    for fv in vz:
        for ch, det in ((0, 0.9972), (1, 1.0028)):
            lfo = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.07, 0.19) * t + rng.uniform(0, 6.28))
            st[:, ch] += sum(np.sin(2 * np.pi * k * fv * det * t + rng.uniform(0, 6.28)) / k ** 2.2 for k in range(1, 6)) * lfo
    cres = np.linspace(0.25, 1.0, n) if era == "mapa" else 1.0
    poe(harm, t0 - 0.6, st * (env_ar(n, 1.6, 3.0) * cres)[:, None] / max(1, len(vz)) * ganho_harm(era) * 0.33)
for i, b in enumerate(lim + [MURAL[0]]):                               # onda antes de cada trimestre; maior na virada de ano e de seção
    grande = b in lim_ano or i in (0, len(lim))
    era = "mapa" if i == 0 else seg_em(b - 0.5)[4]
    if era in ("mapa", 0, 1) or grande: poe(harm, b - (3.0 if grande else 2.0), onda(3.0 if grande else 2.0, 0.085 if grande else 0.045))
for tp in tempos:                                                      # uma nota por passeio
    _, _, p, ac, era = seg_em(tp); cand = notas(ac, 290, 1180); usados = []
    for j, k in enumerate(sorted(entradas[tp], key=pct, reverse=True)):
        idx = int(round((1 - pct(k)) * (len(cand) - 1)))
        while idx in usados: idx = (idx + 1) % len(cand)
        usados.append(idx); poe(pas, tp + 0.045 * j, kalimba(cand[idx]), pan=rng.uniform(-0.45, 0.45), g=0.5)
arp = notas([0, 4, 7], 580, 2400)                                      # no mural: cada passo sobe um degrau do arpejo de ré
for j, tp in enumerate(passos):
    jj = j if j < N_MURAL else max(0, 2 * (N_MURAL - 1) - j)            # no mural sobe; na coda desce de volta
    for q, fq in enumerate(arp[jj:jj + 3]): poe(pas, tp + 0.07 * q, kalimba(fq, 3.0), pan=-0.5 + 0.5 * q, g=0.42)
for i, b in enumerate(lim_ano):                                        # contagem regressiva dos anos
    for q in range(len(anos) - i): poe(sinos, b + 0.5 * q, campainha(), pan=(-0.3, 0.3, 0.0)[q % 3], g=0.32)
poe(sinos, INTRO[1], gongo(), g=0.5); poe(sinos, MURAL[0], gongo(110.0, 10.0), g=0.75)
for (t0, t1, p, ac, era) in SEG:                                       # gotas: só no 1º ano e no mural
    if era not in (0, "mural"): continue
    cand = notas(ac, 1100, 2400)
    for tq in np.arange(math.ceil(t0 * 4) / 4, t1, 0.25):
        fora = abs(tq - round(tq)) > 1e-6                              # fora do tempo: não briga com o clique
        if fora and rng.random() < (0.42 if era == "mural" else 0.2 if abs(tq * 2 - round(tq * 2)) < 1e-6 else 0.09):
            poe(gotas, tq + rng.uniform(-0.012, 0.012), gota(rng.choice(cand)), pan=rng.uniform(-0.8, 0.8), g=rng.uniform(0.15, 0.36))

# ---------- sala (reverberação) e saída ----------
nir = int(2.2 * SR); tir = np.arange(nir) / SR
ir = rng.standard_normal((nir, 2)) * np.exp(-tir / 0.55)[:, None]; ir = lfilter([0.25], [1, -0.75], ir, axis=0); ir /= np.sqrt((ir ** 2).sum(axis=0))
def sala(b, molhado):
    w = np.stack([fftconvolve(b[:, c], ir[:, c])[:len(b)] for c in (0, 1)], axis=1); return b + molhado * w
stems = {"baixo": sala(baixo, 0.06), "harmonia": sala(harm, 0.35), "passeios": sala(pas, 0.3), "sinos": sala(sinos, 0.35), "gotas": sala(gotas, 0.45)}
fade = np.ones(N); nf = int(1.6 * SR); fade[-nf:] = np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
stems = {k: v[:N] * fade[:, None] for k, v in stems.items()}
mix = sum(stems.values()); g = 0.6 / np.abs(mix).max()
out = sys.argv[3]; os.makedirs(out, exist_ok=True)
def grava(nome, x):
    w = wave.open(f"{out}/{nome}.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
for j, (k, v) in enumerate(stems.items()): grava(f"musica-{j + 1}-{k}", v * g)
grava("musica-mix", mix * g)
if len(sys.argv) > 4:
    w = wave.open(sys.argv[4]); c = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767; w.close()
    c = np.pad(c, (0, max(0, N - len(c))))[:N]; grava("musica-mix-com-cliques", mix * g + 0.55 * c[:, None])
nome_grau = ["ré", "mi", "fá#", "sol", "lá", "si", "dó#"]
print(f"fim {FIM:g} s; mapa {INTRO}; mural {MURAL}; passos {passos}; {len(tempos)} entradas de passeio; rotas com comprimento: {sum(1 for k in tours if comprimento(k))}/{len(tours)}")
for (t0, t1, p, ac, era), q in zip(SEG[4:4 + nq], trims): print(f"  {q[0]} T{q[1]}  {t0:6.1f}–{t1:6.1f} s  baixo {nome_grau[p % 7]}{2 + p // 7 + (p % 7 == 6)} ({grau_hz(p):.0f} Hz)")
print("anos:", list(zip(anos, lim_ano)), "| pico de cada camada:", {k: round(float(np.abs(v).max() * g), 3) for k, v in stems.items()})
