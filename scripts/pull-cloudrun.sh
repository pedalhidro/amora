#!/usr/bin/env bash
#
# Inverso de scripts/deploy-cloudrun.sh --state-only: puxa do bucket GCS
# (`phidro-state`) pro repo local o estado vivo do serviço — uploads.ttl,
# data_graphs.ttl, photos/, clips/. Útil pra desenvolver localmente com
# o catálogo atual de produção, ou pra ter backup do que foi enviado via
# upload_images.html / upload_tour.html.
#
# NÃO baixa shapes.ttl/ontology.ttl/tours.ttl: esses ficam versionados no
# git e o deploy é que sobe pro bucket — invertendo a direção corromperia
# o source-of-truth.
#
# Usage:
#   scripts/pull-cloudrun.sh                # uploads.ttl + data_graphs.ttl + photos/ + clips/
#   scripts/pull-cloudrun.sh --dry-run      # preview, sem baixar
#   scripts/pull-cloudrun.sh --photos-only  # só photos/
#   scripts/pull-cloudrun.sh --clips-only   # só clips/
#   scripts/pull-cloudrun.sh --data-only    # só uploads.ttl + data_graphs.ttl
#   scripts/pull-cloudrun.sh --mirror       # espelho exato: deleta local o que
#                                           # não existe no bucket (perigoso)
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
for arg in "$@"; do
  case "$arg" in
    --dry-run)     DRY="echo DRY: "; echo "↻ DRY RUN — nada será baixado." ;;
    --photos-only) SYNC_CLIPS=0; SYNC_DATA=0; EXPLICIT_SCOPE=1 ;;
    --clips-only)  SYNC_PHOTOS=0; SYNC_DATA=0; EXPLICIT_SCOPE=1 ;;
    --data-only)   SYNC_PHOTOS=0; SYNC_CLIPS=0; EXPLICIT_SCOPE=1 ;;
    --mirror)      MIRROR_FLAG="--delete-unmatched-destination-objects" ;;
    -h|--help)     sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "Argumento desconhecido: $arg" >&2; exit 2 ;;
  esac
done

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud CLI não encontrado." >&2
  exit 1
fi
if ! gcloud storage buckets describe "gs://$BUCKET" --project="$PROJECT" >/dev/null 2>&1; then
  echo "ERROR: bucket gs://$BUCKET não acessível (verifique auth + projeto)." >&2
  exit 1
fi

echo "→ Project: $PROJECT"
echo "→ Bucket:  gs://$BUCKET"
[[ -n "$MIRROR_FLAG" ]] && echo "  (modo --mirror: deleta LOCAL o que não existe no bucket)"

# ── Dados mutáveis (uploads.ttl + data_graphs.ttl) ──────────────────────
if [[ "$SYNC_DATA" == 1 ]]; then
  mkdir -p "$REPO_ROOT/web/data"
  for f in uploads.ttl data_graphs.ttl; do
    src="gs://$BUCKET/data/$f"
    dst="$REPO_ROOT/web/data/$f"
    if gcloud storage objects describe "$src" --project="$PROJECT" >/dev/null 2>&1; then
      echo "→ data/$f"
      $DRY gcloud storage cp "$src" "$dst" --project="$PROJECT"
    else
      echo "  ⚠ $src não existe no bucket — skip"
    fi
  done
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
# raw/ não existe no bucket (deploy exclui), então sync limpo é seguro.
if [[ "$SYNC_CLIPS" == 1 ]]; then
  mkdir -p "$REPO_ROOT/web/clips"
  echo "→ clips/"
  $DRY gcloud storage rsync --recursive $MIRROR_FLAG \
    "gs://$BUCKET/clips" "$REPO_ROOT/web/clips" \
    --project="$PROJECT"
fi

echo ""
echo "✓ Done."
