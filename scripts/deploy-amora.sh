#!/usr/bin/env bash
#
# Sync this repo to the GCE instance `phidro` (host amora.pedalhidrografi.co)
# via rsync over an IAP-tunneled SSH, then restart the Flask service.
#
# Backend code = backend/pi/main.py, same que roda no Pi: serve web/ como
# estático + recebe /upload-image.
#
# A VM normalmente não tem IP público; o transporte SSH é o IAP tunnel do
# gcloud, configurado como ProxyCommand do ssh. Não precisa de `gcloud
# compute config-ssh` nem chave instalada no host — gcloud cuida de tudo,
# desde que `gcloud compute ssh phidro` já funcione.
#
# Usage:
#   scripts/deploy-amora.sh             # rsync + restart service
#   scripts/deploy-amora.sh --dry-run   # preview, no transfer/restart
#
# Overridable via env:
#   AMORA_INSTANCE   nome da VM no GCE          (default: phidro)
#   AMORA_ZONE       zona (opcional — gcloud auto-detecta se única)
#   AMORA_PROJECT    projeto (opcional — usa o gcloud config atual)
#   AMORA_USER       usuário SSH no host         (default: $USER) — pode ser
#                    necessário usar o usuário OS Login (algo como
#                    `seu_email_gmail_com`) se OS Login estiver ativo.
#   AMORA_PATH       caminho do repo na VM       (default: /home/$AMORA_USER/pedalhidrografico)
#   PHIDRO_SERVICE   unidade systemd             (default: phidro.service)
#   RSYNC_EXTRA      args extras pro rsync       (default: empty)
#
# Excludes preservados intactos no servidor (estado vivo):
#   web/data/                    catálogo TTL gerado por uploads
#   web/photos/                  variantes de imagem por phash
#   backend/pi/data/             legado Pi
#
# Requirements:
#   - gcloud CLI autenticado (`gcloud auth login`)
#   - `gcloud compute ssh $AMORA_INSTANCE` funcionando
#   - rsync local (macOS 2.6.9 OK; rsync 3.1+ ativa progress2 melhor)
#   - sudo na VM pra reiniciar o serviço (ou PHIDRO_SERVICE="" pra pular)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

AMORA_INSTANCE="${AMORA_INSTANCE:-phidro}"
AMORA_ZONE="${AMORA_ZONE:-southamerica-east1-a}"
AMORA_USER="${AMORA_USER:-danlessa}"
# Caminho do repo na VM. O usuário SSH (OS Login) é diferente do dono do
# diretório — o checkout vive em /home/danlessa/, não no $HOME do OS Login.
AMORA_PATH="${AMORA_PATH:-/home/danlessa/pedalhidrografico}"
PHIDRO_SERVICE="${PHIDRO_SERVICE:-phidro.service}"
RSYNC_EXTRA="${RSYNC_EXTRA:-}"

# ─── Argument parsing ────────────────────────────────────────────────────────
DRY=()
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY=(--dry-run)
  echo "↻ DRY RUN — no remote changes will be made."
fi

# ─── Pre-flight ──────────────────────────────────────────────────────────────
if ! command -v rsync >/dev/null 2>&1; then
  echo "ERROR: rsync not found locally." >&2
  exit 1
fi
if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud CLI não encontrado." >&2
  exit 1
fi
if [[ ! -d "$REPO_ROOT/web" ]]; then
  echo "ERROR: $REPO_ROOT/web missing." >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/web/routes.json" ]]; then
  echo "→ web/routes.json missing — running 'python scripts/build-routes.py'…"
  (cd "$REPO_ROOT" && python scripts/build-routes.py)
fi

# ─── SSH transport via `gcloud compute ssh` ─────────────────────────────────
# Em vez de tentar replicar a autenticação do gcloud (chave provisionada,
# OS Login, IAP), usamos o próprio `gcloud compute ssh` como transport do
# rsync, via wrapper em scripts/gcloud-ssh-rsync.sh. Qualquer ambiente que
# faz `gcloud compute ssh phidro` funcionar também faz o deploy funcionar.
SSH_WRAPPER="$REPO_ROOT/scripts/gcloud-ssh-rsync.sh"
if [[ ! -x "$SSH_WRAPPER" ]]; then
  echo "ERROR: wrapper SSH não encontrado em $SSH_WRAPPER" >&2
  exit 1
fi
export AMORA_ZONE AMORA_PROJECT
SSH_E="$SSH_WRAPPER"

# ─── Progress flag ───────────────────────────────────────────────────────────
PROGRESS=(--progress)
if rsync --version 2>/dev/null | awk 'NR==1{
  split($3, v, ".");
  if ((v[1]+0) > 3 || ((v[1]+0) == 3 && (v[2]+0) >= 1)) exit 0;
  exit 1;
}'; then
  PROGRESS=(--info=progress2,name0)
fi

# ─── rsync ───────────────────────────────────────────────────────────────────
DEST="${AMORA_USER}@${AMORA_INSTANCE}:${AMORA_PATH}/"
echo "→ Syncing $REPO_ROOT  →  $DEST  (via IAP)"

# --rsync-path='sudo rsync' faz o rsync remoto rodar como root, contornando
# qualquer conflito de ownership/perms (a árvore pode ter mistura de donos
# entre o serviço, o usuário do home, e o OS Login user). Requer passwordless
# sudo no destino — usuários com roles/compute.osAdminLogin já têm isso.
# shellcheck disable=SC2086
rsync -avz --human-readable --rsync-path='sudo rsync' "${PROGRESS[@]}" \
  ${DRY[@]+"${DRY[@]}"} \
  --delete \
  -e "$SSH_E" \
  --exclude='.git/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='*.swp' \
  --exclude='.venv/' \
  --exclude='node_modules/' \
  --exclude='web/data/' \
  --exclude='web/photos/' \
  --exclude='web/clips/raw/' \
  --exclude='backend/pi/data/' \
  $RSYNC_EXTRA \
  "$REPO_ROOT/" "$DEST"

# ─── Service restart ─────────────────────────────────────────────────────────
GCLOUD_SSH_OPTS=(--tunnel-through-iap --quiet)
[[ -n "${AMORA_ZONE:-}"    ]] && GCLOUD_SSH_OPTS+=(--zone="$AMORA_ZONE")
[[ -n "${AMORA_PROJECT:-}" ]] && GCLOUD_SSH_OPTS+=(--project="$AMORA_PROJECT")

if [[ "${#DRY[@]}" -eq 0 && -n "$PHIDRO_SERVICE" ]]; then
  echo "→ Restarting $PHIDRO_SERVICE em $AMORA_INSTANCE"
  gcloud compute ssh "$AMORA_INSTANCE" "${GCLOUD_SSH_OPTS[@]}" \
    --command="sudo systemctl restart $PHIDRO_SERVICE"
  gcloud compute ssh "$AMORA_INSTANCE" "${GCLOUD_SSH_OPTS[@]}" \
    --command="systemctl is-active $PHIDRO_SERVICE" || {
    echo "WARN: $PHIDRO_SERVICE não está active após restart. Veja:"
    echo "  gcloud compute ssh $AMORA_INSTANCE -- sudo journalctl -u $PHIDRO_SERVICE -n 50 --no-pager"
    exit 2
  }
fi

echo "✓ Done."
echo "  Public URL: https://amora.pedalhidrografi.co/"
