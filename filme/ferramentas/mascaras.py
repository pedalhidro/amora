#!/usr/bin/env python3
"""Bordas suaves em todos os clipes de passeio: copia o desfoque (feather) e o canto arredondado de uma máscara-modelo feita à mão no CapCut.
  mascaras.py <projeto> <trecho do nome do clipe modelo> [--modelo <outro projeto>] [--apply]
- clipe que JÁ tem máscara (recorte feito à mão): fica com a geometria dele e ganha só o feather e o canto do modelo;
- clipe sem máscara: ganha um retângulo um pouco menor que o clipe (FOLGA) pra o desfoque caber dentro, e cresce 1/FOLGA pra
  continuar ocupando o mesmo lugar na tela;
- mapa, murais, logo e clipes compostos: não mudam. Rodar de novo não acumula (quem já tem máscara só tem os valores igualados)."""
import copy, json, os, re, subprocess, sys, uuid
args = [a for a in sys.argv[1:] if not a.startswith("--")]; proj, trecho = args[0], args[1]
MOD = sys.argv[sys.argv.index("--modelo") + 1] if "--modelo" in sys.argv else proj
if "--modelo" in sys.argv: args = [a for a in args if a != MOD]
FOLGA = 0.95
T = [p for p in sorted(os.listdir(proj + "/Timelines")) if os.path.isfile(f"{proj}/Timelines/{p}/draft_info.json") and open(f"{proj}/Timelines/{p}/draft_info.json", "rb").read() == open(proj + "/draft_info.json", "rb").read()]
assert len(T) == 1; T = f"{proj}/Timelines/{T[0]}"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig)
dm = json.load(open(MOD + "/draft_info.json")); VM = {m["id"]: m for m in dm["materials"]["videos"]}; MKM = {m["id"]: m for m in dm["materials"].get("common_mask", [])}
mods = [MKM[r] for t in dm["tracks"] for s in t["segments"] if s["material_id"] in VM and trecho in VM[s["material_id"]]["path"] for r in s["extra_material_refs"] if r in MKM]
assert len(mods) == 1, f"{len(mods)} máscaras em clipes com '{trecho}' no nome"; modelo = mods[0]; FE, RC = modelo["config"]["feather"], modelo["config"]["roundCorner"]
V = {m["id"]: m for m in d["materials"]["videos"]}; d["materials"].setdefault("common_mask", []); MK = {m["id"]: m for m in d["materials"]["common_mask"]}
KIND = {m["id"]: k for k, v in d["materials"].items() if isinstance(v, list) for m in v if isinstance(m, dict) and "id" in m}
uid = lambda: str(uuid.uuid4()).upper(); novas, igualadas, ja = [], [], 0; desfaz = []
for t in d["tracks"]:
    if t["type"] != "video": continue
    for s in t["segments"]:
        m = V[s["material_id"]]
        if not re.match(r".+?_\d{4}-\d\d-\d\d", os.path.basename(m["path"])): continue
        tem = [MK[r] for r in s["extra_material_refs"] if r in MK]
        if tem:
            c = tem[0]["config"]
            if (c["feather"], c["roundCorner"]) == (FE, RC): ja += 1; continue
            desfaz.append(("cfg", tem[0], c["feather"], c["roundCorner"])); c["feather"], c["roundCorner"] = FE, RC; igualadas.append(s["id"]); continue
        mk = copy.deepcopy(modelo); mk["id"] = uid(); mk["constant_material_id"] = uid()
        mk["config"].update(width=FOLGA, height=FOLGA, centerX=0.0, centerY=0.0, rotation=0.0, feather=FE, roundCorner=RC, invert=False, expansion=0.0)
        d["materials"]["common_mask"].append(mk); refs = s["extra_material_refs"]
        pos = next((i for i, r in enumerate(refs) if KIND.get(r) == "canvases"), len(refs))                  # onde o CapCut põe: logo antes do "canvases"
        desfaz.append(("novo", s, list(refs), s.get("enable_video_mask"), copy.deepcopy(s["clip"]["scale"]), mk["id"]))
        refs.insert(pos, mk["id"]); s["enable_video_mask"] = True
        s["clip"]["scale"] = dict(x=s["clip"]["scale"]["x"] / FOLGA, y=s["clip"]["scale"]["y"] / FOLGA); novas.append(s["id"])
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
ids_novos = {x[5] for x in desfaz if x[0] == "novo"}                       # conferência: desfazendo, volta ao que era
for x in desfaz:
    if x[0] == "cfg": x[1]["config"]["feather"], x[1]["config"]["roundCorner"] = x[2], x[3]
    else: _, s, refs, en, sc, _ = x; s["extra_material_refs"] = refs; s["clip"]["scale"] = sc; s["enable_video_mask"] = en
d["materials"]["common_mask"] = [m for m in d["materials"]["common_mask"] if m["id"] not in ids_novos]
if not orig["materials"].get("common_mask") and "common_mask" not in orig["materials"]: d["materials"].pop("common_mask", None)
assert d == orig, "mudou mais do que devia"
print(f"modelo: feather {FE}, canto {RC}; máscaras novas: {len(novas)} (clipes crescem {1 / FOLGA:.3f}×); máscaras já existentes igualadas: {len(igualadas)}; já estavam iguais: {ja}")
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw
    for p in alvos: open(p, "wb").write(out)
    print("gravado em", len(alvos), "arquivos")
