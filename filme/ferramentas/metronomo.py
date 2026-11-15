#!/usr/bin/env python3
"""Metrônomo 60 BPM com um clique de catraca, em três níveis (fraco / médio / forte):
  - mapa de abertura: um clique FRACO por rota (120 rotas), MÉDIO na que cai no segundo inteiro (o acento);
  - FORTE em toda transição: entra um passeio novo, ou a tela inteira troca (corte total), e em cada deslize do mural;
  - MÉDIO no tempo imediatamente antes de um forte;
  - FRACO nos outros segundos.
  metronomo.py freewheel.f32 draft_info.json saida.wav"""
import sys, json, os, re, wave, collections, numpy as np
x = np.fromfile(sys.argv[1], np.float32).astype(float); sr = 48000
T0 = 47.321                                              # o clique mais limpo e isolado da gravação
k = int(T0 * sr); pk = np.abs(x[k - 480:k + 480]).max()
on = k - 480 + int(np.argmax(np.abs(x[k - 480:k + 480]) > 0.2 * pk))
PRE, L = int(sr * 0.002), int(sr * 0.045)
c = x[on - PRE:on - PRE + L].copy()
c[:PRE] *= np.linspace(0, 1, PRE); fo = int(sr * 0.02); c[-fo:] *= np.linspace(1, 0, fo) ** 2
c /= np.abs(c).max()
AMP = dict(forte=0.95, medio=0.5, fraco=0.2); NROTAS = 120
d = json.load(open(sys.argv[2])); M = {m["id"]: m for m in d["materials"]["videos"]}
segs, deslizes, INTRO, MURAL, inicios_mural = [], [], None, None, []
MURAIS = {"1110-mural-10s-60bpm": (1, 3, 5, 7, 9), "1110-numeros-10s": (4, 7)}   # prefixo do arquivo → segundos em que os deslizes começam
passeios = collections.defaultdict(list)
for t in d["tracks"]:
    if t["type"] != "video": continue
    for s in t["segments"]:
        a = s["target_timerange"]["start"] / 1e6; b = a + s["target_timerange"]["duration"] / 1e6
        p = M[s["material_id"]]["path"]; nm = os.path.basename(p)
        if nm.startswith("Screenshot") or "rotas-flash" in p: continue
        if nm.startswith("1110-intro"): INTRO = (a, b); continue
        segs.append((a, b))
        m = re.match(r"(.+?)_\d{4}-\d\d-\d\d", nm)
        if m: passeios[m.group(1)].append(a)
        for pref, qs in MURAIS.items():                                # murais: cada deslize é um forte
            if nm.startswith(pref):
                s0 = s["source_timerange"]["start"] / 1e6; MURAL = a if MURAL is None else min(MURAL, a); inicios_mural.append(a)
                deslizes += [a + (q - s0) / s["speed"] for q in qs if a <= a + (q - s0) / s["speed"] < b]
assert INTRO, "não achei o mapa de abertura"
total = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"] for t in d["tracks"] if t["type"] != "audio" for s in t["segments"]) / 1e6   # fim da imagem (o áudio antigo pode passar)
r3 = lambda v: round(v, 3)
def corte_total(v):
    ini = sum(abs(a - v) < 1e-3 for a, b in segs); at = sum(a <= v + 1e-3 < b for a, b in segs)
    return ini and ini == at
novos = {r3(min(v)) for v in passeios.values()}
cortes = {r3(a) for a, b in segs if corte_total(a)}
fortes = {v for v in novos | cortes | {r3(v) for v in deslizes} | {r3(v) for v in inicios_mural} | {r3(INTRO[1])} if v < total - 1e-3}
medios = {float(np.ceil(v - 1e-6) - 1) for v in fortes} - fortes
medios = {v for v in medios if v >= 0}
y = np.zeros(int(sr * total) + L)
def clique(tempo, nivel):
    j = max(0, round(tempo * sr) - PRE); y[j:j + L] += c * AMP[nivel]
rotas = [r3(INTRO[0] + i * (INTRO[1] - INTRO[0]) / NROTAS) for i in range(NROTAS)]
ev = {v: ("medio" if v == int(v) else "fraco") for v in rotas}   # no mapa: um clique fraco por rota, com acento (médio) no tempo
for s in range(int(np.ceil(INTRO[1] - 1e-6)), int(np.ceil(total))): ev[float(s)] = "fraco"
for v in medios: ev[v] = "medio"
for v in fortes: ev[v] = "forte"
for v, n in ev.items(): clique(v, n)
wv = wave.open(sys.argv[3], "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((np.clip(y[:int(sr * total)], -1, 1) * 32767).astype("<i2").tobytes()); wv.close()
f = lambda L_: [int(v) if v == int(v) else v for v in sorted(L_)]
print("total", total, "s; mapa", INTRO, "; mural em", MURAL)
print("fortes:", f(fortes))
print("  dos quais só corte total (sem passeio novo):", f(cortes - novos - {r3(INTRO[1])} - {r3(v) for v in inicios_mural}))
print("  passeio novo sem corte total:", f(novos - cortes))
print("  fora do segundo inteiro:", [v for v in sorted(fortes) if v != int(v)])
print("médios:", f(medios))
print("fracos (fora do mapa):", sum(1 for v, n in ev.items() if n == "fraco" and v >= INTRO[1] - 1e-3), "| cliques no mapa:", sum(1 for v in ev if v < INTRO[1] - 1e-3))
