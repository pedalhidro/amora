"""
sign-upload — Cloud Function (2ª geração) que emite URLs assinadas v4 para
o navegador enviar fotos direto ao bucket de uploads do Pedal Hidrográfico.

O navegador NUNCA recebe credenciais. Esta função, rodando com a sua própria
service account, assina uma URL de PUT com validade curta (10 min) presa a
um Content-Type específico; o navegador então envia o arquivo direto ao GCS.

Variáveis de ambiente:
  UPLOAD_BUCKET   bucket de uploads (ex.: pedalhidro-uploads)
  UPLOAD_SECRET   token compartilhado — o cliente precisa enviá-lo em todo POST
  ALLOWED_ORIGIN  origem do site para o CORS (ex.: https://telhas.pedalhidrografi.co)

Entry point: sign_upload    Runtime: python312
Veja README.md para os passos de deploy.
"""
import base64
import datetime
import json
import os
import re
import uuid

import google.auth
from google.auth.transport import requests as g_requests
from google.cloud import storage

BUCKET = os.environ["UPLOAD_BUCKET"]
SECRET = os.environ["UPLOAD_SECRET"]
# Uma ou mais origens permitidas, separadas por vírgula. Ex.:
#   "https://telhas.pedalhidrografi.co,http://localhost:8000"
# Use "*" apenas em desenvolvimento.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGIN", "*").split(",")
    if o.strip()
]
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}

_storage = storage.Client()


def _allow_origin(request):
    """Origem a ecoar no CORS — reflete a do pedido quando ela é permitida."""
    if "*" in ALLOWED_ORIGINS:
        return "*"
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"


def _headers(request, extra=None):
    h = {
        "Access-Control-Allow-Origin": _allow_origin(request),
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Upload-Token",
        "Access-Control-Max-Age": "3600",
    }
    if extra:
        h.update(extra)
    return h


def _json(request, payload, status):
    return (json.dumps(payload), status,
            _headers(request, {"Content-Type": "application/json"}))


def sign_upload(request):
    if request.method == "OPTIONS":
        return ("", 204, _headers(request))
    if request.method != "POST":
        return _json(request, {"error": "method not allowed"}, 405)

    body = request.get_json(silent=True) or {}
    token = request.headers.get("X-Upload-Token") or body.get("token")
    if not token or token != SECRET:
        return _json(request, {"error": "unauthorized"}, 403)

    content_type = (body.get("contentType") or "").lower()
    if content_type not in ALLOWED_TYPES:
        return _json(request, {"error": f"tipo nao permitido: {content_type}"}, 400)

    filename = body.get("filename") or "foto"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)[-80:]
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    leaf = f"{stamp}-{uuid.uuid4().hex[:8]}-{safe}"
    # O pedal detectado no cliente viaja embutido no caminho do objeto
    # (base64url); a process-upload o lê de lá — sem depender de routes.json.
    ride = body.get("ride")
    if isinstance(ride, dict) and ride.get("date"):
        token = (base64.urlsafe_b64encode(
            json.dumps(ride, ensure_ascii=False).encode("utf-8"))
            .decode("ascii").rstrip("="))
        object_name = f"uploads/r-{token}/{leaf}"
    else:
        object_name = f"uploads/{leaf}"

    # Assina a URL v4 usando a SA do runtime via IAM signBlob — sem chave .json.
    creds, _ = google.auth.default()
    creds.refresh(g_requests.Request())
    blob = _storage.bucket(BUCKET).blob(object_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=10),
        method="PUT",
        content_type=content_type,
        service_account_email=creds.service_account_email,
        access_token=creds.token,
    )
    return _json(request, {"uploadUrl": url, "objectPath": object_name}, 200)
