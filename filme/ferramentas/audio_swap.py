#!/usr/bin/env python3
"""Troca arquivos de áudio que já estão na linha do tempo por outros (e ajusta a duração). Volume, trilha muda, fades etc. ficam como estão.
  audio_swap.py <projeto> <antigo> <novo.wav> [<antigo> <novo.wav> ...] [--apply]      (<antigo> = caminho inteiro, ou só o nome se for único)"""
import copy, json, os, subprocess, sys, wave
args = [a for a in sys.argv[1:] if a != "--apply"]; proj = args[0]; pares = list(zip(args[1::2], args[2::2])); assert pares and len(args) % 2 == 1
T = f"{proj}/Timelines/D8BB4915-D0A8-4706-B2A1-CE257E6D490F"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig)
mp = f"{proj}/draft_meta_info.json"; mraw = open(mp, "rb").read(); mo = json.loads(mraw); md = copy.deepcopy(mo)
LOUD = {m["id"]: m for m in d["materials"].get("loudnesses", [])}
desfaz = []                                                             # (objeto novo, {campo: valor antigo}) pra conferência
def muda(o, **kw):
    desfaz.append((o, {k: copy.deepcopy(o[k]) for k in kw})); o.update(kw)
for velho, novo in pares:
    novo = os.path.realpath(novo); w = wave.open(novo); dur = round(w.getnframes() / w.getframerate() * 1e6); w.close()
    mats = [m for m in d["materials"]["audios"] if m["path"] == velho or (os.sep not in velho and os.path.basename(m["path"]) == velho)]; assert len(mats) == 1, (velho, len(mats))
    m = mats[0]; dv, pv = m["duration"], m["path"]
    segs = [s for t in d["tracks"] for s in t["segments"] if s["material_id"] == m["id"]]; assert len(segs) == 1
    s = segs[0]; assert s["source_timerange"] == dict(start=0, duration=dv) and s["target_timerange"]["duration"] == dv and s["speed"] == 1.0
    assert s["target_timerange"]["start"] + dur <= d["duration"], "o novo passa do fim do projeto"
    muda(m, name=os.path.basename(novo), path=novo, duration=dur)
    muda(s["source_timerange"], duration=dur); muda(s["target_timerange"], duration=dur)
    for r in s["extra_material_refs"]:                                   # a medição de volume guarda o trecho medido
        L = LOUD.get(r)
        if L and isinstance(L.get("time_range"), dict) and L["time_range"].get("duration") == dv: muda(L["time_range"], duration=dur)
    ach = []
    def anda(o):
        if isinstance(o, dict):
            if o.get("file_Path") == pv: ach.append(o)
            for v in o.values(): anda(v)
        elif isinstance(o, list):
            for v in o: anda(v)
    anda(md); assert len(ach) <= 1, len(ach)
    for e in ach:
        e.update(file_Path=novo, extra_info=os.path.basename(novo), duration=dur)
        if isinstance(e.get("roughcut_time_range"), dict) and e["roughcut_time_range"].get("duration") == dv: e["roughcut_time_range"]["duration"] = dur
    print(f"{pv.replace(os.path.expanduser('~'), '~')} ({dv / 1e6:g} s) → {os.path.basename(novo)} ({dur / 1e6:g} s); volume {s['volume']:.4f} mantido; na lista de mídia: {len(ach)}")
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
vols = lambda x: [(s["material_id"], s["volume"], s.get("last_nonzero_volume"), t.get("attribute")) for t in x["tracks"] if t["type"] == "audio" for s in t["segments"]]
assert vols(json.loads(out)) == vols(orig), "volume mudou"
for o, antes in reversed(desfaz): o.update(antes)                       # conferência: desfazendo as trocas, volta ao que era
assert d == orig, "mudou mais do que devia"
mesmo = json.dumps(mo, separators=(",", ":"), ensure_ascii=False).encode() == mraw
mout = json.dumps(md, separators=(",", ":"), ensure_ascii=False).encode()
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw and open(mp, "rb").read() == mraw
    for p in alvos: open(p, "wb").write(out)
    if mesmo: open(mp, "wb").write(mout)
    print("gravado em", len(alvos) + mesmo, "arquivos")
