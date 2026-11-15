#!/usr/bin/env python3
"""Troca um prefixo de caminho em TODOS os arquivos de texto de um projeto do CapCut (ex.: a mídia mudou de pasta).
  religar.py <pasta do projeto> <prefixo antigo> <prefixo novo> [--apply]
Ex.: religar.py ".../com.lveditor.draft/bicicultura-pedalhidro" ~/Downloads/1110-midia ~/Desktop/2026-bicicultura/video-pedalhidro/midia/1110-midia --apply
Só troca se o destino de cada caminho existir. CapCut tem que estar fechado. Faça um zip do projeto antes."""
import os, re, subprocess, sys
proj, de, para = sys.argv[1], os.path.abspath(os.path.expanduser(sys.argv[2])), os.path.abspath(os.path.expanduser(sys.argv[3]))
tot, falta = 0, set()
plano = {}
for raiz, _, fs in os.walk(proj):
    for f in fs:
        p = os.path.join(raiz, f)
        if os.path.getsize(p) > 60_000_000: continue
        b = open(p, "rb").read(); n = b
        for a, c in ((de, para), (de.replace("/", "\\/"), para.replace("/", "\\/"))):
            for m in set(re.findall(re.escape(a.encode()) + rb'[^"\\]*(?:\\/[^"\\]*)*', b)):
                alvo = m.decode("utf-8", "replace").replace("\\/", "/").replace(de, para, 1)
                if not os.path.exists(alvo): falta.add(alvo)
            n = n.replace(a.encode(), c.encode())
        if n != b: plano[p] = n; tot += 1
print(f"{tot} arquivos do projeto mudariam; caminhos sem destino: {len(falta)} {sorted(falta)[:3]}")
if "--apply" in sys.argv:
    assert not falta, "há caminhos sem destino — não gravo"
    if subprocess.run("ps -axo comm | grep -i -E 'capcut|jianying'", shell=True, capture_output=True).stdout.strip(): sys.exit("CapCut aberto — não gravo")
    for p, n in plano.items(): open(p, "wb").write(n)
    print("gravado")
