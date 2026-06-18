#!/usr/bin/env bash
#
# Build + deploy do shell nativo (Capacitor) num iPhone físico SEM abrir o
# Xcode. Usa `npx cap run ios`, que por baixo chama xcodebuild + instala/abre
# o app no device. O Xcode (toolchain + SDK) precisa estar instalado e a
# assinatura configurada UMA vez — ver README.md ("Config nativa" / "Rodar em
# device"). Edições só de web/ NÃO precisam disto: o app carrega o site remoto
# (server.url), então um deploy do web/ + pull-to-refresh já basta. Rebuild
# nativo só quando muda plugin / Info.plist / ícone.
#
# Uso:
#   ./run-ios.sh             # device de $IOS_UDID, ou seletor do cap se vazio
#   ./run-ios.sh <UDID>      # device específico
#   ./run-ios.sh --list      # lista devices/simuladores e seus UDIDs
#
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--list" ]]; then
  npx cap run ios --list
  exit 0
fi

# Rejeita flags desconhecidas no 1º arg — senão `./run-ios.sh --target X` viraria
# TARGET=--target e passaria `--target --target` pro cap, calado.
if [[ "${1:-}" == --* ]]; then
  echo "Opção desconhecida: $1" >&2
  echo "Uso: ./run-ios.sh [<UDID>|--list]" >&2
  exit 1
fi

if [[ ! -d ios ]]; then
  echo "Projeto ios/ ausente. Faça o setup uma vez:" >&2
  echo "  npm install && npx cap add ios && npx cap sync ios" >&2
  exit 1
fi

TARGET="${1:-${IOS_UDID:-}}"

# Copia web assets + config/plugins nativos pro projeto ios/.
npx cap sync ios

if [[ -n "$TARGET" ]]; then
  npx cap run ios --target "$TARGET"
else
  # Sem alvo: o cap abre um seletor interativo dos devices conectados.
  npx cap run ios
fi
