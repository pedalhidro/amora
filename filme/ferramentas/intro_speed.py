#!/usr/bin/env python3
"""Encurta (ou alonga) o mapa de abertura mudando a velocidade do clipe, e puxa o resto da linha do tempo junto.
  intro_speed.py <projeto> <segundos> [--apply]      (a trilha de áudio não é tocada: re-renderize o metrônomo depois)"""
import copy, json, os, subprocess, sys
proj, novo = sys.argv[1], round(float(sys.argv[2]) * 1e6)
T = f"{proj}/Timelines/D8BB4915-D0A8-4706-B2A1-CE257E6D490F"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig)
V = {m["id"]: m for m in d["materials"]["videos"]}
intro = [s for t in d["tracks"] if t["type"] == "video" for s in t["segments"] if os.path.basename(V[s["material_id"]]["path"]).startswith("1110-intro")]
assert len(intro) == 1; s = intro[0]; tr = s["target_timerange"]; assert tr["start"] == 0
fim = tr["duration"]; delta = fim - novo; v0 = s["speed"]
sp = [m for m in d["materials"]["speeds"] if m["id"] in s["extra_material_refs"]]; assert len(sp) == 1 and sp[0]["speed"] == v0 and sp[0]["mode"] == 0
vel = s["source_timerange"]["duration"] / novo
s["speed"] = vel; sp[0]["speed"] = vel; tr["duration"] = novo
movidos = []
for t in d["tracks"]:
    for x in t["segments"]:
        if x is s or t["type"] == "audio": continue
        a = x["target_timerange"]["start"]; assert a >= fim, ("começa antes do fim do mapa", t["type"], a)
        x["target_timerange"]["start"] = a - delta; movidos.append(x["id"])
d["duration"] -= delta
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
n = json.loads(out); mv = set(movidos)                       # conferência: desfazendo, volta ao que era
for t in n["tracks"]:
    for x in t["segments"]:
        if x["id"] in mv: x["target_timerange"]["start"] += delta
        if x["id"] == s["id"]: x["speed"] = v0; x["target_timerange"]["duration"] = fim
next(m for m in n["materials"]["speeds"] if m["id"] == sp[0]["id"])["speed"] = v0; n["duration"] += delta
assert n == orig, "mudou mais do que devia"
print(f"mapa: {fim / 1e6:g} s → {novo / 1e6:g} s (velocidade {vel:.6f}×); {len(movidos)} segmentos puxados {delta / 1e6:g} s; projeto {orig['duration'] / 1e6:g} → {d['duration'] / 1e6:g} s")
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw
    for p in alvos: open(p, "wb").write(out)
    print("gravado em", len(alvos), "arquivos")
