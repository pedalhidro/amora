#!/usr/bin/env python3
"""Legendas (texto) pros passeios que ainda não têm, no estilo das que já existem (clona a 'ph93').
  labels_apply.py <projeto> [--apply]
Não mexe nas legendas que já estão lá. A fonte Minuscule (trial) não tem á/í/ó/ú/ã/õ/ç: os nomes novos evitam á/í/ó/ú e mantêm ã/õ/ç, como nas legendas feitas à mão."""
import copy, json, os, re, subprocess, sys, uuid, collections
from PIL import ImageFont
proj = sys.argv[1]
T = f"{proj}/Timelines/D8BB4915-D0A8-4706-B2A1-CE257E6D490F"
alvos = [f"{proj}/draft_info.json", f"{proj}/template-2.tmp", f"{T}/draft_info.json", f"{T}/template-2.tmp"]
raw = open(alvos[0], "rb").read()
for p in alvos: assert open(p, "rb").read() == raw, f"{p} difere"
orig = json.loads(raw); d = copy.deepcopy(orig)
# com "\n" = texto inteiro; sem = só o nome (a 1ª linha vira ph<N>)
NOMES = {"SESC-002": "sesc2\ncartografia bordada", "SESC-001": "sesc1\n%SESC1%", "PH-071": "bonde pedra cachoeira", "PH-070": "cabeceiras ipiranga",
         "PH-069": "tiburtino corujas", "PH-068": "capão do embira", "PH-067": "tietê paraíba", "PH-065": "alpes do jaraguá", "PH-064": "ponte rasa",
         "PH-063": "cumeeiras caaguaçu", "PH-062": "cubatão pilões", "PH-061": "oakland", "PH-060": "águas meridionais", "PH-059": "bico do caaguaçu",
         "PH-057": "três sopés", "PH-055": "ilhota da guapira", "PH-054": "1 ano", "PH-053": "paraisópolis", "PH-052": "rampa do sapateiro",
         "PH-051": "itaquera", "PH-050": "uberaba cupucê", "PH-049": "selas da leste", "PH-048": "sopés da cantareira", "PH-047": "jaguaré e pastel",
         "PH-046": "enchente de 1929", "PH-045": "pirajuçara", "PH-044": "meninos zavuvus", "PH-043": "serra do bananal", "PH-042": "carapicuíba",
         "PH-041": "colina histórica", "PH-040": "crista da mooca",
         "BP-003+PH-076": "ph76 + bp3\ncaaguaçu emboaçu", "PH-056+PH-S-006": "ph56 + phs6\ntrem e meteoro", "PH-S-005": "phs5\njuqueri e dib",
         "PH-039": "agua espraiada", "PH-038": "selas do centro-norte", "PH-S-004": "phs4\ncanions brasilandia", "PH-037": "sertões de pirituba 2",
         "Avistar-2025": "avistar 2025", "PH-035": "vales secos do tiete", "PH-034": "crista do campo limpo", "PH-033": "moinho velho",
         "BT-003+PH-032": "ph32 + bt3\nrios indigenas", "PH-031": "tiquatira", "PH-030": "pirituba jaragua perus", "PH-029": "meridionais de osasco",
         "PH-028": "lavapés aclimação", "PH-027": "sertões do mandaqui", "PH-026": "cabeceiras ipiranga", "PH-025": "pirajuçara agua podre",
         "PH-024": "contornar anhangabau", "PH-023": "crista de sapopema", "PH-022": "contornar pacaembu", "PH-021": "verde e sapateiro",
         "PH-020": "aguas de pinheiros", "PH-019": "nascentes brasilandia", "PH-018": "contornar iquirim", "BP-002+PH-017": "ph17 + bp2\nparanapiacaba",
         "BT-002": "bt2\ntamanduatei acima", "PH-016": "agua preta tiburtino", "PH-015": "parelheiros", "PH-014": "baixo jaguaré",
         "PH-013": "baixo ipiranga", "PH-012": "mirantes do tiete", "PH-011": "pacaembu e sumaré", "BT-001+PH-010": "ph10 + bt1\nabc",
         "PH-009": "sertões de pirituba", "PH-008": "itororo lavapés", "PH-007": "verde anhanguera", "PH-006": "crista de perdizes",
         "PH-005": "santa cecilia saracura", "PH-004": "coruja e bellini", "PH-003": "altos do sumaré", "PH-002": "coruja e verde",
         "PH-001": "agua preta tiburtino"}
NOMES["SESC-001"] = NOMES["SESC-001"].replace("%SESC1%", os.environ.get("SESC1", "sesc"))
V = {m["id"]: m for m in d["materials"]["videos"]}; TX = {m["id"]: m for m in d["materials"]["texts"]}
uid = lambda: str(uuid.uuid4()).upper()
US = 1e6
tours = collections.defaultdict(list)
for t in d["tracks"]:
    if t["type"] != "video": continue
    for s in t["segments"]:
        m = re.match(r"(.+?)_\d{4}-\d\d-\d\d", os.path.basename(V[s["material_id"]]["path"]))
        if m:
            tr = s["target_timerange"]; tours[m.group(1)].append((tr["start"], tr["start"] + tr["duration"], s["clip"]["transform"]["x"], s["clip"]["transform"]["y"]))
info = {k: dict(a=min(x[0] for x in v), b=max(x[1] for x in v), cx=sum(x[2] for x in v) / len(v), cy=sum(x[3] for x in v) / len(v)) for k, v in tours.items()}
ttracks = [t for t in d["tracks"] if t["type"] == "text"]
canto = lambda x, y: (1 if x > 0 else -1, 1 if y > 0 else -1)
# legendas no ar: (início, fim, texto, canto)
noar = [(s["target_timerange"]["start"], s["target_timerange"]["start"] + s["target_timerange"]["duration"], json.loads(TX[s["material_id"]]["content"])["text"],
         canto(s["clip"]["transform"]["x"], s["clip"]["transform"]["y"])) for t in ttracks for s in t["segments"]]
def tem(k):
    a = info[k]["a"]; aqui = [x[2] for x in noar if abs(x[0] - a) < 100000]; juntos = [q for q in info if abs(info[q]["a"] - a) < 100000]
    nums = {str(int(n)) for n in re.findall(r"-(\d+)", k)}
    return len(aqui) >= len(juntos) or any(nums & set(re.findall(r"\d+", x.split("\n")[0])) for x in aqui)
faltam = sorted([k for k in info if not tem(k)], key=lambda k: (info[k]["a"], k))
sem_nome = [k for k in faltam if k not in NOMES]; assert not sem_nome, sem_nome
# modelo: a legenda 'ph93'
mod = next(s for t in ttracks for s in t["segments"] if json.loads(TX[s["material_id"]]["content"])["text"].startswith("ph93\n"))
mmat = TX[mod["material_id"]]; assert json.dumps(mmat).count("zigzag") == 1
manim = next(m for m in d["materials"]["material_animations"] if m["id"] == mod["extra_material_refs"][0]); assert len(mod["extra_material_refs"]) == 1
font = ImageFont.truetype(json.loads(mmat["content"])["styles"][0]["font"]["path"], 100)
larg = lambda txt: max(font.getlength(l) for l in txt.split("\n"))
# calibração: nas legendas de canto que já existem, |x| + k·largura/2 ≈ borda
cal = [(abs(s["clip"]["transform"]["x"]), larg(json.loads(TX[s["material_id"]]["content"])["text"])) for t in ttracks for s in t["segments"]
       if abs(abs(s["clip"]["transform"]["y"]) - 0.935) < 0.002 and abs(s["clip"]["transform"]["x"]) > 0.8 and len(json.loads(TX[s["material_id"]]["content"])["styles"]) == 1]
BORDA = 0.985
ks = sorted((BORDA - x) * 2 / w for x, w in cal); K = ks[len(ks) // 2]
print(f"calibração: {len(cal)} legendas, k mediano {K:.6f} (de {ks[0]:.6f} a {ks[-1]:.6f})")
CANTOS = [(1, -1), (-1, -1), (1, 1), (-1, 1)]               # preferência quando nada decide: embaixo à direita, como ph93/92/90/89
novos = []
for k in faltam:
    i = info[k]
    juntos = [q for q in info if q != k and info[q]["a"] < i["b"] - 1 and i["a"] < info[q]["b"] - 1]
    if juntos:                                              # canto do lado em que os clipes deste passeio estão, em relação aos vizinhos
        dx = i["cx"] - sum(info[q]["cx"] for q in juntos) / len(juntos); dy = i["cy"] - sum(info[q]["cy"] for q in juntos) / len(juntos)
        if abs(dx) < 0.15: dx = 0.01                         # separados só na vertical: à direita
        if abs(dy) < 0.15: dy = -0.01                        # separados só na horizontal: embaixo
        ordem = sorted(CANTOS, key=lambda c: -(c[0] * dx + c[1] * dy))
    else: ordem = CANTOS
    ocupados = {x[3] for x in noar if x[0] < i["b"] and i["a"] < x[1]}
    sx, sy = next(c for c in ordem if c not in ocupados)
    txt = NOMES[k] if ("\n" in NOMES[k] or k == "Avistar-2025") else f"ph{int(k.split('-')[1])}\n{NOMES[k]}"
    noar.append((i["a"], i["b"], txt, (sx, sy)))
    novos.append(dict(k=k, a=i["a"], b=i["b"], txt=txt, x=sx * (BORDA - K * larg(txt) / 2), y=sy * 0.935, sx=sx, sy=sy))
ocup = [[(s["target_timerange"]["start"], s["target_timerange"]["start"] + s["target_timerange"]["duration"]) for s in t["segments"]] for t in ttracks]
trilhas_novas = []
for n in novos:
    ti = next((j for j, oc in enumerate(ocup) if all(n["b"] <= a or n["a"] >= b for a, b in oc)), None)
    if ti is None:                                          # nenhuma trilha de texto livre nesse trecho: abre outra, logo depois da última de texto
        pos = d["tracks"].index(ttracks[-1]) + 1
        nt = {kk: vv for kk, vv in ttracks[-1].items() if kk != "segments"}; nt["id"] = uid(); nt["segments"] = []
        d["tracks"].insert(pos, nt); ttracks.append(nt); ocup.append([]); trilhas_novas.append(nt["id"]); ti = len(ttracks) - 1
        for j in range(pos + 1, len(d["tracks"])):          # as de baixo descem um índice
            for s in d["tracks"][j]["segments"]:
                assert s["track_render_index"] == j - 1; s["track_render_index"] = j
    ocup[ti].append((n["a"], n["b"]))
    m = copy.deepcopy(mmat); c = json.loads(m["content"]); c["text"] = n["txt"]; c["styles"][0]["range"] = [0, len(n["txt"])]
    m.update(id=uid(), content=json.dumps(c, ensure_ascii=False, separators=(",", ":")), alignment=2 if n["sx"] > 0 else 0)
    an = copy.deepcopy(manim); an["id"] = uid()
    s = copy.deepcopy(mod); s.update(id=uid(), material_id=m["id"], extra_material_refs=[an["id"]], target_timerange=dict(start=n["a"], duration=n["b"] - n["a"]))
    s["clip"]["transform"] = dict(x=n["x"], y=n["y"]); n["trilha"] = ttracks[ti]
    d["materials"]["texts"].append(m); d["materials"]["material_animations"].append(an); ttracks[ti]["segments"].append(s); n["seg"] = s
for n in novos:
    n["seg"]["track_render_index"] = d["tracks"].index(n["trilha"])
    print(f"{n['a'] / US:6.1f}–{n['b'] / US:6.1f} trilha {n['seg']['track_render_index']}  {n['txt']!r:38} {'dir' if n['sx'] > 0 else 'esq'}/{'cima' if n['sy'] > 0 else 'baixo'}  x={n['x']:.3f}")
for t in ttracks: t["segments"].sort(key=lambda s: s["target_timerange"]["start"])
for j, t in enumerate(d["tracks"]):
    for s in t["segments"]: assert s["track_render_index"] == j, (j, s["track_render_index"])
for t in ttracks:                                           # nada sobreposto na mesma trilha
    fim = -1
    for s in t["segments"]: assert s["target_timerange"]["start"] >= fim; fim = s["target_timerange"]["start"] + s["target_timerange"]["duration"]
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
# conferência: tirando o que entrou, sobra o que havia
n = json.loads(out); ids = {x["seg"]["id"] for x in novos}; assert not ids & {s["id"] for t in orig["tracks"] for s in t["segments"]}
mids = set()
for t in n["tracks"]:
    for s in t["segments"]:
        if s["id"] in ids: mids |= {s["material_id"], *s["extra_material_refs"]}
n["tracks"] = [t for t in n["tracks"] if t["id"] not in trilhas_novas]
for j, t in enumerate(n["tracks"]):
    t["segments"] = [s for s in t["segments"] if s["id"] not in ids]
    for s in t["segments"]: s["track_render_index"] = j
for kk, v in n["materials"].items():
    if isinstance(v, list): n["materials"][kk] = [m for m in v if not (isinstance(m, dict) and m.get("id") in mids)]
assert n == orig and len(ids) == len(novos) and len(mids) == 2 * len(novos), "mudou mais do que devia"
print(f"{len(novos)} legendas novas, {len(trilhas_novas)} trilha(s) de texto nova(s); {len(raw)} → {len(out)} bytes")
if "--apply" in sys.argv:
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    assert open(alvos[0], "rb").read() == raw
    for p in alvos: open(p, "wb").write(out)
    print("gravado em", len(alvos), "arquivos")
