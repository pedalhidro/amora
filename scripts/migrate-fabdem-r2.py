#!/usr/bin/env python3
"""Migração do fabdem/ (gs://telhas) pro R2 SEM egress do GCS.

Descoberta que motiva o desenho (2026-08-13): o espelho no GCS NÃO é o
upstream verbatim — cada tile foi convertido pra COG (LAYOUT=COG, LZW,
blocos 512, 3 níveis de overview: 1800/900/450). O cameratopo depende dos
overviews pros zooms baixos. Então o pipeline refaz o caminho original:

  Bristol (upstream, grátis) → gdal_translate -of COG → rclone → R2

por zip de 10°×10° (~1,1 GB cada), em streaming: baixa 1 zip, extrai só os
tiles do manifest, converte, sobe, apaga — pico de disco ~6 GB (guard de
espaço livre antes de cada zip; a máquina de origem tinha só ~14 GB livres).

Retomável: o que já está no R2 (rclone lsf) é pulado; zips 100% cobertos nem
são baixados; download com curl -C - (resume). Blocos da América do Sul vêm
primeiro (SP funciona antes do resto do mundo).

O CONTRATO é o manifest (ignore/fabdem-migration/manifest.tsv), gerado do
espelho GCS com:
  gcloud storage ls -l gs://telhas/fabdem/ \
    | awk 'NF>=3 && $NF ~ /tif$/ {n=split($NF,p,"/"); print $1"\t"p[n]}' \
    > ignore/fabdem-migration/manifest.tsv
Paridade = mesmo CONJUNTO DE NOMES (tamanhos divergem por construção — o
COG é re-gerado). Tiles do manifest ausentes no upstream vão pra
missing-upstream.txt (candidatos ao fallback de egress pontual).

Pré-requisitos (uma vez):
  brew install rclone aria2      # gdal_translate já vem do conda; aria2 é o
                                 # download segmentado (16×, Bristol throttla
                                 # ~0,5 MB/s por conexão)
  # Cloudflare dash → R2 → criar bucket `fabdem` + API token S3 (Object R/W),
  # e gravar no .env do repo (o script configura o rclone sozinho via env):
  #   R2_FABDEM_ACCESS_KEY_ID=…
  #   R2_FABDEM_ACCESS_SECRET=…
  #   R2_FABDEM_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
  # (alternativa: um remote `r2` já configurado no rclone.conf também serve)

Uso:
  python scripts/migrate-fabdem-r2.py --dry-run          # plano (não precisa de rclone)
  python scripts/migrate-fabdem-r2.py --zip S30W050-S20W040_FABDEM_V1-2.zip \
      --limit-tiles 2 --no-upload                        # validação local
  python scripts/migrate-fabdem-r2.py                    # migração (noites)
  python scripts/migrate-fabdem-r2.py --verify           # paridade final
  python scripts/migrate-fabdem-r2.py --egress-fallback  # plano B (pago)
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BRISTOL_BASE = "https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/"
REPO = Path(__file__).resolve().parent.parent
WORKDIR = REPO / "ignore" / "fabdem-migration"
MANIFEST = WORKDIR / "manifest.tsv"
STAGE = WORKDIR / "stage"
MISSING_LOG = WORKDIR / "missing-upstream.txt"
R2_REMOTE = os.environ.get("FABDEM_R2_REMOTE", "r2")
R2_BUCKET = os.environ.get("FABDEM_R2_BUCKET", "fabdem")
MIN_FREE_GB = 8          # guard: não começa um zip com menos que isso livre
# Bbox América do Sul (blocos que intersectam vêm primeiro na fila)
SA_LAT, SA_LON = (-60, 15), (-90, -30)

# Perfil COG observado no espelho (gdalinfo em telhas/fabdem/S23W047…):
# LAYOUT=COG, COMPRESSION=LZW, blocos 512, overviews 1800/900/450 (default do
# driver pra 3600px). Resampling dos overviews não é recuperável do arquivo;
# AVERAGE é o adequado pra DEM (suaviza em vez de serrilhar o relevo).
COG_ARGS = ["-of", "COG", "-co", "COMPRESS=LZW", "-co", "BLOCKSIZE=512",
            "-co", "OVERVIEW_RESAMPLING=AVERAGE", "-co", "NUM_THREADS=ALL_CPUS"]


def tile_block(name):
    """N00E006_FABDEM_V1-2.tif → canto SW do bloco 10°×10° (lat, lon)."""
    lat = int(name[1:3]) * (-1 if name[0] == "S" else 1)
    lon = int(name[4:7]) * (-1 if name[3] == "W" else 1)
    return (lat // 10) * 10, (lon // 10) * 10


def fmt_lat(v):
    return f"{'S' if v < 0 else 'N'}{abs(v):02d}"


def fmt_lon(v):
    return f"{'W' if v < 0 else 'E'}{abs(v):03d}"


def zip_candidates(block):
    """Nomes possíveis do zip do bloco (o limite 0° pode ser N00 ou S00/E000
    ou W000 — o chamador testa com HEAD e usa o primeiro que existir)."""
    lat0, lon0 = block
    lat1, lon1 = lat0 + 10, lon0 + 10
    names = []
    for la1 in ({f"{fmt_lat(lat1)}", "S00"} if lat1 == 0 else {fmt_lat(lat1)}):
        for lo1 in ({f"{fmt_lon(lon1)}", "W000"} if lon1 == 0 else {fmt_lon(lon1)}):
            names.append(f"{fmt_lat(lat0)}{fmt_lon(lon0)}-{la1}{lo1}_FABDEM_V1-2.zip")
    return names


def in_south_america(block):
    lat0, lon0 = block
    return (SA_LAT[0] - 10 < lat0 <= SA_LAT[1]) and (SA_LON[0] - 10 < lon0 <= SA_LON[1])


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def _load_dotenv():
    """Best-effort, como no backend: não sobrescreve o ambiente já setado."""
    env_path = REPO / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def rclone_env():
    """Materializa o remote `r2` via RCLONE_CONFIG_* a partir do .env
    (R2_FABDEM_*) — sem precisar de rclone.conf. Se as vars não existirem,
    devolve o ambiente como está (vale um remote `r2` do rclone.conf)."""
    _load_dotenv()
    env = os.environ.copy()
    ak = env.get("R2_FABDEM_ACCESS_KEY_ID")
    sk = env.get("R2_FABDEM_ACCESS_SECRET")
    ep = env.get("R2_FABDEM_ENDPOINT")
    if ak and sk and ep:
        env.update({
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_TYPE": "s3",
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_PROVIDER": "Cloudflare",
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_ACCESS_KEY_ID": ak,
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_SECRET_ACCESS_KEY": sk,
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_ENDPOINT": ep,
            f"RCLONE_CONFIG_{R2_REMOTE.upper()}_NO_CHECK_BUCKET": "true",
        })
    return env


def free_gb(path):
    st = shutil.disk_usage(path)
    return st.free / 2**30


def load_manifest():
    if not MANIFEST.exists():
        sys.exit(f"manifest não encontrado: {MANIFEST}\n(gere com o comando do docstring)")
    tiles = []
    for line in MANIFEST.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].endswith(".tif"):
            tiles.append(parts[1])
    return sorted(set(tiles))


def r2_listing():
    out = subprocess.run(
        ["rclone", "lsf", f"{R2_REMOTE}:{R2_BUCKET}", "--files-only"],
        capture_output=True, text=True, env=rclone_env())
    if out.returncode != 0:
        sys.exit(f"rclone lsf falhou — remote `{R2_REMOTE}` configurado? bucket "
                 f"`{R2_BUCKET}` existe?\n{out.stderr.strip()}")
    return set(out.stdout.split())


def head_ok(url):
    r = subprocess.run(["curl", "-sIf", "-m", "60", "-o", "/dev/null", url])
    return r.returncode == 0


def resolve_zip_name(block, cache={}):
    if block not in cache:
        cands = zip_candidates(block)
        cache[block] = next((z for z in cands if head_ok(BRISTOL_BASE + z)), None)
        if cache[block] is None:
            print(f"  !! nenhum zip upstream pro bloco {block} (tentado: {cands})")
    return cache[block]


def download_zip(zip_name):
    dest = STAGE / zip_name
    STAGE.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ {zip_name}")
    # Bristol limita ~0,5 MB/s POR CONEXÃO; segmentado em 16 conexões escala
    # quase linear (medido 2026-08-13). aria2c retoma (-c) e re-tenta sozinho.
    if shutil.which("aria2c"):
        sh(["aria2c", "-x", "16", "-s", "16", "-k", "4M", "-c", "--quiet",
            "--max-tries", "10", "--retry-wait", "15", "--file-allocation", "none",
            "-d", str(STAGE), "-o", zip_name, BRISTOL_BASE + zip_name])
    else:
        sh(["curl", "-fL", "-C", "-", "--retry", "5", "--retry-delay", "15",
            "-o", str(dest), BRISTOL_BASE + zip_name])
    return dest


def cog_translate(src, dst):
    sh(["gdal_translate", *COG_ARGS, str(src), str(dst)],
       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def assert_cog(path):
    info = subprocess.run(["gdalinfo", str(path)], capture_output=True, text=True).stdout
    if "LAYOUT=COG" not in info or "Overviews:" not in info:
        sys.exit(f"transform NÃO produziu COG com overviews: {path}\n"
                 "(gdal_translate antigo demais? precisa do driver COG, GDAL ≥ 3.1)")


def upload(dir_):
    sh(["rclone", "copy", str(dir_), f"{R2_REMOTE}:{R2_BUCKET}",
        "--transfers", "8", "--s3-no-check-bucket",
        "--header-upload", "Cache-Control: public, max-age=31536000, immutable"],
       env=rclone_env())


def process_zip(zip_name, wanted, jobs, no_upload, limit_tiles):
    """Baixa um zip, converte os tiles pedidos pra COG, sobe, limpa."""
    zip_path = download_zip(zip_name)
    raw = STAGE / "raw"
    cog = STAGE / "cog"
    for d in (raw, cog):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)

    with zipfile.ZipFile(zip_path) as zf:
        members = {Path(m).name: m for m in zf.namelist() if m.endswith(".tif")}
        todo = [t for t in wanted if t in members][:limit_tiles or None]
        absent = [t for t in wanted if t not in members]
        if absent:
            with open(MISSING_LOG, "a") as f:
                f.writelines(t + "\n" for t in absent)
            print(f"  !! {len(absent)} tiles do manifest ausentes no upstream "
                  f"(→ {MISSING_LOG.name})")
        for t in todo:
            zf.extract(members[t], raw)

    def one(t):
        src = raw / members[t]
        cog_translate(src, cog / t)
        src.unlink()
        return t

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for i, fut in enumerate(as_completed([ex.submit(one, t) for t in todo]), 1):
            fut.result()
            if i % 10 == 0 or i == len(todo):
                print(f"  ⚙ COG {i}/{len(todo)}")

    if todo:
        assert_cog(cog / todo[0])
    if no_upload:
        print(f"  (--no-upload: {len(todo)} COGs ficaram em {cog})")
        return
    print(f"  ↑ R2 ({len(todo)} tiles)")
    upload(cog)
    shutil.rmtree(raw); shutil.rmtree(cog); zip_path.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="só o plano, sem rede/rclone")
    ap.add_argument("--verify", action="store_true", help="paridade manifest × R2")
    ap.add_argument("--egress-fallback", action="store_true",
                    help="imprime o plano B (cópia GCS→R2 paga)")
    ap.add_argument("--zip", help="processa só este zip (nome Bristol)")
    ap.add_argument("--limit-tiles", type=int, help="máx. tiles por zip (validação)")
    ap.add_argument("--no-upload", action="store_true", help="não sobe (validação local)")
    ap.add_argument("--jobs", type=int, default=4, help="gdal_translate paralelos")
    args = ap.parse_args()

    tiles = load_manifest()
    print(f"manifest: {len(tiles)} tiles")

    if args.egress_fallback:
        print("\nPlano B — cópia direta GCS→R2 (paga ~US$0,12/GB de egress; "
              "byte-idêntica, horas em vez de noites):\n"
              "  rclone copy gcs:telhas/fabdem r2:fabdem --transfers 16 \\\n"
              "    --gcs-bucket-policy-only\n"
              "Pros tiles de missing-upstream.txt (se houver), use:\n"
              "  rclone copy gcs:telhas/fabdem r2:fabdem "
              "--files-from ignore/fabdem-migration/missing-upstream.txt")
        return

    # Sem rclone só dá pra seguir nos modos que não tocam o R2 (plano/validação
    # local) — aí o "já feito" é vazio e a fila é o manifest inteiro.
    if args.dry_run or args.no_upload:
        done = r2_listing() if shutil.which("rclone") else set()
    else:
        done = r2_listing()
    remaining = [t for t in tiles if t not in done]
    blocks = {}
    for t in remaining:
        blocks.setdefault(tile_block(t), []).append(t)
    queue = sorted(blocks, key=lambda b: (not in_south_america(b), b))

    if args.verify:
        extra = sorted(done - set(tiles))
        print(f"R2: {len(done)} objetos · faltam {len(remaining)} · sobram {len(extra)}")
        for t in remaining[:20]:
            print(f"  falta {t}")
        if extra[:5]:
            print(f"  extras no R2: {extra[:5]}")
        sys.exit(0 if not remaining else 1)

    if args.dry_run:
        est_gb = len(remaining) * 25 / 1024   # upstream ~25 MB/tile
        print(f"R2 já tem {len(done)}; faltam {len(remaining)} tiles em "
              f"{len(queue)} blocos (~{est_gb:.0f} GB de download)")
        for b in queue[:15]:
            print(f"  {fmt_lat(b[0])}{fmt_lon(b[1])}: {len(blocks[b])} tiles"
                  + ("  ← América do Sul" if in_south_america(b) else ""))
        if len(queue) > 15:
            print(f"  … +{len(queue)-15} blocos")
        return

    for tool in ("curl", "gdal_translate", "rclone" if not args.no_upload else "curl"):
        if shutil.which(tool) is None:
            sys.exit(f"{tool} não está no PATH (ver pré-requisitos no docstring)")

    if args.zip:
        queue = [b for b in queue if args.zip in zip_candidates(b)]
        if not queue:
            sys.exit(f"--zip {args.zip} não corresponde a nenhum bloco pendente")

    print(f"fila: {len(queue)} blocos ({len(remaining)} tiles); "
          f"disco livre {free_gb(STAGE.parent):.1f} GB")
    for n, block in enumerate(queue, 1):
        if free_gb(WORKDIR) < MIN_FREE_GB:
            sys.exit(f"disco < {MIN_FREE_GB} GB livres — libere espaço e rode de novo "
                     "(o progresso fica; é retomável)")
        zip_name = resolve_zip_name(block)
        if zip_name is None:
            with open(MISSING_LOG, "a") as f:
                f.writelines(t + "\n" for t in blocks[block])
            continue
        print(f"[{n}/{len(queue)}] {zip_name} ({len(blocks[block])} tiles)")
        process_zip(zip_name, blocks[block], args.jobs, args.no_upload,
                    args.limit_tiles)

    print("fila concluída — rode --verify pra fechar a paridade")


if __name__ == "__main__":
    main()
