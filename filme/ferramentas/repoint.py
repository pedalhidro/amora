#!/usr/bin/env python3
"""Aponta o projeto pras cópias locais da mídia (em vez do mount WebDAV).   repoint.py <projeto> <pasta local> [--apply]"""
import json, os, re, subprocess, sys
proj, DEST = sys.argv[1], os.path.realpath(sys.argv[2])
home = os.path.expanduser("~")
T = f"{proj}/Timelines/D8BB4915-D0A8-4706-B2A1-CE257E6D490F"
iguais = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw0 = open(iguais[0], "rb").read()
for p in iguais: assert open(p, "rb").read() == raw0, f"{p} difere"
outros = [f"{proj}/draft_meta_info.json", f"{proj}/draft_agency_config.json"]
pat = re.compile((re.escape(home) + r"/Amora(Photos|Videos)/([^\"\\]+)").replace("/", r"(?:\\?/)").encode())
plano = {}
for p in [iguais[0]] + outros:
    raw = open(p, "rb").read(); falta = set(); n = 0
    def troca(m):
        global n
        f = f"{DEST}/Amora{m.group(1).decode()}/{m.group(2).decode()}"
        if not os.path.exists(f): falta.add(f); return m.group(0)
        n += 1
        esc = b"\\/" in m.group(0)
        return f.replace("/", "\\/").encode() if esc else f.encode()
    out = pat.sub(troca, raw)
    json.loads(out)
    print(f"{os.path.basename(p)}: {n} caminhos trocados, {len(falta)} sem cópia local {sorted(falta)[:3]}, restam no mount: {len(pat.findall(out))}")
    assert not falta
    plano[p] = out
for p in iguais[1:]: plano[p] = plano[iguais[0]]
a, b = json.loads(raw0), json.loads(plano[iguais[0]])
def volta(o):   # caminhos repontados em qualquer nível (clipes compostos guardam um rascunho aninhado)
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "path" and isinstance(v, str) and v.startswith(DEST + "/"):
                assert os.path.exists(v); o[k] = home + "/" + "/".join(v.split("/")[-2:])
            else: volta(v)
    elif isinstance(o, list):
        for v in o: volta(v)
volta(a); volta(b)   # 'a' também: o que já estava local de uma rodada anterior
assert a == b, "mudou mais do que os caminhos"
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(iguais[0], "rb").read() == raw0
    for p, out in plano.items(): open(p, "wb").write(out)
    print("gravado em", len(plano), "arquivos")
