# Pedal Hidrográfico — backend container.
# Mesmo Dockerfile serve dois alvos:
#   • Cloud Run (com STORAGE_BACKEND=gcs + GCS_BUCKET)
#   • Local docker (com STORAGE_BACKEND=local OU
#                   STORAGE_BACKEND=gcs + STORAGE_EMULATOR_HOST + GCS_BUCKET
#                    apontando pra fake-gcs-server)
#
# Build a partir do repo root:
#   docker build -t phidro-cloud .
# Run localmente (modo local):
#   docker run --rm -p 8080:8080 phidro-cloud
# Run localmente (modo gcs c/ emulador):
#   docker run --rm -p 8080:8080 \
#     -e STORAGE_BACKEND=gcs -e GCS_BUCKET=phidro-dev \
#     -e STORAGE_EMULATOR_HOST=http://host.docker.internal:4443 \
#     phidro-cloud
#
# Em produção (Cloud Run), o build é feito via `gcloud run deploy --source=.`
# que aciona Cloud Build automaticamente.

FROM python:3.12-slim AS base

# Native deps mínimas — rdflib/pyshacl são puro Python; libcurl ajuda
# no google-cloud-storage em algumas situações.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências primeiro pra cache layer eficiente.
COPY backend/pi/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código do backend.
COPY backend/pi/main.py backend/pi/storage.py ./

# Conteúdo estático do app (HTML/JS/CSS + shapes/ontology/tours).
# Estado mutável (web/data/uploads.ttl, web/data/data_graphs.ttl,
# web/photos/) é DELIBERADAMENTE excluído via .dockerignore — esse
# estado vive no STORE (filesystem ou GCS), não no container.
COPY web/ ./web/

ENV PHIDRO_WEB=/app/web \
    PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

# gunicorn em modo single-worker — Cloud Run faz scaling horizontal por
# instâncias, não por workers. 4 threads por instância pra absorver bursts.
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 \
      --timeout 60 --access-logfile - main:app
