#!/usr/bin/env bash
#
# Build + deploy do shell nativo (Capacitor) num device/emulador Android SEM
# abrir o Android Studio. Usa `npx cap run android` (gradle + adb por baixo).
# Requer o SDK do Android e o `adb` no PATH; o device precisa de Depuração USB
# ligada e autorizada (ou um emulador rodando). Ver README.md.
#
# Uso:
#   ./run-android.sh            # device de $ANDROID_SERIAL, ou seletor do cap
#   ./run-android.sh <serial>   # device específico (veja `adb devices`)
#   ./run-android.sh --list     # lista devices/emuladores e seus serials
#
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--list" ]]; then
  npx cap run android --list
  exit 0
fi

# Rejeita flags desconhecidas no 1º arg — senão `./run-android.sh --target X`
# viraria TARGET=--target e passaria `--target --target` pro cap, calado.
if [[ "${1:-}" == --* ]]; then
  echo "Opção desconhecida: $1" >&2
  echo "Uso: ./run-android.sh [<serial>|--list]" >&2
  exit 1
fi

if [[ ! -d android ]]; then
  echo "Projeto android/ ausente. Faça o setup uma vez:" >&2
  echo "  npm install && npx cap add android && npx cap sync android" >&2
  exit 1
fi

TARGET="${1:-${ANDROID_SERIAL:-}}"

# A tela "sem conexão" (server.errorPath) mora no webDir e o `cap sync` a copia
# pro projeto nativo (assets/public). Se o arquivo faltar, o Capacitor entra
# em laço: a falha ao carregar a própria página de erro dispara outro load dela.
ERROR_PAGE="$(node -e "const c = JSON.parse(require('fs').readFileSync('capacitor.config.json', 'utf8')); const p = (c.server || {}).errorPath; if (p) process.stdout.write((c.webDir || 'www') + '/' + p);")"
if [[ -n "$ERROR_PAGE" && ! -f "$ERROR_PAGE" ]]; then
  echo "server.errorPath aponta pra $ERROR_PAGE, que não existe." >&2
  exit 1
fi

# Copia web assets (a tela sem conexão do www/) + config/plugins nativos pro
# projeto android/.
npx cap sync android

# --no-sync: o sync acabou de rodar.
if [[ -n "$TARGET" ]]; then
  npx cap run android --no-sync --target "$TARGET"
else
  npx cap run android --no-sync
fi
