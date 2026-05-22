"""
Pedal Hidrográfico — API (serviço único no Cloud Run)

Substitui as três Cloud Functions por um só serviço Flask com rotas:
  POST /sign-upload   emite URL assinada para upload         (era sign-upload)
  POST /delete-photo  apaga uma foto do acervo               (era delete-photo)
  POST /events        processa upload novo via Eventarc/GCS  (era process-upload)
  GET  /              health check

As fotos do acervo ficam no Firestore (coleção `photos`) — fonte da verdade,
com gravações atômicas. O photos.jsonld no GCS é só um cache estático,
recriado a cada upload/remoção, servido pelo CDN ao app.

Variáveis de ambiente:
  UPLOAD_BUCKET   bucket de uploads crus       (padrão: pedalhidro-uploads)
  OUT_BUCKET      bucket do acervo             (padrão: telhas)
  OUT_PREFIX      prefixo no acervo            (padrão: fotos)
  PUBLIC_BASE     URL pública da pasta do acervo
  UPLOAD_SECRET   token compartilhado (sign-upload e delete-photo)
  ALLOWED_ORIGIN  origem(ns) do site p/ CORS   (padrão: *)
  ROUTES_URL      (opcional) routes.json — reserva p/ ligar foto↔pedal

Roda com gunicorn (ver Procfile). Deploy e IAM: ver README.md.
"""
import base64
import datetime
import io
import json
import os
import re
import urllib.request
import uuid
from pathlib import PurePosixPath

import google.auth
import pillow_heif
from flask import Flask, request
from google.auth.transport import requests as g_requests
from google.cloud import firestore, storage
from PIL import ExifTags, Image, ImageOps

pillow_heif.register_heif_opener()

UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET", "pedalhidro-uploads")
OUT_BUCKET = os.environ.get("OUT_BUCKET", "telhas")
OUT_PREFIX = os.environ.get("OUT_PREFIX", "fotos").strip("/")
PUBLIC_BASE = os.environ.get(
    "PUBLIC_BASE", "https://telhas.pedalhidrografi.co/fotos").rstrip("/")
SECRET = os.environ["UPLOAD_SECRET"]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGIN", "*").split(",")
    if o.strip()
]
ROUTES_URL = os.environ.get("ROUTES_URL", "")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}
IMG_EXTS = {".heic", ".heif", ".jpg", ".jpeg", ".png"}
DISPLAY_MAX, THUMB_MAX, QUALITY = 1600, 400, 82

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

_gcs = storage.Client()
_db = firestore.Client()
PHOTOS_COLL = "photos"  # coleção do Firestore — fonte da verdade das fotos
_routes_cache = None
app = Flask(__name__)


# ── CORS ─────────────────────────────────────────────────────────────────
def _allow_origin():
    if "*" in ALLOWED_ORIGINS:
        return "*"
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"


@app.after_request
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = _allow_origin()
    resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Upload-Token"
    resp.headers["Access-Control-Max-Age"] = "3600"
    return resp


def _authorized(body):
    token = request.headers.get("X-Upload-Token") or body.get("token")
    return bool(token) and token == SECRET


# ── EXIF ─────────────────────────────────────────────────────────────────
def _dms_to_decimal(dms, ref):
    try:
        d, m, s = (float(x) for x in dms)
    except (TypeError, ValueError):
        return None
    dec = d + m / 60.0 + s / 3600.0
    if str(ref).strip().upper() in ("S", "W"):
        dec = -dec
    return dec


def read_exif(img):
    import math
    out = {"lat": None, "lng": None, "alt": None, "datetime": None,
           "bearing": None, "fov": None}
    try:
        exif = img.getexif()
    except Exception:
        return out
    if not exif:
        return out
    try:
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    except Exception:
        gps = {}
    if gps:
        lat = _dms_to_decimal(gps.get(2), gps.get(1))
        lng = _dms_to_decimal(gps.get(4), gps.get(3))
        if lat is not None and lng is not None:
            out["lat"] = round(lat, 6)
            out["lng"] = round(lng, 6)
        alt = gps.get(6)
        if alt is not None:
            try:
                out["alt"] = round(float(alt), 1)
            except (TypeError, ValueError):
                pass
        direction = gps.get(17)  # GPSImgDirection
        if direction is not None:
            try:
                out["bearing"] = round(float(direction) % 360, 1)
            except (TypeError, ValueError):
                pass
    f35 = exif.get(41989)  # FocalLengthIn35mmFilm
    if f35:
        try:
            f = float(f35)
            if f > 0:
                portrait = (exif.get(274) or 1) in (5, 6, 7, 8)
                frame = 24.0 if portrait else 36.0
                out["fov"] = round(
                    math.degrees(2 * math.atan(frame / (2 * f))), 1)
        except (TypeError, ValueError):
            pass
    dt_raw = exif.get(36867) or exif.get(306)
    if dt_raw:
        try:
            out["datetime"] = datetime.datetime.strptime(
                str(dt_raw).strip(), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            pass
    return out


# ── Ligação foto ↔ pedal ─────────────────────────────────────────────────
def _load_routes():
    global _routes_cache
    if _routes_cache is not None:
        return _routes_cache
    _routes_cache = {}
    if ROUTES_URL:
        try:
            req = urllib.request.Request(ROUTES_URL, headers={
                "User-Agent":
                    "Mozilla/5.0 (compatible; PedalHidrografico-api)",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            for rt in data.get("routes", []):
                d = rt.get("date")
                if not d:
                    continue
                num = rt.get("number") or {}
                code = (f"{num.get('source')} {num.get('value')}"
                        if num.get("value") else None)
                _routes_cache[d] = {"code": code, "name": rt.get("name")}
        except Exception as e:  # noqa: BLE001
            print(f"[routes] nao carregou {ROUTES_URL}: {e}")
    return _routes_cache


def ride_for(dt_iso):
    if not dt_iso:
        return None
    routes = _load_routes()
    cand = [dt_iso[:10]]
    try:
        t = datetime.datetime.fromisoformat(dt_iso)
        if t.hour < 6:
            cand.append((t.date() - datetime.timedelta(days=1)).isoformat())
    except ValueError:
        pass
    for d in cand:
        if d in routes:
            return {"date": d, **routes[d]}
    return None


def ride_from_name(name):
    """Lê o pedal embutido no caminho 'uploads/r-<base64url>/...'."""
    for part in name.split("/"):
        if part.startswith("r-"):
            try:
                token = part[2:]
                token += "=" * (-len(token) % 4)
                ride = json.loads(base64.urlsafe_b64decode(token))
                if isinstance(ride, dict) and ride.get("date"):
                    return ride
            except Exception:  # noqa: BLE001
                return None
    return None


# ── Imagens / acervo ─────────────────────────────────────────────────────
def _render(raw, max_size):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return buf.getvalue()


def _put(bucket, path, data, content_type, immutable):
    blob = bucket.blob(path)
    blob.cache_control = ("public, max-age=31536000, immutable" if immutable
                          else "no-cache, max-age=60")
    blob.upload_from_string(data, content_type=content_type)


def _rebuild_manifest():
    """Gera o photos.jsonld a partir da coleção `photos` do Firestore.

    O Firestore é a fonte da verdade (gravações atômicas por documento, sem
    a corrida que havia ao reconstruir de sidecars). O photos.jsonld é só um
    cache estático servido pelo CDN ao app.
    """
    photos = [d.to_dict() for d in _db.collection(PHOTOS_COLL).stream()]
    photos.sort(key=lambda p: p.get("datetime") or "")
    manifest = {
        "@context": CONTEXT,
        "generatedAt": datetime.datetime.utcnow().isoformat(
            timespec="seconds") + "Z",
        "count": len(photos),
        "photos": photos,
    }
    _put(_gcs.bucket(OUT_BUCKET), f"{OUT_PREFIX}/photos.jsonld",
         json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
         "application/ld+json", immutable=False)
    print(f"[manifest] {len(photos)} fotos")


# ── Rotas HTTP ───────────────────────────────────────────────────────────
@app.get("/")
def health():
    return "pedalhidrografico api ok\n"


@app.route("/sign-upload", methods=["POST", "OPTIONS"])
def sign_upload():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(silent=True) or {}
    if not _authorized(body):
        return ({"error": "unauthorized"}, 403)
    content_type = (body.get("contentType") or "").lower()
    if content_type not in ALLOWED_TYPES:
        return ({"error": f"tipo nao permitido: {content_type}"}, 400)

    safe = re.sub(r"[^A-Za-z0-9._-]", "_", body.get("filename") or "foto")[-80:]
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    leaf = f"{stamp}-{uuid.uuid4().hex[:8]}-{safe}"
    ride = body.get("ride")
    if isinstance(ride, dict) and ride.get("date"):
        token = (base64.urlsafe_b64encode(
            json.dumps(ride, ensure_ascii=False).encode("utf-8"))
            .decode("ascii").rstrip("="))
        object_name = f"uploads/r-{token}/{leaf}"
    else:
        object_name = f"uploads/{leaf}"

    creds, _ = google.auth.default()
    creds.refresh(g_requests.Request())
    blob = _gcs.bucket(UPLOAD_BUCKET).blob(object_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=10),
        method="PUT",
        content_type=content_type,
        service_account_email=creds.service_account_email,
        access_token=creds.token,
    )
    return {"uploadUrl": url, "objectPath": object_name}


@app.route("/delete-photo", methods=["POST", "OPTIONS"])
def delete_photo():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(silent=True) or {}
    if not _authorized(body):
        return ({"error": "unauthorized"}, 403)
    pid = str(body.get("id") or "").strip()
    if not pid or not re.fullmatch(r"[A-Za-z0-9._-]+", pid):
        return ({"error": "id invalido"}, 400)

    bucket = _gcs.bucket(OUT_BUCKET)
    removed = []
    for path in (f"{OUT_PREFIX}/photos/{pid}.jpg",
                 f"{OUT_PREFIX}/thumbs/{pid}.jpg"):
        try:
            bucket.blob(path).delete()
            removed.append(path)
        except Exception:  # noqa: BLE001
            pass
    _db.collection(PHOTOS_COLL).document(pid).delete()
    _rebuild_manifest()
    print(f"apagado: {pid} ({len(removed)} objetos)")
    return {"deleted": pid, "removed": removed}


@app.post("/events")
def events():
    """Recebe o evento GCS object-finalized entregue pelo Eventarc."""
    data = request.get_json(silent=True) or {}
    src_bucket = data.get("bucket")
    name = data.get("name")
    if not src_bucket or not name:
        return ("ignored: sem bucket/name", 200)
    if not name.startswith("uploads/"):
        return (f"ignored: fora de uploads/ ({name})", 200)
    ext = PurePosixPath(name).suffix.lower()
    if ext not in IMG_EXTS:
        return (f"ignored: nao-imagem ({name})", 200)

    raw = _gcs.bucket(src_bucket).blob(name).download_as_bytes()
    try:
        meta = read_exif(Image.open(io.BytesIO(raw)))
    except Exception as e:  # noqa: BLE001
        print(f"falha ao abrir {name}: {e}")
        return (f"ignored: nao abriu ({name})", 200)
    if meta["lat"] is None or meta["lng"] is None:
        return (f"ignored: sem GPS ({name})", 200)

    pid = re.sub(r"[^A-Za-z0-9._-]", "_", PurePosixPath(name).stem)
    out = _gcs.bucket(OUT_BUCKET)
    _put(out, f"{OUT_PREFIX}/photos/{pid}.jpg",
         _render(raw, DISPLAY_MAX), "image/jpeg", immutable=True)
    _put(out, f"{OUT_PREFIX}/thumbs/{pid}.jpg",
         _render(raw, THUMB_MAX), "image/jpeg", immutable=True)
    item = {
        "id": pid,
        "type": "ph:Image",
        "orig": PurePosixPath(name).name,
        "file": f"{PUBLIC_BASE}/photos/{pid}.jpg",
        "thumb": f"{PUBLIC_BASE}/thumbs/{pid}.jpg",
        "lat": meta["lat"],
        "lng": meta["lng"],
        "alt": meta["alt"],
        "datetime": meta["datetime"],
        "bearing": meta["bearing"],
        "fov": meta["fov"],
        "ride": ride_from_name(name) or ride_for(meta["datetime"]),
    }
    _db.collection(PHOTOS_COLL).document(pid).set(item)
    _rebuild_manifest()
    print(f"processado: {name} -> {pid}")
    return (f"ok: {pid}", 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
