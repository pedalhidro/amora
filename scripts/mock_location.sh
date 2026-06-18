#!/usr/bin/env bash
#
# Empurra posições de teste de "localização ao vivo" pra um backend, simulando
# alguém andando (random walk, ~2 min, 1 ponto a cada 3s). Útil pra ver o
# marcador + rastro aparecerem no app — inclusive no app iOS, que carrega o
# amora (server.url). curl NÃO precisa de CORS (CORS é só no browser).
#
# Por padrão bate no REMOTO (amora); passe --local pra usar 127.0.0.1:8080.
#
# Uso:
#   ./scripts/mock_location.sh                       # remoto (amora)
#   ./scripts/mock_location.sh --local               # local (127.0.0.1:8080)
#   ./scripts/mock_location.sh [--local] <id-hex> <apelido>
#
# NB (Cloud Run): a localização ao vivo é estado EM MEMÓRIA por processo. Pra
# funcionar no amora, o serviço precisa estar fixo em 1 instância (min=max=1),
# senão o POST e o GET do app podem cair em instâncias diferentes e o app não vê.
#
set -euo pipefail

BASE="https://amora.pedalhidrografi.co"
if [ "${1:-}" = "--local" ]; then
  BASE="http://127.0.0.1:${LOCAL_PORT:-8080}"
  shift
fi

ID="${1:-abcdef01}"          # precisa ser hex (+hífens); o backend rejeita o resto
NAME="${2:-fulanapedalante}"
TTL="${TTL:-10800}"          # retenção do rastro em s (3h)

lat=-23.55; lng=-46.63
echo "POST $BASE/live-location  ·  id=$ID  name=$NAME  ·  40 pontos (~2 min)"
for i in $(seq 1 40); do
  read lat lng acc <<<"$(python -c "import random; print($lat+random.uniform(-3e-4,3e-4), $lng+random.uniform(-3e-4,3e-4), round(random.uniform(8,40),1))")"
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/live-location" \
    -H 'Content-Type: application/json' \
    -d "{\"id\":\"$ID\",\"name\":\"$NAME\",\"lat\":$lat,\"lng\":$lng,\"accuracy\":$acc,\"ttl\":$TTL}")
  printf '%2d/40  HTTP %s  (%.5f, %.5f)  acc=%s\n' "$i" "$code" "$lat" "$lng" "$acc"
  sleep 3
done
echo "done. GET $BASE/live-locations to inspect."
