#!/usr/bin/env bash
#
# state-history.sh — navega o histórico de Object Versioning do bucket GCS
# (phidro-state) pros arquivos de estado mutável. Versioning é habilitado pelo
# deploy-cloudrun.sh: cada sobrescrita server-side (upload, Tour CRUD, delete)
# deixa a geração anterior como versão não-corrente. Este script lista, faz
# diff e restaura gerações — a "history-track" do que está no GCS.
#
# Uso:
#   scripts/state-history.sh list    <arquivo>
#   scripts/state-history.sh diff    <arquivo> <genA> <genB>
#   scripts/state-history.sh restore <arquivo> <gen>
#
#   <arquivo>: uploads.ttl | tours.ttl | data_graphs.ttl (sob data/) OU
#              routes.json (raiz do bucket). Nome simples; o script resolve a key.
#
# Exemplos:
#   scripts/state-history.sh list uploads.ttl
#   scripts/state-history.sh diff tours.ttl 1700000000123456 1700000999123456
#   scripts/state-history.sh restore uploads.ttl 1700000000123456
#
# restore é NÃO-destrutivo: copia a geração escolhida por cima da corrente, o
# que cria uma nova geração (a corrente atual vira não-corrente, ainda
# recuperável). Depois rode POST /reload no backend pra ele reler o catálogo.
#
# Env (mesmas defaults do deploy/pull):
#   GCP_PROJECT  default: pedal-hidrografico
#   GCS_BUCKET   default: phidro-state

set -euo pipefail

PROJECT="${GCP_PROJECT:-pedal-hidrografico}"
BUCKET="${GCS_BUCKET:-phidro-state}"
RELOAD_URL="${RELOAD_URL:-https://amora.pedalhidrografi.co/reload}"

usage() {
  cat >&2 <<'EOF'
uso:
  scripts/state-history.sh list    <arquivo>
  scripts/state-history.sh diff    <arquivo> <genA> <genB>
  scripts/state-history.sh restore <arquivo> <gen>

<arquivo>: uploads.ttl | tours.ttl | data_graphs.ttl | routes.json
env: GCP_PROJECT (default pedal-hidrografico), GCS_BUCKET (default phidro-state)
EOF
  exit "${1:-0}"
}

command -v gcloud >/dev/null 2>&1 || {
  echo "ERROR: gcloud CLI não encontrado." >&2; exit 1; }

# Resolve o nome simples (uploads.ttl) na key do bucket. routes.json fica na
# raiz; os TTLs ficam sob data/. Uma key já completa (com /) passa direto.
state_key() {
  local f="$1"
  case "$f" in
    routes.json) echo "routes.json" ;;
    */*)         echo "$f" ;;          # já é uma key (ex.: data/uploads.ttl)
    *.ttl)       echo "data/$f" ;;
    *) echo "ERROR: arquivo de estado não reconhecido: $f" >&2; return 1 ;;
  esac
}

cmd="${1:-}"; shift || true
case "$cmd" in
  list)
    [[ $# -eq 1 ]] || usage 2
    key="$(state_key "$1")"
    echo "→ Gerações de gs://$BUCKET/$key (inclui não-correntes):"
    gcloud storage ls --all-versions --long \
      "gs://$BUCKET/$key" --project="$PROJECT"
    ;;
  diff)
    [[ $# -eq 3 ]] || usage 2
    key="$(state_key "$1")"; genA="$2"; genB="$3"
    tmpA="$(mktemp)"; tmpB="$(mktemp)"
    trap 'rm -f "$tmpA" "$tmpB"' EXIT
    gcloud storage cp "gs://$BUCKET/$key#$genA" "$tmpA" --project="$PROJECT"
    gcloud storage cp "gs://$BUCKET/$key#$genB" "$tmpB" --project="$PROJECT"
    echo "→ diff $key  #$genA → #$genB"
    diff -u "$tmpA" "$tmpB" || true   # diff sai != 0 quando há diferenças
    ;;
  restore)
    [[ $# -eq 2 ]] || usage 2
    key="$(state_key "$1")"; gen="$2"
    echo "→ Restaurando gs://$BUCKET/$key para a geração #$gen"
    echo "  (não-destrutivo: a corrente atual vira não-corrente, recuperável)"
    read -r -p "  Continuar? [y/N] " ans
    [[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "Abortado."; exit 1; }
    gcloud storage cp "gs://$BUCKET/$key#$gen" "gs://$BUCKET/$key" \
      --project="$PROJECT"
    echo "✓ Restaurado. Recarregue o backend pra reler o catálogo:"
    echo "    curl -X POST $RELOAD_URL"
    ;;
  ""|-h|--help) usage 0 ;;
  *) echo "Subcomando desconhecido: $cmd" >&2; usage 2 ;;
esac
