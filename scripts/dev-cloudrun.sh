#!/usr/bin/env bash
#
# Dev local do backend (Cloud-Run-style): sobe o container Flask com ./web
# do repo montado como volume (itera no frontend sem rebuild). Dois modos
# de DADOS:
#
#   --hosted-data (DEFAULT)  STORAGE_BACKEND=gcs apontando pro bucket de
#       PRODUÇÃO (phidro-state) com as credenciais ADC do gcloud da máquina.
#       O app local consome e MODIFICA o mesmo estado servido em
#       https://amora.pedalhidrografi.co/ — catálogos TTL, routes.json,
#       fotos/clips (302 pro bucket). Bom pra desenvolver o frontend contra
#       os dados reais. CUIDADO: uploads/edições feitos aqui vão direto pra
#       produção; ao sair, o script manda POST /reload pra produção
#       invalidar os caches em memória dela (dedup, feed, sitemap).
#
#   --local-data  STORAGE_BACKEND=local lendo/escrevendo os arquivos do
#       repo (./web/data/*.ttl, ./web/photos/). Exercita 95% do código sem
#       tocar em nada hospedado — o modo antigo deste script.
#
# Usage:
#   scripts/dev-cloudrun.sh               # build + run (dados de produção)
#   scripts/dev-cloudrun.sh --local-data  # estado nos arquivos do repo
#   scripts/dev-cloudrun.sh --no-build    # skip rebuild (usa cache)
#
# Pra testar o code path GCS SEM tocar produção, deploy num bucket de teste:
#   GCS_BUCKET=phidro-dev-meu CLOUDRUN_SERVICE=phidro-dev \
#     scripts/deploy-cloudrun.sh
# É mais confiável que o emulator (fake-gcs-server tem quirks que divergem
# do GCS real).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PORT="${DEV_APP_PORT:-8080}"
IMAGE="phidro-cloud:dev"
GCS_BUCKET="${GCS_BUCKET:-phidro-state}"
GCP_PROJECT="${GCP_PROJECT:-pedal-hidrografico}"
PROD_URL="${PROD_URL:-https://amora.pedalhidrografi.co}"
ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"

BUILD=1
DATA_MODE=hosted
for arg in "$@"; do
  case "$arg" in
    --no-build)    BUILD=0 ;;
    --hosted-data) DATA_MODE=hosted ;;
    --local-data)  DATA_MODE=local ;;
    -h|--help)
      sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//; $d'; exit 0 ;;
    *)
      echo "ERROR: flag desconhecida: $arg (use --help)" >&2; exit 1 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker não está no PATH." >&2
  exit 1
fi

if [[ "$DATA_MODE" == hosted && ! -f "$ADC_FILE" ]]; then
  echo "ERROR: modo --hosted-data precisa das credenciais ADC do gcloud." >&2
  echo "  Rode:  gcloud auth application-default login" >&2
  echo "  (ou use --local-data pra ficar nos arquivos do repo)" >&2
  exit 1
fi

cleanup() {
  echo ""
  echo "→ Parando container…"
  docker stop phidro-app >/dev/null 2>&1 || true
  docker rm   phidro-app >/dev/null 2>&1 || true
  if [[ "$DATA_MODE" == hosted ]]; then
    # A produção mantém caches em memória (dedup de hashes, feed, sitemap) e
    # não vê escritas out-of-band no bucket até um /reload. Best-effort.
    echo "→ POST ${PROD_URL}/reload (invalida caches da produção)…"
    curl -fsS -X POST --max-time 10 "${PROD_URL}/reload" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "$BUILD" -eq 1 ]]; then
  echo "→ Building ${IMAGE}…"
  docker build -t "$IMAGE" "$REPO_ROOT"
fi

RUN_ARGS=(
  -d --rm
  --name phidro-app
  -p "$APP_PORT:8080"
  -e PHIDRO_WEB=/app/web
  -v "${REPO_ROOT}/web:/app/web"
)
# RWGPS_API_KEY/RWGPS_AUTH_TOKEN pro sync de rota no Tour CRUD (best-effort;
# rotas públicas funcionam sem). SÓ essas duas chaves — passar o .env inteiro
# (--env-file) vazaria PORT=3000/PUBLIC_BASE_URL de outros usos pro container,
# e o PORT desviaria o bind do gunicorn do :8080 que o docker mapeia
# (browser: ERR_CONNECTION_RESET). Extração idêntica à do deploy-cloudrun.sh.
if [[ -f "${REPO_ROOT}/.env" ]]; then
  for k in RWGPS_API_KEY RWGPS_AUTH_TOKEN; do
    v="$(grep -E "^${k}=" "${REPO_ROOT}/.env" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
    [[ -n "$v" ]] && RUN_ARGS+=(-e "${k}=${v}")
  done
fi

if [[ "$DATA_MODE" == hosted ]]; then
  RUN_ARGS+=(
    -e STORAGE_BACKEND=gcs
    -e GCS_BUCKET="$GCS_BUCKET"
    -e GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
    # Sem isso, um tour editado daqui assaria http://localhost:8080/… num
    # schema:image que vai DIRETO pro estado de produção (caso PH/96).
    -e PUBLIC_BASE_URL="$PROD_URL"
    -v "$HOME/.config/gcloud:/root/.config/gcloud:ro"
  )
else
  RUN_ARGS+=(-e STORAGE_BACKEND=local)
fi

echo "→ Subindo app em :${APP_PORT}…"
if [[ "$DATA_MODE" == hosted ]]; then
  echo "  Modo: STORAGE_BACKEND=gcs → bucket ${GCS_BUCKET} (PRODUÇÃO)"
  echo "  ⚠  Uploads/edições feitos aqui modificam o estado servido em"
  echo "     ${PROD_URL} — o mesmo que o site no ar."
  echo "     (Pra sandbox local: scripts/dev-cloudrun.sh --local-data)"
else
  echo "  Modo: STORAGE_BACKEND=local (estado nos arquivos do repo)"
fi
echo "  Volume: ${REPO_ROOT}/web  →  /app/web (rw)"
docker run "${RUN_ARGS[@]}" "$IMAGE" >/dev/null

echo ""
echo "✓ Container rodando."
echo "  App:    http://localhost:${APP_PORT}"
echo "  Health: http://localhost:${APP_PORT}/health"
echo ""
echo "Logs (Ctrl-C pra parar):"
docker logs -f phidro-app
