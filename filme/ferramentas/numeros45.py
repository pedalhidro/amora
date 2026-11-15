#!/usr/bin/env python3
"""Mural de números em RETRATO (1080×1350, 3 colunas — NC; "quilojaules" vira "kJ" pra caber): uma célula por passeio, mais novos primeiro, rolando pra baixo em 2 passos
que começam nos segundos 4 e 7 (10 s, 60 BPM — o mesmo deslize do mural de artes). No topo, um parágrafo com os totais ocupa a 1ª fileira. Só texto, em IBM Plex Mono. Números como no censo:
  intensidade pelas faixas de kJ; coletividade = participantes × tempo total; gasolina = participantes × kJ ÷ 34.200 kJ/L.
  numeros.py <pasta com tours.ttl e images.ttl> <saida.mp4> [--still quadro.png]"""
import sys, os, re, json, subprocess, collections, datetime, unicodedata
import rdflib
from PIL import Image, ImageDraw, ImageFont
C, out = sys.argv[1], sys.argv[2]
W, H, FPS, TOTAL, NC = 1080, 1350, 30, 10.0, int(os.environ.get("NC", 3))
F_CEL, LH_CEL, ALT_CEL, F_TXT, LH_TXT = {5: (12, 15, 132, 28, 38), 3: (16, 20, 176, 30, 40)}[NC]   # por nº de colunas: letra e linha da célula, altura da célula, letra e linha do parágrafo
CW, CH, PAD = W // NC, ALT_CEL, 12
INICIOS, MOVE = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 0.4                     # seis passos, um por segundo; a 1ª tela (com o texto) fica 3 s
PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#"); DC = rdflib.Namespace("http://purl.org/dc/terms/")
g = rdflib.Graph(); g.parse(f"{C}/tours.ttl", format="turtle")
TTL_IMG = open(f"{C}/images.ttl", encoding="utf-8").read()
N_FOTOS, N_VIDEOS = (len(re.findall(r"\ba\s[^;.]*ph:" + k + r"\b", TTL_IMG)) for k in ("StillImage", "MotionImage"))
midias = collections.Counter(re.findall(r"ph:capturedDuring\s+(?:pas:|<https://id\.pedalhidrografi\.co/passeio/)([0-9a-z]+)", TTL_IMG))
def horas(iso):
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", iso or ""); return (int(m.group(1) or 0) + int(m.group(2) or 0) / 60 + int(m.group(3) or 0) / 3600) if m else None
def num(t, p):
    v = next(g.objects(t, p), None)
    try: return float(v) if v is not None else None
    except Exception: return None
ROT = {"S": "PH-S"}
tours = []
for t in set(g.subjects(rdflib.RDF.type, PH.Tour)):
    cods = []
    for e in g.objects(t, PH.inSeriesEdition):
        s = next(g.objects(e, PH.inEventSeries), None); q = next(g.objects(e, PH.sequenceInSeries), None)
        if s is not None and q is not None: s = str(s).rsplit("/", 1)[-1]; cods.append((0 if s == "PH" else 1, f"{ROT.get(s, s)} {int(q)}"))
    dep, arr = next(g.objects(t, PH.departedAt), None), next(g.objects(t, PH.arrivedAt), None); el = None
    if dep and arr:
        try: el = (datetime.datetime.fromisoformat(str(arr)) - datetime.datetime.fromisoformat(str(dep))).total_seconds() / 3600
        except Exception: pass
    if not el or el <= 0: el = horas(str(next(g.objects(t, PH.totalDuration), "")))
    tours.append(dict(slug=str(t).rsplit("/", 1)[-1], data=str(next(g.objects(t, DC.date), "")), titulo=str(next(g.objects(t, DC.title), "")).strip().lower(),
                      cod=" + ".join(c for _, c in sorted(cods)), kj=num(t, PH.energyEstimate), gente=num(t, PH.countAttendee), h=el,
                      incidentes=len(list(g.objects(t, PH.hadIncident)))))
for t in tours: t["midias"] = midias.get(t["slug"], 0)
tours.sort(key=lambda t: t["data"], reverse=True)
def faixa(kj): return None if kj is None else "de boa" if kj < 150 else "ok" if kj < 300 else "endorfinado" if kj < 500 else "frito" if kj < 1000 else "insano"
COR = {"de boa": "#c2ffe1", "ok": "#c1ff72", "endorfinado": "#ffbd59", "frito": "#ff751f", "insano": "#ff4d6d", None: "#bdbdbd"}
br = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")
def fh(h):
    if h is None: return None
    m = round(h * 60); return f"{m // 60}h" if m % 60 == 0 else f"{m // 60}h{m % 60:02d}"
def linhas(t):
    kj, n, h, m = t["kj"], t["gente"], t["h"], t["midias"]; pl = lambda q, s, p: f"{q:.0f} {s if q == 1 else p}"
    L = [", ".join(x for x in [f"{kj:.0f} kJ {faixa(kj)}" if kj is not None else None, fh(h) if h else None] if x),
         ", ".join(x for x in [pl(n, "participante", "participantes") if n is not None else None, pl(m, "mídia", "mídias") if m else None] if x),
         " e ".join(x for x in [f"{br(n * h)}h" if n and h else None, f"{n * kj:.0f} kJ" if n and kj else None] if x) + (" coletivos" if n and (h or kj) else ""),
         (lambda ml: f"{ml:.0f}mL de gasolina equiv." if ml < 1000 else f"{br(ml / 1000, 2)}L de gasolina equiv.")(n * kj / 34200 * 1000) if n and kj else "",
         pl(t["incidentes"], "incidente", "incidentes")]
    return [x for x in L if x]
FD = os.path.expanduser("~/Library/Fonts/IBMPlexMono-")
f_cod, f_nome, f_num = (ImageFont.truetype(FD + peso + ".ttf", F_CEL) for peso in ("Bold", "Medium", "Regular"))
AV = f_num.getlength("0"); COLS = int((CW - 10) // AV); LH = LH_CEL      # fonte monoespaçada: cabe COLS caracteres por linha
def quebra(txt, maxl):
    out_, atual = [], ""
    for pal in txt.split(" "):
        tenta = (atual + " " + pal).strip()
        if len(tenta) <= COLS or not atual: atual = tenta
        else: out_.append(atual); atual = pal
    out_.append(atual)
    if len(out_) > maxl: out_ = out_[:maxl]; out_[-1] = out_[-1][:COLS - 1].rstrip(" ,") + "…"
    return out_
mil = lambda v: f"{v:,.0f}".replace(",", ".")
MES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
dia = lambda d: f"{d.day:02d} de {MES[d.month - 1]} de {d.year}"
presencas = sum(t["gente"] or 0 for t in tours); horas_col = sum((t["gente"] or 0) * (t["h"] or 0) for t in tours); kj_col = sum((t["gente"] or 0) * (t["kj"] or 0) for t in tours)
INI = datetime.date.fromisoformat(os.environ.get("NUMEROS_INICIO", "2024-09-01")); ATE = datetime.date.fromisoformat(os.environ.get("NUMEROS_FIM", datetime.date.today().isoformat()))
TEXTO = (f"Produção possível devido aos contribuintes do amora ajudante bicienergético, os quais disponibilizaram {mil(N_FOTOS)} fotos e {mil(N_VIDEOS)} vídeos sob licença "
         f"CC BY-SA 4.0, mesmos termos deste vídeo. De {dia(INI)} até {dia(ATE)}, ocorreram {len(tours)} passeios com {mil(presencas)} presenças combinadas debaixo do "
         f"guarda-chuva do Pedal Hidrográfico, resultando num total de {mil(horas_col)} horas coletivas totais destinadas para o passeio, e nos quais foram investidos "
         f"energeticamente {mil(kj_col)} quilojaules - equivalente à entalpia de combustão de {br(kj_col / 34200, 2)} litros de gasolina. Discrimina-se em detalhes e por passeio:")
f_txt = ImageFont.truetype(FD + "Regular.ttf", F_TXT); AVT = f_txt.getlength("0"); LHT = LH_TXT
_c, COLS = COLS, int((W - 28) // AVT); par = quebra(TEXTO, 99); COLS = _c
HEAD = 16 + len(par) * LHT + 18                                         # o parágrafo, em cima, com letra que dá pra ler no celular
linhas_tot = -(-len(tours) // NC)
mural = Image.new("RGB", (W, HEAD + linhas_tot * CH), "#0c0c0c"); dr = ImageDraw.Draw(mural); estouro = 0
for j, l in enumerate(par): dr.text((14, 16 + j * LHT), l, font=f_txt, fill="#ffffff")
for i, t in enumerate(tours):                                          # só texto: sem bordas nem barras
    x, y0 = (i % NC) * CW + 7, HEAD + (i // NC) * CH; y = y0 + 9; cod = t["cod"] or "—"
    for j, l in enumerate(quebra(cod + " " + t["titulo"], 2)):           # código (na cor da intensidade) + nome, na mesma linha
        if j == 0: dr.text((x, y), cod, font=f_cod, fill=COR[faixa(t["kj"])]); dr.text((x + AV * (len(cod) + 1), y), l[len(cod) + 1:], font=f_nome, fill="#ffffff")
        else: dr.text((x, y), l, font=f_nome, fill="#ffffff")
        y += LH
    y += 3
    for bloco in linhas(t):
        for l in quebra(bloco, 2): dr.text((x, y), l, font=f_num, fill="#c4c4c4"); y += LH
    estouro += y > y0 + CH - 2
travel = mural.height - H; passos = [travel / len(INICIOS)] * len(INICIOS)      # passos iguais, em px
acum = [travel * k / len(INICIOS) for k in range(len(INICIOS) + 1)]
def pos(tm):
    k = sum(tm >= s + MOVE for s in INICIOS); u = next(((tm - s) / MOVE for s in INICIOS if s <= tm < s + MOVE), 0.0)
    return acum[k] + (acum[min(k + 1, len(passos))] - acum[k]) * (u * u * u * (u * (u * 6 - 15) + 10))
sem = {k: sum(1 for t in tours if t[k] in (None, 0)) for k in ("kj", "gente", "h", "midias")}
print(TEXTO)
print(f"{len(tours)} passeios, {linhas_tot} fileiras de {CH} px + texto de {HEAD} px = {mural.height} px; passos de {passos[0]:.0f} px ({passos[0] / H:.0%} da tela); {COLS} caracteres por célula; células que estouram a altura: {estouro}; sem dado: {sem}")
if "--still" in sys.argv: mural.crop((0, 0, W, H)).save(sys.argv[sys.argv.index("--still") + 1]); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
                       "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for i in range(round(TOTAL * FPS)):
    y = pos(i / FPS); ff.stdin.write(mural.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, y), resample=Image.BICUBIC).tobytes())
ff.stdin.close(); sys.exit(ff.wait())
