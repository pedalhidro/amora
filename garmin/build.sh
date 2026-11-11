#!/bin/bash
# Compila os três apps Connect IQ pros dois aparelhos.
#
#   CIQ_SDK=/caminho/do/sdk garmin/build.sh            # tudo
#   CIQ_SDK=… garmin/build.sh quilojaules              # só um app
#
# Precisa de: Java 17+, o SDK do Connect IQ descompactado (CIQ_SDK = a pasta
# que tem bin/monkeyc) e as definições de aparelho em
# ~/.Garmin/ConnectIQ/Devices/{edge1040,fr955} (o SDK Manager baixa; dá pra
# copiar essas duas pastas de outra máquina). A chave de desenvolvedor é
# garmin/developer_key.der (gerada na primeira vez; fora do git).
# Saída: garmin/<app>/bin/<app>-<aparelho>.prg
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${CIQ_SDK:?defina CIQ_SDK com a pasta do SDK do Connect IQ}"
KEY="$HERE/developer_key.der"
if [ ! -f "$KEY" ]; then
  openssl genrsa -out "$HERE/developer_key.pem" 4096 2>/dev/null
  openssl pkcs8 -topk8 -inform PEM -outform DER -in "$HERE/developer_key.pem" -out "$KEY" -nocrypt
fi
APPS=("$@")
[ ${#APPS[@]} -eq 0 ] && APPS=(quilojaules pessoas amora)
fail=0
for app in "${APPS[@]}"; do
  mkdir -p "$HERE/$app/bin"
  for dev in edge1040 fr955; do
    echo "=== $app · $dev"
    if ! bash "$CIQ_SDK/bin/monkeyc" -f "$HERE/$app/monkey.jungle" -d "$dev" \
        -o "$HERE/$app/bin/$app-$dev.prg" -y "$KEY" -l 3 -w; then
      fail=1
    fi
  done
done
exit $fail
