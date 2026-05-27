#!/usr/bin/env bash
#
# Dev local do backend (Cloud-Run-style): sobe o container Flask em modo
# STORAGE_BACKEND=local, montando ./web do repo como volume. Lê e escreve
# direto dos arquivos locais — exercita 95% do código (storage abstraction,
# rotas, validador SHACL) sem precisar do GCS emulator.
#
# Os uploads que o app fizer aparecem em ./web/photos/ e ./web/data/uploads.ttl
# do repo (rw mount). Ctrl-C derruba o container.
#
# Usage:
#   scripts/dev-cloudrun.sh             # build + run
#   scripts/dev-cloudrun.sh --no-build  # skip rebuild (usa cache)
#
# Pra testar o code path GCS de verdade, deploy num bucket de teste:
#   GCS_BUCKET=phidro-dev-meu CLOUDRUN_SERVICE=phidro-dev \
#     scripts/deploy-cloudrun.sh
# É mais confiável que o emulator (fake-gcs-server tem quirks que divergem
# do GCS real).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PORT="${DEV_APP_PORT:-8080}"
IMAGE="phidro-cloud:dev"

BUILD=1
for arg in "$@"; do
  case "$arg" in
    --no-build) BUILD=0 ;;
    -h|--help)
      sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker não está no PATH." >&2
  exit 1
fi

cleanup() {
  echo ""
  echo "→ Parando container…"
  docker stop phidro-app >/dev/null 2>&1 || true
  docker rm   phidro-app >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

if [[ "$BUILD" -eq 1 ]]; then
  echo "→ Building ${IMAGE}…"
  docker build -t "$IMAGE" "$REPO_ROOT"
fi

echo "→ Subindo app em :${APP_PORT}…"
echo "  Modo: STORAGE_BACKEND=local"
echo "  Volume: ${REPO_ROOT}/web  →  /app/web (rw)"
docker run -d --rm \
  --name phidro-app \
  -p "$APP_PORT:8080" \
  -e STORAGE_BACKEND=local \
  -e PHIDRO_WEB=/app/web \
  -v "${REPO_ROOT}/web:/app/web" \
  "$IMAGE" \
  >/dev/null

echo ""
echo "✓ Container rodando."
echo "  App:    http://localhost:${APP_PORT}"
echo "  Health: http://localhost:${APP_PORT}/health"
echo ""
echo "Logs (Ctrl-C pra parar):"
docker logs -f phidro-app
