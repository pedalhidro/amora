#!/usr/bin/env python3
"""Folha de contato de um projeto (pelo modelo do capcut_layout), com as legendas desenhadas onde vão ficar.
  previa45.py <pasta com draft_info.json> <saida.jpg> <colunas> <t1> [t2 ...]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut_layout import carrega, quadro
from PIL import Image, ImageDraw, ImageFont
d = carrega(sys.argv[1]); nc = int(sys.argv[3]); ts = [float(x) for x in sys.argv[4:]]
CW, CH = d["canvas_config"]["width"], d["canvas_config"]["height"]; k = 400 / CW
TX = {m["id"]: m for m in d["materials"]["texts"]}; f = ImageFont.truetype(os.path.expanduser("~/Library/Fonts/IBMPlexMono-Bold.ttf"), 13)
qs = []
for t in ts:
    q = quadro(d, t, k, fundo=(24, 24, 24)); dr = ImageDraw.Draw(q)
    for tr in d["tracks"]:
        if tr["type"] != "text": continue
        for s in tr["segments"]:
            a = s["target_timerange"]["start"] / 1e6; b = a + s["target_timerange"]["duration"] / 1e6
            if a <= t < b:
                txt = json.loads(TX[s["material_id"]]["content"])["text"]; c = s["clip"]["transform"]; x, y = CW / 2 * (1 + c["x"]) * k, CH / 2 * (1 - c["y"]) * k
                bb = dr.multiline_textbbox((x, y), txt, font=f, anchor="mm", align="center"); dr.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=(0, 0, 0)); dr.multiline_text((x, y), txt, font=f, anchor="mm", align="center", fill=(255, 255, 255))
    dr.text((6, 4), f"{t:g} s", font=f, fill=(255, 255, 0)); qs.append(q)
w, h = qs[0].size; nl = -(-len(qs) // nc); folha = Image.new("RGB", (nc * (w + 6) - 6, nl * (h + 6) - 6), (255, 0, 255))
for i, q in enumerate(qs): folha.paste(q, ((i % nc) * (w + 6), (i // nc) * (h + 6)))
folha.save(sys.argv[2], quality=85)
