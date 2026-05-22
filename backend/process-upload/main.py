"""
process-upload — Cloud Function (2ª geração) disparada quando um arquivo
novo chega em gs://pedalhidro-uploads.

Para cada foto enviada:
  1. lê o GPS do EXIF;
  2. gera uma versão de exibição (JPEG ~1600 px) e um thumbnail (~400 px);
  3. grava ambos em gs://telhas/fotos/{photos,thumbs}/;
  4. escreve um sidecar items/<id>.json com os metadados;
  5. reconstrói o manifesto fotos/photos.jsonld a partir de todos os sidecars.

O manifesto é sempre reconstruído da lista completa de itens — então uploads
quase simultâneos convergem (cada disparo relista tudo). É consistência
eventual, adequada ao volume do projeto.

Variáveis de ambiente:
  OUT_BUCKET    bucket de saída (padrão: telhas)
  OUT_PREFIX    prefixo dentro do bucket (padrão: fotos)
  PUBLIC_BASE   URL pública da pasta (padrão: https://telhas.pedalhidrografi.co/fotos)
  ROUTES_URL    (opcional) routes.json para ligar foto↔pedal pela data

Entry point: process_upload    Runtime: python312
Veja README.md para deploy e IAM.
"""
import base64
import datetime
import io
import json
import math
import os
import re
import urllib.request
from pathlib import PurePosixPath

import functions_framework
import pillow_heif
from google.cloud import storage
from PIL import ExifTags, Image, ImageOps

pillow_heif.register_heif_opener()

OUT_BUCKET = os.environ.get("OUT_BUCKET", "telhas")
OUT_PREFIX = os.environ.get("OUT_PREFIX", "fotos").strip("/")
PUBLIC_BASE = os.environ.get(
    "PUBLIC_BASE", "https://telhas.pedalhidrografi.co/fotos").rstrip("/")
ROUTES_URL = os.environ.get("ROUTES_URL", "")

IMG_EXTS = {".heic", ".heif", ".jpg", ".jpeg", ".png"}
DISPLAY_MAX = 1600
THUMB_MAX = 400
QUALITY = 82

_gcs = storage.Client()
_routes_cache = None

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
        direction = gps.get(17)  # GPSImgDirection — bússola da câmera
        if direction is not None:
            try:
                out["bearing"] = round(float(direction) % 360, 1)
            except (TypeError, ValueError):
                pass
    f35 = exif.get(41989)  # FocalLengthIn35mmFilm → campo de visão
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


# ── Ligação foto ↔ pedal (best-effort, via routes.json) ──────────────────
def _load_routes():
    global _routes_cache
    if _routes_cache is not None:
        return _routes_cache
    _routes_cache = {}
    if ROUTES_URL:
        try:
            req = urllib.request.Request(ROUTES_URL, headers={
                "User-Agent":
                    "Mozilla/5.0 (compatible; PedalHidrografico-process-upload)",
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
            print(f"[routes] não carregou {ROUTES_URL}: {e}")
    return _routes_cache


def ride_from_name(name):
    """Lê o pedal embutido no caminho 'uploads/r-<base64url>/...' (se houver).

    A função sign-upload codifica ali o pedal que o app detectou no
    navegador — é a fonte preferida, dispensando o fetch de routes.json.
    """
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


def ride_for(dt_iso):
    if not dt_iso:
        return None
    routes = _load_routes()
    cand = [dt_iso[:10]]
    try:
        t = datetime.datetime.fromisoformat(dt_iso)
        if t.hour < 6:  # foto de madrugada → pode ser o pedal da véspera
            cand.append((t.date() - datetime.timedelta(days=1)).isoformat())
    except ValueError:
        pass
    for d in cand:
        if d in routes:
            return {"date": d, **routes[d]}
    return None


# ── Imagens ──────────────────────────────────────────────────────────────
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


def _rebuild_manifest(bucket):
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
    _put(bucket, f"{OUT_PREFIX}/photos.jsonld",
         json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
         "application/ld+json", immutable=False)
    print(f"[manifest] {len(items)} fotos → {OUT_PREFIX}/photos.jsonld")


# ── Entry point ──────────────────────────────────────────────────────────
@functions_framework.cloud_event
def process_upload(cloud_event):
    data = cloud_event.data
    src_bucket = data["bucket"]
    name = data["name"]

    # Só processa as fotos cruas que a função sign-upload deposita em uploads/.
    if not name.startswith("uploads/"):
        print(f"ignorado (fora de uploads/): {name}")
        return
    ext = PurePosixPath(name).suffix.lower()
    if ext not in IMG_EXTS:
        print(f"ignorado (não-imagem): {name}")
        return

    raw = _gcs.bucket(src_bucket).blob(name).download_as_bytes()
    try:
        meta = read_exif(Image.open(io.BytesIO(raw)))
    except Exception as e:  # noqa: BLE001
        print(f"falha ao abrir {name}: {e}")
        return
    if meta["lat"] is None or meta["lng"] is None:
        print(f"sem GPS no EXIF, não entra no mapa: {name}")
        return

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
        # Prefere o pedal detectado pelo app; routes.json é só o reserva.
        "ride": ride_from_name(name) or ride_for(meta["datetime"]),
    }
    _put(out, f"{OUT_PREFIX}/items/{pid}.json",
         json.dumps(item, ensure_ascii=False).encode("utf-8"),
         "application/json", immutable=False)

    _rebuild_manifest(out)
    print(f"processado: {name} → {pid}")
