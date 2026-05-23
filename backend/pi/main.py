"""
Pedal Hidrográfico — backend auto-hospedável (Raspberry Pi)

Um único serviço Flask, sem nenhuma dependência de nuvem:
  - serve o app do mapa (public/)
  - serve as fotos do acervo (data/fotos/)
  - recebe uploads, processa (EXIF + thumbnail) e mantém o photos.jsonld
  - apaga fotos

Arquivos ficam em disco; o índice das fotos fica em SQLite.

Rotas:
  GET  /                health do app — public/index.html
  GET  /<arquivo>       estáticos do app (app.js, style.css, sw.js, ...)
  GET  /fotos/<cam>     fotos processadas, thumbnails e photos.jsonld
  GET  /health          "ok"
  POST /sign-upload     devolve uma URL de PUT no próprio host
  PUT  /put/<cam>       recebe o arquivo e o processa
  POST /delete-photo    apaga uma foto

Sem autenticação: presume-se que quem alcança o servidor é de confiança.

Variáveis de ambiente:
  PHIDRO_DATA     pasta de dados             (padrão: ./data)
  PHIDRO_PUBLIC   pasta do app               (padrão: ../../public)
  PUBLIC_BASE     prefixo das URLs de foto   (padrão: /fotos)

Deploy no Raspberry Pi: ver README.md.
"""
import base64
import datetime
import io
import json
import math
import os
import re
import sqlite3
import uuid
import zipfile
from pathlib import Path, PurePosixPath

import pillow_heif
from flask import Flask, abort, jsonify, request, send_from_directory
from PIL import ExifTags, Image, ImageOps

pillow_heif.register_heif_opener()

DATA = Path(os.environ.get("PHIDRO_DATA", "data")).resolve()
PUBLIC = Path(os.environ.get(
    "PHIDRO_PUBLIC",
    Path(__file__).resolve().parents[2] / "public")).resolve()
PUBLIC_BASE = os.environ.get("PUBLIC_BASE", "/fotos").rstrip("/")

FOTOS = DATA / "fotos"
PHOTOS_DIR = FOTOS / "photos"
THUMBS_DIR = FOTOS / "thumbs"
ORIGINALS = DATA / "originals"
DB_PATH = DATA / "photos.db"
for _d in (PHOTOS_DIR, THUMBS_DIR, ORIGINALS):
    _d.mkdir(parents=True, exist_ok=True)

IMG_EXTS = {".heic", ".heif", ".jpg", ".jpeg", ".png"}
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}
DISPLAY_MAX, THUMB_MAX, QUALITY = 1600, 400, 82
# Limiar do hash perceptual (dHash de 64 bits, distancia de Hamming). Um
# upload a ate esta distancia de uma foto ja no acervo entra no mesmo
# "cluster": e a mesma foto, vista por vozes diferentes. 8/64 (~12%) pega
# recompressoes e redimensionamentos sem casar cenas apenas parecidas.
PHASH_THRESHOLD = int(os.environ.get("PHASH_THRESHOLD", "8"))

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
    "cluster": "ph:cluster",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024  # uploads e import .zip


# ── SQLite ───────────────────────────────────────────────────────────────
def _now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db():
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS photos "
                "(id TEXT PRIMARY KEY, datetime TEXT, data TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS voices "
                "(id TEXT PRIMARY KEY, label TEXT, created TEXT)")
    for _col in ("voice TEXT", "phash TEXT"):
        try:
            con.execute(f"ALTER TABLE photos ADD COLUMN {_col}")
        except sqlite3.OperationalError:
            pass  # a coluna já existe
    for _col in ("kind TEXT", "pubkey TEXT", "verified INTEGER"):
        try:
            con.execute(f"ALTER TABLE voices ADD COLUMN {_col}")
        except sqlite3.OperationalError:
            pass  # a coluna já existe
    # garante a voz padrão
    con.execute(
        "INSERT OR IGNORE INTO voices (id, label, created, kind) "
        "VALUES (?, ?, ?, ?)",
        ("voice/censo", "Censo Hidrográfico", _now(), "model"))
    # tipo da voz: 'model' (inanimada, p.ex. o censo) ou 'person' (animada).
    # A divergência só fica visível quando uma voz-modelo está envolvida.
    con.execute("UPDATE voices SET kind='model' "
                "WHERE id='voice/censo' AND (kind IS NULL OR kind='')")
    con.execute("UPDATE voices SET kind='person' "
                "WHERE kind IS NULL OR kind=''")
    con.commit()
    return con


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
        direction = gps.get(17)
        if direction is not None:
            try:
                out["bearing"] = round(float(direction) % 360, 1)
            except (TypeError, ValueError):
                pass
    f35 = exif.get(41989)
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


def meta_from_name(name):
    """Lê {ride, voice} embutidos no caminho 'uploads/r-<base64url>/...'."""
    for part in name.split("/"):
        if part.startswith("r-"):
            try:
                token = part[2:]
                token += "=" * (-len(token) % 4)
                payload = json.loads(base64.urlsafe_b64decode(token))
                if isinstance(payload, dict):
                    return payload
            except Exception:
                return {}
    return {}


def _render(raw, max_size):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return buf.getvalue()


# ── Hash perceptual (dedup entre vozes) ──────────────────────────────────
def _dhash(img):
    """dHash de 64 bits em hex (16 chars). Compara o brilho de pixels
    vizinhos numa miniatura 9x8 — robusto a recompressao e redimensionamento.
    Aplica exif_transpose para que uma copia girada nao deixe de casar."""
    g = ImageOps.exif_transpose(img).convert("L").resize(
        (9, 8), Image.LANCZOS)
    px = g.tobytes()  # 72 bytes, um por pixel (linha a linha)
    bits = 0
    for row in range(8):
        base = row * 9
        for col in range(8):
            bits = (bits << 1) | (1 if px[base + col] > px[base + col + 1]
                                  else 0)
    return f"{bits:016x}"


def _hamming(a, b):
    """Distancia de Hamming entre dois dHashes hex."""
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def _match_cluster(con, phash, exclude=None):
    """Acha no acervo a foto mais parecida com `phash`. Devolve
    (cluster, distancia) se estiver dentro do limiar; senao (None, dist)."""
    best_cluster, best_d = None, 65
    for pid, ph, data in con.execute(
            "SELECT id, phash, data FROM photos "
            "WHERE phash IS NOT NULL AND phash != ''"):
        if pid == exclude:
            continue
        try:
            d = _hamming(phash, ph)
        except (ValueError, TypeError):
            continue
        if d < best_d:
            best_d = d
            try:
                best_cluster = json.loads(data).get("cluster") or pid
            except Exception:  # noqa: BLE001
                best_cluster = pid
    if best_cluster is not None and best_d <= PHASH_THRESHOLD:
        return best_cluster, best_d
    return None, best_d


def _ensure_hashes():
    """Backfill: calcula o phash das fotos antigas a partir do display jpg,
    para que uploads novos possam casar contra elas."""
    con = _db()
    todo = [r[0] for r in con.execute(
        "SELECT id FROM photos WHERE phash IS NULL OR phash = ''")]
    done = 0
    for pid in todo:
        jpg = PHOTOS_DIR / f"{pid}.jpg"
        if not jpg.exists():
            continue
        try:
            with Image.open(jpg) as im:
                h = _dhash(im)
        except Exception:  # noqa: BLE001
            continue
        con.execute("UPDATE photos SET phash = ? WHERE id = ?", (h, pid))
        done += 1
    if done:
        con.commit()
        print(f"[hash] backfill de {done} foto(s)")
    con.close()


def _rebuild_manifest():
    """Gera photos.jsonld como um dataset de vozes (grafos nomeados).

    Cada foto pertence a uma voz; o manifesto agrupa por voz e inclui também
    as vozes registradas que ainda não têm fotos (para aparecerem no app).
    """
    con = _db()
    voice_rows = con.execute(
        "SELECT id, label, kind, pubkey, verified "
        "FROM voices ORDER BY created").fetchall()
    photo_rows = con.execute("SELECT voice, data FROM photos").fetchall()
    con.close()

    by_voice = {}
    for vid, data in photo_rows:
        by_voice.setdefault(vid or "voice/censo", []).append(json.loads(data))

    now = _now()
    known = {row[0] for row in voice_rows}
    voices = []
    for vid, label, kind, pubkey, verified in voice_rows:
        photos = sorted(by_voice.get(vid, []),
                        key=lambda p: p.get("datetime") or "")
        voices.append({"id": vid, "label": label, "kind": kind or "person",
                       "signed": bool(pubkey), "verified": bool(verified),
                       "pubkey": pubkey, "generatedAt": now,
                       "photos": photos})
    # defensivo: fotos cuja voz não está registrada na tabela
    for vid, photos in by_voice.items():
        if vid not in known:
            voices.append({
                "id": vid, "label": vid, "kind": "person",
                "signed": False, "verified": False, "pubkey": None,
                "generatedAt": now,
                "photos": sorted(photos, key=lambda p: p.get("datetime") or ""),
            })

    manifest = {"@context": CONTEXT, "generatedAt": now, "voices": voices}
    (FOTOS / "photos.jsonld").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v["photos"]) for v in voices)
    print(f"[manifest] {total} fotos em {len(voices)} voz(es)")


# ── Servir o app e as fotos ──────────────────────────────────────────────
@app.get("/health")
def health():
    return "ok\n"


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/fotos/<path:p>")
def fotos(p):
    resp = send_from_directory(FOTOS, p)
    if p.endswith(".jsonld"):
        resp.headers["Content-Type"] = "application/ld+json"
        resp.headers["Cache-Control"] = "no-cache"
    else:
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


@app.get("/<path:p>")
def public_files(p):
    if (PUBLIC / p).is_file():
        return send_from_directory(PUBLIC, p)
    abort(404)


# ── API ──────────────────────────────────────────────────────────────────
@app.post("/sign-upload")
def sign_upload():
    body = request.get_json(silent=True) or {}
    ct = (body.get("contentType") or "").lower()
    if ct not in ALLOWED_TYPES:
        return jsonify(error=f"tipo nao permitido: {ct}"), 400
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", body.get("filename") or "foto")[-80:]
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    leaf = f"{stamp}-{uuid.uuid4().hex[:8]}-{safe}"
    # Embute {ride, voice} (detectados/escolhidos no cliente) no caminho.
    payload = {}
    ride = body.get("ride")
    if isinstance(ride, dict) and ride.get("date"):
        payload["ride"] = ride
    voice = body.get("voice")
    if isinstance(voice, str) and voice and voice != "all":
        payload["voice"] = voice
    if payload:
        token = (base64.urlsafe_b64encode(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            .decode("ascii").rstrip("="))
        objname = f"uploads/r-{token}/{leaf}"
    else:
        objname = f"uploads/{leaf}"
    return jsonify(uploadUrl=f"/put/{objname}", objectPath=objname)


@app.route("/put/<path:objpath>", methods=["PUT"])
def put(objpath):
    if not objpath.startswith("uploads/"):
        abort(400)
    ext = PurePosixPath(objpath).suffix.lower()
    if ext not in IMG_EXTS:
        abort(400)
    raw = request.get_data()
    if not raw:
        abort(400)

    pid = re.sub(r"[^A-Za-z0-9._-]", "_", PurePosixPath(objpath).stem)
    (ORIGINALS / f"{pid}{ext}").write_bytes(raw)  # arquiva o original

    try:
        meta = read_exif(Image.open(io.BytesIO(raw)))
    except Exception as e:  # noqa: BLE001
        print(f"[put] imagem ilegível {objpath}: {e}")
        return ("imagem ilegivel", 200)
    if meta["lat"] is None or meta["lng"] is None:
        return ("sem GPS — arquivada, fora do mapa", 200)

    (PHOTOS_DIR / f"{pid}.jpg").write_bytes(_render(raw, DISPLAY_MAX))
    (THUMBS_DIR / f"{pid}.jpg").write_bytes(_render(raw, THUMB_MAX))
    embedded = meta_from_name(objpath)
    voice = embedded.get("voice") or "voice/censo"
    # Hash perceptual: se este upload for quase identico a uma foto ja no
    # acervo, herda o cluster dela — e a mesma foto, vista por outra voz.
    try:
        with Image.open(io.BytesIO(raw)) as _im:
            phash = _dhash(_im)
    except Exception:  # noqa: BLE001
        phash = None
    con = _db()
    cluster = pid
    if phash:
        matched, dist = _match_cluster(con, phash)
        if matched:
            cluster = matched
            print(f"[put] {pid} ~ cluster {cluster} (dist {dist})")
    item = {
        "id": pid,
        "type": "ph:Image",
        "cluster": cluster,
        "orig": PurePosixPath(objpath).name,
        "file": f"{PUBLIC_BASE}/photos/{pid}.jpg",
        "thumb": f"{PUBLIC_BASE}/thumbs/{pid}.jpg",
        "lat": meta["lat"],
        "lng": meta["lng"],
        "alt": meta["alt"],
        "datetime": meta["datetime"],
        "bearing": meta["bearing"],
        "fov": meta["fov"],
        "ride": embedded.get("ride"),
    }
    # rede de segurança: registra a voz se ela ainda não existir
    con.execute("INSERT OR IGNORE INTO voices (id, label, created) "
                "VALUES (?, ?, ?)", (voice, voice, _now()))
    con.execute("INSERT OR REPLACE INTO photos "
                "(id, datetime, voice, data, phash) VALUES (?, ?, ?, ?, ?)",
                (pid, meta["datetime"] or "", voice,
                 json.dumps(item, ensure_ascii=False), phash))
    con.commit()
    con.close()
    _rebuild_manifest()
    print(f"[put] processado {objpath} -> {pid}")
    return ("ok", 200)


@app.post("/delete-photo")
def delete_photo():
    body = request.get_json(silent=True) or {}
    pid = str(body.get("id") or "").strip()
    if not pid or not re.fullmatch(r"[A-Za-z0-9._-]+", pid):
        return jsonify(error="id invalido"), 400
    removed = 0
    for p in (PHOTOS_DIR / f"{pid}.jpg", THUMBS_DIR / f"{pid}.jpg"):
        if p.exists():
            p.unlink()
            removed += 1
    for orig in ORIGINALS.glob(f"{pid}.*"):
        orig.unlink()
        removed += 1
    con = _db()
    con.execute("DELETE FROM photos WHERE id = ?", (pid,))
    con.commit()
    con.close()
    _rebuild_manifest()
    print(f"[delete] {pid} ({removed} arquivos)")
    return jsonify(deleted=pid, removed=removed)


@app.post("/voices")
def create_voice():
    """Cria uma voz nova. Recebe {label, kind?}; devolve {id, label, kind}."""
    body = request.get_json(silent=True) or {}
    label = (body.get("label") or "").strip()
    if not label:
        return jsonify(error="label vazio"), 400
    kind = (body.get("kind") or "person").strip()
    if kind not in ("person", "model"):
        kind = "person"
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:40] or "voz"
    vid = f"voice/{slug}-{uuid.uuid4().hex[:6]}"
    con = _db()
    con.execute("INSERT INTO voices (id, label, created, kind) "
                "VALUES (?, ?, ?, ?)", (vid, label, _now(), kind))
    con.commit()
    con.close()
    _rebuild_manifest()  # para a voz nova já aparecer no manifesto
    print(f"[voices] criada {vid} ({label}, {kind})")
    return jsonify(id=vid, label=label, kind=kind)


@app.post("/voice-kind")
def set_voice_kind():
    """Marca uma voz como 'person' (animada) ou 'model' (inanimada)."""
    body = request.get_json(silent=True) or {}
    vid = (body.get("voice") or "").strip()
    kind = (body.get("kind") or "").strip()
    if kind not in ("person", "model"):
        return jsonify(error="kind invalido"), 400
    con = _db()
    row = con.execute("SELECT id FROM voices WHERE id = ?", (vid,)).fetchone()
    if not row:
        con.close()
        return jsonify(error="voz inexistente"), 404
    con.execute("UPDATE voices SET kind = ? WHERE id = ?", (kind, vid))
    con.commit()
    con.close()
    _rebuild_manifest()
    print(f"[voice-kind] {vid} -> {kind}")
    return jsonify(voice=vid, kind=kind)


@app.post("/voice-export")
def export_voice():
    """Empacota uma voz num .zip — voice.json + originais + fotos + thumbs."""
    body = request.get_json(silent=True) or {}
    vid = (body.get("voice") or "").strip()
    if not vid:
        return jsonify(error="voice vazio"), 400
    con = _db()
    row = con.execute(
        "SELECT label, kind FROM voices WHERE id = ?", (vid,)).fetchone()
    photo_rows = con.execute(
        "SELECT data FROM photos WHERE voice = ?", (vid,)).fetchall()
    con.close()
    if not row:
        return jsonify(error="voz inexistente"), 404

    items = [json.loads(r[0]) for r in photo_rows]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("voice.json", json.dumps(
            {"id": vid, "label": row[0], "kind": row[1] or "person",
             "photos": items},
            ensure_ascii=False, indent=2))
        for it in items:
            pid = it.get("id")
            if not pid:
                continue
            disp = PHOTOS_DIR / f"{pid}.jpg"
            thumb = THUMBS_DIR / f"{pid}.jpg"
            if disp.exists():
                zf.write(disp, f"photos/{pid}.jpg")
            if thumb.exists():
                zf.write(thumb, f"thumbs/{pid}.jpg")
            for orig in ORIGINALS.glob(f"{pid}.*"):
                zf.write(orig, f"originals/{orig.name}")
    fname = re.sub(r"[^A-Za-z0-9._-]+", "-", vid).strip("-") + ".zip"
    return (buf.getvalue(), 200, {
        "Content-Type": "application/zip",
        "Content-Disposition": f'attachment; filename="{fname}"',
    })


@app.post("/voice-import")
def import_voice():
    """Lê um .zip de voz e o incorpora ao acervo (idempotente por id)."""
    raw = request.get_data()
    if not raw:
        return jsonify(error="zip vazio"), 400
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        meta = json.loads(zf.read("voice.json"))
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"zip invalido: {e}"), 400
    vid = (meta.get("id") or "").strip()
    label = (meta.get("label") or vid).strip()
    kind = (meta.get("kind") or "person").strip()
    if kind not in ("person", "model"):
        kind = "person"
    if not vid:
        return jsonify(error="voice.json sem id"), 400

    # Assinatura (passo 5): o cliente verifica a voice.sig e reporta o
    # resultado por cabeçalho — guardamos a impressão digital e o veredito.
    pubkey = (request.headers.get("X-Voice-Pubkey") or "").strip()[:120] or None
    verified = 1 if request.headers.get("X-Voice-Verified") == "1" else 0
    con = _db()
    con.execute("INSERT OR REPLACE INTO voices "
                "(id, label, created, kind, pubkey, verified) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (vid, label, _now(), kind, pubkey, verified))
    n = 0
    for it in meta.get("photos") or []:
        pid = it.get("id")
        # nunca confiar nos caminhos do zip — o destino é montado do pid.
        if not pid or not re.fullmatch(r"[A-Za-z0-9._-]+", pid):
            continue
        try:
            (PHOTOS_DIR / f"{pid}.jpg").write_bytes(
                zf.read(f"photos/{pid}.jpg"))
            (THUMBS_DIR / f"{pid}.jpg").write_bytes(
                zf.read(f"thumbs/{pid}.jpg"))
        except KeyError:
            continue  # foto sem imagens no zip — pula
        for name in zf.namelist():
            if name.startswith(f"originals/{pid}.") and "/" not in name[10:]:
                (ORIGINALS / f"{pid}{PurePosixPath(name).suffix}").write_bytes(
                    zf.read(name))
                break
        # phash + cluster: calcula do jpg recem-escrito; preserva o cluster
        # do exportador se houver, senao casa contra o acervo local.
        try:
            with Image.open(PHOTOS_DIR / f"{pid}.jpg") as _im:
                phash = _dhash(_im)
        except Exception:  # noqa: BLE001
            phash = None
        if not it.get("cluster"):
            cluster = pid
            if phash:
                matched, _d = _match_cluster(con, phash, exclude=pid)
                if matched:
                    cluster = matched
            it["cluster"] = cluster
        con.execute("INSERT OR REPLACE INTO photos "
                    "(id, datetime, voice, data, phash) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (pid, it.get("datetime") or "", vid,
                     json.dumps(it, ensure_ascii=False), phash))
        n += 1
    con.commit()
    con.close()
    _rebuild_manifest()
    print(f"[voice-import] {vid} ({n} fotos)")
    return jsonify(voice=vid, label=label, imported=n)


@app.post("/voice-delete")
def delete_voice():
    """Apaga uma voz e todas as suas fotos (definitivo). Censo é protegida."""
    body = request.get_json(silent=True) or {}
    vid = (body.get("voice") or "").strip()
    if not vid:
        return jsonify(error="voice vazio"), 400
    if vid == "voice/censo":
        return jsonify(error="a voz Censo nao pode ser apagada"), 400
    con = _db()
    pids = [r[0] for r in con.execute(
        "SELECT id FROM photos WHERE voice = ?", (vid,)).fetchall()]
    con.execute("DELETE FROM photos WHERE voice = ?", (vid,))
    con.execute("DELETE FROM voices WHERE id = ?", (vid,))
    con.commit()
    con.close()
    for pid in pids:
        for p in (PHOTOS_DIR / f"{pid}.jpg", THUMBS_DIR / f"{pid}.jpg"):
            if p.exists():
                p.unlink()
        for orig in ORIGINALS.glob(f"{pid}.*"):
            orig.unlink()
    _rebuild_manifest()
    print(f"[voice-delete] {vid} ({len(pids)} fotos)")
    return jsonify(deleted=vid, photos=len(pids))


# Backfill do phash das fotos antigas — roda uma vez por processo (idempotente).
_ensure_hashes()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
