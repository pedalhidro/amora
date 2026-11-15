#!/usr/bin/env python3
"""Um quadro do intro_3d.py SEM PERDAS (o --still dele grava JPEG q88 na pasta de cache).
Não é parte do pipeline recuperado: é só um invólucro — troca o destino do save do --still.

  [mesmas variáveis de ambiente do intro_3d.py] quadro_png.py <dir> <t em s> <saida.png>

Convenção do intro_3d.py: --still t  ↔  quadro n = round(t*30) - 1 do vídeo (0-based)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
dir_, t, out = sys.argv[1:4]
_save = Image.Image.save


def save(self, fp, *a, **k):
    if isinstance(fp, str) and "/all3d-" in fp and fp.endswith(".jpg"):
        return _save(self, out)
    return _save(self, fp, *a, **k)


Image.Image.save = save
sys.argv = ["intro_3d.py", dir_, "--still", t]
import intro_3d
intro_3d.main()
