#!/usr/bin/env bash
#
# Deploy do backend pra Cloud Run no projeto `pedal-hidrografico`, região
# southamerica-east1 (São Paulo). Cria o bucket GCS de estado se faltando,
# concede leitura pública (pra servir as fotos por redirect), enable das
# APIs necessárias, build via Cloud Build a partir do Dockerfile na raiz,
# deploy do service.
#
# Usage:
#   scripts/deploy-cloudrun.sh                # build + deploy
#   scripts/deploy-cloudrun.sh --dry-run      # imprime configs sem executar
#   scripts/deploy-cloudrun.sh --state        # build + deploy + também
#                                             # sincroniza estado mutável
#                                             # (uploads.ttl, data_graphs.ttl,
#                                             #  routes.json, photos/, clips/)
#                                             # pro bucket
#   scripts/deploy-cloudrun.sh --state-only   # SÓ sincroniza estado mutável,
#                                             # sem rebuild/redeploy
#   scripts/deploy-cloudrun.sh --state --mirror   # sync com espelho exato
#                                                 # (apaga no bucket o que
#                                                 #  não existe localmente)
#
# Overridable via env:
#   GCP_PROJECT        default: pedal-hidrografico
#   GCP_REGION         default: southamerica-east1
#   CLOUDRUN_SERVICE   default: phidro
#   GCS_BUCKET         default: phidro-state
#   CLOUDRUN_MEMORY    default: 512Mi
#   CLOUDRUN_CPU       default: 1
#   CLOUDRUN_MAX_INSTANCES  default: 5
#   CLOUDRUN_MIN_INSTANCES  default: 0  (scale-to-zero)
#
# Pré-requisitos:
#   • gcloud autenticado (`gcloud auth login`)
#   • Permissões: Cloud Run Admin, Storage Admin, Cloud Build Editor,
#     Service Account User no projeto.
#   • Cloud Build, Cloud Run e Cloud Storage APIs ativadas (o script
#     ativa idempotentemente).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${GCP_PROJECT:-pedal-hidrografico}"
REGION="${GCP_REGION:-southamerica-east1}"
SERVICE="${CLOUDRUN_SERVICE:-phidro}"
BUCKET="${GCS_BUCKET:-phidro-state}"
MEMORY="${CLOUDRUN_MEMORY:-512Mi}"
CPU="${CLOUDRUN_CPU:-1}"
MAX_INSTANCES="${CLOUDRUN_MAX_INSTANCES:-5}"
MIN_INSTANCES="${CLOUDRUN_MIN_INSTANCES:-0}"

DRY=""
SYNC_STATE=0
DEPLOY_CODE=1
MIRROR_FLAG=""
for arg in "$@"; do
  case "$arg" in
    --dry-run)    DRY="echo DRY: "; echo "↻ DRY RUN — nenhuma mudança real será aplicada." ;;
    --state)      SYNC_STATE=1 ;;
    --state-only) SYNC_STATE=1; DEPLOY_CODE=0 ;;
    --mirror)     MIRROR_FLAG="--delete-unmatched-destination-objects" ;;
    -h|--help)    sed -n '2,35p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done
if [[ "$MIRROR_FLAG" != "" && "$SYNC_STATE" == 0 ]]; then
  echo "WARN: --mirror sem --state/--state-only não tem efeito." >&2
fi

echo "→ Project:  $PROJECT"
echo "→ Region:   $REGION"
echo "→ Service:  $SERVICE"
echo "→ Bucket:   gs://$BUCKET"
echo "→ Resources: $CPU CPU, $MEMORY mem, instances $MIN_INSTANCES..$MAX_INSTANCES"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud CLI não encontrado." >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/Dockerfile" ]]; then
  echo "ERROR: Dockerfile não encontrado em $REPO_ROOT" >&2
  exit 1
fi

# ── 1. Enable APIs (idempotente) ────────────────────────────────────────
echo "→ Ativando APIs necessárias…"
$DRY gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  --project="$PROJECT"

# ── 2. Bucket ───────────────────────────────────────────────────────────
if gcloud storage buckets describe "gs://$BUCKET" --project="$PROJECT" >/dev/null 2>&1; then
  echo "→ Bucket gs://$BUCKET já existe — preservado."
else
  echo "→ Criando bucket gs://$BUCKET em $REGION"
  # Sem --public-access-prevention: o default ("inherited" / disabled) já é o
  # que queremos — a IAM binding allUsers:objectViewer abaixo depende disso.
  $DRY gcloud storage buckets create "gs://$BUCKET" \
    --location="$REGION" \
    --project="$PROJECT" \
    --uniform-bucket-level-access

  echo "→ Concedendo leitura pública (pra servir fotos via redirect)…"
  $DRY gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
    --member=allUsers \
    --role=roles/storage.objectViewer \
    --project="$PROJECT"
fi

# CORS: aplicado em TODO deploy (idempotente), não só na criação do bucket.
# Buckets criados antes desta config não tinham CORS — e o player ghost-video
# usa `crossOrigin=anonymous` pro pulse de áudio via Web Audio, que SÓ recebe
# sinal se a resposta vier com Access-Control-Allow-Origin. Sem isto, áudio
# silencioso no modo gcs em qualquer bucket pré-existente.
echo "→ Configurando CORS no bucket (idempotente)…"
CORS_FILE="$(mktemp)"
cat > "$CORS_FILE" <<EOF
[{"origin":["*"],"method":["GET","HEAD"],"responseHeader":["Content-Type"],"maxAgeSeconds":3600}]
EOF
$DRY gcloud storage buckets update "gs://$BUCKET" \
  --cors-file="$CORS_FILE" \
  --project="$PROJECT"
rm -f "$CORS_FILE"

# ── 2b. Sync TTLs estáticos pro bucket ──────────────────────────────────
# shapes.ttl, ontology.ttl, tours.ttl ficam tanto baked-in no container
# (seed/fallback) quanto no bucket (fonte vigente — bucket-first read).
# Re-upload em cada deploy garante que git é a source-of-truth e o bucket
# nunca fica permanentemente desatualizado.
echo "→ Sincronizando TTLs estáticos pro bucket…"
for f in shapes.ttl ontology.ttl tours.ttl; do
  if [[ -f "$REPO_ROOT/web/data/$f" ]]; then
    $DRY gcloud storage cp "$REPO_ROOT/web/data/$f" "gs://$BUCKET/data/$f" \
      --project="$PROJECT"
  else
    echo "  ⚠ $REPO_ROOT/web/data/$f não existe localmente — skip"
  fi
done

# ── 3. Deploy ───────────────────────────────────────────────────────────
if [[ "$DEPLOY_CODE" == 1 ]]; then
  # Credenciais RWGPS pro sync incremental de routes.json no /upload-tour.
  # O container NÃO leva o .env (segredo, fora do build context); injetamos
  # como env vars do service, lendo do .env local. Sem elas o backend ainda
  # funciona — só rotas privadas/unlisted falham o fetch (latlngs:null).
  RUN_ENV_VARS="STORAGE_BACKEND=gcs,GCS_BUCKET=$BUCKET"
  if [[ -f "$REPO_ROOT/.env" ]]; then
    RWGPS_API_KEY="$(grep -E '^RWGPS_API_KEY=' "$REPO_ROOT/.env" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
    RWGPS_AUTH_TOKEN="$(grep -E '^RWGPS_AUTH_TOKEN=' "$REPO_ROOT/.env" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
    if [[ -n "$RWGPS_API_KEY" && -n "$RWGPS_AUTH_TOKEN" ]]; then
      if [[ -n "$DRY" ]]; then
        # Dry-run ecoa o comando inteiro — não vaza os tokens no terminal.
        RUN_ENV_VARS="$RUN_ENV_VARS,RWGPS_API_KEY=***,RWGPS_AUTH_TOKEN=***"
      else
        RUN_ENV_VARS="$RUN_ENV_VARS,RWGPS_API_KEY=$RWGPS_API_KEY,RWGPS_AUTH_TOKEN=$RWGPS_AUTH_TOKEN"
      fi
      echo "→ Credenciais RWGPS do .env serão injetadas no service."
    else
      echo "  ⚠ .env sem RWGPS_API_KEY/RWGPS_AUTH_TOKEN — sync de rotas privadas falhará."
    fi
  else
    echo "  ⚠ $REPO_ROOT/.env não existe — sync de rotas privadas falhará."
  fi

  echo "→ Deploy do service $SERVICE (build pelo Cloud Build a partir de $REPO_ROOT/Dockerfile)…"
  $DRY gcloud run deploy "$SERVICE" \
    --source="$REPO_ROOT" \
    --region="$REGION" \
    --project="$PROJECT" \
    --allow-unauthenticated \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --timeout=120 \
    --concurrency=80 \
    --max-instances="$MAX_INSTANCES" \
    --min-instances="$MIN_INSTANCES" \
    --set-env-vars="$RUN_ENV_VARS"
else
  echo "→ Pulando deploy de código (--state-only)."
fi

# ── 4. Estado mutável (--state / --state-only) ──────────────────────────
# Sync de uploads.ttl + data_graphs.ttl + routes.json + photos/ + clips/ pro bucket.
# Por padrão o deploy NÃO faz isso pra não clobberar uploads server-side;
# rode com a flag quando quiser espelhar o local pra cloud.
if [[ "$SYNC_STATE" == 1 ]]; then
  echo ""
  echo "→ Sincronizando estado mutável pra gs://$BUCKET"
  [[ -n "$MIRROR_FLAG" ]] && echo "  (modo --mirror: deleta no bucket o que não existe local)"

  for f in uploads.ttl data_graphs.ttl; do
    if [[ -f "$REPO_ROOT/web/data/$f" ]]; then
      $DRY gcloud storage cp "$REPO_ROOT/web/data/$f" "gs://$BUCKET/data/$f" \
        --project="$PROJECT"
    else
      echo "  ⚠ web/data/$f não existe localmente — skip"
    fi
  done

  # routes.json é servido bucket-first (o backend faz upsert incremental por
  # upload de tour). Um rebuild local completo (build-routes.py) só chega na
  # cloud se empurrado aqui — mesma tensão dual-writer que uploads.ttl.
  if [[ -f "$REPO_ROOT/web/routes.json" ]]; then
    $DRY gcloud storage cp "$REPO_ROOT/web/routes.json" "gs://$BUCKET/routes.json" \
      --project="$PROJECT"
  else
    echo "  ⚠ web/routes.json não existe localmente — skip"
  fi

  if [[ -d "$REPO_ROOT/web/photos" ]]; then
    echo "→ photos/"
    $DRY gcloud storage rsync --recursive $MIRROR_FLAG \
      "$REPO_ROOT/web/photos" "gs://$BUCKET/photos" \
      --project="$PROJECT"
  fi

  # web/clips/raw/ é fonte (originais ~800MB) — não vai pro bucket.
  if [[ -d "$REPO_ROOT/web/clips" ]]; then
    echo "→ clips/ (excluindo raw/)"
    $DRY gcloud storage rsync --recursive $MIRROR_FLAG \
      --exclude='^raw/.*$' \
      "$REPO_ROOT/web/clips" "gs://$BUCKET/clips" \
      --project="$PROJECT"
  fi
fi

if [[ -z "$DRY" ]]; then
  URL=$(gcloud run services describe "$SERVICE" \
    --region="$REGION" --project="$PROJECT" \
    --format='value(status.url)' 2>/dev/null || true)

  if [[ -n "$URL" ]]; then
    # Limpa caches in-memory (validator + manifesto). Vale tanto pra deploy
    # novo (que já começa frio, mas talvez tenha tráfego split) quanto pra
    # --state-only (no qual o service em si não muda, mas o catálogo sim).
    curl -fsS -X POST "$URL/reload" >/dev/null 2>&1 || true
  fi

  echo ""
  if [[ "$DEPLOY_CODE" == 1 ]]; then
    echo "✓ Deployed."
    echo "  Cloud Run URL: $URL"
    echo "  Custom domain (se mapeado): https://amora.pedalhidrografi.co/"
    echo ""
    echo "Pra mapear domínio custom (uma única vez):"
    echo "  gcloud beta run domain-mappings create \\"
    echo "    --service=$SERVICE --domain=amora.pedalhidrografi.co \\"
    echo "    --region=$REGION --project=$PROJECT"
  else
    echo "✓ Estado sincronizado."
  fi
fi
