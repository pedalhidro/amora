#!/usr/bin/env python3
"""Baixa os vídeos originais do projeto (Fotos da Apple, senão Drive) pra uma pasta local. Só LÊ das origens; retomável.
  baixa_originais.py <pasta de destino com _plano.json>     (o app Fotos tem que estar aberto; Drive rodando; Mac destravado)"""
import importlib.util, json, os, shutil, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
D = Path(sys.argv[1]); plano = json.load(open(D / "_plano.json")); MAN = D / "_manifesto.json"
man = json.load(open(MAN)) if MAN.exists() else {}
def log(*a):
    with open(D / "_log.txt", "a") as f: print(time.strftime("%H:%M:%S"), *a, file=f, flush=True)
def salva(): MAN.write_text(json.dumps(man, ensure_ascii=False, indent=0))
def feito(p): return man.get(p["hash"], {}).get("ok") and os.path.exists(D / man[p["hash"]]["arquivo"])
# ---- Drive (rápido, em paralelo)
try:                                                                  # o caminho do acervo mora no audit-captura.py (lido como texto: importar o arrasta junto)
    import ast, re
    fonte = open(os.path.join(os.environ.get("AMORA_REPO", "/Volumes/home/repos/pedalhidro/amora"), "scripts/audit-captura.py"), encoding="utf-8").read()
    ACERVO = Path(ast.literal_eval(re.search(r"ACERVO_PADRAO = (\([^)]*\))", fonte).group(1)))
    assert ACERVO.is_dir(), "pasta do acervo não existe"
except Exception as e: ACERVO = None; log("sem o caminho do acervo:", repr(e))
def do_drive(p):
    if feito(p): return
    try:
        src = ACERVO / p["caminho"]; alvo = D / f"{p['hash']}__{p['nome']}"
        shutil.copyfile(src, str(alvo) + ".part"); assert os.path.getsize(str(alvo) + ".part") > 0
        os.replace(str(alvo) + ".part", alvo); man[p["hash"]] = dict(ok=True, arquivo=alvo.name, fonte=p["fonte"], bytes=os.path.getsize(alvo))
    except Exception as e: man[p["hash"]] = dict(ok=False, fonte=p["fonte"], erro=repr(e)[:200])
drv = [p for p in plano if (p.get("fonte") or "").startswith("drive")]
if ACERVO and drv:
    with ThreadPoolExecutor(8) as ex: list(ex.map(do_drive, drv))
    salva(); log("drive:", sum(1 for p in drv if man.get(p["hash"], {}).get("ok")), "de", len(drv))
# ---- Fotos (um a um; o app Fotos baixa do iCloud)
import osxphotos
fot = sorted([p for p in plano if p.get("fonte") == "fotos" and not feito(p)], key=lambda p: p.get("tam") or 0)
if fot:
    db = osxphotos.PhotosDB(os.path.expanduser("~/Pictures/Local Photos Library.photoslibrary"))
    por = {f.uuid: f for f in db.photos(uuid=[p["uuid"] for p in fot], movies=True, images=False)}
    for i, p in enumerate(fot):
        f = por.get(p["uuid"]); t0 = time.time()
        try:
            assert f is not None, "não está na biblioteca"
            tmp = D / "_tmp" / p["uuid"]; tmp.mkdir(parents=True, exist_ok=True)
            if f.path and os.path.isfile(f.path): src = Path(tmp / os.path.basename(f.path)); shutil.copyfile(f.path, src)
            else:
                out = f.export(str(tmp), edited=False, use_photos_export=True, timeout=1800, overwrite=True)
                assert out, "o Fotos não exportou"; src = Path(out[0])
            alvo = D / f"{p['hash']}__{src.name}"; os.replace(src, alvo); shutil.rmtree(tmp, ignore_errors=True)
            man[p["hash"]] = dict(ok=True, arquivo=alvo.name, fonte="fotos", bytes=os.path.getsize(alvo), uuid=p["uuid"])
            log(f"fotos {i + 1}/{len(fot)} ok {alvo.name} {os.path.getsize(alvo) / 1e6:.0f} MB em {time.time() - t0:.0f} s")
        except Exception as e:
            man[p["hash"]] = dict(ok=False, fonte="fotos", uuid=p["uuid"], erro=repr(e)[:200]); log(f"fotos {i + 1}/{len(fot)} ERRO {p.get('nome')}: {e!r}"[:300])
        salva()
ok = sum(1 for v in man.values() if v.get("ok")); log("FIM:", ok, "ok,", sum(1 for v in man.values() if not v.get("ok")), "com erro, de", len([p for p in plano if p.get("fonte")]))
print("FIM", ok, "ok;", {k: v.get("erro") for k, v in man.items() if not v.get("ok")})
