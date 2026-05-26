#!/usr/bin/env bash
#
# rsync `-e` transport que usa `gcloud compute ssh` em vez de ssh direto.
# Herda toda a autenticação do gcloud (OS Login + IAP + chave provisionada),
# então qualquer setup que faz `gcloud compute ssh INSTANCE` funcionar também
# faz rsync funcionar via este wrapper.
#
# rsync invoca: WRAPPER [ssh-opts...] user@host rsync-server-cmd args...
# Traduzimos:   gcloud compute ssh INSTANCE --zone=... --tunnel-through-iap
#                                   --command="<rsync-server-cmd args>"
#
# Config via env (lê do shell que chama o wrapper):
#   AMORA_ZONE      zona da VM        (opcional — gcloud auto-detecta se única)
#   AMORA_PROJECT   projeto GCP       (opcional — usa o gcloud config atual)
#   GCLOUD_VERBOSE  se setado, não passa --quiet (pra debug)

set -euo pipefail

# ── Extrai o host das opções ssh que rsync passa antes do positional ───────
HOST=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -l|-i|-p|-o|-F|-c|-e|-D|-J|-L|-R|-S|-w|-b|-B|-E|-I|-Q)
      # Flag com argumento — descarta os dois
      shift
      [[ $# -gt 0 ]] && shift
      ;;
    -*)
      # Flag sem argumento — descarta
      shift
      ;;
    *)
      # Primeiro positional = user@host (ou só host)
      HOST="$1"
      shift
      break
      ;;
  esac
done

if [[ -z "$HOST" ]]; then
  echo "gcloud-ssh-rsync: nenhum host encontrado nos args do rsync." >&2
  exit 2
fi
INSTANCE="${HOST##*@}"

# ── Re-quota o comando remoto pra mandar como string única ─────────────────
# Cada arg vira 'arg' (com aspas simples escapadas). O shell remoto vai
# re-parsear isso e executar o rsync --server com os args corretos.
CMD=""
for arg in "$@"; do
  esc=${arg//\'/\'\\\'\'}
  CMD+="'$esc' "
done

# ── Monta args do gcloud ───────────────────────────────────────────────────
GCLOUD_ARGS=(compute ssh "$INSTANCE" --tunnel-through-iap)
[[ -n "${AMORA_ZONE:-}"    ]] && GCLOUD_ARGS+=(--zone="$AMORA_ZONE")
[[ -n "${AMORA_PROJECT:-}" ]] && GCLOUD_ARGS+=(--project="$AMORA_PROJECT")
[[ -z "${GCLOUD_VERBOSE:-}" ]] && GCLOUD_ARGS+=(--quiet)
GCLOUD_ARGS+=(--command="$CMD")

exec gcloud "${GCLOUD_ARGS[@]}"
