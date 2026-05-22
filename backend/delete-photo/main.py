"""
delete-photo — Cloud Function (2ª geração) que apaga uma foto do acervo.

Recebe POST { "id": "<id da foto>" } com o cabeçalho X-Upload-Token. Se o
token confere, apaga photos/<id>.jpg, thumbs/<id>.jpg e items/<id>.json em
gs://telhas/fotos/ e reconstrói o manifesto photos.jsonld.

ATENÇÃO: a remoção é DEFINITIVA — não há lixeira.

Variáveis de ambiente:
  OUT_BUCKET     bucket do acervo (padrão: telhas)
  OUT_PREFIX     prefixo dentro do bucket (padrão: fotos)
  UPLOAD_SECRET  token compartilhado — o MESMO usado pela função sign-upload
  ALLOWED_ORIGIN origem(ns) do site para o CORS (padrão: *)

Entry point: delete_photo    Runtime: python312
Veja README.md para deploy.
"""
import datetime
import json
import os
import re

from google.cloud import storage

OUT_BUCKET = os.environ.get("OUT_BUCKET", "telhas")
OUT_PREFIX = os.environ.get("OUT_PREFIX", "fotos").strip("/")
SECRET = os.environ["UPLOAD_SECRET"]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGIN", "*").split(",")
    if o.strip()
]

_gcs = storage.Client()

CONTEXT = {
    "ph": "https://pedalhidrografi.co/vocab/1.0/",
    "schema": "https://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "id": "@id",
    "type": "@type",
    "photos": "@graph",
    "orig": "schema:name",
    "file": {"@id": "schema:contentUrl", "@type": "@id"},
    "thumb": {"@id": "schema:thumbnailUrl", "@type": "@id"},
    "lat": "schema:latitude",
    "lng": "schema:longitude",
    "alt": "schema:elevation",
    "datetime": {"@id": "schema:dateCreated", "@type": "xsd:dateTime"},
}


def _allow_origin(request):
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


def _rebuild_manifest(bucket):
    """Reconstrói photos.jsonld a partir dos sidecars items/ restantes."""
    items = []
    for blob in bucket.list_blobs(prefix=f"{OUT_PREFIX}/items/"):
        if not blob.name.endswith(".json"):
            continue
        try:
            items.append(json.loads(blob.download_as_bytes()))
        except Exception as e:  # noqa: BLE001
            print(f"[manifest] item inválido {blob.name}: {e}")
    items.sort(key=lambda p: p.get("datetime") or "")
    manifest = {
        "@context": CONTEXT,
        "generatedAt": datetime.datetime.utcnow().isoformat(
            timespec="seconds") + "Z",
        "count": len(items),
        "photos": items,
    }
    out = bucket.blob(f"{OUT_PREFIX}/photos.jsonld")
    out.cache_control = "no-cache, max-age=60"
    out.upload_from_string(
        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        content_type="application/ld+json")
    print(f"[manifest] {len(items)} fotos → {OUT_PREFIX}/photos.jsonld")


def delete_photo(request):
    if request.method == "OPTIONS":
        return ("", 204, _headers(request))
    if request.method != "POST":
        return _json(request, {"error": "method not allowed"}, 405)

    body = request.get_json(silent=True) or {}
    token = request.headers.get("X-Upload-Token") or body.get("token")
    if not token or token != SECRET:
        return _json(request, {"error": "unauthorized"}, 403)

    pid = str(body.get("id") or "").strip()
    # ids do manifesto só têm [A-Za-z0-9._-]; rejeita o resto (path traversal).
    if not pid or not re.fullmatch(r"[A-Za-z0-9._-]+", pid):
        return _json(request, {"error": "id invalido"}, 400)

    bucket = _gcs.bucket(OUT_BUCKET)
    removed = []
    for path in (f"{OUT_PREFIX}/photos/{pid}.jpg",
                 f"{OUT_PREFIX}/thumbs/{pid}.jpg",
                 f"{OUT_PREFIX}/items/{pid}.json"):
        try:
            bucket.blob(path).delete()
            removed.append(path)
        except Exception:  # noqa: BLE001
            pass  # objeto já não existia

    _rebuild_manifest(bucket)
    print(f"apagado: {pid} ({len(removed)} objetos)")
    return _json(request, {"deleted": pid, "removed": removed}, 200)
