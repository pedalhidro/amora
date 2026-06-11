#!/usr/bin/env bash
#
# Inverso de scripts/deploy-cloudrun.sh --state-only: puxa do bucket GCS
# (`phidro-state`) pro repo local o estado vivo do serviço — uploads.ttl,
# data_graphs.ttl, tours.ttl, routes.json, photos/, clips/. Útil pra desenvolver
# localmente com o catálogo atual de produção, ou pra ter backup do que foi
# enviado via upload_images.html / upload_tour.html.
#
# tours.ttl é baixado porque os endpoints de Tour CRUD (/upload-tour,
# /delete-tour) o mutam server-side: edições feitas pelo upload_tour.html /
# Censo vivem só no bucket até o próximo deploy sobrescrevê-las com a cópia
# do git. Puxe e reconcilie antes de commitar — lembrando que tours.ttl
# também é regenerado por build-tours.py a partir do CSV.
#
# NÃO baixa shapes.ttl/ontology.ttl: esses ficam versionados no git e o
# deploy é que sobe pro bucket — invertendo a direção corromperia o
# source-of-truth.
#
# Guarda anti-clobber: o pull dos arquivos dual-writer (uploads.ttl,
# data_graphs.ttl, tours.ttl, routes.json) é recusado se o LOCAL mudou
# desde o último sync E difere do bucket — senão um build/edição local
# ainda não empurrado seria sobrescrito. Nesse caso: commit/backup do
# local (ou deploy-cloudrun.sh --state-only pra empurrá-lo) e rode de
# novo; `--force` pula a checagem. Ver scripts/sync-guard.sh.
#
# Usage:
#   scripts/pull-cloudrun.sh                # TTLs mutáveis + routes.json + photos/ + clips/
#   scripts/pull-cloudrun.sh --dry-run      # preview, sem baixar
#   scripts/pull-cloudrun.sh --photos-only  # só photos/
#   scripts/pull-cloudrun.sh --clips-only   # só clips/
#   scripts/pull-cloudrun.sh --data-only    # só uploads.ttl + data_graphs.ttl + tours.ttl + routes.json
#   scripts/pull-cloudrun.sh --mirror       # espelho exato: deleta local o que
#                                           # não existe no bucket (perigoso)
#   scripts/pull-cloudrun.sh --force        # ignora a guarda anti-clobber
#
# Overridable via env (mesmas defaults do deploy):
#   GCP_PROJECT  default: pedal-hidrografico
#   GCS_BUCKET   default: phidro-state

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${GCP_PROJECT:-pedal-hidrografico}"
BUCKET="${GCS_BUCKET:-phidro-state}"

DRY=""
SYNC_PHOTOS=1
SYNC_CLIPS=1
SYNC_DATA=1
MIRROR_FLAG=""
EXPLICIT_SCOPE=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run)     DRY="echo DRY: "; echo "↻ DRY RUN — nada será baixado." ;;
    --photos-only) SYNC_CLIPS=0; SYNC_DATA=0; EXPLICIT_SCOPE=1 ;;
    --clips-only)  SYNC_PHOTOS=0; SYNC_DATA=0; EXPLICIT_SCOPE=1 ;;
    --data-only)   SYNC_PHOTOS=0; SYNC_CLIPS=0; EXPLICIT_SCOPE=1 ;;
    --mirror)      MIRROR_FLAG="--delete-unmatched-destination-objects" ;;
    --force)       FORCE=1 ;;
    -h|--help)     sed -n '2,34p' "$0"; exit 0 ;;
    *) echo "Argumento desconhecido: $arg" >&2; exit 2 ;;
  esac
done

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud CLI não encontrado." >&2
  exit 1
fi

# ── Guarda anti-clobber (ver scripts/sync-guard.sh) ─────────────────────
[[ -n "$DRY" ]] && SYNC_GUARD_DRY=1
# shellcheck source=scripts/sync-guard.sh
source "$REPO_ROOT/scripts/sync-guard.sh"

GUARD_CONFLICTS=""
# Pull guardado de um arquivo de estado dual-writer: bucket → local.
guarded_pull() {
  local gs_url="$1" local_path="$2"
  local name local_md5 remote_md5 verdict
  name="$(basename "$local_path")"
  remote_md5="$(sync_guard_remote_md5 "$gs_url")"
  if [[ -z "$remote_md5" ]]; then
    echo "  ⚠ $gs_url não existe no bucket — skip"
    return 0
  fi
  local_md5="$(sync_guard_local_md5 "$local_path")"
  verdict="$(sync_guard_verdict "$name" "$remote_md5" "$local_md5")"
  case "$verdict" in
    insync)
      echo "  = $name já em sync com o bucket."
      sync_guard_stash_write "$name" "$remote_md5"
      return 0
      ;;
    conflict)
      if [[ "$FORCE" == 0 ]]; then
        echo "  ✗ $name: local mudou desde o último sync E difere do bucket — pull RECUSADO."
        GUARD_CONFLICTS="$GUARD_CONFLICTS $name"
        return 0
      fi
      echo "  ⚠ $name: conflito ignorado (--force) — sobrescrevendo o local."
      ;;
  esac
  echo "→ $name"
  $DRY gcloud storage cp "$gs_url" "$local_path" --project="$PROJECT"
  sync_guard_stash_write "$name" "$remote_md5"
}
if ! gcloud storage buckets describe "gs://$BUCKET" --project="$PROJECT" >/dev/null 2>&1; then
  echo "ERROR: bucket gs://$BUCKET não acessível (verifique auth + projeto)." >&2
  exit 1
fi

echo "→ Project: $PROJECT"
echo "→ Bucket:  gs://$BUCKET"
[[ -n "$MIRROR_FLAG" ]] && echo "  (modo --mirror: deleta LOCAL o que não existe no bucket)"

# --mirror deleta arquivos locais ausentes no bucket. Confirmação obrigatória
# (exceto em dry-run) — clips/raw/ é protegido pelo --exclude abaixo, mas o
# resto de photos/ e clips/ transcodados ainda some se o bucket estiver
# incompleto.
if [[ -n "$MIRROR_FLAG" && -z "$DRY" ]]; then
  echo "  ⚠ --mirror vai DELETAR arquivos locais que não existam no bucket."
  read -r -p "  Continuar? [y/N] " _ans
  [[ "$_ans" == "y" || "$_ans" == "Y" ]] || { echo "Abortado."; exit 1; }
fi

# ── Dados mutáveis (uploads.ttl + data_graphs.ttl + tours.ttl) ──────────
if [[ "$SYNC_DATA" == 1 ]]; then
  mkdir -p "$REPO_ROOT/web/data"
  for f in uploads.ttl data_graphs.ttl tours.ttl; do
    guarded_pull "gs://$BUCKET/data/$f" "$REPO_ROOT/web/data/$f"
  done

  # routes.json: mesmo racional do tours.ttl — o /upload-tour faz upsert
  # incremental server-side (bucket-first); sem o pull, o próximo
  # deploy --state clobbera essas edições com a cópia local stale.
  guarded_pull "gs://$BUCKET/routes.json" "$REPO_ROOT/web/routes.json"
fi

# ── photos/ ─────────────────────────────────────────────────────────────
if [[ "$SYNC_PHOTOS" == 1 ]]; then
  mkdir -p "$REPO_ROOT/web/photos"
  echo "→ photos/"
  $DRY gcloud storage rsync --recursive $MIRROR_FLAG \
    "gs://$BUCKET/photos" "$REPO_ROOT/web/photos" \
    --project="$PROJECT"
fi

# ── clips/ ──────────────────────────────────────────────────────────────
# raw/ NÃO existe no bucket (deploy exclui). Por isso o --exclude abaixo é
# OBRIGATÓRIO: sem ele, `--mirror` (--delete-unmatched-destination-objects)
# apagaria web/clips/raw/ inteiro — centenas de MB de vídeos-fonte
# insubstituíveis — por estarem "ausentes na origem".
if [[ "$SYNC_CLIPS" == 1 ]]; then
  mkdir -p "$REPO_ROOT/web/clips"
  echo "→ clips/ (raw/ protegido)"
  $DRY gcloud storage rsync --recursive $MIRROR_FLAG \
    --exclude='^raw/.*$' \
    "gs://$BUCKET/clips" "$REPO_ROOT/web/clips" \
    --project="$PROJECT"
fi

echo ""
if [[ -n "$GUARD_CONFLICTS" ]]; then
  echo "⚠ PULL RECUSADO (lost update) para:$GUARD_CONFLICTS"
  echo "  O local mudou desde o último sync e difere do bucket — provavelmente"
  echo "  um build (build-tours.py / build-routes.py / build-clips.py) ou"
  echo "  edição local ainda não empurrado. Pra reconciliar:"
  echo "    1. faça backup/commit do arquivo local"
  echo "    2. rode com --force pra trazer o lado do bucket, e faça o merge"
  echo "  Ou, se o bucket é mesmo o vigente: rode com --force direto."
  echo "  (Primeiro uso sem baseline em .sync-state/ também cai aqui —"
  echo "   confira qual lado está certo e use --force uma vez.)"
  exit 3
fi
echo "✓ Done."
