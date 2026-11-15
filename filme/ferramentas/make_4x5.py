#!/usr/bin/env python3
"""Gera um projeto do CapCut em RETRATO (1080×1350, post do Instagram) a partir do projeto deitado. Só LÊ a origem.
  make_4x5.py <projeto origem> <projeto destino> [--previa pasta] [--apply] [--refaz] [--sem-cortes]
O que muda: tela 1080×1350; cada cena (clipes que se sobrepõem no tempo) vira um mosaico de fileiras justificadas, sem sobreposição,
com os clipes de cada passeio juntos; as legendas vão pro pé do bloco do passeio delas, centralizadas; mapa de abertura, mural de artes
e mural de números trocam pelos renders em retrato (mesma duração e mesmos tempos — a trilha não muda). Tempos, cortes e áudio: intactos.
--apply cria o destino (cópia inteira da origem + registro na lista do CapCut); --refaz regrava só a linha do tempo de um destino que já
existe (APAGA o que tiver sido editado à mão nele). Quando um passeio entra ou sai no meio de uma cena, os clipes que atravessam esse
instante são cortados ali e a tela é re-ladrilhada (--sem-cortes desliga: cada clipe fica inteiro, numa posição só)."""
import copy, json, os, re, shutil, subprocess, sys, time, uuid, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut_layout import tamanho, ret
args = [a for a in sys.argv[1:] if not a.startswith("--")]; SRC, DST = os.path.realpath(args[0]), os.path.abspath(args[1]); assert SRC != DST
PREVIA = sys.argv[sys.argv.index("--previa") + 1] if "--previa" in sys.argv else None
if PREVIA: args.remove(PREVIA) if PREVIA in args else None
CW, CH, GAP = 1080, 1350, 6
DL = os.path.expanduser("~/Downloads/")
NOVOS = {"1110-intro": DL + "1110-intro-3d-60bpm-4x5.mp4", "1110-mural-10s-60bpm": DL + "1110-mural-10s-60bpm-4x5.mp4", "1110-numeros-10s": DL + "1110-numeros-10s-60bpm-4x5.mp4"}
raw = open(SRC + "/draft_info.json", "rb").read()
TL = [p for p in sorted(os.listdir(SRC + "/Timelines")) if os.path.isfile(f"{SRC}/Timelines/{p}/draft_info.json") and open(f"{SRC}/Timelines/{p}/draft_info.json", "rb").read() == raw]
assert len(TL) == 1, TL; TL = TL[0]
orig = json.loads(raw); d = copy.deepcopy(orig); SW, SH = orig["canvas_config"]["width"], orig["canvas_config"]["height"]
V = {m["id"]: m for m in d["materials"]["videos"]}; DR = {x["id"]: x for x in d["materials"].get("drafts", [])}; TX = {m["id"]: m for m in d["materials"]["texts"]}
base = lambda m: os.path.basename(m["path"])
chave = lambda nm: (re.match(r"(.+?)_\d{4}-\d\d-\d\d", nm) or [None, None])[1]
norm = lambda cx, cy: dict(x=(cx - CW / 2) / (CW / 2), y=-(cy - CH / 2) / (CH / 2))

# ---------- 1. telas especiais ----------
d["canvas_config"]["width"], d["canvas_config"]["height"] = CW, CH
especiais, outros, cont = [], [], []
for ti, t in enumerate(d["tracks"]):
    if t["type"] != "video": continue
    for s in t["segments"]:
        m = V[s["material_id"]]; nm = base(m); pref = next((p for p in NOVOS if nm.startswith(p)), None)
        if pref:
            novo = NOVOS[pref]; assert os.path.exists(novo), novo
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", novo], capture_output=True, text=True).stdout)
            assert abs(dur * 1e6 - m["duration"]) < 50000, (novo, dur, m["duration"])
            m.update(path=novo, material_name=os.path.basename(novo), width=CW, height=CH)
            s["clip"]["scale"] = dict(x=1.0, y=1.0); s["clip"]["transform"] = dict(x=0.0, y=0.0); especiais.append(nm)
        elif "placeholder" in m["path"] or chave(nm): cont.append((ti, s))
        else: outros.append(nm)

# ---------- 2. clipes de conteúdo ----------
def info(ti, s):
    m = V[s["material_id"]]; a = s["target_timerange"]["start"]; b = a + s["target_timerange"]["duration"]; c = s["clip"]
    ocx, ocy = SW / 2 * (1 + c["transform"]["x"]), SH / 2 * (1 - c["transform"]["y"])
    if "placeholder" in m["path"]:                                       # clipe composto: uma tela 16:9 com um clipe pequeno dentro
        dd = next(DR[r] for r in s["extra_material_refs"] if r in DR)["draft"]
        isg = [x for t in dd["tracks"] if t["type"] == "video" for x in t["segments"]][0]; im = {x["id"]: x for x in dd["materials"]["videos"]}[isg["material_id"]]
        icw, ich = dd["canvas_config"]["width"], dd["canvas_config"]["height"]; cx_i, cy_i, w_i, h_i = ret(isg, im, icw, ich)
        fo = min(SW / m["width"], SH / m["height"]) * c["scale"]["x"]
        return dict(ti=ti, s=s, m=m, a=a, b=b, asp=w_i / h_i, cx=ocx + (cx_i - icw / 2) * fo, cy=ocy + (cy_i - ich / 2) * fo, tour=chave(base(im)), comp=(cx_i - icw / 2, cy_i - ich / 2, w_i), rot=0)
    Wc, Hc = tamanho(m); rot = round(c.get("rotation") or 0); a0 = Wc * (c["scale"]["x"] / c["scale"]["y"]) / Hc
    return dict(ti=ti, s=s, m=m, a=a, b=b, asp=a0 if rot % 180 == 0 else 1 / a0, cx=ocx, cy=ocy, tour=chave(base(m)), comp=None, rot=rot)
# ---------- 2b. cenas, e re-ladrilhar no tempo ----------
# Cena = clipes que se sobrepõem no tempo. Dentro dela, toda vez que um passeio entra ou sai a tela é re-ladrilhada: o clipe que
# atravessa esse instante é CORTADO ali (como o "dividir" do CapCut) e cada pedaço ganha a posição do seu trecho.
MAT = {}
for kk, v in d["materials"].items():
    if isinstance(v, list):
        for m in v:
            if isinstance(m, dict) and "id" in m: MAT[m["id"]] = (kk, m)
uid = lambda: str(uuid.uuid4()).upper()
novos_seg, novos_mat, mexidos, fades0 = set(), set(), {}, {}
def clona_mat(mid):
    kk, m = MAT[mid]; c = copy.deepcopy(m); c["id"] = uid(); d["materials"][kk].append(c); MAT[c["id"]] = (kk, c); novos_mat.add(c["id"]); return c
def fades_de(p):
    out_ = [MAT[r][1] for r in p["extra_material_refs"] if r in MAT and MAT[r][0] == "audio_fades"]
    m = MAT[p["material_id"]][1]
    if isinstance(m.get("audio_fade"), dict): out_.append(m["audio_fade"])
    return out_
def divide(trilha, s, cortes):
    a = s["target_timerange"]["start"]; b = a + s["target_timerange"]["duration"]; sp = s.get("speed") or 1.0
    src = copy.deepcopy(s.get("source_timerange")); mexidos[s["id"]] = (copy.deepcopy(s["target_timerange"]), src)
    for f in fades_de(s): fades0[id(f)] = (f, f.get("fade_in_duration"), f.get("fade_out_duration"))
    molde = copy.deepcopy(s); lim = [a] + list(cortes) + [b]; pecas = []
    for i in range(len(lim) - 1):
        p = s if i == 0 else copy.deepcopy(molde)
        if i > 0:
            p["id"] = uid(); novos_seg.add(p["id"]); p["material_id"] = clona_mat(molde["material_id"])["id"]
            p["extra_material_refs"] = [clona_mat(r)["id"] if r in MAT else r for r in molde["extra_material_refs"]]
            trilha["segments"].append(p)
        p["target_timerange"] = dict(start=lim[i], duration=lim[i + 1] - lim[i])
        if src is not None: p["source_timerange"] = dict(start=src["start"] + round((lim[i] - a) * sp), duration=round((lim[i + 1] - lim[i]) * sp))
        for f in fades_de(p):                                            # fade de entrada só no 1º pedaço, de saída só no último
            if i > 0 and "fade_in_duration" in f: f["fade_in_duration"] = 0
            if i < len(lim) - 2 and "fade_out_duration" in f: f["fade_out_duration"] = 0
        pecas.append(p)
    trilha["segments"].sort(key=lambda z: z["target_timerange"]["start"])
def tour_do(s):
    m = V[s["material_id"]]
    if "placeholder" not in m["path"]: return chave(base(m))
    dd = next(DR[r] for r in s["extra_material_refs"] if r in DR)["draft"]
    isg = [x for t in dd["tracks"] if t["type"] == "video" for x in t["segments"]][0]; return chave(base({x["id"]: x for x in dd["materials"]["videos"]}[isg["material_id"]]))
ini_fim = lambda s: (s["target_timerange"]["start"], s["target_timerange"]["start"] + s["target_timerange"]["duration"])
pre = sorted(((*ini_fim(s), ti, s) for ti, s in cont), key=lambda z: (z[0], z[1]))
span = {}
for a, b, ti, s in pre:
    k = tour_do(s)
    if k: x0, x1 = span.get(k, (1e18, 0)); span[k] = (min(x0, a), max(x1, b))
blocos, fim = [], -1                                                     # (início, fim) de cada cena
for a, b, ti, s in pre:
    if a >= fim: blocos.append([a, b]); fim = b
    else: blocos[-1][1] = max(blocos[-1][1], b); fim = blocos[-1][1]
CORTES = [] if "--sem-cortes" in sys.argv else sorted({c for a0, b0 in blocos for (ta, tb) in span.values() for c in (ta, tb) if a0 < c < b0})
MINP = 400000                                                            # não cria pedaço menor que 0,4 s
def cortes_pra(a, b):
    out_, ult = [], a
    for c in CORTES:
        if c - ult >= MINP and b - c >= MINP and a < c < b: out_.append(c); ult = c
    return out_
for a, b, ti, s in pre:
    if "placeholder" in V[s["material_id"]]["path"]: continue             # composto: fica inteiro
    cs = cortes_pra(a, b)
    if cs: divide(d["tracks"][ti], s, cs)
for t in d["tracks"]:
    if t["type"] != "text": continue
    for s in list(t["segments"]):
        cs = cortes_pra(*ini_fim(s))
        if cs: divide(t, s, cs)
V = {m["id"]: m for m in d["materials"]["videos"]}; TX = {m["id"]: m for m in d["materials"]["texts"]}
cont = [(ti, s) for ti, t in enumerate(d["tracks"]) if t["type"] == "video" for s in t["segments"]
        if not any(base(V[s["material_id"]]).startswith(os.path.basename(p)) for p in NOVOS.values()) and ("placeholder" in V[s["material_id"]]["path"] or chave(base(V[s["material_id"]])))]
segs = sorted((info(ti, s) for ti, s in cont), key=lambda x: (x["a"], x["b"]))
grupos = collections.OrderedDict()                                       # (cena, trecho entre cortes) → clipes
for x in segs:
    meio = (x["a"] + x["b"]) / 2; bi = next(i for i, (a0, b0) in enumerate(blocos) if a0 <= meio < b0)
    grupos.setdefault((bi, sum(c <= meio for c in CORTES)), []).append(x)
cenas = list(grupos.values())

def resolve(lanes):
    """Fileiras justificadas: cada fileira ocupa a largura toda; escolhe a divisão (contígua, na ordem dada) que mais enche a tela."""
    melhor = None
    passeios = collections.OrderedDict()
    for l in sorted(lanes, key=lambda l: l["cx"]): passeios.setdefault(l["tour"], []).append(l)
    # quem entra primeiro fica em cima (a tela enche de cima pra baixo); empate: da esquerda pra direita, como no original
    ordem_p = sorted(passeios, key=lambda p: (min(l["t0"] for l in passeios[p]), sum(l["cx"] * l["peso"] for l in passeios[p]) / sum(l["peso"] for l in passeios[p])))
    ordens = [[l for p in ordem_p for l in sorted(passeios[p], key=lambda l: (l["t0"], 0 if l["cy"] < SH * 0.62 else 1, l["cx"]))],
              [l for p in ordem_p for l in sorted(passeios[p], key=lambda l: (l["t0"], -l["asp"]))],
              [l for p in ordem_p for l in sorted(passeios[p], key=lambda l: (l["t0"], l["asp"]))]]
    K = len(lanes)
    for oi, ordem in enumerate(ordens):
        for mask in range(1 << (K - 1)):
            fileiras, cur = [], [ordem[0]]
            for i in range(1, K):
                if mask >> (i - 1) & 1: fileiras.append(cur); cur = [ordem[i]]
                else: cur.append(ordem[i])
            fileiras.append(cur)
            if len(fileiras) > 6: continue
            hs = [(CW - GAP * (len(f) - 1)) / sum(l["asp"] for l in f) for f in fileiras]
            Ht = sum(hs) + GAP * (len(fileiras) - 1); k = min(1.0, CH / Ht)
            areas = [l["asp"] * h * h * k * k for f, h in zip(fileiras, hs) for l in f]
            nota = sum(areas) / (CW * CH) + 0.18 * min(areas) / max(areas) - 0.01 * oi
            if melhor is None or nota > melhor[0]: melhor = (nota, fileiras, hs, k, Ht, sum(areas) / (CW * CH))
    _, fileiras, hs, k, Ht, enche = melhor
    y = (CH - Ht * k) / 2; rets = {}
    for f, h in zip(fileiras, hs):
        larg = sum(l["asp"] * h for l in f) * k + GAP * k * (len(f) - 1); x = (CW - larg) / 2
        for l in f:
            w = l["asp"] * h * k; rets[l["id"]] = (x, y, w, h * k); x += w + GAP * k
        y += h * k + GAP * k
    return rets, enche, len(fileiras)

ret_seg, cena_de, resumo = {}, {}, []
for ci, cena in enumerate(cenas):
    vagas = []                                                           # uma "vaga" é uma célula; clipes que não coexistem no tempo podem dividir a mesma
    for x in sorted(cena, key=lambda x: (x["a"], x["ti"])):
        prox = lambda v: max(x["asp"], v["asp"]) / min(x["asp"], v["asp"])
        livres_ = [v for v in vagas if v["fim"] <= x["a"] + 1000 and prox(v) <= (2.5 if v["ti"] == x["ti"] else 1.5)]
        v = min(livres_, key=lambda v: (v["ti"] != x["ti"], v["tour"] != x["tour"], prox(v))) if livres_ else None
        if v is None: v = dict(id=len(vagas), l=[], asp=x["asp"]); vagas.append(v)
        v["l"].append(x); v.update(fim=x["b"], ti=x["ti"], tour=x["tour"]); x["vaga"] = v["id"]
    lanes = []
    for v in vagas:
        l = v["l"]; dom = max(l, key=lambda x: x["b"] - x["a"]); peso = sum(x["b"] - x["a"] for x in l)
        lanes.append(dict(id=v["id"], asp=dom["asp"], tour=dom["tour"], peso=peso, t0=min(x["a"] for x in l), cx=sum(x["cx"] * (x["b"] - x["a"]) for x in l) / peso, cy=sum(x["cy"] * (x["b"] - x["a"]) for x in l) / peso))
    rets, enche, nf = resolve(lanes)
    resumo.append((cena[0]["a"] / 1e6, max(x["b"] for x in cena) / 1e6, len(lanes), nf, enche, len({x["ti"] for x in cena})))
    for x in cena:
        rx, ry, rw, rh = rets[x["vaga"]]; ret_seg[x["s"]["id"]] = (rx, ry, rw, rh); cena_de[x["s"]["id"]] = ci
        fw, fh = (rw, rw / x["asp"]) if x["asp"] > rw / rh else (rh * x["asp"], rh)       # o clipe inteiro dentro da célula
        ccx, ccy = rx + rw / 2, ry + rh / 2; c = x["s"]["clip"]; m = x["m"]
        if x["comp"]:
            dx, dy, w_i = x["comp"]; fo = min(CW / m["width"], CH / m["height"]); S = fw / (w_i * fo)
            c["scale"] = dict(x=S, y=S); c["transform"] = norm(ccx - dx * fo * S, ccy - dy * fo * S)
        else:
            Wc, Hc = tamanho(m); fit = min(CW / Wc, CH / Hc); uw, uh = (fw, fh) if x["rot"] % 180 == 0 else (fh, fw)
            igual = abs(c["scale"]["x"] - c["scale"]["y"]) < 1e-9; sx = uw / (Wc * fit)
            c["scale"] = dict(x=sx, y=sx if igual else uh / (Hc * fit)); c["transform"] = norm(ccx, ccy)
    rs = list(rets.values())                                             # conferência: dentro da tela, sem sobreposição
    for i, (x0, y0, w, h) in enumerate(rs):
        assert x0 > -1 and y0 > -1 and x0 + w < CW + 1 and y0 + h < CH + 1, (ci, x0, y0, w, h)
        for (x1, y1, w1, h1) in rs[i + 1:]: assert x0 + w <= x1 + 0.5 or x1 + w1 <= x0 + 0.5 or y0 + h <= y1 + 0.5 or y1 + h1 <= y0 + 0.5, ci

# ---------- 3. legendas ----------
textos = sorted(((s["target_timerange"]["start"], s["target_timerange"]["start"] + s["target_timerange"]["duration"], s) for t in d["tracks"] if t["type"] == "text" for s in t["segments"]), key=lambda z: z[0])
dono, livres = {}, collections.defaultdict(list)
for a, b, s in textos:
    cands = [k for k, (ta, tb) in span.items() if abs(ta - a) < 50000 and abs(tb - b) < 50000] or sorted((k for k, (ta, tb) in span.items() if ta < b and a < tb), key=lambda k: -(min(b, span[k][1]) - max(a, span[k][0])))[:3]
    digs = set(re.findall(r"\d+", json.loads(TX[s["material_id"]]["content"])["text"].split("\n")[0]))
    certos = [k for k in cands if {str(int(n)) for n in re.findall(r"-(\d+)", k)} & digs]
    if len(certos) >= 1: dono[s["id"]] = certos[0]
    else: livres[(a, b)].append((s, cands))
for (a, b), l in livres.items():                                         # sem número que decida: o que sobrou, da esquerda pra direita
    usados = {dono[s["id"]] for aa, bb, s in textos if s["id"] in dono and aa < b and a < bb}
    for s, cands in sorted(l, key=lambda z: z[0]["clip"]["transform"]["x"]):
        resto = [k for k in cands if k not in usados] or cands
        if resto: dono[s["id"]] = sorted(resto, key=lambda k: sum(x["cx"] for x in segs if x["tour"] == k) / max(1, sum(1 for x in segs if x["tour"] == k)))[0]; usados.add(dono[s["id"]])
postas, sem_dono = [], 0
for a, b, s in textos:
    k = dono.get(s["id"]); meus = [ret_seg[x["s"]["id"]] for x in segs if x["tour"] == k and x["a"] < b and a < x["b"]] if k else []
    if not meus: meus = [ret_seg[x["s"]["id"]] for x in segs if x["a"] < b and a < x["b"]]; sem_dono += 1
    if not meus: continue
    x0, y0 = min(r[0] for r in meus), min(r[1] for r in meus); x1, y1 = max(r[0] + r[2] for r in meus), max(r[1] + r[3] for r in meus)
    meia = 12 + 11.5 * max(len(l) for l in json.loads(TX[s["material_id"]]["content"])["text"].split("\n"))   # meia largura estimada do texto (px), por cima
    cx = min(max((x0 + x1) / 2, meia), CW - meia) if 2 * meia < CW else CW / 2
    cands = [min(y1 - 62, CH - 62), max(y0 + 62, 62)] + [min(y1 - 62, CH - 62) - 115 * j for j in range(1, 8)]
    cy = next((y for y in cands if y > 50 and not any(aa < b and a < bb and abs(px - cx) < pm + meia and abs(py - y) < 105 for aa, bb, px, py, pm in postas)), cands[0])
    postas.append((a, b, cx, cy, meia)); s["clip"]["transform"] = norm(cx, cy); TX[s["material_id"]]["alignment"] = 1

# ---------- relatório ----------
e = sorted(r[4] for r in resumo)
print(f"{len(segs)} clipes em {len(cenas)} cenas; ocupação da tela: mediana {e[len(e) // 2]:.0%}, pior {e[0]:.0%}, melhor {e[-1]:.0%}; {len(textos)} legendas ({sem_dono} sem passeio definido)")
print(f"cortes pra re-ladrilhar: {len(CORTES)} instantes, {len(novos_seg)} pedaços novos ({sum(1 for k in mexidos)} clipes/legendas divididos)")
print("células poupadas por dividir vaga:", sum(r[5] - r[2] for r in resumo), "em", sum(r[5] > r[2] for r in resumo), "cenas")
print("telas trocadas:", especiais, "| deixados como estão:", sorted(set(outros)))
for a, b, nl, nf, en, ntr in resumo:
    if en < 0.62: print(f"   cena {a:6.1f}–{b:6.1f} s: {nl} clipes em {nf} fileiras, ocupa {en:.0%}")
out = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
chk = json.loads(out)                                                    # conferência: fora tela/posição/escala/3 arquivos, é o projeto de origem
for tr in chk["tracks"]:
    tr["segments"] = [s for s in tr["segments"] if s["id"] not in novos_seg]
    for s in tr["segments"]:
        if s["id"] in mexidos: s["target_timerange"], s["source_timerange"] = copy.deepcopy(mexidos[s["id"]][0]), copy.deepcopy(mexidos[s["id"]][1])
for kk, v in chk["materials"].items():
    if isinstance(v, list): chk["materials"][kk] = [m for m in v if not (isinstance(m, dict) and m.get("id") in novos_mat)]
FD = {f["id"]: (fi, fo) for f, fi, fo in fades0.values() if "id" in f}
for m in chk["materials"].get("audio_fades", []) + [m["audio_fade"] for m in chk["materials"]["videos"] if isinstance(m.get("audio_fade"), dict)]:
    if m.get("id") in FD: m["fade_in_duration"], m["fade_out_duration"] = FD[m["id"]]
chk["canvas_config"] = copy.deepcopy(orig["canvas_config"])
OV = {m["id"]: m for m in orig["materials"]["videos"]}; OT = {m["id"]: m for m in orig["materials"]["texts"]}
for m in chk["materials"]["videos"]:
    for kk in ("path", "material_name", "width", "height"): m[kk] = OV[m["id"]][kk]
for m in chk["materials"]["texts"]: m["alignment"] = OT[m["id"]]["alignment"]
OS = {s["id"]: s for t in orig["tracks"] for s in t["segments"]}
for t in chk["tracks"]:
    for s in t["segments"]:
        if t["type"] in ("video", "text"): s["clip"]["scale"] = OS[s["id"]]["clip"]["scale"]; s["clip"]["transform"] = OS[s["id"]]["clip"]["transform"]
assert chk == orig, "mudou mais do que devia"
if PREVIA:
    os.makedirs(PREVIA, exist_ok=True); open(PREVIA + "/draft_info.json", "wb").write(out); print("prévia em", PREVIA)
if "--apply" not in sys.argv and "--refaz" not in sys.argv: sys.exit()

# ---------- gravação ----------
if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
assert open(SRC + "/draft_info.json", "rb").read() == raw
RAIZ = os.path.dirname(DST); NOME = os.path.basename(DST); assert os.path.dirname(SRC) == RAIZ
novo = not os.path.exists(DST)
if novo:
    assert "--apply" in sys.argv, "o destino não existe: use --apply"
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".locked"), symlinks=True)
    for raiz, _, fs in os.walk(DST):                                     # caminhos absolutos que apontam pro projeto de origem passam a apontar pra cópia
        for f in fs:
            p = os.path.join(raiz, f)
            if os.path.getsize(p) > 60_000_000: continue
            b = open(p, "rb").read()
            n = b.replace(SRC.encode(), DST.encode()).replace(SRC.replace("/", "\\/").encode(), DST.replace("/", "\\/").encode())
            if n != b: open(p, "wb").write(n)
    mp = DST + "/draft_meta_info.json"; mraw = open(mp, "rb").read(); meta = json.loads(mraw); DID = str(uuid.uuid4()).upper(); agora = int(time.time() * 1e6)
    compacto = json.dumps(meta, separators=(",", ":"), ensure_ascii=False).encode() == mraw
    meta.update(draft_id=DID, draft_name=NOME, draft_fold_path=DST, tm_draft_create=agora, tm_draft_modified=agora)
    open(mp, "wb").write(json.dumps(meta, separators=(",", ":"), ensure_ascii=False).encode() if compacto else json.dumps(meta, ensure_ascii=False).encode())
else:
    assert "--refaz" in sys.argv, "o destino já existe: --refaz regrava a linha do tempo dele (apaga edições feitas à mão)"
for p in ("draft_info.json", "draft_info.json.bak", "template-2.tmp", f"Timelines/{TL}/draft_info.json", f"Timelines/{TL}/draft_info.json.bak", f"Timelines/{TL}/template-2.tmp"):
    if os.path.exists(f"{DST}/{p}") or not p.endswith(".bak"): open(f"{DST}/{p}", "wb").write(out)
st = DST + "/draft_settings"
if os.path.exists(st):
    t = open(st, encoding="utf-8").read(); t = re.sub(r"custom_ratio_height=\d+", f"custom_ratio_height={CH}", t); t = re.sub(r"custom_ratio_width=\d+", f"custom_ratio_width={CW}", t); open(st, "w", encoding="utf-8").write(t)
if novo:                                                                 # registro na lista de projetos do CapCut
    rp = RAIZ + "/root_meta_info.json"; rraw = open(rp, "rb").read(); root = json.loads(rraw)
    assert json.dumps(root, separators=(",", ":"), ensure_ascii=False).encode() == rraw, "root_meta_info não regrava idêntico: não mexo"
    shutil.copyfile(rp, os.path.expanduser(f"~/Downloads/root_meta_info-antes-do-4x5-{time.strftime('%H%M%S')}.json"))
    ent = copy.deepcopy(next(x for x in root["all_draft_store"] if x["draft_fold_path"] == SRC))
    ent.update(draft_id=DID, draft_name=NOME, draft_fold_path=DST, draft_cover=DST + "/draft_cover.jpg", draft_json_file=DST + "/draft_info.json", tm_draft_create=agora, tm_draft_modified=agora)
    assert not any(x["draft_fold_path"] == DST for x in root["all_draft_store"])
    root["all_draft_store"].insert(0, ent)
    if isinstance(root.get("draft_ids"), int): root["draft_ids"] = len(root["all_draft_store"])
    open(rp, "wb").write(json.dumps(root, separators=(",", ":"), ensure_ascii=False).encode())
print("gravado:", DST, "(novo)" if novo else "(linha do tempo refeita)")
