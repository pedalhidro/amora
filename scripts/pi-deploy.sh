#!/usr/bin/env bash
#
# Roda NO RASPBERRY PI. Atualiza o checkout, aplica migrações pequenas
# (rename de extensões), reinicia o serviço e mostra status.
#
# Uso (no Pi, via ssh):
#   bash scripts/pi-deploy.sh           # pull + restart + status
#   bash scripts/pi-deploy.sh --no-pull # só restart (depois de hotfix manual)
#   bash scripts/pi-deploy.sh --dry-run # mostra o que faria, sem aplicar
#
# Pré-requisitos:
#   - O repo já clonado e o serviço `phidro.service` (systemd) instalado
#     conforme backend/pi/README.md. Em macOS (launchd), o script detecta
#     `phidro.plist` carregado e usa `launchctl` no lugar.
#   - Usuário tem permissão pra rodar `systemctl restart phidro` (em geral
#     via systemd user service ou via sudo sem senha pro restart).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DO_PULL=1
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --no-pull) DO_PULL=0 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "argumento desconhecido: $arg" >&2; exit 2 ;;
  esac
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "  (dry-run) $*"; else eval "$@"; fi
}

# ─── 1. git pull ─────────────────────────────────────────────────────────────
if [[ $DO_PULL -eq 1 ]]; then
  echo "▸ git status (antes do pull)"
  git status --short || true
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "AVISO: working tree do Pi não está limpo — pull com rebase pode falhar." >&2
    echo "       Resolva antes de continuar, ou rode com --no-pull pra só reiniciar." >&2
    [[ $DRY_RUN -eq 0 ]] && exit 1
  fi
  echo "▸ git pull --ff-only"
  run "git pull --ff-only"
else
  echo "▸ pulando git pull (--no-pull)"
fi

# ─── 2. rename original.jpeg → original.jpg ──────────────────────────────────
# O backend agora normaliza extensão pra .jpg, mas arquivos antigos podem
# ter ficado como .jpeg — o frontend não tenta o fallback, então 404a.
if [[ -d web/photos ]]; then
  COUNT=$(find web/photos -type f -name 'original.jpeg' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$COUNT" -gt 0 ]]; then
    echo "▸ renomeando $COUNT arquivo(s) original.jpeg → original.jpg"
    if [[ $DRY_RUN -eq 0 ]]; then
      find web/photos -type f -name 'original.jpeg' \
        -execdir mv original.jpeg original.jpg \;
    fi
  fi
fi

# ─── 3. restart serviço ──────────────────────────────────────────────────────
restart_service() {
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^phidro\.service'; then
    echo "▸ systemctl restart phidro.service"
    run "sudo systemctl restart phidro.service"
    sleep 1
    echo "▸ systemctl status phidro.service --no-pager"
    systemctl --no-pager status phidro.service | head -12 || true
    return
  fi
  if command -v launchctl >/dev/null 2>&1 && launchctl list 2>/dev/null | grep -q phidro; then
    echo "▸ launchctl kickstart -k (macOS)"
    run "launchctl kickstart -k system/co.pedalhidrografi.phidro || launchctl kickstart -k gui/$(id -u)/co.pedalhidrografi.phidro"
    return
  fi
  echo "AVISO: nem systemd nem launchctl têm o phidro registrado. Reinicie o serviço manualmente." >&2
}
restart_service

# ─── 4. smoke check ──────────────────────────────────────────────────────────
PORT="${PORT:-8000}"
if [[ $DRY_RUN -eq 0 ]] && command -v curl >/dev/null 2>&1; then
  echo "▸ smoke check (http://localhost:$PORT/)"
  HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/" || echo "000")
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  OK ($HTTP_CODE)"
  else
    echo "  FALHA (HTTP $HTTP_CODE) — confira logs com: journalctl -u phidro -n 50" >&2
    exit 1
  fi
fi

echo "✓ deploy concluído"
