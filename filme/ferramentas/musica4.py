#!/usr/bin/env python3
"""Trilha SECA e mínima: só notas com começo e fim, sem reverberação, sem eco, sem fundo contínuo. Só a estrutura que precisa:
  seção      mapa: a nota de casa (ré) a cada 5 s, sob os cliques das rotas; mural: a nota de casa, uma oitava abaixo, na entrada e em cada passo
  ano        golpes curtos da multidão em contagem regressiva (3, 2, 1) na virada de cada ano
  trimestre  a ALTURA da nota: desce um grau da escala de ré menor a cada trimestre e chega no ré quando entra o mural
  passeio    UMA nota grave e seca a cada passeio que entra (passeios que entram juntos = uma nota só)
O timbre vem dos vídeos: um estalo do trem excita ressonadores afinados (um seno discreto garante a altura).
  musica4.py <draft_info.json> <pasta de saída> [metronomo.wav]"""
import sys, json, os, re, wave, math, subprocess, collections, numpy as np
from scipy.signal import lfilter, butter, sosfilt, iirpeak
SR = 48000; rng = np.random.default_rng(60)
MIDIA = os.path.expanduser("~/Downloads/1110-midia/AmoraVideos/")
TREM, MULTIDAO = "PH-113_2026-09-25_2150_e6b811f3_360p.webm", "Pedalula-002_2026-10-24_c288d4b6_360p.webm"
D2 = 73.416; MENOR = [0, 2, 3, 5, 7, 8, 10]
grau_hz = lambda p: D2 * 2 ** ((12 * (p // 7) + MENOR[p % 7]) / 12)
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
tempos = sorted({round(a, 3) for a, q in tours.values()})
trims = sorted({q for a, q in tours.values()}, reverse=True)
lim = [INTRO[1]]
for i in range(1, len(trims)):
    ant = [a for a, q in tours.values() if q == trims[i - 1]]; nov = [a for a, q in tours.values() if q == trims[i]]
    lim.append(min([t for t in tempos if t > lim[-1]], key=lambda b: (sum(a >= b for a in ant) + sum(a < b for a in nov), -b)))
anos = sorted({q[0] for q in trims}, reverse=True); lim_ano = [lim[[q[0] for q in trims].index(y)] for y in anos]
nq = len(trims); N = int(SR * FIM)
def le(nome, lo, hi):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", MIDIA + nome, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32).astype(float); assert len(x) > SR, f"sem áudio: {nome}"
    x = sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x); return x / (np.sqrt((x ** 2).mean()) + 1e-9)
trem, mult = le(TREM, 50, 2500), le(MULTIDAO, 150, 1800)
def nota(f, forca=1.0, dur=1.5):
    """Uma nota seca: um estalo de 25 ms do trem em ressonadores afinados em f, 2f, 3f, 4f (cada um apaga sozinho) + um seno discreto em f."""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n); m = int(0.025 * SR); i0 = rng.integers(0, len(trem) - m)
    x[:m] = trem[i0:i0 + m] * np.exp(-np.arange(m) / SR / 0.007)
    y = sum(lfilter(*iirpeak(h, max(6, math.pi * h * tau), fs=SR), x) * w for h, tau, w in zip([f, 2 * f, 3 * f, 4 * f], [0.55, 0.3, 0.16, 0.08], [1, 0.6, 0.35, 0.2]))
    y = y / (np.abs(y).max() + 1e-9) + 0.6 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) * np.minimum(1, t / 0.004)
    nf = int(0.05 * SR); y[-nf:] *= np.linspace(1, 0, nf); return y / np.abs(y).max() * forca
notas, golpes = np.zeros(N + SR * 3), np.zeros(N + SR * 3)
def poe(b, t0, sig):
    i = int(round(t0 * SR)); n = min(len(sig), len(b) - i); b[i:i + n] += sig[:n]
reg = []
for tm in np.arange(INTRO[0], INTRO[1] - 1e-6, 5.0): poe(notas, tm, nota(grau_hz(7), 0.5)); reg.append((float(tm), 7))        # mapa: a casa (ré3)
for tp in tempos:                                                      # conteúdo: uma nota por entrada, na altura do trimestre
    i = max(j for j in range(nq) if lim[j] <= tp + 1e-6); p = nq - i
    forca = 1.0 if tp in lim_ano else 0.85 if tp in lim else 0.6        # a 1ª nota de cada ano e de cada trimestre vem mais forte
    poe(notas, tp, nota(grau_hz(p), forca)); reg.append((tp, p))
for j, tp in enumerate([MURAL[0]] + passos): poe(notas, tp, nota(grau_hz(0), 1.0 if j == 0 else 0.8, 1.9)); reg.append((tp, 0))   # mural: a casa (ré2)
jan = int(0.3 * SR); en = np.convolve(mult ** 2, np.ones(jan) / jan, mode="valid"); picos = []
for i in np.argsort(-en):
    if all(abs(i - q) > jan for q in picos): picos.append(int(i))
    if len(picos) == 3: break
for i, b in enumerate(lim_ano):                                        # anos: 3, 2, 1 golpes
    for q in range(len(anos) - i):
        x = mult[picos[q % 3]:picos[q % 3] + int(0.26 * SR)].copy(); na, nr = int(0.006 * SR), int(0.07 * SR)
        x[:na] *= np.linspace(0, 1, na); x[-nr:] *= np.linspace(1, 0, nr); poe(golpes, b + 0.5 * q, x / np.abs(x).max() * 0.45)
notas, golpes = notas[:N], golpes[:N]; mix = notas + golpes; g = 0.7 / np.abs(mix).max()
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
def grava(nome, x):
    w = wave.open(f"{out}/{nome}.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
grava("seca-1-notas", notas * g); grava("seca-2-anos", golpes * g); grava("seca-mix", mix * g)
if len(sys.argv) > 3:
    w = wave.open(sys.argv[3]); c = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767; w.close()
    grava("seca-mix-com-cliques", mix * g + 0.55 * np.pad(c, (0, max(0, N - len(c))))[:N])
nome = ["ré", "mi", "fá", "sol", "lá", "sib", "dó"]
print(f"fim {FIM:g} s; {len(reg)} notas ({len(tempos)} de passeio); anos {list(zip(anos, lim_ano))}")
for i, q in enumerate(trims):
    p = nq - i; n_ = sum(1 for tp, pp in reg if pp == p and lim[i] <= tp); print(f"  {q[0]} T{q[1]}  desde {lim[i]:6.1f} s  {nome[p % 7]} ({grau_hz(p):.0f} Hz)  {n_} notas")
