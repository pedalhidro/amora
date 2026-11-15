#!/usr/bin/env python3
"""Os originais baixados chamam "<hash8>__IMG_1234.MOV"; as outras ferramentas leem o passeio e a data do NOME do arquivo
("PH-118_2026-11-11_…"). Cria, na mesma pasta, um nome com o prefixo do amora pra cada original (hard link: não ocupa espaço) e
aponta o projeto pra ele.   nomes_originais.py <projeto> <pasta dos originais> <pasta AmoraVideos> [--apply]"""
import copy, json, os, re, subprocess, sys
proj, ORIG, AMORA = sys.argv[1], os.path.realpath(sys.argv[2]), sys.argv[3]
T = [p for p in sorted(os.listdir(proj + "/Timelines")) if os.path.isfile(f"{proj}/Timelines/{p}/draft_info.json") and open(f"{proj}/Timelines/{p}/draft_info.json", "rb").read() == open(proj + "/draft_info.json", "rb").read()]
assert len(T) == 1; T = f"{proj}/Timelines/{T[0]}"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw
orig = json.loads(raw); d = copy.deepcopy(orig)
prefixo = {}
for f in os.listdir(AMORA):
    g = re.match(r"(.+)_([0-9a-f]{8})_(?:360p|720p)\.\w+$", f)
    if g: prefixo[g.group(2)] = g.group(1)
mp = f"{proj}/draft_meta_info.json"; mraw = open(mp, "rb").read(); mo = json.loads(mraw); md = copy.deepcopy(mo); bin_ = {}
def anda(o):
    if isinstance(o, dict):
        if "file_Path" in o: bin_.setdefault(o["file_Path"], []).append(o)
        for v in o.values(): anda(v)
    elif isinstance(o, list):
        for v in o: anda(v)
anda(md)
plano, desfaz, sem = {}, [], []
for m in d["materials"]["videos"]:
    if os.path.dirname(m["path"]) != ORIG: continue
    b = os.path.basename(m["path"]); g = re.match(r"([0-9a-f]{8})__(.+)$", b)
    if not g: continue
    if g.group(1) not in prefixo: sem.append(b); continue
    novo = f"{ORIG}/{prefixo[g.group(1)]}_{g.group(1)}__{g.group(2)}"; plano[m["path"]] = novo
    desfaz.append((m, dict(path=m["path"], material_name=m["material_name"]))); m.update(path=novo, material_name=os.path.basename(novo))
for velho, novo in plano.items():
    for e in bin_.get(velho, []): e.update(file_Path=novo, extra_info=os.path.basename(novo))
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
for m, antes in desfaz: m.update(antes)
assert d == orig
print(f"{len(desfaz)} clipes / {len(plano)} arquivos ganham nome com passeio; sem prefixo conhecido: {sem}"); print("  ex.:", os.path.basename(next(iter(plano.values()))) if plano else "-")
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    for velho, novo in plano.items():
        if not os.path.exists(novo): os.link(velho, novo)
        assert os.path.samefile(velho, novo)
    for p in alvos: open(p, "wb").write(out)
    if json.dumps(mo, separators=(",", ":"), ensure_ascii=False).encode() == mraw: open(mp, "wb").write(json.dumps(md, separators=(",", ":"), ensure_ascii=False).encode())
    print("gravado")
