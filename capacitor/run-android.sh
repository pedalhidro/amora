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

# Copia web assets + config/plugins nativos pro projeto android/.
npx cap sync android

if [[ -n "$TARGET" ]]; then
  npx cap run android --target "$TARGET"
else
  npx cap run android
fi
