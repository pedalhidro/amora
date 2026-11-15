#!/usr/bin/env python3
"""Troca os vídeos do projeto (cópias 360p/720p do amora) pelos originais baixados por baixa_originais.py.
  troca_originais.py <projeto> <pasta dos originais> [--apply]
Só troca o que confere: mesma duração (±0,35 s), mesma proporção (±6 %) e o MESMO quadro em dois instantes (correlação ≥ 0,55) — o
corte de cada clipe na linha do tempo fica como está. O que não confere fica como está e sai na lista. Clipes dentro de compostos: não mexe."""
import copy, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
proj, ORIG = sys.argv[1], os.path.realpath(sys.argv[2])
T = [p for p in sorted(os.listdir(proj + "/Timelines")) if os.path.isfile(f"{proj}/Timelines/{p}/draft_info.json") and open(f"{proj}/Timelines/{p}/draft_info.json", "rb").read() == open(proj + "/draft_info.json", "rb").read()]
assert len(T) == 1; T = f"{proj}/Timelines/{T[0]}"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig)
man = json.load(open(ORIG + "/_manifesto.json")); CONF = ORIG + "/_conferencia.json"; conf = json.load(open(CONF)) if os.path.exists(CONF) else {}
def sonda(p):
    r = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,codec_name,color_transfer:stream_side_data=rotation:stream_tags=rotate:format=duration", "-of", "json", p], capture_output=True, text=True).stdout or "{}")
    if not r.get("streams"): return None
    s = r["streams"][0]; rot = 0
    for sd in s.get("side_data_list", []): rot = sd.get("rotation", rot)
    rot = int(float(s.get("tags", {}).get("rotate", rot) or 0)); w, h = s["width"], s["height"]
    if abs(rot) % 180 == 90: w, h = h, w
    return dict(w=w, h=h, dur=float(r.get("format", {}).get("duration") or 0), codec=s.get("codec_name"), hdr=s.get("color_transfer") in ("arib-std-b67", "smpte2084"))
def quadro(p, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", p, "-frames:v", "1", "-vf", "scale=48:48,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(r, np.uint8).astype(float) if len(r) == 48 * 48 else None
def confere(par):
    h, velho, novo, dur_mat = par
    if h in conf and conf[h].get("novo") == novo: return h, conf[h]
    a, b = sonda(velho), sonda(novo)
    if not a or not b: return h, dict(novo=novo, ok=False, motivo="não deu pra ler o arquivo")
    da = a["dur"] or dur_mat; D = min(da, b["dur"]); cs = []
    for f in (0.25, 0.75):
        qa, qb = quadro(velho, D * f), quadro(novo, D * f)
        if qa is not None and qb is not None and qa.std() > 1 and qb.std() > 1: cs.append(float(np.corrcoef(qa, qb)[0, 1]))
    r = dict(novo=novo, w=b["w"], h=b["h"], dur=b["dur"], dur_amora=da, codec=b["codec"], hdr=b["hdr"], corr=cs, asp=(b["w"] / b["h"]) / (a["w"] / a["h"]))
    motivo = (f"duração difere {b['dur'] - da:+.2f} s" if abs(b["dur"] - da) > 0.35 else f"proporção difere ({r['asp']:.2f}×)" if abs(r["asp"] - 1) > 0.06
              else "quadros não batem" if not cs or max(cs) < 0.55 else None)
    r.update(ok=motivo is None, motivo=motivo); return h, r
mats = [m for m in d["materials"]["videos"] if "/AmoraVideos/" in m["path"]]
pares, sem = {}, set()
for m in mats:
    g = re.search(r"_([0-9a-f]{8})_(?:360p|720p)\.\w+$", m["path"]); h = g.group(1) if g else None
    if h and man.get(h, {}).get("ok") and os.path.exists(f"{ORIG}/{man[h]['arquivo']}"): pares[h] = (h, m["path"], f"{ORIG}/{man[h]['arquivo']}", m["duration"] / 1e6)
    else: sem.add(os.path.basename(m["path"]))
with ThreadPoolExecutor(6) as ex: res = dict(ex.map(confere, pares.values()))
conf.update(res); json.dump(conf, open(CONF, "w"), indent=0)
SEG = {}
for t in d["tracks"]:
    for s in t["segments"]: SEG.setdefault(s["material_id"], []).append(s)
mp = f"{proj}/draft_meta_info.json"; mraw = open(mp, "rb").read(); mo = json.loads(mraw); md = copy.deepcopy(mo); bin_ = {}
def anda(o):
    if isinstance(o, dict):
        if "file_Path" in o: bin_.setdefault(o["file_Path"], []).append(o)
        for v in o.values(): anda(v)
    elif isinstance(o, list):
        for v in o: anda(v)
anda(md)
trocados, recusados, desfaz, vistos = [], {}, [], set()
for m in mats:
    g = re.search(r"_([0-9a-f]{8})_(?:360p|720p)\.\w+$", m["path"]); h = g.group(1) if g else None; r = res.get(h)
    if not r: continue
    motivo = r["motivo"]
    if r["ok"]:
        fim = max((s["source_timerange"]["start"] + s["source_timerange"]["duration"] for s in SEG.get(m["id"], [])), default=0)
        if fim > r["dur"] * 1e6 + 40000: motivo = f"o corte usado vai até {fim / 1e6:.2f} s e o original tem {r['dur']:.2f} s"
    if motivo: recusados[os.path.basename(m["path"])] = motivo; continue
    velho = m["path"]; desfaz.append((m, {k: m[k] for k in ("path", "material_name", "width", "height", "duration")}))
    m.update(path=r["novo"], material_name=os.path.basename(r["novo"]), width=r["w"], height=r["h"], duration=max(round(r["dur"] * 1e6), m["duration"] if abs(r["dur"] * 1e6 - m["duration"]) < 40000 else 0))
    trocados.append((h, r))
    if velho not in vistos:
        vistos.add(velho)
        for e in bin_.get(velho, []):
            e.update(file_Path=r["novo"], extra_info=os.path.basename(r["novo"]), width=r["w"], height=r["h"], duration=round(r["dur"] * 1e6))
            if isinstance(e.get("roughcut_time_range"), dict) and e["roughcut_time_range"].get("duration", -1) > 0: e["roughcut_time_range"]["duration"] = round(r["dur"] * 1e6)
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
for m, antes in desfaz: m.update(antes)                                   # conferência: desfazendo, volta ao que era
assert d == orig, "mudou mais do que devia"
us = {h: r for h, r in trocados}; alt = sorted(min(r["w"], r["h"]) for r in us.values())
print(f"{len(mats)} clipes de vídeo ({len(pares)} arquivos com original baixado); trocados: {len(trocados)} clipes / {len(us)} arquivos; sem original: {len(sem)} arquivos; recusados: {len(recusados)}")
if alt: print(f"resolução dos trocados (lado menor): {alt[0]}–{alt[-1]} px, mediana {alt[len(alt) // 2]}; HDR: {sum(1 for r in us.values() if r['hdr'])}; correlação mínima aceita: {min(max(r['corr']) for r in us.values()):.2f}")
for k, v in sorted(recusados.items()): print("   recusado:", k, "—", v)
print("   sem original:", ", ".join(sorted(sem)))
print("   dentro de clipes compostos (não mexi):", sum(1 for dr in d["materials"].get("drafts", []) for x in dr["draft"]["materials"]["videos"] if "/AmoraVideos/" in x["path"]))
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw and open(mp, "rb").read() == mraw
    for p in alvos: open(p, "wb").write(out)
    mesmo = json.dumps(mo, separators=(",", ":"), ensure_ascii=False).encode() == mraw
    if mesmo: open(mp, "wb").write(json.dumps(md, separators=(",", ":"), ensure_ascii=False).encode())
    print("gravado em", len(alvos) + mesmo, "arquivos")
