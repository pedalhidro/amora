#!/usr/bin/env python3
"""Lê um projeto do CapCut e desenha um quadro do jeito que (pelo meu modelo) o CapCut desenharia: serve pra conferir o modelo contra uma
exportação de verdade e pra pré-visualizar um leiaute novo.   capcut_layout.py <projeto> <saida.jpg> <t1> [t2 ...] [--export video.mp4]"""
import json, os, subprocess, sys, io, hashlib
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass
CACHE = os.environ.get("CAPCUT_CACHE", "/tmp/capcut-layout-cache"); os.makedirs(CACHE, exist_ok=True)
def carrega(proj):
    d = json.load(open(proj + "/draft_info.json")); return d
def crop_frac(m):
    c = m.get("crop") or {}
    return (c.get("upper_left_x", 0.0), c.get("upper_left_y", 0.0), c.get("lower_right_x", 1.0), c.get("lower_right_y", 1.0))
def tamanho(m):
    """Tamanho do conteúdo (depois do recorte) em px do material."""
    x0, y0, x1, y1 = crop_frac(m); return m["width"] * (x1 - x0), m["height"] * (y1 - y0)
def ret(seg, m, CW, CH):
    """Retângulo (cx, cy, w, h) em px da tela, antes da rotação: escala 1 = o conteúdo recortado encaixado inteiro na tela."""
    Wc, Hc = tamanho(m); fit = min(CW / Wc, CH / Hc); c = seg["clip"]
    return CW / 2 * (1 + c["transform"]["x"]), CH / 2 * (1 - c["transform"]["y"]), Wc * fit * c["scale"]["x"], Hc * fit * c["scale"]["y"]
def imagem(m, t_src, proj=None):
    p = m["path"]
    if m.get("type") == "photo" or p.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".heif")):
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    else:
        k = f"{CACHE}/{hashlib.md5((p + str(round(t_src, 2))).encode()).hexdigest()}.jpg"
        if not os.path.exists(k): subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t_src):.3f}", "-i", p, "-frames:v", "1", "-q:v", "3", k], capture_output=True)
        if not os.path.exists(k): return None
        im = Image.open(k).convert("RGB")
    if im.size != (m["width"], m["height"]): im = im.resize((m["width"], m["height"]))
    x0, y0, x1, y1 = crop_frac(m)
    return im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
def quadro(d, t, k=1.0, fundo=(0, 0, 0)):
    CW, CH = d["canvas_config"]["width"], d["canvas_config"]["height"]; V = {m["id"]: m for m in d["materials"]["videos"]}
    tela = Image.new("RGB", (round(CW * k), round(CH * k)), fundo); us = t * 1e6
    for tr in d["tracks"]:                                               # trilha de cima cobre a de baixo
        if tr["type"] != "video": continue
        for s in tr["segments"]:
            a = s["target_timerange"]["start"]; b = a + s["target_timerange"]["duration"]
            if not (a <= us < b): continue
            m = V[s["material_id"]]
            if "placeholder" in m["path"]: continue                     # clipe composto: não dá pra ler
            im = imagem(m, (s["source_timerange"]["start"] + (us - a) * s.get("speed", 1.0)) / 1e6)
            if im is None: continue
            cx, cy, w, h = ret(s, m, CW, CH); im = im.resize((max(1, round(w * k)), max(1, round(h * k))))
            rot = s["clip"].get("rotation") or 0
            if rot: im = im.convert("RGBA").rotate(-rot, expand=True, resample=Image.BICUBIC)   # CapCut: positivo = horário
            tela.paste(im, (round(cx * k - im.width / 2), round(cy * k - im.height / 2)), im if im.mode == "RGBA" else None)
    return tela
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; exp = sys.argv[sys.argv.index("--export") + 1] if "--export" in sys.argv else None
    if exp: args.remove(exp)
    d = carrega(args[0]); ts = [float(x) for x in args[2:]]; k = 640 / d["canvas_config"]["width"]; linhas = []
    for t in ts:
        q = quadro(d, t, k)
        if exp:
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", exp, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
            e = Image.open(io.BytesIO(r.stdout)).convert("RGB").resize(q.size); par = Image.new("RGB", (q.width * 2 + 8, q.height), (255, 0, 255)); par.paste(e, (0, 0)); par.paste(q, (q.width + 8, 0)); q = par
        linhas.append(q)
    folha = Image.new("RGB", (linhas[0].width, sum(l.height + 6 for l in linhas)), (255, 0, 255)); y = 0
    for l in linhas: folha.paste(l, (0, y)); y += l.height + 6
    folha.save(args[1], quality=88)
