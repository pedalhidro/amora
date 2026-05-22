#!/usr/bin/env python3
"""
coletor_apple_photos.py — para cada pedal na planilha Censo Hidrográfico,
copia da biblioteca do Apple Photos as fotos/vídeos feitos na data do pedal,
dentro de uma janela de tempo a partir do horário de início, organizando-os
em pastas por pedal e gravando metadados da ontologia Pedal Hidrográfico
como tags XMP (namespace `ph:`).

Como funciona
  1. Lê a aba "Geral" da planilha: data, horário de início e códigos
     (eH/PH/BP/S/BT) de cada pedal.
  2. Carrega a biblioteca do Photos via osxphotos.
  3. Para cada pedal, monta a janela [início, início + --window-hours] e
     seleciona as fotos cujo horário local cai dentro dela. A janela usa o
     relógio LOCAL da foto, então um pedal feito em outro fuso (ex. Oakland)
     continua sendo casado corretamente.
  4. Copia as fotos para  <out>/<data - código - nome>/  e grava as tags
     XMP-ph (exiftool) com a referência ao pedal.

A planilha é a fonte da verdade sobre quando cada pedal acontece.

Requisitos (macOS)
  pip3 install osxphotos openpyxl
  brew install exiftool          # necessário p/ gravar os metadados XMP
  Conceda "Acesso Total ao Disco" ao app que roda o script (Terminal/iTerm)
  em  Ajustes do Sistema → Privacidade e Segurança → Acesso Total ao Disco,
  senão a biblioteca do Photos fica ilegível.

Uso
  python3 coletor_apple_photos.py --list-tours          # só lista os pedais
  python3 coletor_apple_photos.py --out ~/pedais --dry-run
  python3 coletor_apple_photos.py --out ~/pedais
  python3 coletor_apple_photos.py --out ~/pedais --window-hours 7
  python3 coletor_apple_photos.py --out ~/pedais --download-missing

Notas
  --window-hours 6 (padrão) cobre pedais que passam da meia-noite.
  --download-missing baixa do iCloud os originais não presentes no Mac
  (mais lento). Sem essa flag, fotos só-no-iCloud são puladas e reportadas.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time as dtime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
XLSX_DEFAULT   = REPO / "Censo Hidrográfico - microdados-atualizado.xlsx"
CONFIG_DEFAULT = Path(__file__).resolve().parent / "exiftool_ph.config"
ID_BASE    = "https://pedalhidrografi.co/id/tour/"
COLLECTIVE = "Pedal Hidrográfico"

# Colunas da aba "Geral" (1-based)
COL = dict(data=1, eH=2, PH=3, BP=4, S=5, BT=6, nome=7, horario=19)
# Precedência do código exibido (igual ao app e à ontologia)
SERIES_PREC = ["PH", "eH", "BT", "BP", "S"]


def sanitize(s):
    """Texto seguro para nome de pasta."""
    s = re.sub(r'[\\/:*?"<>|\n\r\t]+', "-", str(s)).strip()
    s = re.sub(r'\s+', " ", s)
    return s[:90].strip(" .-")


def read_tours(xlsx):
    """Lê a aba Geral → lista de dicts {date, title, ride_code, codes, start}."""
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb["Geral"]
    tours = []
    for r in range(2, ws.max_row + 1):
        cell = lambda c: ws.cell(row=r, column=c).value
        d, nome = cell(COL["data"]), cell(COL["nome"])
        if d is None and nome is None:
            continue
        if not isinstance(d, datetime):
            continue  # sem data não dá para janelar
        codes = {}
        for name in ("eH", "PH", "BP", "S", "BT"):
            v = cell(COL[name])
            if isinstance(v, int):
                codes[name] = v
        ride_code = next(
            (f"{n} {codes[n]}" for n in SERIES_PREC if n in codes), None)
        hor = cell(COL["horario"])
        tours.append(dict(
            date=d.date(),
            title=str(nome).strip() if nome else "",
            ride_code=ride_code,
            codes=codes,
            start=hor if isinstance(hor, dtime) else None,
        ))
    return tours


def folder_name(t):
    parts = [t["date"].isoformat()]
    if t["ride_code"]:
        parts.append(t["ride_code"])
    if t["title"]:
        parts.append(t["title"])
    return sanitize(" - ".join(parts))


def label(t):
    return t["ride_code"] or t["title"] or t["date"].isoformat()


def fetch(photo, folder, download_missing):
    """Copia o original da foto para `folder`. Devolve o Path ou None."""
    name = photo.original_filename or photo.filename or (photo.uuid + ".jpg")
    dest = folder / name
    n = 1
    while dest.exists():
        dest = folder / f"{Path(name).stem}_{n}{Path(name).suffix}"
        n += 1
    src = photo.path
    if src and os.path.exists(src):
        shutil.copy2(src, dest)
        return dest
    if not download_missing:
        return None  # original só no iCloud e --download-missing desligado
    # Original ausente: baixa do iCloud via API de exportação do osxphotos.
    # A partir do osxphotos recente isso é feito por PhotoExporter +
    # ExportOptions (o antigo export(download_missing=...) foi removido).
    try:
        import osxphotos
        opts = osxphotos.ExportOptions(download_missing=True,
                                       use_photos_export=True,
                                       overwrite=True)
        results = osxphotos.PhotoExporter(photo).export(
            str(folder), dest.name, options=opts)
        got = list(getattr(results, "exported", None) or [])
        return Path(got[0]) if got else None
    except Exception as e:
        print(f"     ⚠️  falha ao baixar {name}: {e}")
        return None


def write_exif(config, folder, t):
    """Grava as tags XMP-ph (e palavras-chave) em todos os arquivos da pasta."""
    iri  = ID_BASE + t["date"].isoformat()
    desc = " — ".join(x for x in (t["ride_code"], t["title"]) if x) \
           or t["date"].isoformat()
    cmd = ["exiftool", "-config", str(config), "-overwrite_original",
           "-q", "-api", "NoDups=1",
           f"-XMP-ph:CapturedDuring={iri}",
           f"-XMP-ph:RideName={t['title']}",
           f"-XMP-ph:RideDate={t['date'].isoformat()}",
           f"-XMP-ph:Collective={COLLECTIVE}",
           f"-XMP-dc:Description={desc}",
           f"-XMP-dc:Subject+={COLLECTIVE}"]
    if t["ride_code"]:
        cmd.append(f"-XMP-ph:RideCode={t['ride_code']}")
        cmd.append(f"-XMP-dc:Subject+={t['ride_code']}")
    for name in ("eH", "PH", "BP", "S", "BT"):
        if name in t["codes"]:
            cmd.append(f"-XMP-ph:RideCodes+={name} {t['codes'][name]}")
    cmd.append(str(folder))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"     ⚠️  exiftool: {res.stderr.strip()}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", type=Path, default=XLSX_DEFAULT,
                    help="planilha Censo Hidrográfico")
    ap.add_argument("--out", type=Path,
                    help="pasta base onde criar as pastas por pedal")
    ap.add_argument("--library", type=Path, default=None,
                    help="biblioteca do Photos (padrão: a do sistema)")
    ap.add_argument("--window-hours", type=float, default=6.0,
                    help="horas após o início a incluir (padrão: 6)")
    ap.add_argument("--default-start", default="20:00",
                    help="horário usado quando a planilha não traz um (HH:MM)")
    ap.add_argument("--config", type=Path, default=CONFIG_DEFAULT,
                    help="arquivo de config do exiftool (namespace ph)")
    ap.add_argument("--download-missing", action="store_true",
                    help="baixa do iCloud os originais ausentes (mais lento)")
    ap.add_argument("--no-exif", action="store_true",
                    help="não gravar metadados XMP")
    ap.add_argument("--dry-run", action="store_true",
                    help="só mostra o que faria, sem copiar")
    ap.add_argument("--list-tours", action="store_true",
                    help="lista os pedais e janelas e sai (não toca no Photos)")
    args = ap.parse_args()

    if not args.xlsx.exists():
        sys.exit(f"ERRO: planilha não encontrada: {args.xlsx}")
    try:
        hh, mm = (int(x) for x in args.default_start.split(":"))
        default_start = dtime(hh, mm)
    except Exception:
        sys.exit(f"ERRO: --default-start inválido: {args.default_start}")

    tours = read_tours(args.xlsx)
    print(f"📋 {len(tours)} pedais com data na planilha")

    if args.list_tours:
        for t in tours:
            st = t["start"] or default_start
            end = (datetime.combine(t["date"], st)
                   + timedelta(hours=args.window_hours))
            flag = "" if t["start"] else "  (horário padrão)"
            print(f"  {t['date']}  {st.strftime('%H:%M')}–{end:%H:%M}"
                  f"  {label(t)}{flag}")
        return

    if not args.out:
        sys.exit("ERRO: informe --out (pasta base) ou use --list-tours")

    try:
        import osxphotos
    except ImportError:
        sys.exit("ERRO: osxphotos não instalado — `pip3 install osxphotos`")

    exif_ok = (not args.no_exif) and bool(shutil.which("exiftool"))
    if not args.no_exif and not exif_ok:
        print("⚠️  exiftool não encontrado — metadados XMP não serão gravados "
              "(`brew install exiftool`)")
    if exif_ok and not args.config.exists():
        print(f"⚠️  config não encontrada ({args.config}) — XMP não gravado")
        exif_ok = False

    print("📷 carregando a biblioteca do Photos…")
    db = (osxphotos.PhotosDB(str(args.library)) if args.library
          else osxphotos.PhotosDB())

    # Agrupa as fotos pelo dia local — acelera o casamento por janela.
    bucket = defaultdict(list)
    for p in db.photos():
        if p.date is None:
            continue
        wall = p.date.replace(tzinfo=None)   # relógio local da foto
        bucket[wall.date()].append((wall, p))
    print(f"   {sum(len(v) for v in bucket.values())} itens na biblioteca")

    args.out.mkdir(parents=True, exist_ok=True)
    used_names, total, tours_hit = set(), 0, 0

    for t in tours:
        st = t["start"] or default_start
        start_dt = datetime.combine(t["date"], st)
        end_dt = start_dt + timedelta(hours=args.window_hours)
        cand = (bucket.get(t["date"], [])
                + bucket.get(t["date"] + timedelta(days=1), []))
        matched = [p for (wall, p) in cand if start_dt <= wall < end_dt]
        if not matched:
            continue
        tours_hit += 1

        fname = folder_name(t)
        while fname in used_names:
            fname += "_2"
        used_names.add(fname)
        folder = args.out / fname

        if args.dry_run:
            print(f"  ✓  {label(t):14s} {len(matched):3d} fotos → {fname}/"
                  f"  (dry-run)")
            continue

        folder.mkdir(parents=True, exist_ok=True)
        copied = [d for d in (fetch(p, folder, args.download_missing)
                              for p in matched) if d]
        if exif_ok and copied:
            write_exif(args.config, folder, t)
        total += len(copied)
        miss = len(matched) - len(copied)
        extra = f"  ({miss} só no iCloud)" if miss else ""
        print(f"  ✓  {label(t):14s} {len(copied):3d} fotos → {fname}/{extra}")

    print(f"\n✅ {total} fotos copiadas em {tours_hit} pedais → {args.out}")
    if not exif_ok and not args.no_exif:
        print("   (metadados XMP não gravados — veja avisos acima)")


if __name__ == "__main__":
    main()
