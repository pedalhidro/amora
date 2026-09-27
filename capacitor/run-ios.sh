#!/usr/bin/env bash
#
# Build + deploy do shell nativo (Capacitor) num iPhone físico SEM abrir o
# Xcode. Usa `npx cap run ios`, que por baixo chama xcodebuild + instala/abre
# o app no device. O Xcode (toolchain + SDK) precisa estar instalado e a
# assinatura configurada UMA vez — ver README.md ("Config nativa" / "Rodar em
# device"). Edições só de web/ NÃO precisam disto: o app carrega o site remoto
# (server.url), então um deploy do web/ chega sozinho, como no PWA (ver
# "Limitações do shell" no README — não há pull-to-refresh). Rebuild nativo só
# quando muda plugin / capacitor.config.json / Info.plist / ícone.
#
# A cada execução o script também (re)aplica as chaves do Info.plist que o
# shell exige (ver apply_info_plist): o ios/ é gerado e gitignorado, então
# qualquer `npx cap add ios` as perde.
#
# Uso:
#   ./run-ios.sh             # device de $IOS_UDID, ou seletor do cap se vazio
#   ./run-ios.sh <UDID>      # device específico
#   ./run-ios.sh --list      # lista devices/simuladores e seus UDIDs
#   ./run-ios.sh --prepare   # só sync + Info.plist, sem build (pra buildar
#                            # pelo Xcode depois: `npx cap open ios`)
#
set -euo pipefail
cd "$(dirname "$0")"

PREPARE_ONLY=0
case "${1:-}" in
  --list)
    npx cap run ios --list
    exit 0
    ;;
  --prepare)
    PREPARE_ONLY=1
    shift
    ;;
  --*)
    # Rejeita flags desconhecidas no 1º arg — senão `./run-ios.sh --target X`
    # viraria TARGET=--target e passaria `--target --target` pro cap, calado.
    echo "Opção desconhecida: $1" >&2
    echo "Uso: ./run-ios.sh [<UDID>|--list|--prepare]" >&2
    exit 1
    ;;
esac

if [[ ! -d ios ]]; then
  echo "Projeto ios/ ausente. Faça o setup uma vez:" >&2
  echo "  npm install && npx cap add ios && ./run-ios.sh --prepare" >&2
  exit 1
fi

TARGET="${1:-${IOS_UDID:-}}"
PLIST="ios/App/App/Info.plist"

# Roda um trecho de JS com `c` = capacitor.config.json (node já é
# pré-requisito do npx cap).
config_js() {
  node -e "const c = JSON.parse(require('fs').readFileSync('capacitor.config.json', 'utf8')); $1"
}

# A tela "sem conexão" (server.errorPath) mora no webDir e o `cap sync` a copia
# pro projeto nativo. Se o arquivo faltar, o Capacitor entra em laço: a falha
# ao carregar a própria página de erro dispara outro load dela.
ERROR_PAGE="$(config_js "const p = (c.server || {}).errorPath; if (p) process.stdout.write((c.webDir || 'www') + '/' + p);")"
if [[ -n "$ERROR_PAGE" && ! -f "$ERROR_PAGE" ]]; then
  echo "server.errorPath aponta pra $ERROR_PAGE, que não existe." >&2
  exit 1
fi

# ─── Info.plist ──────────────────────────────────────────────────────────────
# O template do Capacitor não traz NENHUMA destas chaves. Sem as
# *UsageDescription o iOS ENCERRA o app na hora em que o seletor de arquivos
# do WebKit abre a câmera ("Tirar Foto" / "Tirar Foto ou Gravar Vídeo" — todo
# <input type=file> de imagem oferece) ou em que uma imagem vai pras Fotos
# (toque longo → "Salvar nas Fotos", folha de compartilhar → "Salvar Imagem").
# `plutil -replace` insere ou sobrescreve (e recebe o valor como argumento,
# sem o parser de aspas do PlistBuddy), então reaplicar é idempotente.
# Mantenha os textos em sincronia com o bloco do README.md.
apply_info_plist() {
  if [[ "$(uname -s)" != Darwin ]] || ! command -v plutil >/dev/null 2>&1; then
    echo "Aviso: plutil indisponível (só existe no macOS) — Info.plist NÃO atualizado." >&2
    echo "       Aplique à mão o bloco \"iOS — Info.plist\" do README.md." >&2
    return 0
  fi
  if [[ ! -f "$PLIST" ]]; then
    echo "Info.plist não encontrado em $PLIST." >&2
    exit 1
  fi

  set_string() { plutil -replace "$1" -string "$2" "$PLIST"; }

  # Localização ao vivo (plugin background-geolocation).
  set_string NSLocationWhenInUseUsageDescription \
    'Mostra sua posição no mapa e a compartilha ao vivo enquanto você usa o app.'
  set_string NSLocationAlwaysAndWhenInUseUsageDescription \
    'Mantém o compartilhamento da sua localização ao vivo durante o pedal, mesmo com a tela apagada. Você liga e desliga quando quiser.'
  # Câmera/microfone do seletor de arquivos e gravação nas Fotos.
  set_string NSCameraUsageDescription \
    'Tira fotos e grava vídeos na hora, quando você escolhe a câmera para enviar imagens ao acervo do pedal.'
  set_string NSMicrophoneUsageDescription \
    'Grava o som dos vídeos que você filma pela câmera do app para enviar ao acervo do pedal.'
  set_string NSPhotoLibraryAddUsageDescription \
    'Salva nas suas Fotos as imagens que você pedir para guardar, como a colagem do álbum.'
  # Ícones escuros na barra de status: a barra do app é branca, e o default
  # (automático) vira ícones brancos no Modo Escuro — branco no branco.
  set_string UIStatusBarStyle UIStatusBarStyleDarkContent

  # UIBackgroundModes: garante "location" sem apagar outros modos.
  local modes
  modes="$(plutil -extract UIBackgroundModes json -o - "$PLIST" 2>/dev/null || true)"
  if [[ -z "$modes" ]]; then
    plutil -replace UIBackgroundModes -json '["location"]' "$PLIST"
  elif [[ "$modes" != *'"location"'* ]]; then
    plutil -insert UIBackgroundModes.0 -string location "$PLIST"
  fi

  # App-Bound Domains: é o que liga o service worker na WKWebView. Anda JUNTO
  # com `ios.limitsNavigationsToAppBoundDomains` do capacitor.config.json — a
  # chave SEM a flag marca toda navegação como fora do domínio, e o WebKit
  # passa a bloquear os scripts injetados e o evaluateJavaScript: a ponte do
  # Capacitor (e com ela a localização em segundo plano) morre. Por isso a
  # lista sai da config: flag ligada → host do server.url + localhost (a tela
  # sem conexão, capacitor://localhost); flag desligada → a chave SAI.
  local bound
  bound="$(config_js "
    if (!(c.ios && c.ios.limitsNavigationsToAppBoundDomains === true)) process.exit(0);
    const d = [];
    if (c.server && c.server.url) d.push(new URL(c.server.url).hostname);
    d.push((c.server && c.server.hostname) || 'localhost');
    process.stdout.write(JSON.stringify([...new Set(d)]));
  ")"
  if [[ -n "$bound" ]]; then
    plutil -replace WKAppBoundDomains -json "$bound" "$PLIST"
  else
    plutil -remove WKAppBoundDomains "$PLIST" >/dev/null 2>&1 || true
  fi

  plutil -lint -s "$PLIST"
  echo "Info.plist: localização, câmera/microfone/Fotos, barra de status escura${bound:+, WKAppBoundDomains $bound}."
}

# Copia web assets (a tela sem conexão do www/) + config/plugins nativos pro
# projeto ios/, e só DEPOIS mexe no Info.plist.
npx cap sync ios
apply_info_plist

if [[ "$PREPARE_ONLY" == 1 ]]; then
  echo "Pronto. Abra no Xcode com: npx cap open ios"
  exit 0
fi

# --no-sync: o sync acabou de rodar (o `cap run` faria outro, com pod install).
if [[ -n "$TARGET" ]]; then
  npx cap run ios --no-sync --target "$TARGET"
else
  # Sem alvo: o cap abre um seletor interativo dos devices conectados.
  npx cap run ios --no-sync
fi
