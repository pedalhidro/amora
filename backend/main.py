"""
Pedal Hidrográfico — backend Flask.

Mesmo código serve dois alvos:

  STORAGE_BACKEND=local (padrão)  — dev/local: estado mutável no filesystem
  STORAGE_BACKEND=gcs              — Cloud Run: estado num bucket GCS

Cada upload contém:
  - `ttl`        : bloco Turtle com exatamente 1 `ph:Image` (texto ou arquivo)
  - `original`   : arquivo da foto fonte (jpg/png/heic). Opcional.
  - `large`      : foto reduzida (~500 KB). Opcional.
  - `thumb`      : miniatura. Opcional.

Validação SHACL contra `web/data/shapes.ttl` (sempre do filesystem do
container/repo); variantes vão para `photos/<phash>/...` no store; triples
deduplicadas em `data/uploads.ttl` no store; manifesto em
`data/data_graphs.ttl` no store.

Rotas:
  GET  /                          serve web/index.html
  GET  /health                    "ok"
  GET  /data/uploads.ttl          do store (mutável)
  GET  /data/data_graphs.ttl      do store (mutável)
  GET  /photos/<path>             do store (redirect p/ URL pública em GCS,
                                  stream local em modo local)
  GET  /clips/<path>              idem (vídeo/áudio/thumb)
  GET  /tour_assets/<path>        idem (arte de anúncio de passeios)
  GET  /<path>                    estáticos de web/ (app.js, shapes.ttl, …)
  POST /upload-image              multipart com `ttl` + variantes
  POST /upload-video              multipart com `ttl` + audio/vídeo/thumb
  POST /upload-tour               upsert de 1 ph:Tour em tours.ttl
  POST /delete-image/<phash>      remove arquivos + triples
  POST /delete-video/<vhash>      remove clipes + triples
  POST /delete-tour/<tour_id>     remove triples do tour + assets
  POST /live-location             upsert da posição ao vivo (efêmera, em memória)
  GET  /live-locations            posições ao vivo não-expiradas
  POST /live-location/stop        remove a própria posição na hora
  POST /reload                    invalida caches in-memory

Sem auth — quem alcança o servidor é de confiança. Todas as mutações são
serializadas por um lock global (ver `serialized` / `_state_lock`) pra que
POSTs concorrentes não corrompam os catálogos TTL compartilhados.

Variáveis de ambiente:
  STORAGE_BACKEND   local | gcs                 (padrão: local)
  GCS_BUCKET        nome do bucket (modo gcs)
  PHIDRO_WEB        pasta do app                (padrão: ../../web)
  PORT              porta HTTP                  (padrão: 8000)
  MAX_UPLOAD_BYTES  teto do multipart por req   (padrão: 256 MiB)
  PUBLIC_BASE_URL   host público deste servidor (ex.: https://amora.example)
                    — usado nas IRIs absolutas que entram no catálogo
                    (schema:image do anúncio) quando o store não tem URL
                    pública própria. Sem ele, cai no host da requisição, que
                    num backend de dev grava `http://localhost:8080/…` no dado.
  STORAGE_EMULATOR_HOST   p/ rodar contra fake-gcs-server localmente
                          (https://github.com/fsouza/fake-gcs-server)
"""
import functools
import json
import math
import os
import re
import threading
import time
import unicodedata
import uuid
from pathlib import Path

from datetime import datetime, timezone
from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory

from storage import make_store_from_env

# ── Caminhos ─────────────────────────────────────────────────────────────
# WEB é o filesystem read-only do container/repo: HTML/JS/CSS/icons + os
# TTLs estáticos (shapes, ontology, tours). Resolve em duas tentativas:
#   1. Local/dev:  backend/main.py → repo_root/web ( parents[1] / "web" )
#   2. Container:  /app/main.py    → /app/web      ( parent  / "web" )
# `os.environ.get(k, default)` avalia `default` SEMPRE — não dá pra confiar
# em parents[1] cru porque dá IndexError no container (/app/main.py).
def _default_web_path():
    here = Path(__file__).resolve()
    try:
        repo_layout = here.parents[1] / "web"
        if repo_layout.is_dir():
            return repo_layout
    except IndexError:
        pass
    return here.parent / "web"

WEB = Path(os.environ.get("PHIDRO_WEB") or _default_web_path()).resolve()
DATA_DIR      = WEB / "data"
SHAPES_PATH   = DATA_DIR / "shapes.ttl"
ONTOLOGY_PATH = DATA_DIR / "ontology.ttl"

# Host público deste servidor, sem barra final. Só entra em jogo quando o
# store não expõe URL pública (modo local): é o que impede um backend de dev
# de assar `http://localhost:8080/…` numa IRI do catálogo.
PUBLIC_BASE_URL = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")

# Store = estado mutável. Em modo local, raiz = PHIDRO_WEB (layout:
# data/uploads.ttl, photos/<phash>/...); em modo gcs, raiz é o
# bucket GCS. Os "keys" são strings relativas, mesmas em ambos os modos.
STORE = make_store_from_env(WEB)

# Keys de estado mutável (usados como `STORE.read_text(...)` etc.)
# Catálogos separados: images.ttl (mídia ph:StillImage/ph:MotionImage),
# identities.ttl (pessoas schema:Person — fonte única), tours.ttl (passeios +
# associações + rotas). Antes tudo vinha em tours.ttl + uploads.ttl.
KEY_IMAGES   = "data/images.ttl"
KEY_IDENTITIES = "data/identities.ttl"
KEY_TOURS    = "data/tours.ttl"
# routes.json é pré-bakado por scripts/build-routes.py mas também é atualizado
# incrementalmente aqui (upsert/remove de 1 rota por upload/delete de tour).
# Vira estado mutável: servido bucket-first, com o arquivo bakeado no
# container/repo como seed/fallback. Em modo local o root do STORE é `web/`,
# então isto grava o MESMO `web/routes.json` que o script — sem divergência.
KEY_ROUTES   = "routes.json"
# saved_routes.json — biblioteca de rotas que o usuário salva pelo editor
# (waypoints + geometria roteada + parâmetros + modo, no MESMO formato dos
# links de compartilhamento `#st=`). Estado mutável, servido bucket-first,
# sem auth (mesma premissa de acesso confiável do resto do backend).
# Envelope: { "routes": { "<id>": {name, state, points, created, updated} } }.
KEY_SAVED_ROUTES = "saved_routes.json"

# Credenciais do RideWithGPS pra buscar a geometria das rotas (privadas/
# unlisted exigem auth; públicas funcionam sem). Lidas de `os.environ` por
# `rwgps.decorate_rwgps`; carregamos o `.env` do repo best-effort pra que o
# dev local pegue as mesmas chaves que o build-routes.py usa.
try:  # python-dotenv é dep do build-routes; pode faltar no container slim.
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(WEB.parent / ".env")
except Exception:  # noqa: BLE001
    pass

PH_NS  = "https://id.pedalhidrografi.co/terms#"
PHD_NS = "https://pedalhidrografi.co/data/"
SCHEMA_NS = "https://schema.org/"
# Namespace de IDENTIDADE de pessoas — neutro (não acoplado ao app) e resolvível:
# https://id.pedalhidrografi.co/pessoas/<slug8> (slug opaco aleatório). A página
# humana é servida pelo amora em /pessoas/<slug> (schema:mainEntityOfPage).
PES_NS = "https://id.pedalhidrografi.co/pessoas/"
# Namespace de LISTAS/álbuns (schema:Collection) — resolvível e fora do catálogo
# de mídia: as Collections vivem em lists.ttl (não mais inline em images.ttl).
# IRI: https://id.pedalhidrografi.co/listas/<slug>.
LST_NS = "https://id.pedalhidrografi.co/listas/"
KEY_LISTS = "data/lists.ttl"
# Mídia (foto/vídeo) — content-addressed pelo hash; o host mudou pra resolvível,
# mas o discriminador image_/video_ (e o hash como identidade) fica no local name
# (blobs, dedup e delete seguem intactos — só o prefixo do IRI muda).
# IRI: https://id.pedalhidrografi.co/midia/image_<phash16> | .../video_<vhash16>.
MED_NS = "https://id.pedalhidrografi.co/midia/"
# Atividade de envio (ph:Upload) — provenance server-side. IRI: .../envio/<ts>.
ENV_NS = "https://id.pedalhidrografi.co/envio/"
# Passeio (ph:Tour) — id agora é um slug aleatório Crockford (não mais o id
# numérico legado). IRI: https://id.pedalhidrografi.co/passeio/<slug8>. O "tour_id"
# no código passa a ser esse slug (localname após o prefixo).
PAS_NS = "https://id.pedalhidrografi.co/passeio/"
# Série de eventos (schema:EventSeries). IRI: .../serie/<ES> (PH/BT/BP/S/SESC).
SER_NS = "https://id.pedalhidrografi.co/serie/"


def _intensity_for(kj):
    """Classificação de intensidade derivada do valor em kJ por faixas fixas.
    Antes vivia em ph:intensityClassification num nó qudt:QuantityValue; agora
    a energia é um literal e a intensidade é derivada na leitura."""
    if kj is None:
        return None
    if kj < 150:
        return "De boa"
    if kj < 300:
        return "Ok"
    if kj < 500:
        return "Endorfinado"
    if kj < 1000:
        return "Frito"
    return "Insano"

# Limite por requisição. Um upload de vídeo manda 360p + 720p (webm) +
# áudio + thumb num único multipart, então o teto precisa acomodar a soma.
# Override via env pra hosts com clipes mais longos.
MAX_PER_UPLOAD = int(os.environ.get("MAX_UPLOAD_BYTES") or (256 * 1024 * 1024))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_PER_UPLOAD

# Compressão transparente (gzip/brotli) — routes.json sai de ~2 MB pra
# ~210 KB e app.js de ~280 KB pra ~90 KB. Import best-effort (mesmo
# espírito do load do .env): um host que ainda não rodou pip install
# continua servindo, só que sem compressão.
app.config["COMPRESS_MIMETYPES"] = [
    "text/html", "text/css", "text/plain",
    "text/javascript", "application/javascript",
    "application/json", "text/turtle", "image/svg+xml",
    "application/manifest+json", "application/gpx+xml",
    "application/rss+xml", "application/xml", "text/xml",
]
# send_from_directory devolve resposta *streamed* (file wrapper) e o
# flask-compress pula essas por padrão — sem isto app.js/style.css sairiam
# crus. Só afeta os mimetypes de texto acima; mídia (mp4/webm/jpg) segue
# fora da lista e mantém range requests intactos.
app.config["COMPRESS_STREAMS"] = True
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:                                   # pragma: no cover
    print("[main] flask-compress ausente — servindo sem compressão "
          "(pip install -r backend/requirements.txt)")


def _conditional(resp):
    """ETag + suporte a If-None-Match nas respostas construídas de string
    (routes.json e /data/*.ttl). Elas são `Cache-Control: no-cache`, ou
    seja, o browser revalida a cada visita — sem ETag a revalidação baixa
    o corpo inteiro de novo; com ela, vira um 304 vazio. (Os estáticos via
    send_from_directory já ganham ETag/conditional do próprio Flask.)"""
    resp.add_etag()
    return resp.make_conditional(request)

# Todas as mutações fazem read-modify-write num único catálogo TTL
# compartilhado (uploads.ttl / tours.ttl / data_graphs.ttl) sem CAS. Sem
# serialização, dois POSTs concorrentes (o servidor Flask é threaded, e o
# form de upload manda os cards em paralelo) intercalam: o segundo writer
# sobrescreve os triples do primeiro (lost update) ou um leitor pega o
# arquivo truncado no meio da escrita. Um lock global serializa as mutações;
# combinado com a escrita atômica do LocalStateStore, o catálogo fica íntegro.
# (Em Cloud Run multi-instância isto cobre só uma instância — ali ainda
# faltaria precondição de generation no GCS; ver storage.py.)
_state_lock = threading.RLock()
# Lock DEDICADO à validação SHACL. pyshacl (via o parser SPARQL do rdflib/
# pyparsing, disparado pelo sh:sparql das shapes) NÃO é thread-safe: duas
# validações concorrentes corrompem o estado global do parser. Além disso é
# CPU-bound (o GIL serializa de qualquer jeito). Então validação é serializada
# à parte — mas SEM o _state_lock, pra não bloquear o RMW do catálogo (rápido)
# atrás de uma validação lenta (~1,2 s). Ver upload_image.
_validate_lock = threading.Lock()


def serialized(fn):
    """Serializa o handler inteiro sob `_state_lock` (validação + escrita)."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with _state_lock:
            return fn(*args, **kwargs)
    return wrapper


# ── Posições ao vivo (efêmeras, em memória) ──────────────────────────────
# Compartilhamento de localização ao vivo: cada participante faz POST da sua
# posição a cada poucos segundos; todos leem via GET. NADA disto é persistido
# (não toca TTL/disco/bucket) — é um dict em memória no único worker gunicorn,
# com TTL curto. Opt-in, pseudônimo, expira sozinho. Como o estado é
# per-process, depende de --workers 1 / 1 instância (mesma premissa do
# _state_lock); em multi-instância as posições se fragmentariam. Tem lock
# próprio (leve) em vez do _state_lock pra não competir com os uploads.
_live_positions = {}            # token -> {name, lat, lng, ts, accuracy?, heading?, trail}
_live_positions_lock = threading.Lock()
LIVE_TRAIL_S = 3 * 3600         # janela de visibilidade/rastro: 3h
LIVE_TRAIL_MIN_GAP_S = 8        # thinning: tempo mínimo entre pontos guardados (s)
LIVE_TRAIL_MIN_MOVE_M = 12      # thinning: distância mínima entre pontos guardados (m)
LIVE_TRAIL_MAX_POINTS = 500     # teto de pontos de rastro por pessoa (memória)
LIVE_MAX_PEERS = 500            # teto defensivo de participantes

# CORS restrito aos endpoints /live-* — o app rodando dentro do shell nativo
# (Capacitor: capacitor://localhost / https://localhost) bate aqui cross-origin
# se empacotar os assets. NÃO abre CORS nos uploads/CRUD: esses seguem
# same-origin/confiança local. No browser (same-origin) é inócuo.
_LIVE_CORS_ORIGINS = {"capacitor://localhost", "https://localhost",
                      "ionic://localhost", "http://localhost"}


def _prune_live(now):
    """Remove tokens cujo último ponto saiu da janela de retenção e poda os
    pontos de rastro expirados dos que sobram. A janela é por token (`ttl`, em
    segundos, escolhido por quem compartilha; default LIVE_TRAIL_S). Chamar já
    sob _live_positions_lock."""
    dead = []
    for t, p in _live_positions.items():
        cutoff = now - (p.get("ttl") or LIVE_TRAIL_S)
        if p["ts"] <= cutoff:
            dead.append(t)
            continue
        tr = p.get("trail")
        if tr and tr[0][2] <= cutoff:
            p["trail"] = [pt for pt in tr if pt[2] > cutoff]
    for t in dead:
        del _live_positions[t]


def _valid_live_token(t):
    """Token pseudônimo do cliente (crypto.randomUUID() ou hex). Aceita
    hex + hífens, 1–64 chars — não confia em nada do corpo além disto."""
    return isinstance(t, str) and 1 <= len(t) <= 64 and all(
        c in "0123456789abcdefABCDEF-" for c in t)


@app.after_request
def _live_cors(resp):
    if request.path.startswith("/live-location"):  # cobre singular, /stop e plural
        # A resposta varia por origem (ACAO só p/ origens da allowlist), então
        # Origin SEMPRE entra no Vary — inclusive p/ origens fora da lista, senão
        # um cache compartilhado poderia servir a resposta de uma origem a outra.
        # vary.add NÃO sobrescreve um Vary já presente (ex.: Accept-Encoding do
        # flask-compress), ao contrário de `headers["Vary"] = ...`.
        resp.vary.add("Origin")
        origin = request.headers.get("Origin")
        if origin in _LIVE_CORS_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/live-location", methods=["POST", "OPTIONS"])
def post_live_location():
    """Atualiza a posição ao vivo de um participante e acumula o rastro (3h).
    Efêmero, sem o lock de estado pesado. Body JSON:
    {id, name?, lat, lng, accuracy?, heading?}."""
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    token = str(data.get("id") or "").strip()
    if not _valid_live_token(token):
        return jsonify(error="id inválido"), 400
    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (TypeError, ValueError):
        return jsonify(error="lat/lng inválidos"), 400
    if not (math.isfinite(lat) and math.isfinite(lng)) or \
            not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify(error="lat/lng fora de faixa"), 400
    now = time.time()
    head = {"name": str(data.get("name") or "").strip()[:40],
            "lat": lat, "lng": lng, "ts": now}
    for k in ("accuracy", "heading"):
        try:
            v = data.get(k)
            if v is not None and math.isfinite(float(v)):
                head[k] = float(v)
        except (TypeError, ValueError):
            pass
    # Retenção escolhida por quem compartilha (segundos): por quanto tempo o
    # servidor guarda o rastro deste token. Default 3h, teto defensivo de 24h.
    ttl = LIVE_TRAIL_S
    try:
        v = data.get("ttl")
        if v is not None and math.isfinite(float(v)):
            ttl = int(max(60, min(24 * 3600, float(v))))
    except (TypeError, ValueError):
        pass
    head["ttl"] = ttl
    from rwgps import haversine_meters   # cacheado em sys.modules; boot barato
    with _live_positions_lock:
        _prune_live(now)
        prev = _live_positions.get(token)
        if prev is None and len(_live_positions) >= LIVE_MAX_PEERS:
            return jsonify(error="muitos participantes ao vivo"), 503
        trail = prev["trail"] if prev else []
        # Thinning: só guarda um ponto novo se passou tempo OU distância
        # suficiente desde o último — limita memória e suaviza a linha. O
        # `head` sempre reflete o último fix (marcador preciso entre pontos).
        if not trail:
            keep = True
        else:
            llat, llng, lts = trail[-1][0], trail[-1][1], trail[-1][2]
            keep = (now - lts >= LIVE_TRAIL_MIN_GAP_S
                    or haversine_meters(llat, llng, lat, lng) >= LIVE_TRAIL_MIN_MOVE_M)
        if keep:
            # Ponto = [lat, lng, ts, accuracy?]. A precisão por ponto alimenta
            # a faixa de incerteza desenhada ao longo do rastro no cliente.
            trail.append([lat, lng, now, head.get("accuracy")])
            if len(trail) > LIVE_TRAIL_MAX_POINTS:
                del trail[:len(trail) - LIVE_TRAIL_MAX_POINTS]
        head["trail"] = trail
        _live_positions[token] = head
    return jsonify(ok=True)


@app.get("/live-locations")
def get_live_locations():
    """Posições ao vivo (janela de 3h) + rastro de cada pessoa. Muda toda hora,
    então SEM ETag/_conditional e com Cache-Control: no-store."""
    now = time.time()
    out = []
    with _live_positions_lock:
        _prune_live(now)
        for t, p in _live_positions.items():
            item = {"id": t, "name": p["name"], "lat": p["lat"], "lng": p["lng"],
                    "ts": p["ts"], "age": round(now - p["ts"], 1),
                    "trail": [[round(pt[0], 5), round(pt[1], 5),
                               (round(pt[3], 1) if len(pt) > 3 and pt[3] is not None else None),
                               round(now - pt[2])]   # idade (s) do ponto, p/ tooltip
                              for pt in p["trail"]]}
            if "accuracy" in p:
                item["accuracy"] = p["accuracy"]
            if "heading" in p:
                item["heading"] = p["heading"]
            out.append(item)
    return Response(json.dumps({"positions": out}, ensure_ascii=False),
                    mimetype="application/json",
                    headers={"Cache-Control": "no-store"})


@app.route("/live-location/stop", methods=["POST", "OPTIONS"])
def post_live_location_stop():
    """Apaga token + rastro na hora. Não é mais chamado automaticamente (o
    rastro fica até expirar da janela de 3h) — fica disponível pra uma ação
    explícita futura de "apagar meu rastro agora"."""
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    with _live_positions_lock:   # mesma disciplina dos outros acessos ao dict
        _live_positions.pop(str(data.get("id") or "").strip(), None)
    return jsonify(ok=True)


# ── Validador SHACL (lazy) ───────────────────────────────────────────────
# rdflib + pyshacl são pesados: carregamos só na primeira validação para
# manter o boot do servidor barato.
_validator = None


def _load_validator():
    global _validator
    if _validator is not None:
        return _validator
    import pyshacl
    from rdflib import Graph
    # Lê via _load_dump_text — bucket-first (permite override sem redeploy),
    # com fallback pro arquivo baked-in no container. Mesma semântica que
    # o catálogo: bucket é a fonte vigente, container é o seed inicial.
    shapes_text = _load_dump_text("shapes.ttl")
    ont_text    = _load_dump_text("ontology.ttl")
    if not shapes_text:
        raise RuntimeError("shapes.ttl ausente em bucket e container")
    if not ont_text:
        raise RuntimeError("ontology.ttl ausente em bucket e container")
    shapes = Graph().parse(data=shapes_text, format="turtle")
    ont    = Graph().parse(data=ont_text, format="turtle")
    _validator = {
        "pyshacl": pyshacl,
        "Graph":   Graph,
        "shapes":  shapes,
        "ont":     ont,
    }
    print(f"[shacl] carregados shapes={len(shapes)} triples, "
          f"ontology={len(ont)} triples")
    return _validator


# Mundo (TTLs listadas no manifesto), construído sob demanda e invalidado
# após cada upload/delete. O validador o mescla com o TTL recebido para
# que `sh:class ph:Tour` etc. enxerguem o universo todo (passeios,
# pessoas, uploads anteriores).
_catalog_cache = None
_catalog_types_cache = None


def _invalidate_catalog():
    global _catalog_cache, _catalog_types_cache
    _catalog_cache = None
    _catalog_types_cache = None


def _load_dump_text(fname):
    """Resolve um dump TTL — bucket primeiro, container como fallback.

    Bucket-first permite override de shapes/ontology/tours sem redeploy do
    container: basta `gcloud storage cp` pro bucket. O container traz uma
    cópia "seed" usada quando o bucket ainda não tem o arquivo (boot inicial,
    rollback, dev local sem GCS).
    """
    text = STORE.read_text(f"data/{fname}")
    if text:
        return text
    static_path = DATA_DIR / fname
    if static_path.exists() and static_path.stat().st_size > 0:
        return static_path.read_text()
    return None


# Dumps que compõem o universo de validação. Era descoberto seguindo os
# void:dataDump do manifesto (data_graphs.ttl); hoje a lista é fixa —
# tours.ttl traz tours/pessoas/séries (referenciados por sh:class) e
# uploads.ttl traz imagens + vídeos. shapes/ontology entram à parte no
# validador. O manifesto vira só um shim estático servido pro frontend.
CATALOG_DUMPS = ("tours.ttl", "images.ttl", "identities.ttl", "lists.ttl")


def _load_catalog():
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    v = _load_validator()
    catalog = v["Graph"]()
    loaded = 0
    for fname in CATALOG_DUMPS:
        text = _load_dump_text(fname)
        if not text:
            continue
        try:
            catalog.parse(data=text, format="turtle")
            loaded += 1
        except Exception as e:  # noqa: BLE001
            print(f"[validator] não consegui parsear {fname}: {e}")
    _catalog_cache = catalog
    print(f"[validator] catálogo: {loaded} arquivo(s), {len(catalog)} triples")
    return catalog


def _load_catalog_types():
    """Subconjunto do catálogo com SÓ as triples `rdf:type` — o suficiente pras
    checagens `sh:class` das shapes (autor→schema:Person, lista→schema:Collection,
    ph:capturedDuring→ph:Tour, …). Validar contra este subconjunto em vez do
    catálogo inteiro encolhe o grafo de ~9500 p/ ~2100 triples (~25% menos tempo
    de SHACL por upload) SEM mudar o veredito do sujeito em curso: as shapes só
    consultam o catálogo por `sh:class`, e o único `sh:sparql` é escopado a
    passeios/séries (focus nodes filtrados por `own_subjects`). Cacheado junto do
    catálogo (invalidado no mesmo `_invalidate_catalog`)."""
    global _catalog_types_cache
    if _catalog_types_cache is not None:
        return _catalog_types_cache
    from rdflib import RDF
    catalog = _load_catalog()
    types = _load_validator()["Graph"]()
    for triple in catalog.triples((None, RDF.type, None)):
        types.add(triple)
    _catalog_types_cache = types
    return types


def validate_image_ttl(ttl_text):
    """Verifica que o TTL contém exatamente 1 ph:Image e satisfaz as shapes.
    Retorna (ok, phash, errors). `errors` traz só violations (warnings passam)
    cujo focusNode está no TTL recebido — ruído do catálogo (passeios velhos
    com warnings, etc.) não bloqueia o upload."""
    v = _load_validator()
    from rdflib import URIRef, Namespace
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    images = list(data.subjects(RDFT, URIRef(PH_NS + "StillImage")))
    if len(images) != 1:
        return False, None, [
            f"TTL deve conter exatamente 1 ph:Image (achou {len(images)})"
        ]
    image_iri = str(images[0])
    # IRI de mídia é opaco: med:<hash> (sem discriminador image_/video_ — o tipo
    # vem da CLASSE). phash = pHash de 64 bits → exatamente 16 hex (evita cunhar
    # diretórios photos/<phash>/ de tamanho arbitrário).
    if not image_iri.startswith(MED_NS):
        return False, None, [
            f"IRI da Image deve começar com med: (atual: {image_iri})"
        ]
    phash = image_iri[len(MED_NS):]
    if len(phash) != 16 or not all(c in "0123456789abcdef" for c in phash.lower()):
        return False, phash, [f"phash inválido na IRI (esperado 16 hex): {phash}"]

    img_uri = URIRef(image_iri)
    catalog = _load_catalog()
    # Guarda de colisão CROSS-TYPE: sem o discriminador, um phash igual a um
    # vhash existente viraria o MESMO IRI. Rejeita antes de sobrescrever o vídeo.
    if (img_uri, RDFT, URIRef(PH_NS + "MotionImage")) in catalog:
        return False, phash, [
            f"colisão: med:{phash} já existe como VÍDEO (ph:MotionImage) — "
            f"phash colidiu com um vhash. Não dá pra reusar o IRI."
        ]
    # Mescla data + ontology + catálogo, MAS exclui triples do catálogo cujo
    # subject é a imagem em curso (ou bnodes alcançáveis a partir dela). Sem
    # isso, re-upload da mesma foto sobrepõe os triples antigos aos novos, e
    # SHACL flagra cardinalidade > 1 em `dcterms:date` etc.
    # Exclui o próprio sujeito + seus nós derivados (hash, locationCreated).
    exclude = {img_uri} | _derived_subjects(catalog, img_uri)
    # Universo de validação: data + ontology + SÓ as triples rdf:type do catálogo
    # (não o catálogo inteiro) — o bastante pras checagens sh:class das shapes.
    # A colisão cross-type e o `exclude` acima seguem calculados sobre o catálogo
    # COMPLETO (comportamento de dedup/re-upload inalterado). Ver _load_catalog_types.
    merged = data + v["ont"]
    for s, p, o in _load_catalog_types():
        if s not in exclude:
            merged.add((s, p, o))
    with _validate_lock:   # pyshacl não é thread-safe (parser SPARQL) — ver _validate_lock
        conforms, results_graph, _txt = v["pyshacl"].validate(
            merged, shacl_graph=v["shapes"], inference="rdfs", advanced=True)
    if conforms:
        return True, phash, []

    # Reporta apenas violations cujo focusNode é um sujeito do TTL recebido.
    # Catálogo (tours.ttl) pode ter warnings legítimos; não são problema do
    # upload em curso.
    own_subjects = set(data.subjects())
    SH = Namespace("http://www.w3.org/ns/shacl#")
    errors = []
    for r in results_graph.subjects(SH.resultSeverity, SH.Violation):
        focus = next(results_graph.objects(r, SH.focusNode), None)
        if focus is None or focus in own_subjects:
            msg = next(results_graph.objects(r, SH.resultMessage), None)
            errors.append(str(msg) if msg else "(sem mensagem)")
    if not errors:
        return True, phash, []
    return False, phash, errors


def _upload_filename():
    """Timestamp único (microssegundos) — `upload_20260526T012345-678901Z.ttl`."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-%f")
    return f"upload_{ts}Z.ttl"


def _ttl_escape(s):
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ── Mapa de IRIs de passeio (migração P4) ────────────────────────────────
# tour-iri-map.json: id numérico legado ↔ slug novo. Só os 109 passeios da
# migração precisam dele — passeios novos já nascem com slug e não têm id
# antigo. Usado pra: (a) alias 303 de deep links ?tour=<id-numérico> antigos,
# (b) guids estáveis no feed (emite o IRI antigo pra não churnar o RSS).
_TOUR_MAP_PATH = WEB / "data" / "tour-iri-map.json"
_tour_map_cache = None


def _tour_iri_map():
    """{'byOldId': {<numid>: <slug>}, 'byNewSlug': {<slug>: <numid>}}.
    Estático (baked no container); cache em processo. Vazio se ausente."""
    global _tour_map_cache
    if _tour_map_cache is None:
        try:
            _tour_map_cache = json.loads(_TOUR_MAP_PATH.read_text())
        except Exception:  # noqa: BLE001 — sem mapa = degrada sem alias/guid antigo
            _tour_map_cache = {"byOldId": {}, "byNewSlug": {}}
    return _tour_map_cache


def _legacy_tour_iri(slug):
    """IRI antigo (phd:tour_<numid>) de um passeio migrado, ou None. Pra guid
    estável do feed — o IRI antigo é opaco/permanente, o slug novo churna."""
    numid = _tour_iri_map().get("byNewSlug", {}).get(slug)
    return (PHD_NS + "tour_" + numid) if numid else None


def _build_audit_ttl(upload_local, phash):
    """Bloco PROV server-side anexado ao TTL do upload. A atividade de envio vira
    env:<ts> (resolvível) e aponta pra mídia em med:<phash>."""
    ts = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    ts = ts.replace("+00:00", "Z")
    # env:<ts> — descarta o prefixo `upload_` do local (o path `/envio/` já diz).
    env_local = upload_local[len("upload_"):] if upload_local.startswith("upload_") else upload_local
    return (
        "\n# Registro de envio (provenance) — adicionado server-side.\n"
        "@prefix prov: <http://www.w3.org/ns/prov#> .\n"
        "@prefix ph:   <https://id.pedalhidrografi.co/terms#> .\n"
        "@prefix med:  <https://id.pedalhidrografi.co/midia/> .\n"
        "@prefix env:  <https://id.pedalhidrografi.co/envio/> .\n"
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .\n"
        "\n"
        f"env:{env_local} a ph:Upload ;\n"
        f"    prov:startedAtTime \"{ts}\"^^xsd:dateTime ;\n"
        f"    prov:generated med:{phash} .\n"
    )


# Manifesto VoID servido em /data/data_graphs.ttl. O frontend (e os agentes
# via llms.txt) seguem os void:dataDump pra achar os dumps. Antes era um Graph
# mutado a cada upload (registrava uploads.ttl on-the-fly); hoje a lista é fixa
# (= CATALOG_DUMPS) e isto é só um shim estático de compatibilidade pros
# clientes/SWs em cache que ainda buscam o manifesto.
DATA_GRAPHS_SHIM = """\
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix void:    <http://rdfs.org/ns/void#> .

<> a void:Dataset ;
    dcterms:title "Pedal Hidrográfico — grafos de dados"@pt ;
    void:dataDump <tours.ttl>, <images.ttl>, <identities.ttl>, <lists.ttl> .
"""


def _derived_subjects(graph, root):
    """Sujeitos `<root>_*` — os nós que antes eram bnodes aninhados (geo, hash,
    energy, measured, route) e hoje são IRIs derivadas com o IRI do pai como
    prefixo. O `_` final evita casar IRIs irmãs (phd:tour_1 não pega
    phd:tour_10). Substitui o antigo walk de bnodes alcançáveis."""
    from rdflib import URIRef
    prefix = str(root) + "_"
    return {s for s in set(graph.subjects())
            if isinstance(s, URIRef) and str(s).startswith(prefix)}


def _purge_subject(graph, root):
    """Apaga as triples de `root` e dos seus nós derivados `<root>_*`, mais a
    closure de 1 nível de objetos bnode (geo/hash legados, pré-migração pra
    IRI derivada — ver _resource_slice_ttl, mesmo padrão). Não recursa além
    de 1 nível: nós aninhados são sempre IRIs mintadas, não cadeias de bnode.
    Retorna nº de triples removidas."""
    from rdflib import BNode
    removed = 0
    for subj in {root} | _derived_subjects(graph, root):
        for s, p, o in list(graph.triples((subj, None, None))):
            graph.remove((s, p, o))
            removed += 1
            if isinstance(o, BNode):
                for bs, bp, bo in list(graph.triples((o, None, None))):
                    graph.remove((bs, bp, bo))
                    removed += 1
    return removed


# ── Dereferência (Linked Data) — content negotiation + slice de recurso ──────
# id.pedalhidrografi.co/<tipo>/<slug> é o IRI das coisas; a Cloudflare faz um
# 303 path-preserving pra amora.pedalhidrografi.co/<tipo>/<slug>, onde estes
# handlers respondem: Accept: text/turtle → as triples do recurso; senão a
# página humana (SSR/SPA). Padrão httpRange-14: o IRI nunca devolve 200, o
# documento sobre ele sim.
_RDF_MIMES = ("text/turtle", "application/x-turtle", "application/ld+json",
              "application/rdf+xml", "application/n-triples")


def _wants_turtle(request):
    """True quando o cliente prefere RDF/turtle a HTML. `?format=ttl|turtle`
    força; senão negocia pelo Accept (curl/browser com */* ou text/html → HTML)."""
    fmt = (request.args.get("format") or "").lower()
    if fmt in ("ttl", "turtle", "rdf"):
        return True
    if fmt in ("html", "web"):
        return False
    best = request.accept_mimetypes.best_match(["text/html"] + list(_RDF_MIMES))
    return best is not None and best != "text/html"


def _resource_slice_ttl(subject_iri, *dump_keys):
    """Turtle descrevendo `subject_iri`: suas triples + os nós derivados
    `<iri>_*` (geo/hash/route) + a closure de 1 nível dos objetos bnode (geo/hash
    legados). Referências a IRIs nomeadas (pessoas, passeios, edições) ficam como
    referência — cada uma dereferencia por conta própria. Lê os dumps dados
    (bucket-first). Devolve turtle str, ou None se o sujeito não tem triples."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef, BNode
    cat = Graph()
    for k in dump_keys:
        text = _load_dump_text(k)
        if text:
            cat.parse(data=text, format="turtle")
    subj = URIRef(subject_iri)
    roots = {subj} | _derived_subjects(cat, subj)
    out = Graph()
    for pfx, ns in (("ph", PH_NS), ("phd", PHD_NS), ("pes", PES_NS),
                    ("schema", SCHEMA_NS), ("dcterms", "http://purl.org/dc/terms/"),
                    ("prov", "http://www.w3.org/ns/prov#"), ("pav", "http://purl.org/pav/"),
                    ("nfo", "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#"),
                    ("exif", "http://www.w3.org/2003/12/exif/ns#"),
                    ("rdfs", "http://www.w3.org/2000/01/rdf-schema#")):
        out.bind(pfx, ns)
    seen = set()
    for r in roots:
        for s, p, o in cat.triples((r, None, None)):
            out.add((s, p, o))
            if isinstance(o, BNode) and o not in seen:   # closure só p/ bnodes
                seen.add(o)
                for t in cat.triples((o, None, None)):
                    out.add(t)
    if len(out) == 0:
        return None
    return out.serialize(format="turtle")


def _route_new_persons(graph):
    """Move definições de schema:Person do `graph` (fragmento de tour/mídia sendo
    persistido) pra identities.ttl (upsert), deixando o `graph` sem pessoas.

    Pós-split, pessoas vivem SÓ em identities.ttl; tours.ttl/images.ttl apenas as
    referenciam. Quando um cadastro de passeio ou upload de mídia declara uma
    pessoa NOVA inline (Tom Select create-on-the-fly), esta função a desvia pro
    arquivo certo — senão a pessoa vazaria de volta pro catálogo de mídia/passeio
    e recriaria o problema de definição duplicada. Referências (posição de
    objeto) não são tocadas; só definições (sujeito `a schema:Person`)."""
    from rdflib import URIRef
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    person_cls = (URIRef(SCHEMA_NS + "Person"), URIRef("http://schema.org/Person"))
    persons = set()
    for c in person_cls:
        persons |= set(graph.subjects(RDFT, c))
    if not persons:
        return
    idg = _load_validator()["Graph"]()
    existing = _load_dump_text("identities.ttl")
    if existing:
        idg.parse(data=existing, format="turtle")
    for p in persons:
        _purge_subject(idg, p)   # upsert: limpa def anterior (pessoas não têm derivados)
        for t in list(graph.triples((p, None, None))):
            idg.add(t)
            graph.remove(t)
    STORE.write_text(KEY_IDENTITIES, idg.serialize(format="turtle"))


def _route_new_collections(graph):
    """Move definições de schema:Collection (listas/álbuns) do `graph` pra
    lists.ttl (upsert), deixando o `graph` de mídia sem Collections.

    Pós-split as listas vivem SÓ em lists.ttl; images.ttl só as referencia via
    schema:isPartOf. Quando um upload/edição de mídia declara uma lista NOVA
    inline (create-on-the-fly na galeria/form), esta função a desvia pro arquivo
    certo — mesma mecânica de [_route_new_persons]. Só definições (sujeito
    `a schema:Collection`) são movidas; referências (isPartOf) ficam."""
    from rdflib import URIRef
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    coll_cls = (URIRef(SCHEMA_NS + "Collection"), URIRef("http://schema.org/Collection"))
    colls = set()
    for c in coll_cls:
        colls |= set(graph.subjects(RDFT, c))
    if not colls:
        return
    lg = _load_validator()["Graph"]()
    existing = _load_dump_text("lists.ttl")
    if existing:
        lg.parse(data=existing, format="turtle")
    for li in colls:
        _purge_subject(lg, li)   # upsert: substitui def anterior (listas não têm derivados)
        for t in list(graph.triples((li, None, None))):
            lg.add(t)
            graph.remove(t)
    STORE.write_text(KEY_LISTS, lg.serialize(format="turtle"))


PROV_GEN_URI = "http://www.w3.org/ns/prov#generated"


def upsert_image_in_uploads(image_ttl, phash, audit_ttl):
    """Mescla os blocos da imagem + da activity no único `uploads.ttl`,
    sobrescrevendo qualquer dado prévio para essa mesma imagem."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    image_iri = URIRef(MED_NS + phash)
    catalog = Graph()
    existing = STORE.read_text(KEY_IMAGES)
    if existing:
        catalog.parse(data=existing, format="turtle")
    # 1) Tira da imagem (+ bnodes de hash/loc).
    _purge_subject(catalog, image_iri)
    # 2) Tira qualquer ph:Upload activity que tenha gerado essa imagem.
    for s in list(catalog.subjects(URIRef(PROV_GEN_URI), image_iri)):
        _purge_subject(catalog, s)
    # 3) Mescla os novos blocos (imagem + nova activity).
    catalog += Graph().parse(data=image_ttl + audit_ttl, format="turtle")
    # 4) Desvia pessoas novas (autora criada on-the-fly) pra identities.ttl
    #    e listas novas inline pra lists.ttl.
    _route_new_persons(catalog)
    _route_new_collections(catalog)
    STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))


def remove_image_from_uploads(phash):
    """Remove triples da imagem + da sua activity de envio. Retorna nº de triples."""
    existing = STORE.read_text(KEY_IMAGES)
    if not existing:
        return 0
    v = _load_validator()
    from rdflib import URIRef
    image_iri = URIRef(MED_NS + phash)
    catalog = v["Graph"]()
    catalog.parse(data=existing, format="turtle")
    n = _purge_subject(catalog, image_iri)
    for s in list(catalog.subjects(URIRef(PROV_GEN_URI), image_iri)):
        n += _purge_subject(catalog, s)
    STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))
    return n


# ── Media metadata patch (edição, sem blobs) ─────────────────────────────
# Análogo ao synthesize_tour_patch, mas pra med:<hash> (foto ou vídeo) em
# uploads.ttl. Usado por /update-image e /update-video (edição de metadados +
# listas pelo popup e pelo modo de edição do form) — NÃO toca nos blobs nem
# regenera a activity ph:Upload (sujeito à parte, preservado).
def synthesize_media_patch(media_iri, patch_ttl, remove_preds):
    """Transforma um patch por-predicado (só os predicados afirmados no patch
    sobre a mídia + os listados em `remove_preds`) no documento full-replace
    equivalente. O estado atual da mídia em uploads.ttl é copiado verbatim; os
    predicados a substituir (e a closure `<iri>_*` dos objetos derivados
    descartados) são removidos; o patch inteiro é somado (inclusive sujeitos
    auxiliares novos, ex.: schema:Collection inline). SHACL valida o ESTADO
    FINAL. Retorna o TTL sintetizado."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    media_uri = URIRef(media_iri)
    patch = Graph().parse(data=patch_ttl, format="turtle")
    preds_to_replace = set(patch.predicates(media_uri)) | set(remove_preds)

    result = Graph()
    existing = STORE.read_text(KEY_IMAGES)
    if existing:
        from rdflib import BNode
        catalog = Graph().parse(data=existing, format="turtle")
        for subj in {media_uri} | _derived_subjects(catalog, media_uri):
            for s, p, o in catalog.triples((subj, None, None)):
                result.add((s, p, o))
                # Copia também a closure de 1 nível dos objetos bnode (geo/hash
                # antigos ainda são bnodes na maioria das mídias). Sem isso, um
                # predicado NÃO substituído (ex.: schema:locationCreated) ficaria
                # apontando pra um bnode sem triples → SHACL sh:class falharia.
                if isinstance(o, BNode):
                    for s2, p2, o2 in catalog.triples((o, None, None)):
                        result.add((s2, p2, o2))

    for p in preds_to_replace:
        for o in list(result.objects(media_uri, p)):
            result.remove((media_uri, p, o))
            if isinstance(o, URIRef) and str(o).startswith(str(media_uri) + "_"):
                _purge_subject(result, o)
    for triple in patch:
        result.add(triple)
    return result.serialize(format="turtle")


def upsert_media_node(media_iri, node_ttl):
    """Substitui as triples da mídia (sujeito + nós derivados) em images.ttl
    pelo node_ttl, PRESERVANDO os blobs e a activity ph:Upload (sujeito à parte).
    node_ttl pode trazer schema:Collection novos inline — desviados pra lists.ttl
    por _route_new_collections, nunca persistidos em images.ttl."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    media_uri = URIRef(media_iri)
    catalog = Graph()
    existing = STORE.read_text(KEY_IMAGES)
    if existing:
        catalog.parse(data=existing, format="turtle")
    _purge_subject(catalog, media_uri)
    catalog += Graph().parse(data=node_ttl, format="turtle")
    _route_new_collections(catalog)   # listas novas inline → lists.ttl
    STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))


# ── Tour upserts ─────────────────────────────────────────────────────────
# Mesma mecânica de validação/merge das imagens, mas pra pas:<slug>
# e gravando em tours.ttl em vez de uploads.ttl. Pra dar suporte ao form
# upload_tour.html, que cria/edita 1 tour por vez.

def _single_tour_id(data):
    """Acha exatamente 1 ph:Tour no graph `data` e devolve (tour_id, errors).

    `tour_id` é o sufixo após `pas:` (o slug do passeio). Compartilhado entre a
    validação e a síntese de patch (que precisa do ID antes de montar o resultado).
    """
    from rdflib import URIRef
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    tours = list(data.subjects(RDFT, URIRef(PH_NS + "Tour")))
    if len(tours) != 1:
        return None, [
            f"TTL deve conter exatamente 1 ph:Tour (achou {len(tours)})"
        ]
    tour_iri = str(tours[0])
    if not tour_iri.startswith(PAS_NS):
        return None, [
            f"IRI do Tour deve começar com pas: (atual: {tour_iri})"
        ]
    tour_id = tour_iri[len(PAS_NS):]
    if not tour_id:
        return None, ["IRI do Tour vazio"]
    # Mesmo charset que delete_tour exige. Sem isso, um IRI completo tipo
    # <https://id.pedalhidrografi.co/passeio/../x> passa (a forma full-IRI
    # aceita "/" e "."), e o tour_id vira componente de path no store
    # (tour_assets/<id>/...) — traversal pra qualquer lugar sob web/ — além
    # de criar tours que o delete-tour depois recusa. `_` é REJEITADO: é o
    # separador dos nós derivados (pas:<slug>_route), então um slug com `_`
    # colidiria com um irmão derivado na hora do purge.
    if not all(c.isalnum() or c == "-" for c in tour_id):
        return None, [
            f"tour_id inválido (apenas [A-Za-z0-9-], sem '_'): {tour_id!r}"
        ]
    return tour_id, []


def validate_tour_ttl(ttl_text):
    """Verifica que o TTL contém exatamente 1 ph:Tour e satisfaz TourShape.

    Retorna (ok, tour_id, errors). `tour_id` é o slug (sufixo após `pas:`).
    """
    v = _load_validator()
    from rdflib import URIRef, Namespace
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    tour_id, id_errors = _single_tour_id(data)
    if tour_id is None:
        return False, None, id_errors

    # Mescla com ontology + catálogo (excluindo o próprio tour + seus nós
    # derivados pra evitar cardinalidade falsa por sobreposição de re-upload).
    tour_uri = URIRef(PAS_NS + tour_id)
    catalog = _load_catalog()
    exclude = {tour_uri} | _derived_subjects(catalog, tour_uri)
    merged = data + v["ont"]
    for s, p, o in catalog:
        if s not in exclude:
            merged.add((s, p, o))

    with _validate_lock:   # pyshacl não é thread-safe (parser SPARQL) — ver _validate_lock
        conforms, results_graph, _txt = v["pyshacl"].validate(
            merged, shacl_graph=v["shapes"], inference="rdfs", advanced=True)
    if conforms:
        return True, tour_id, []

    own_subjects = set(data.subjects())
    SH = Namespace("http://www.w3.org/ns/shacl#")
    errors = []
    for r in results_graph.subjects(SH.resultSeverity, SH.Violation):
        focus = next(results_graph.objects(r, SH.focusNode), None)
        if focus is None or focus in own_subjects:
            msg = next(results_graph.objects(r, SH.resultMessage), None)
            errors.append(str(msg) if msg else "(sem mensagem)")
    if not errors:
        # Só warnings (severidade != Violation) — tratamos como ok.
        return True, tour_id, []
    return False, tour_id, errors


def upsert_tour_in_tours_ttl(tour_ttl, tour_id):
    """Mescla os blocos do tour novo em tours.ttl, sobrescrevendo qualquer
    dado prévio para o mesmo tour IRI. Mantém pessoas/associações antigas
    intactas (não cleanup orfanizados — git history preserva)."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    tour_iri = URIRef(PAS_NS + tour_id)
    catalog = Graph()
    existing = _load_dump_text("tours.ttl")
    if existing:
        catalog.parse(data=existing, format="turtle")
    _purge_subject(catalog, tour_iri)
    # Mescla os novos blocos (tour + eventual associação/pessoa nova).
    catalog += Graph().parse(data=tour_ttl, format="turtle")
    # Desvia pessoas novas (participante/autora criada on-the-fly) pra
    # identities.ttl — tours.ttl só referencia pessoas, não as define.
    _route_new_persons(catalog)
    STORE.write_text(KEY_TOURS, catalog.serialize(format="turtle"))


# Prefixos aceitos no campo `remove` do mode=patch (CURIEs → IRIs).
TOUR_PATCH_PREFIXES = {
    "ph":      PH_NS,
    "phd":     PHD_NS,
    "schema":  "https://schema.org/",
    "dcterms": "http://purl.org/dc/terms/",
    "dct":     "http://purl.org/dc/terms/",
    "prov":    "http://www.w3.org/ns/prov#",
    "pav":     "http://purl.org/pav/",
    "qudt":    "http://qudt.org/schema/qudt/",
    "exif":    "http://www.w3.org/2003/12/exif/ns#",
}


def _expand_remove_preds(remove_field):
    """Expande o form field `remove` ("ph:departedAt,dcterms:description")
    num set de URIRefs. Aceita CURIEs dos prefixos conhecidos ou IRIs
    completas; `schema:` expande pras formas https E http (catálogos antigos
    podem carregar qualquer uma). Levanta ValueError em token inválido."""
    from rdflib import URIRef
    preds = set()
    for tok in (remove_field or "").split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok.startswith("http://") or tok.startswith("https://"):
            preds.add(URIRef(tok))
            continue
        pfx, sep, local = tok.partition(":")
        ns = TOUR_PATCH_PREFIXES.get(pfx)
        if not sep or ns is None or not local:
            raise ValueError(f"predicado inválido em remove: {tok!r}")
        preds.add(URIRef(ns + local))
        if pfx == "schema":
            preds.add(URIRef("http://schema.org/" + local))
    return preds


def synthesize_tour_patch(patch_ttl, remove_preds, replace_image=False):
    """Transforma um patch (mode=patch) no documento full-replace equivalente.

    Merge-patch por predicado: cada predicado afirmado no patch sobre o tour
    (ou listado em `remove_preds`) substitui os triples existentes desse
    predicado — incluindo a closure de bnodes dos objetos descartados (um
    ph:energyEstimate antigo não deixa órfãos). Todo o resto do tour atual é
    copiado verbatim pro documento sintetizado, então clientes não precisam
    round-tripar predicados que não conhecem. Sujeitos auxiliares do patch
    (pessoas/assocs/séries novas) passam adiante intactos, como no replace.

    `replace_image=True` (announcement novo no request) descarta também o
    schema:image atual, pro handler injetar a URL fresca do upload.

    O resultado segue o pipeline normal (validate_tour_ttl → upsert →
    route-sync), ou seja, o SHACL valida o ESTADO FINAL do tour.

    Retorna (tour_id, result_ttl). Levanta ValueError se o patch não contém
    exatamente 1 ph:Tour com IRI pas:<slug> válido.
    """
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef

    patch = Graph().parse(data=patch_ttl, format="turtle")
    tour_id, errors = _single_tour_id(patch)
    if tour_id is None:
        raise ValueError("; ".join(errors))
    tour_uri = URIRef(PAS_NS + tour_id)

    preds_to_replace = set(patch.predicates(tour_uri)) | set(remove_preds)
    if replace_image:
        preds_to_replace.add(URIRef("https://schema.org/image"))
        preds_to_replace.add(URIRef("http://schema.org/image"))

    # Estado atual do tour (subject + nós derivados energy/measured/route) em
    # tours.ttl, copiado verbatim pro documento sintetizado.
    result = Graph()
    existing = _load_dump_text("tours.ttl")
    if existing:
        catalog = Graph().parse(data=existing, format="turtle")
        for subj in {tour_uri} | _derived_subjects(catalog, tour_uri):
            for s, p, o in catalog.triples((subj, None, None)):
                result.add((s, p, o))

    # Substituição por predicado: tira (tour, p, *) + as triples do nó
    # derivado que esse predicado apontava, depois soma o patch inteiro.
    for p in preds_to_replace:
        for o in list(result.objects(tour_uri, p)):
            result.remove((tour_uri, p, o))
            if isinstance(o, URIRef) and str(o).startswith(str(tour_uri) + "_"):
                _purge_subject(result, o)
    for triple in patch:
        result.add(triple)
    return tour_id, result.serialize(format="turtle")


def remove_tour_from_tours_ttl(tour_id):
    """Remove o tour (e bnodes alcançáveis) do tours.ttl. Não toca em pessoas
    nem associações — git history preserva e elas podem ser referenciadas
    por outros tours. Retorna nº de triples removidos."""
    existing = _load_dump_text("tours.ttl")
    if not existing:
        return 0
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    tour_iri = URIRef(PAS_NS + tour_id)
    catalog = Graph()
    catalog.parse(data=existing, format="turtle")
    n = _purge_subject(catalog, tour_iri)
    STORE.write_text(KEY_TOURS, catalog.serialize(format="turtle"))
    return n


# ── routes.json (geometria pré-bakada) ───────────────────────────────────
# Atualização incremental: um upload/edit de tour faz upsert da rota daquele
# passeio; um delete (ou edit que tira o linkRoute) remove a entrada. O fetch
# da geometria no RideWithGPS NÃO roda sob o lock global — só o read-modify-
# write do JSON é serializado. Assim um POST /upload-tour não trava uploads de
# fotos concorrentes durante os (até 60 s de) IO de rede.
def _load_routes_payload():
    """Lê routes.json — bucket-first, arquivo bakeado como seed/fallback.

    Devolve o dict `{generatedAt, source, routes:[...]}`. AUSENTE em ambos
    os lugares → payload vazio válido (seed). CORROMPIDO/formato inesperado
    → levanta — coagir pra vazio aqui faria o próximo upsert PERSISTIR o
    catálogo zerado (data loss silencioso); melhor falhar o sync (que é
    best-effort no caller) e deixar o catálogo intacto pra diagnóstico.
    """
    text = STORE.read_text(KEY_ROUTES)
    if text is None:
        baked = WEB / "routes.json"
        if baked.exists() and baked.stat().st_size > 0:
            text = baked.read_text(encoding="utf-8")
    if not text:
        return {"routes": []}
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("routes"), list):
        raise ValueError("routes.json com formato inesperado (sem lista 'routes')")
    return data


def _write_routes_payload(routes):
    """Persiste a lista de entradas (ordenada por data desc, como o build-
    routes.py), regravando metadados do envelope. Sob `_state_lock` pelo
    caller."""
    routes = sorted(routes, key=lambda e: e.get("dateMs") or 0, reverse=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"file": "web/data/tours.ttl", "updatedBy": "backend/upload-tour"},
        "routes": routes,
    }
    STORE.write_text(
        KEY_ROUTES,
        json.dumps(payload, indent=2, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
    )


def _current_tour_route_id(tour_id):
    """Lê o tours.ttl VIGENTE e devolve o id RWGPS do tour — ou None se o
    tour não existe ou não tem `ph:linkRoute`. Usado pra re-checar, sob o
    lock, que o estado não mudou durante o fetch de geometria fora do lock
    (TOCTOU: um delete-tour ou re-edit concorrente durante os até ~120 s de
    IO de rede não pode ser ressuscitado/sobrescrito por um upsert cego)."""
    import rwgps
    from rdflib import Graph as _RdfGraph, URIRef as _URIRef
    text = _load_dump_text("tours.ttl")
    if not text:
        return None
    try:
        g = _RdfGraph().parse(data=text, format="turtle")
        meta = rwgps.tour_entry_from_graph(g, _URIRef(PAS_NS + tour_id))
    except Exception:  # noqa: BLE001
        return None
    return meta["id"] if meta else None


def _sync_tour_route(tour_id):
    """Sincroniza a entrada de routes.json do tour `tour_id` com o estado atual.

    • Se o tour (no tours.ttl persistido) tem `ph:linkRoute` → RideWithGPS:
      busca a geometria (fora do lock) e faz upsert da entrada (keyed por
      tourIri).
    • Senão (sem linkRoute): remove qualquer entrada existente daquele tour.

    Lê o CATÁLOGO persistido, não o TTL postado: a entrada precisa resolver
    `ph:inSeriesEdition` → assoc → `ph:inEventSeries`/`ph:sequenceInSeries`
    (a numeração de série da sidebar), e os sujeitos `phd:assoc_*` moram fora
    do fragmento do tour — um doc sintetizado pelo mode=patch (e qualquer
    fragmento que referencie assocs já existentes) não os carrega; parsear só
    o fragmento zerava o `number` da entrada. Roda depois do upsert, então o
    catálogo é a fonte da verdade.

    Best-effort: o caller (upload_tour) envolve a chamada em try/except — o
    tour já foi salvo no tours.ttl; uma falha aqui só significa que a
    geometria não entrou (re-rodar build-routes.py conserta). Retorna um
    dict de status pro handler reportar ao form.
    """
    import rwgps
    from rdflib import Graph as _RdfGraph, URIRef as _URIRef

    tour_iri = PAS_NS + tour_id
    text = _load_dump_text("tours.ttl")
    if not text:
        return {"status": "error", "error": "tours.ttl ausente"}
    try:
        g = _RdfGraph().parse(data=text, format="turtle")
        meta = rwgps.tour_entry_from_graph(g, _URIRef(tour_iri))
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"parse: {e}"}

    # Sem rota RWGPS → garante que a entrada não fica órfã no JSON.
    if meta is None:
        with _state_lock:
            if _current_tour_route_id(tour_id) is not None:
                # Outro edit concorrente (re)adicionou um linkRoute depois
                # deste request; deixa o sync DELE mandar.
                return {"status": "stale"}
            payload = _load_routes_payload()
            before = len(payload["routes"])
            payload["routes"] = [r for r in payload["routes"] if r.get("tourIri") != tour_iri]
            removed = before - len(payload["routes"])
            if removed:
                _write_routes_payload(payload["routes"])
        return {"status": "removed" if removed else "absent"}

    # A geometria já está em routes.json, pra ESTA mesma rota? Então não busca
    # de novo. Traçado de rota é imutável na prática (o próprio código abaixo
    # já apostava nisso ao preservar a geometria antiga quando o fetch falha),
    # enquanto os METADADOS da entrada (título, data, numeração de série) sim
    # mudam a cada patch — e são recalculados do catálogo, de graça.
    #
    # Sem esse curto-circuito, todo patch de qualquer predicado puxava um GPX
    # inteiro do RideWithGPS. Passes em lote (audit-captura.py --sync: 87
    # passeios) e o backfill de gravações (~40) viravam ~130 fetches inúteis,
    # cada um seguido de um rewrite do routes.json de 2 MB — e como o bucket
    # tem Object Versioning, cada rewrite deixa uma geração noncurrent parada
    # por 90 dias. Pra forçar a rebusca da geometria: scripts/build-routes.py.
    cached = None
    with _state_lock:
        _p = _load_routes_payload()
        _old = next((r for r in _p["routes"] if r.get("tourIri") == tour_iri), None)
        if _old and _old.get("id") == meta["id"] and _old.get("latlngs"):
            cached = {"latlngs": _old["latlngs"], "pois": _old.get("pois") or []}

    if cached is not None:
        entry = {**meta, **cached}
    else:
        # Fetch da geometria FORA do lock (IO de rede, pode demorar).
        entry = rwgps.build_route_entry(meta)

    with _state_lock:
        # Re-checa sob o lock: o tour ainda existe e ainda aponta pra MESMA
        # rota? Se não (deletado ou re-editado durante o fetch), descarta —
        # o estado vigente já foi/será sincronizado por quem o mudou.
        if _current_tour_route_id(tour_id) != entry["id"]:
            return {"status": "stale", "rwgpsId": entry["id"]}
        payload = _load_routes_payload()
        old = next((r for r in payload["routes"] if r.get("tourIri") == tour_iri), None)
        # Fetch falhou mas a entrada antiga tem geometria DA MESMA rota →
        # preserva (metadados novos, latlngs/pois antigos). Clobberar com
        # null fazia a rota sumir do mapa a cada save com o RWGPS fora do
        # ar / sem credenciais. Geometria de rota é quase imutável; se um
        # dia precisar forçar, scripts/build-routes.py rebuilda do zero.
        kept = False
        if (not entry.get("latlngs") and old and old.get("latlngs")
                and old.get("id") == entry["id"]):
            entry["latlngs"] = old["latlngs"]
            entry["pois"] = old.get("pois") or []
            kept = True
        # Entrada idêntica à que já está lá → não reescreve. routes.json tem
        # ~2 MB e cada escrita cria uma geração noncurrent no bucket (Object
        # Versioning), que fica ocupando espaço por 90 dias. Um patch que não
        # mexe na rota não tem por que deixar rastro.
        if old == entry:
            return {"status": "unchanged", "rwgpsId": entry["id"]}
        payload["routes"] = [r for r in payload["routes"] if r.get("tourIri") != tour_iri]
        payload["routes"].append(entry)
        _write_routes_payload(payload["routes"])

    if kept:
        return {"status": "fetch_failed", "rwgpsId": entry["id"],
                "error": entry.get("error"), "kept": True}
    if entry.get("latlngs"):
        return {"status": "ok", "rwgpsId": entry["id"], "points": len(entry["latlngs"])}
    return {"status": "fetch_failed", "rwgpsId": entry["id"], "error": entry.get("error")}


def _remove_tour_route(tour_id):
    """Remove a entrada de routes.json do tour (chamado no delete-tour).
    Retorna nº de entradas removidas. Sob lock curto (sem IO de rede)."""
    tour_iri = PAS_NS + tour_id
    with _state_lock:
        payload = _load_routes_payload()
        before = len(payload["routes"])
        payload["routes"] = [r for r in payload["routes"] if r.get("tourIri") != tour_iri]
        removed = before - len(payload["routes"])
        if removed:
            _write_routes_payload(payload["routes"])
    return removed


# ── Rotas ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return "ok\n"


@app.post("/reload")
def reload_caches():
    """Invalida os caches do validador (shapes/ontology) e do catálogo
    (uploads, tours). Chame após mexer manualmente em qualquer TTL no
    bucket pra forçar a próxima requisição a re-ler do GCS.

    Sem auth — quem alcança o servidor é de confiança (mesma política
    do resto da API). Restrinja na borda (Cloudflare Worker / Access)
    se isso deixar de valer.

    Em Cloud Run com múltiplas instâncias, isto só invalida o cache
    *desta* instância. Pra forçar todas as instâncias a recarregar,
    role um novo deploy ou:
       gcloud run services update-traffic phidro --to-latest \\
         --region=southamerica-east1 --project=pedal-hidrografico
    (Touchar o traffic recria todas as instâncias.)"""
    global _validator
    _validator = None
    _invalidate_catalog()
    return jsonify(ok=True, reloaded=["validator", "catalog"])


@app.get("/")
@app.get("/index.html")
def index():
    """index.html — com SSR mínimo por passeio quando há ?tour=<id>.

    Também registrado em /index.html: a Cloudflare reescreve `/` → `/index.html`
    antes do worker, então o deep link /?tour= chega na origem como
    /index.html?tour= — sem esta rota, cairia no static file (sem SSR/alias).

    O render é best-effort: qualquer falha (catálogo corrompido, tour sem
    os campos esperados) degrada pro index estático, que é o comportamento
    de sempre. Ver _render_tour_index lá embaixo."""
    import re
    tour_id = (request.args.get("tour") or "").strip()
    # Continuidade (F4): deep links antigos usam ?tour=<id-numérico>. Se o id
    # bater num passeio migrado, 303 pro slug novo — o link antigo segue vivo.
    legacy_slug = _tour_iri_map().get("byOldId", {}).get(tour_id)
    if legacy_slug and legacy_slug != tour_id:
        return redirect(f"/?tour={legacy_slug}", code=303)
    if tour_id and re.fullmatch(r"[A-Za-z0-9\-]+", tour_id):
        try:
            page = _render_tour_index(tour_id)
        except Exception as e:  # noqa: BLE001
            print(f"[tour-page] render falhou pra tour_{tour_id}: {e}")
            page = None
        if page is not None:
            return _conditional(Response(page, mimetype="text/html",
                                         headers={"Cache-Control": "no-cache"}))
    return send_from_directory(WEB, "index.html")


@app.get("/pessoas/<slug>")
def person_page(slug):
    """Dereferência de uma pessoa. O IRI é https://id.pedalhidrografi.co/pessoas/
    <slug> (a Cloudflare faz 303 path-preserving pra cá).

    Conneg (httpRange-14): `Accept: text/turtle` (ou `?format=ttl`) devolve as
    triples da pessoa fatiadas de identities.ttl; senão serve pessoas.html — a
    página humana, que foca a pessoa pelo slug da URL. O arquivo servido é SEMPRE
    pessoas.html (slug ignorado no servidor → sem risco de path); as URLs
    relativas do app resolvem via `<base href="/">`."""
    if _wants_turtle(request):
        ttl = _resource_slice_ttl(PES_NS + slug, "identities.ttl")
        if ttl is None:
            abort(404)
        return _conditional(Response(ttl, mimetype="text/turtle",
                                     headers={"Cache-Control": "no-cache"}))
    return send_from_directory(WEB, "pessoas.html")


def _render_terms_html():
    """Página humana do vocabulário ph: — gerada de ontology.ttl (bucket-first).
    Cada termo ganha um âncora = seu localname, então o fragmento do IRI
    (id.pedalhidrografi.co/terms#StillImage) rola até a definição certa depois
    do 303 pra cá. Best-effort: se o ontology.ttl não parsear, devolve None e o
    handler cai pro turtle."""
    from rdflib import Graph, URIRef, RDF, RDFS, Namespace
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    DCT = Namespace("http://purl.org/dc/terms/")
    text = _load_dump_text("ontology.ttl")
    if not text:
        return None
    g = Graph()
    g.parse(data=text, format="turtle")
    NS = {
        "https://id.pedalhidrografi.co/terms#": "ph:",
        "https://schema.org/": "schema:", "http://schema.org/": "schema:",
        "http://www.w3.org/ns/prov#": "prov:",
        "http://purl.org/dc/terms/": "dcterms:",
        "http://www.w3.org/2001/XMLSchema#": "xsd:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/2002/07/owl#": "owl:",
        "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#": "nfo:",
        "http://www.w3.org/2003/12/exif/ns#": "exif:",
        "http://purl.org/pav/": "pav:",
    }
    def curie(u):
        s = str(u)
        for full, pfx in NS.items():
            if s.startswith(full):
                return pfx + s[len(full):]
        return s
    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))
    def label(subj):
        return next((str(o) for o in g.objects(subj, RDFS.label)), None)
    def comment(subj):
        return next((str(o) for o in g.objects(subj, RDFS.comment)), None)
    def objs(subj, pred):
        return sorted(curie(o) for o in g.objects(subj, pred))

    PH = Namespace("https://id.pedalhidrografi.co/terms#")
    onto = URIRef("https://id.pedalhidrografi.co/terms")
    title = next((str(o) for o in g.objects(onto, DCT.title)), "Vocabulário ph:")
    desc = next((str(o) for o in g.objects(onto, DCT.description)), "")
    ver = next((str(o) for o in g.objects(onto, OWL.versionInfo)), "")

    def is_ph(subj):
        return isinstance(subj, URIRef) and str(subj).startswith(str(PH))
    classes = sorted((s for s in g.subjects(RDF.type, OWL.Class) if is_ph(s)), key=str)
    props = sorted(
        (s for s in set(g.subjects(RDF.type, OWL.ObjectProperty))
         | set(g.subjects(RDF.type, OWL.DatatypeProperty)) if is_ph(s)),
        key=str)

    def term_card(subj, extra_rows):
        loc = str(subj)[len(str(PH)):]
        lab = label(subj)
        com = comment(subj)
        dep = (subj, OWL.deprecated, None) in g \
            and next(g.objects(subj, OWL.deprecated)) \
            and str(next(g.objects(subj, OWL.deprecated))).lower() == "true"
        rows = "".join(
            f'<div class="row"><span class="k">{esc(k)}</span>'
            f'<span class="v">{esc(v)}</span></div>'
            for k, v in extra_rows if v)
        badge = ' <span class="dep">deprecado</span>' if dep else ""
        return (
            f'<section id="{esc(loc)}" class="term">'
            f'<h3><code>ph:{esc(loc)}</code>{" — " + esc(lab) if lab else ""}{badge}</h3>'
            f'{f"<p>{esc(com)}</p>" if com else ""}'
            f'<div class="meta">{rows}</div></section>')

    class_html = "".join(term_card(c, [
        ("subclasse de", ", ".join(objs(c, RDFS.subClassOf)) or None),
    ]) for c in classes)
    prop_kind = {}
    for p in props:
        prop_kind[p] = ("ObjectProperty"
                        if (p, RDF.type, OWL.ObjectProperty) in g
                        else "DatatypeProperty")
    prop_html = "".join(term_card(p, [
        ("tipo", prop_kind[p]),
        ("domínio", ", ".join(objs(p, RDFS.domain)) or None),
        ("imagem", ", ".join(objs(p, RDFS.range)) or None),
        ("subpropriedade de", ", ".join(objs(p, RDFS.subPropertyOf)) or None),
    ]) for p in props)

    return f"""<!doctype html><html lang="pt"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{color-scheme:dark}}
body{{margin:0;background:#12141a;color:#e6e8ee;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:0 1rem 4rem}}
.wrap{{max-width:820px;margin:0 auto}}
header{{padding:2rem 0 1rem;border-bottom:1px solid #2a2e39}}
h1{{margin:0 0 .3rem;font-size:1.6rem}}
h2{{margin:2.4rem 0 .6rem;font-size:1.15rem;color:#9fd3c7;border-bottom:1px solid #2a2e39;padding-bottom:.3rem}}
h3{{margin:0 0 .35rem;font-size:1rem;font-weight:600}}
code{{background:#1c2029;padding:.08em .35em;border-radius:4px;color:#cfe3ff;font-size:.92em}}
a{{color:#7fb2ff}}
p{{margin:.35rem 0 .5rem;color:#c2c6d2}}
.lede{{color:#c2c6d2}}
.term{{padding:.9rem 0;border-bottom:1px solid #21252f;scroll-margin-top:1rem}}
.meta{{display:flex;flex-direction:column;gap:.15rem;margin-top:.3rem}}
.row{{display:flex;gap:.5rem;font-size:.86rem}}
.k{{color:#7d8296;min-width:9.5rem;flex:0 0 auto}}
.v{{color:#d7dbe6;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.dep{{color:#f2a5a5;font-size:.72rem;border:1px solid #6a3a3a;border-radius:4px;padding:.05em .4em;vertical-align:middle}}
.ttl-link{{margin-top:.8rem;font-size:.9rem}}
footer{{margin-top:3rem;color:#7d8296;font-size:.82rem}}
</style></head><body><div class="wrap">
<header>
<h1>{esc(title)}</h1>
<p class="lede">{esc(desc)}</p>
<p class="lede"><code>@prefix ph: &lt;https://id.pedalhidrografi.co/terms#&gt;</code>{f" · versão {esc(ver)}" if ver else ""}</p>
<p class="ttl-link"><a href="/terms?format=ttl">↓ ontology.ttl (Turtle)</a></p>
</header>
<h2>Classes</h2>
{class_html}
<h2>Propriedades</h2>
{prop_html}
<footer>Pedal Hidrográfico · vocabulário servido de <code>ontology.ttl</code>.
Reusa PROV-O, schema.org, Dublin Core, NFO, EXIF, GeoSPARQL.</footer>
</div></body></html>"""


@app.get("/terms")
def terms_vocab():
    """Dereferência do vocabulário ph:. O namespace é
    https://id.pedalhidrografi.co/terms# — o fragmento (#StillImage) é
    resolvido pelo cliente contra o documento inteiro (F8). Conneg:
    Accept: text/turtle (ou ?format=ttl) → ontology.ttl; senão a página humana
    gerada de ontology.ttl (com âncora por termo). Sem `#` no path — a CF já
    tira o fragmento antes do 303 pra cá."""
    if _wants_turtle(request):
        text = _load_dump_text("ontology.ttl")
        if text is None:
            abort(404)
        return _conditional(Response(text, mimetype="text/turtle",
                                     headers={"Cache-Control": "no-cache"}))
    try:
        html = _render_terms_html()
    except Exception as e:  # noqa: BLE001
        print(f"[terms] render falhou: {e}")
        html = None
    if html is None:  # fallback: entrega o turtle mesmo sem Accept
        text = _load_dump_text("ontology.ttl") or ""
        return _conditional(Response(text, mimetype="text/turtle",
                                     headers={"Cache-Control": "no-cache"}))
    return _conditional(Response(html, mimetype="text/html",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/listas/<slug>")
def list_page(slug):
    """Dereferência de uma lista/álbum (schema:Collection). IRI:
    https://id.pedalhidrografi.co/listas/<slug> (CF 303 pra cá). Conneg:
    Accept: text/turtle (ou ?format=ttl) → a Collection (de lists.ttl) + seus
    membros como schema:hasPart (calculados de images.ttl via schema:isPartOf
    inverso); senão 303 pra galeria JÁ FILTRADA por esta lista
    (imagens.html?list=<slug> — a galeria pré-seleciona a faceta Listas)."""
    list_iri = LST_NS + slug
    if not _wants_turtle(request):
        from urllib.parse import quote
        return redirect(f"/imagens.html?list={quote(slug, safe='')}", code=303)
    from rdflib import URIRef, Literal
    Graph = _load_validator()["Graph"]
    ISPARTOF = URIRef(SCHEMA_NS + "isPartOf")
    HASPART = URIRef(SCHEMA_NS + "hasPart")
    lu = URIRef(list_iri)
    lists_text = _load_dump_text("lists.ttl")
    out = Graph()
    for pfx, ns in (("lst", LST_NS), ("phd", PHD_NS), ("schema", SCHEMA_NS)):
        out.bind(pfx, ns)
    if lists_text:
        lg = Graph().parse(data=lists_text, format="turtle")
        for t in lg.triples((lu, None, None)):
            out.add(t)
    # Membros: mídias que declaram schema:isPartOf <lista> em images.ttl.
    img_text = _load_dump_text("images.ttl")
    if img_text:
        ig = Graph().parse(data=img_text, format="turtle")
        for m in ig.subjects(ISPARTOF, lu):
            out.add((lu, HASPART, m))
    if len(out) == 0:
        abort(404)
    return _conditional(Response(out.serialize(format="turtle"),
                                 mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/passeio/<slug>")
def tour_page(slug):
    """Dereferência de um passeio. IRI: https://id.pedalhidrografi.co/passeio/
    <slug> (CF 303 pra cá). Conneg: Accept: text/turtle (ou ?format=ttl) → as
    triples do passeio fatiadas de tours.ttl; senão 303 pro deep link do app
    (/?tour=<slug>), que abre o modal da rota (com SSR pra crawlers/no-JS).
    (A forma de 2 segmentos /passeio/<ES>/<seq> é a edição — rota à parte.)"""
    if not _wants_turtle(request):
        return redirect(f"/?tour={slug}", code=303)
    ttl = _resource_slice_ttl(PAS_NS + slug, "tours.ttl")
    if ttl is None:
        abort(404)
    return _conditional(Response(ttl, mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


def _render_series_html(g, series_iri, es, editions):
    """Página humana de uma série de eventos — lista as edições (mais recente
    primeiro), cada uma linkando pro passeio que a realizou. Mesmo estilo
    escuro de _render_terms_html; best-effort (nunca falha o request)."""
    from rdflib import URIRef, Namespace
    DCT = Namespace("http://purl.org/dc/terms/")
    SCHEMA = Namespace(SCHEMA_NS)
    PH = Namespace(PH_NS)
    INSERIES = PH.inSeriesEdition
    SEQ = PH.sequenceInSeries

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    title = str(g.value(series_iri, DCT.title) or es)

    rows = []
    for ed in editions:
        seq_lit = g.value(ed, SEQ)
        try:
            seq_n = int(seq_lit)
        except (TypeError, ValueError):
            seq_n = 0
        seg = str(ed)[len(PAS_NS):]   # "<ES>/<n>" — segmento pro link da edição
        realizer = next(iter(g.subjects(INSERIES, ed)), None)
        tour_title = str(g.value(realizer, DCT.title)) if realizer is not None else None
        tour_date = g.value(realizer, DCT.date) if realizer is not None else None
        tour_slug = str(realizer)[len(PAS_NS):] if realizer is not None else None
        rows.append((seq_n, seg, tour_title, tour_date, tour_slug))
    rows.sort(key=lambda r: r[0], reverse=True)

    def row_html(seq_n, seg, tour_title, tour_date, tour_slug):
        label = tour_title or "(passeio sem título)"
        date_s = str(tour_date)[:10] if tour_date else ""
        link = f"/?tour={esc(tour_slug)}" if tour_slug else f"/passeio/{esc(seg)}"
        return (
            f'<div class="row"><span class="k"><a href="{esc(link)}">'
            f'{esc(es)} {seq_n}</a></span>'
            f'<span class="v">{esc(label)}{f" · {esc(date_s)}" if date_s else ""}</span></div>')

    rows_html = "".join(row_html(*r) for r in rows) or '<p class="lede">Sem edições.</p>'

    return f"""<!doctype html><html lang="pt"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — série</title>
<style>
:root{{color-scheme:dark}}
body{{margin:0;background:#12141a;color:#e6e8ee;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:0 1rem 4rem}}
.wrap{{max-width:640px;margin:0 auto}}
header{{padding:2rem 0 1rem;border-bottom:1px solid #2a2e39}}
h1{{margin:0 0 .3rem;font-size:1.6rem}}
code{{background:#1c2029;padding:.08em .35em;border-radius:4px;color:#cfe3ff;font-size:.92em}}
a{{color:#7fb2ff;text-decoration:none}}
a:hover{{text-decoration:underline}}
p{{margin:.35rem 0 .5rem;color:#c2c6d2}}
.lede{{color:#c2c6d2}}
.row{{display:flex;gap:.8rem;padding:.55rem 0;border-bottom:1px solid #21252f;font-size:.92rem}}
.k{{min-width:5.5rem;flex:0 0 auto;font-weight:600}}
.v{{color:#d7dbe6}}
.ttl-link{{margin-top:.8rem;font-size:.9rem}}
footer{{margin-top:2rem;color:#7d8296;font-size:.82rem}}
</style></head><body><div class="wrap">
<header>
<h1>{esc(title)}</h1>
<p class="lede"><code>ser:{esc(es)}</code> · {len(rows)} edição{'ões' if len(rows) != 1 else ''}</p>
<p class="ttl-link"><a href="/serie/{esc(es)}?format=ttl">↓ Turtle</a></p>
</header>
{rows_html}
<footer>Pedal Hidrográfico · série de eventos, servida de tours.ttl.</footer>
</div></body></html>"""


@app.get("/serie/<es>")
def series_page(es):
    """Dereferência de uma série de eventos (schema:EventSeries). IRI:
    https://id.pedalhidrografi.co/serie/<ES> (ex.: .../serie/PH). Conneg:
    Accept: text/turtle (ou ?format=ttl) → a série + suas edições
    (ph:SeriesEdition, via ph:inEventSeries inverso) + o passeio que realiza
    cada uma; senão uma página HTML gerada listando as edições (mais recente
    primeiro), cada uma linkando pro passeio realizador."""
    from rdflib import URIRef
    Graph = _load_validator()["Graph"]
    tours_text = _load_dump_text("tours.ttl")
    if not tours_text:
        abort(404)
    g = Graph().parse(data=tours_text, format="turtle")
    series_iri = URIRef(SER_NS + es)
    if (series_iri, None, None) not in g:
        abort(404)
    INEVENTSERIES = URIRef(PH_NS + "inEventSeries")
    INSERIES = URIRef(PH_NS + "inSeriesEdition")
    editions = list(g.subjects(INEVENTSERIES, series_iri))
    if not _wants_turtle(request):
        try:
            html = _render_series_html(g, series_iri, es, editions)
        except Exception as e:  # noqa: BLE001
            print(f"[series] render falhou pra ser:{es}: {e}")
            html = None
        if html is not None:
            return _conditional(Response(html, mimetype="text/html",
                                         headers={"Cache-Control": "no-cache"}))
    out = Graph()
    for pfx, ns in (("pas", PAS_NS), ("ser", SER_NS), ("ph", PH_NS),
                    ("dcterms", "http://purl.org/dc/terms/")):
        out.bind(pfx, ns)
    for t in g.triples((series_iri, None, None)):
        out.add(t)
    for ed in editions:
        for t in g.triples((ed, None, None)):
            out.add(t)
        realizer = next(iter(g.subjects(INSERIES, ed)), None)
        if realizer is not None:
            out.add((realizer, INSERIES, ed))
    return _conditional(Response(out.serialize(format="turtle"),
                                 mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/passeio/<es>/<seq>")
def edition_page(es, seq):
    """Dereferência de uma EDIÇÃO de série (ph:SeriesEdition). IRI:
    https://id.pedalhidrografi.co/passeio/<ES>/<seq> (ex.: .../passeio/BP/4,
    .../passeio/BP/3-5). 2 segmentos — não confunde com o passeio (1 segmento,
    /passeio/<slug>). Conneg: turtle → as triples da edição (de tours.ttl) + a
    aresta do passeio que a realiza; senão 303 pro passeio realizador
    (/?tour=<slug>), resolvido via ph:inSeriesEdition inverso em tours.ttl."""
    from rdflib import URIRef
    edition_iri = f"{PAS_NS}{es}/{seq}"
    Graph = _load_validator()["Graph"]
    tours_text = _load_dump_text("tours.ttl")
    if not tours_text:
        abort(404)
    g = Graph().parse(data=tours_text, format="turtle")
    ed = URIRef(edition_iri)
    INSERIES = URIRef(PH_NS + "inSeriesEdition")
    realizer = next(iter(g.subjects(INSERIES, ed)), None)
    if not _wants_turtle(request):
        if realizer is None:
            abort(404)
        return redirect(f"/?tour={str(realizer)[len(PAS_NS):]}", code=303)
    out = Graph()
    for pfx, ns in (("pas", PAS_NS), ("ser", SER_NS), ("ph", PH_NS)):
        out.bind(pfx, ns)
    for t in g.triples((ed, None, None)):
        out.add(t)
    if len(out) == 0:
        abort(404)
    if realizer is not None:
        out.add((realizer, INSERIES, ed))
    return _conditional(Response(out.serialize(format="turtle"),
                                 mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/midia/<local>")
def media_page(local):
    """Dereferência de uma mídia (foto/vídeo). IRI opaco:
    https://id.pedalhidrografi.co/midia/<hash16> (o tipo vem da classe, não do
    IRI). CF 303 pra cá. Conneg: Accept: text/turtle (ou ?format=ttl) → as
    triples da mídia fatiadas de images.ttl; senão 303 pra galeria com a mídia
    pré-selecionada (imagens.html?pick=<hash>). Aceita a forma legada
    /midia/image_<hash> / video_<hash> (tira o prefixo)."""
    for pfx in ("image_", "video_"):
        if local.startswith(pfx):
            local = local[len(pfx):]
            break
    if len(local) != 16 or not all(c in "0123456789abcdef" for c in local.lower()):
        abort(404)
    if not _wants_turtle(request):
        return redirect("/imagens.html?pick=" + local, code=303)
    ttl = _resource_slice_ttl(MED_NS + local, "images.ttl")
    if ttl is None:
        abort(404)
    return _conditional(Response(ttl, mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/data/<filename>")
def get_data_ttl(filename):
    """Handler único pra /data/*.ttl — bucket-first, container fallback.

    Inclui os mutáveis (uploads.ttl, data_graphs.ttl) e os estáticos
    overrideables (shapes.ttl, ontology.ttl, tours.ttl). Quando o arquivo
    não existe em nenhum dos dois lugares, devolve um seed razoável pros
    dois mutáveis ou 404 pros demais.
    """
    # Mapa de IRIs de passeio (JSON, estático): o app precisa dele client-side
    # pra resolver deep links ?tour=<id-numérico> antigos → slug (a Cloudflare
    # tira a query string antes de chegar no backend, então o 303 do index()
    # não roda via amora — a continuidade é feita no app.js). Servido do
    # container (byOldId só; byNewSlug não interessa ao cliente).
    if filename == "tour-iri-map.json":
        body = json.dumps({"byOldId": _tour_iri_map().get("byOldId", {})},
                          ensure_ascii=False, separators=(",", ":"))
        return _conditional(Response(body, mimetype="application/json",
                                     headers={"Cache-Control": "no-cache"}))
    # O converter padrão do Flask bloqueia "/" mas não um ".." solto —
    # `DATA_DIR / ".."` é um diretório existente e o read_text estourava
    # IsADirectoryError → 500 feio. Só servimos *.ttl de nome simples.
    if not filename.endswith(".ttl") or "/" in filename or ".." in filename:
        abort(404)
    text = _load_dump_text(filename)
    if text is None:
        if filename in ("images.ttl", "identities.ttl", "uploads.ttl", "lists.ttl"):
            text = ""             # catálogo vazio — válido (uploads.ttl: legado)
        elif filename == "data_graphs.ttl":
            text = DATA_GRAPHS_SHIM  # manifesto estático (tours + images + identities)
        else:
            abort(404)
    return _conditional(Response(text, mimetype="text/turtle",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/tour_assets/<path:p>")
def get_tour_asset(p):
    """Imagens de anúncio + qualquer arquivo associado a um tour. Mesma
    lógica de /photos: redireciona pra GCS público quando o store tiver
    URL, stream local caso contrário."""
    key = f"tour_assets/{p}"
    url = STORE.public_url(key)
    if url:
        return redirect(url, code=302)
    local = WEB / "tour_assets" / p
    if local.is_file():
        resp = send_from_directory(WEB / "tour_assets", p)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    abort(404)


@app.get("/photos/<path:p>")
def get_photo(p):
    key = f"photos/{p}"
    # Se o store expõe URL pública (GCS), redireciona — muito mais eficiente
    # que streamar via Flask. Local store retorna None e cai no fallback.
    url = STORE.public_url(key)
    if url:
        return redirect(url, code=302)
    # Fallback: serve diretamente do filesystem (modo local).
    if (WEB / "photos" / p).is_file():
        resp = send_from_directory(WEB / "photos", p)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    abort(404)


@app.get("/clips/<path:p>")
def get_clip(p):
    """Mesma lógica do /photos/<p>: redireciona pro bucket em modo GCS,
    senão serve do filesystem. Cobre uploads via /upload-video (vivem em
    gs://<bucket>/clips/<vhash>.*) E os transcodes de build-clips.py (que
    em modo local ficam em web/clips/<stem>.* / web/clips/audio/<stem>.m4a;
    em modo GCS o sync push-eles via deploy-cloudrun.sh --state)."""
    key = f"clips/{p}"
    url = STORE.public_url(key)
    if url:
        return redirect(url, code=302)
    if (WEB / "clips" / p).is_file():
        resp = send_from_directory(WEB / "clips", p)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    abort(404)


@app.get("/routes.json")
def get_routes_json():
    """routes.json — bucket-first, arquivo bakeado como seed/fallback.

    Mutável: além do rebuild completo via scripts/build-routes.py, o backend
    faz upsert/remove incremental por upload/delete de tour. Bucket-first faz
    o Cloud Run servir a versão atualizada server-side sem redeploy; em modo
    local o store é o próprio `web/`, então é o mesmo arquivo."""
    text = STORE.read_text(KEY_ROUTES)
    if text is None:
        baked = WEB / "routes.json"
        if baked.exists() and baked.stat().st_size > 0:
            text = baked.read_text(encoding="utf-8")
    if text is None:
        text = '{"routes": []}'
    return _conditional(Response(text, mimetype="application/json",
                                 headers={"Cache-Control": "no-cache"}))


# ── Rotas salvas (biblioteca de rotas do editor) ─────────────────────────
def _read_saved_routes(strict=False):
    """Catálogo de rotas salvas — bucket-first, {"routes": {}} se ausente.

    Por padrão (strict=False, uso em GET) um arquivo corrompido também
    degrada pra vazio, pra não derrubar o endpoint de leitura. Em strict=True
    (uso nos mutadores save/delete-route) um arquivo PRESENTE mas corrompido
    levanta em vez de degradar — coagir pra vazio ali faria o upsert/delete
    seguinte PERSISTIR o catálogo zerado (mesmo raciocínio de
    `_load_routes_payload` pro routes.json)."""
    text = STORE.read_text(KEY_SAVED_ROUTES)
    if not text:
        return {"routes": {}}
    try:
        obj = json.loads(text)
        if not isinstance(obj, dict) or not isinstance(obj.get("routes"), dict):
            raise ValueError("saved_routes.json com formato inesperado (sem dict 'routes')")
    except (ValueError, TypeError):
        if strict:
            raise
        return {"routes": {}}
    return obj


def _write_saved_routes(catalog):
    STORE.write_text(KEY_SAVED_ROUTES, json.dumps(catalog, ensure_ascii=False),
                     content_type="application/json")


def _route_slug(name):
    """Slug do link /route/<slug> — derivado do NOME da rota (a identidade
    humana dela): minúsculas, sem acento, [a-z0-9] ligados por '-'. Mesmo
    algoritmo do filenameFromName do app.js, pra link e arquivo baterem."""
    s = unicodedata.normalize("NFD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60].strip("-")


def _entry_slug(entry):
    """Slug de uma entrada do catálogo — o gravado, ou derivado do nome
    (entradas legadas, salvas antes do slug existir)."""
    return entry.get("slug") or _route_slug(entry.get("name"))


@app.get("/saved-routes")
def list_saved_routes():
    """Lista resumida das rotas salvas (sem geometria) — mais novas primeiro."""
    cat = _read_saved_routes()
    items = []
    for rid, r in cat.get("routes", {}).items():
        if not isinstance(r, dict):
            continue
        items.append({
            "id": rid,
            "name": r.get("name") or "",
            "slug": _entry_slug(r),
            "created": r.get("created"),
            "points": r.get("points"),
        })
    items.sort(key=lambda x: x.get("created") or "", reverse=True)
    text = json.dumps({"routes": items}, ensure_ascii=False)
    return _conditional(Response(text, mimetype="application/json",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/saved-route/<ref>")
def get_saved_route(ref):
    """Estado completo (formato de compartilhamento) de uma rota salva.

    `ref` é o id hex OU o slug do nome (é o que o deep link /route/<slug>
    resolve). A resposta leva `id`/`slug` junto do estado — o cliente adota o
    id pra um re-salvar atualizar a MESMA rota (applyShareState ignora chaves
    desconhecidas)."""
    ref = (ref or "").strip()
    routes = _read_saved_routes().get("routes", {})
    rid, r = ref, routes.get(ref)
    if not isinstance(r, dict):
        # Busca por slug; empate (nomes duplicados legados, de antes da
        # unicidade) → vence a atualizada mais recentemente.
        matches = [(k, v) for k, v in routes.items()
                   if isinstance(v, dict) and _entry_slug(v) == ref]
        if not matches:
            abort(404)
        rid, r = max(matches, key=lambda kv: kv[1].get("updated")
                     or kv[1].get("created") or "")
    if not isinstance(r, dict) or not isinstance(r.get("state"), dict):
        abort(404)
    payload = dict(r["state"])
    payload["id"] = rid
    payload["slug"] = _entry_slug(r)
    text = json.dumps(payload, ensure_ascii=False)
    return _conditional(Response(text, mimetype="application/json",
                                 headers={"Cache-Control": "no-cache"}))


@app.get("/route/<slug>")
def route_deep_link(slug):
    """Link compartilhável de uma rota salva, POR NOME: /route/<slug>.

    303 pro app com o slug no FRAGMENTO (/#rt=<slug>) — fragmento nunca chega
    na Cloudflare nem no service worker (mesma razão do #st=), então o deep
    link sobrevive ao strip de query do worker e ao cache do SW. O app resolve
    o #rt= no cliente via GET /saved-route/<slug>."""
    slug = (slug or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9\-]{0,80}", slug):
        abort(404)
    return redirect(f"/#rt={slug}", code=303)


@app.post("/save-route")
@serialized
def save_route():
    """Upsert de uma rota salva. Body JSON: {name, state, id?}. Devolve
    {id, slug}. `state` é o objeto de snapshotForShare() do editor
    (wp + sg + rm + n). Passar `id` (de uma rota existente) sobrescreve
    in-place; sem id, gera um. O NOME é obrigatório e único (case/acento-
    insensível, via slug): é ele que vira o link /route/<slug> — colisão com
    outra rota devolve 409 e o cliente pede outro nome."""
    data = request.get_json(silent=True) or {}
    state = data.get("state")
    if (not isinstance(state, dict) or not isinstance(state.get("wp"), list)
            or not state["wp"]):
        return jsonify(error="state inválido (sem waypoints)"), 400
    name = str(data.get("name") or state.get("n") or "").strip()
    if not name:
        return jsonify(error="dê um nome à rota (é ele que vira o link)"), 400
    slug = _route_slug(name)
    if not slug:
        return jsonify(error="nome inválido pro link — use ao menos uma letra ou número"), 400
    rid = str(data.get("id") or "").strip() or uuid.uuid4().hex[:12]
    if not (1 <= len(rid) <= 32) or not all(c in "0123456789abcdef" for c in rid):
        return jsonify(error="id inválido (esperado hex)"), 400
    try:
        cat = _read_saved_routes(strict=True)
    except (ValueError, TypeError) as e:
        return jsonify(error=f"saved_routes.json corrompido, recusando salvar: {e}"), 500
    routes = cat.setdefault("routes", {})
    for other_id, other in routes.items():
        if other_id == rid or not isinstance(other, dict):
            continue
        if _entry_slug(other) == slug:
            return jsonify(
                error=f'já existe uma rota chamada "{other.get("name") or slug}" — escolha outro nome',
                slug=slug), 409
    existing = routes.get(rid)
    now = datetime.now(timezone.utc).isoformat()
    routes[rid] = {
        "name": name,
        "slug": slug,
        "state": state,
        "points": len(state["wp"]),
        "created": (existing or {}).get("created") if isinstance(existing, dict) else None,
        "updated": now,
    }
    if not routes[rid]["created"]:
        routes[rid]["created"] = now
    try:
        _write_saved_routes(cat)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"persistência: {e}"), 500
    print(f"[save-route] id={rid} slug={slug} pts={routes[rid]['points']} name={name!r}")
    return jsonify(id=rid, slug=slug)


@app.post("/delete-route/<rid>")
@serialized
def delete_route(rid):
    rid = (rid or "").strip()
    try:
        cat = _read_saved_routes(strict=True)
    except (ValueError, TypeError) as e:
        return jsonify(error=f"saved_routes.json corrompido, recusando apagar: {e}"), 500
    if rid not in cat.get("routes", {}):
        return jsonify(error="rota não encontrada", id=rid), 404
    del cat["routes"][rid]
    try:
        _write_saved_routes(cat)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"persistência: {e}"), 500
    print(f"[delete-route] id={rid}")
    return jsonify(id=rid, deleted=True)


# URL pública canônica — usada no feed RSS (links absolutos). Override por
# env pra quem servir o app em outro domínio.
SITE_URL = (os.environ.get("PUBLIC_BASE_URL")
            or "https://amora.pedalhidrografi.co").rstrip("/") + "/"

# Cache do XML do feed, chaveado pelo hash do tours.ttl — parsear 100 KB de
# Turtle por request seria caro; assim só re-renderiza quando o
# catálogo de tours muda (upload/delete de tour ou edição out-of-band).
_feed_cache = {"digest": None, "xml": None}
_feed_lock = threading.Lock()


def _fmt_moving_duration(dur):
    """xsd:duration 'PT3H30M' → '3h30' / 'PT45M' → '45min'. None se não parsear."""
    import re
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:[\d.]+S)?", str(dur))
    if not m or (m.group(1) is None and m.group(2) is None):
        return None
    h, mi = int(m.group(1) or 0), int(m.group(2) or 0)
    return f"{h}h{mi:02d}" if h else f"{mi}min"


def _person_name(g, p):
    """Nome de exibição: schema:name (nome real), senão schema:alternateName
    (apelido/handle), senão o slug opaco da IRI (pes:<slug8> → '<slug8>') como
    último recurso — alternateName é só Warning no PersonShape, não obrigatório."""
    from rdflib import Namespace
    SCHEMA = Namespace("https://schema.org/")
    name = g.value(p, SCHEMA.name)
    if name:
        return str(name)
    alt = g.value(p, SCHEMA.alternateName)
    if alt:
        return str(alt)
    return str(p).split("/")[-1].split("#")[-1]


def _tour_display_title(g, t):
    """dcterms:title com prefixo de série(s): "PH 95: …" / "PH 79 & BP 4: …".
    Código = slug da IRI da série (phd:PH → "PH"), como no app. Ordena por
    sequência decrescente pra série de longa data vir primeiro — o grafo RDF
    não preserva a ordem do Turtle."""
    from rdflib import Namespace
    PH = Namespace(PH_NS)
    DCT = Namespace("http://purl.org/dc/terms/")
    title = str(g.value(t, DCT.title) or t).strip()
    editions = []
    for assoc in g.objects(t, PH.inSeriesEdition):
        ev = g.value(assoc, PH.inEventSeries)
        seq = g.value(assoc, PH.sequenceInSeries)
        if ev is not None and seq is not None:
            code = str(ev).split("/")[-1].split("#")[-1]
            try:
                editions.append((code, int(seq)))
            except (TypeError, ValueError):
                pass
    editions.sort(key=lambda e: e[1], reverse=True)
    if editions:
        title = " & ".join(f"{c} {n}" for c, n in editions) + f": {title}"
    return title


def _tour_date_sort_key(dt):
    """Chave de ordenação p/ (None | datetime naive | datetime aware) sem
    TypeError: datetimes naive e aware não são comparáveis entre si, e um
    único dcterms:date sem timezone junto de outros com timezone derrubava
    /feed.xml e /sitemap.xml de vez (500 permanente até o dado ser corrigido).
    Datas naive são tratadas como UTC — mesma convenção do resto do backend."""
    if dt is None:
        return (False, 0.0)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (True, dt.timestamp())


def _tours_with_identities_text():
    """tours.ttl + identities.ttl concatenados. Pós-split de catálogos, pessoas
    (schema:name/alternateName) vivem só em identities.ttl — qualquer render
    que resolve nomes de autoria (feed, página SSR do passeio) via
    prov:wasAttributedTo precisa das duas, senão _person_name cai pro slug
    opaco da IRI (pes:<slug8>) por falta da definição da pessoa no grafo."""
    tours = _load_dump_text("tours.ttl") or ""
    idents = _load_dump_text("identities.ttl") or ""
    return tours + "\n\n" + idents


def _build_feed_xml(tours_text):
    import re
    from email.utils import format_datetime
    from xml.sax.saxutils import escape
    from rdflib import Graph, Namespace, RDF

    def attr_escape(v):
        # escape() só cobre &/</> — sem isso um valor com `"` fecha o
        # atributo antes da hora (injeção de handler/atributo).
        return escape(v, {'"': "&quot;", "'": "&#39;"})

    PH = Namespace(PH_NS)
    SCHEMA = Namespace("https://schema.org/")
    DCT = Namespace("http://purl.org/dc/terms/")
    PROV = Namespace("http://www.w3.org/ns/prov#")

    g = Graph().parse(data=tours_text, format="turtle")

    tours = []
    for t in g.subjects(RDF.type, PH.Tour):
        date = g.value(t, DCT.date)
        try:
            dt = datetime.fromisoformat(str(date)) if date else None
        except ValueError:
            dt = None
        tours.append((dt, t))
    tours.sort(key=lambda x: _tour_date_sort_key(x[0]), reverse=True)

    items = []
    for dt, t in tours[:50]:
        title = _tour_display_title(g, t)

        ig = g.value(t, PH.linkInstagram)
        link = str(ig) if ig else SITE_URL

        # Métricas pós-pedal (sem energia — ela vai junto da rota no corpo).
        metrics = []

        energy_line = None
        kj = g.value(t, PH.energyEstimate)
        if kj is not None:
            try:
                kj_val = float(kj)
            except (TypeError, ValueError):
                # Forma legada (IRI de QuantityValue) ou lixo — não 500a o
                # feed inteiro por causa de um tour com dado malformado.
                kj_val = None
            if kj_val is not None:
                intensity = _intensity_for(kj_val)
                energy_line = (f"{kj_val:.0f} quilojaules"
                               + (f" ({intensity})" if intensity else ""))

        # <description>: resumo plano — fallback pra leitores que ignoram
        # content:encoded.
        desc = " · ".join(metrics + ([energy_line] if energy_line else [])) \
            or "Passeio do Pedal Hidrográfico."

        # <content:encoded>: corpo rico em HTML — arte do anúncio, narrativa,
        # rota + energia, métricas, elaboradores.
        html = []
        img = g.value(t, SCHEMA.image)
        if img:
            html.append(f'<p><img src="{attr_escape(str(img))}" '
                        f'alt="{attr_escape(title)}" style="max-width:100%"/></p>')
        narrative = g.value(t, DCT.description)
        if narrative:
            for para in re.split(r"\r?\n+", str(narrative).strip()):
                if para.strip():
                    html.append(f"<p>{escape(para.strip())}</p>")
        route_ref = g.value(t, PH.linkRoute)
        route_url = g.value(route_ref, SCHEMA.url) if route_ref else None
        route_block = []
        if route_url:
            u = escape(str(route_url))
            route_block.append(f'Rota: <a href="{attr_escape(str(route_url))}">{u}</a>')
        if energy_line:
            route_block.append(escape(energy_line))
        if route_block:
            html.append("<p>" + "<br/>".join(route_block) + "</p>")
        if metrics:
            html.append(f"<p>{escape(' · '.join(metrics))}</p>")
        authors = sorted(_person_name(g, p) for p in g.objects(t, PROV.wasAttributedTo))
        if authors:
            html.append(f"<p>Alguns elaboradores: {escape(', '.join(authors))}</p>")
        # "]]>" dentro de CDATA encerraria a seção — quebra o token em duas.
        content = "\n".join(html).replace("]]>", "]]]]><![CDATA[>")

        # guid ESTÁVEL (F4): p/ passeios migrados emite o IRI legado
        # (phd:tour_<numid>), que é opaco e permanente — assim a troca do IRI
        # pra pas:<slug> não faz todos os itens reaparecerem como novos no RSS.
        _slug = str(t)[len(PAS_NS):] if str(t).startswith(PAS_NS) else None
        guid = (_legacy_tour_iri(_slug) if _slug else None) or str(t)

        items.append(
            "    <item>\n"
            f"      <title>{escape(title)}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid isPermaLink=\"false\">{escape(guid)}</guid>\n"
            + (f"      <pubDate>{format_datetime(dt)}</pubDate>\n" if dt else "")
            + f"      <description>{escape(desc)}</description>\n"
            + (f"      <content:encoded><![CDATA[{content}]]></content:encoded>\n"
               if content else "")
            + "    </item>"
        )

    newest = next((dt for dt, _ in tours if dt), None)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:webfeeds="http://webfeeds.org/rss/1.0">\n'
        "  <channel>\n"
        "    <title>Passeios Pedal Hidrográfico</title>\n"
        f"    <link>{escape(SITE_URL)}</link>\n"
        "    <description>Passeios do coletivo de ciclismo urbano Pedal "
        "Hidrográfico na Grande São Paulo — rotas, fotos e histórias.</description>\n"
        "    <language>pt-br</language>\n"
        f"    <atom:link href=\"{escape(SITE_URL)}feed.xml\" rel=\"self\" "
        "type=\"application/rss+xml\"/>\n"
        # Logo do canal — derivado 144px de web/logo-phidro.jpg (o original
        # de 3543px/5MB pesaria nos leitores de feed; o spec do RSS 2.0
        # limita a largura a 144 de todo jeito). Título deve casar com o
        # do canal.
        "    <image>\n"
        f"      <url>{escape(SITE_URL)}logo-phidro-144.jpg</url>\n"
        "      <title>Passeios Pedal Hidrográfico</title>\n"
        f"      <link>{escape(SITE_URL)}</link>\n"
        "      <width>144</width>\n"
        "      <height>144</height>\n"
        "    </image>\n"
        # A maioria dos leitores modernos IGNORA o <image> do RSS 2.0 e usa
        # a extensão webfeeds (Feedly & cia) ou o favicon do domínio do
        # <link>. O webfeeds:icon cobre o primeiro grupo; derivado 512px
        # (buscado uma vez só pelo agregador, peso importa menos).
        f"    <webfeeds:icon>{escape(SITE_URL)}logo-phidro-512.jpg</webfeeds:icon>\n"
        f"    <webfeeds:accentColor>0f1721</webfeeds:accentColor>\n"
        + (f"    <lastBuildDate>{format_datetime(newest)}</lastBuildDate>\n" if newest else "")
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )


@app.get("/feed.xml")
def get_feed():
    """Feed RSS 2.0 dos passeios, derivado de tours.ttl (50 mais recentes).

    Cada item: título + data do tour, link pro post do IG quando houver
    (senão a home), métricas no description e a arte de anúncio quando o
    tour tiver schema:image. ETag igual aos demais mutáveis — leitores de
    feed revalidam de graça."""
    import hashlib
    text = _tours_with_identities_text()
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    with _feed_lock:
        if _feed_cache["digest"] != digest:
            _feed_cache["xml"] = _build_feed_xml(text)
            _feed_cache["digest"] = digest
        xml = _feed_cache["xml"]
    return _conditional(Response(xml, mimetype="application/rss+xml",
                                 headers={"Cache-Control": "no-cache"}))


# Sitemap dinâmico (sobrepõe o web/sitemap.xml estático, que fica como
# fallback de host estático): home + uma URL por passeio (/?tour=<id> — o
# app abre o modal da rota via deep link). Passeios com data nas últimas
# 48 h ganham o bloco <news:news> do Google News; o cache expira em 1 h
# pra essa janela deslizar mesmo sem mudança no tours.ttl.
_NEWS_WINDOW_S = 48 * 3600
_sitemap_cache = {"digest": None, "xml": None, "built_at": None}


def _build_sitemap_xml(tours_text):
    from xml.sax.saxutils import escape
    from rdflib import Graph, Namespace, RDF

    PH = Namespace(PH_NS)
    DCT = Namespace("http://purl.org/dc/terms/")

    tours = []
    if tours_text:
        g = Graph().parse(data=tours_text, format="turtle")
        for t in g.subjects(RDF.type, PH.Tour):
            date = g.value(t, DCT.date)
            try:
                dt = datetime.fromisoformat(str(date)) if date else None
            except ValueError:
                dt = None
            tour_id = str(t)[len(PAS_NS):] if str(t).startswith(PAS_NS) else str(t).rsplit("/", 1)[-1]
            title = str(g.value(t, DCT.title) or tour_id).strip()
            tours.append((dt, tour_id, title))
    tours.sort(key=lambda x: _tour_date_sort_key(x[0]), reverse=True)

    now = datetime.now(timezone.utc)
    urls = [
        "  <url>\n"
        f"    <loc>{escape(SITE_URL)}</loc>\n"
        "    <changefreq>weekly</changefreq>\n"
        "  </url>"
    ]
    for dt, tour_id, title in tours:
        lines = ["  <url>",
                 f"    <loc>{escape(f'{SITE_URL}?tour={tour_id}')}</loc>"]
        if dt:
            lines.append(f"    <lastmod>{dt.date().isoformat()}</lastmod>")
            # Google News só considera artigos das últimas ~48 h; usamos a
            # data do passeio como publication_date (anúncios futuros dentro
            # da janela também entram — o |Δ| cobre os dois lados).
            if (dt.tzinfo is not None
                    and abs((now - dt.astimezone(timezone.utc)).total_seconds())
                    < _NEWS_WINDOW_S):
                lines.append(
                    "    <news:news>\n"
                    "      <news:publication>\n"
                    "        <news:name>Pedal Hidrográfico</news:name>\n"
                    "        <news:language>pt</news:language>\n"
                    "      </news:publication>\n"
                    f"      <news:publication_date>{escape(dt.isoformat())}</news:publication_date>\n"
                    f"      <news:title>{escape(title)}</news:title>\n"
                    "    </news:news>"
                )
        lines.append("  </url>")
        urls.append("\n".join(lines))

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "\n".join(urls) + "\n"
        "</urlset>\n"
    )


@app.get("/sitemap.xml")
def get_sitemap():
    """Sitemap (com extensão Google News) renderizado de tours.ttl.

    Mesma mecânica de cache do feed, mais um TTL de 1 h porque o bloco
    de news depende do relógio, não só do conteúdo do catálogo."""
    import hashlib
    text = _load_dump_text("tours.ttl") or ""
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    with _feed_lock:
        stale = (_sitemap_cache["digest"] != digest
                 or _sitemap_cache["built_at"] is None
                 or (now - _sitemap_cache["built_at"]).total_seconds() > 3600)
        if stale:
            _sitemap_cache["xml"] = _build_sitemap_xml(text)
            _sitemap_cache["digest"] = digest
            _sitemap_cache["built_at"] = now
        xml = _sitemap_cache["xml"]
    return _conditional(Response(xml, mimetype="application/xml",
                                 headers={"Cache-Control": "no-cache"}))


# ── Página por passeio (SSR mínimo) ───────────────────────────────────────
# GET /?tour=<id> devolve o index.html com <title>/description/canonical/OG
# trocados pros do passeio, um JSON-LD NewsArticle e um <article> com o
# corpo renderizado de tours.ttl — é o que crawlers e bots de preview (que
# não rodam JS) leem. No browser o app abre o modal da rota (deep link) e
# remove o <article>; o conteúdo SSR fica abaixo do mapa (grid 100vh),
# então não pisca pra usuários com JS.
_tours_graph_cache = {"digest": None, "graph": None}

_MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
              "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _tours_graph():
    """Grafo parseado de tours.ttl + identities.ttl (autoria via
    prov:wasAttributedTo resolve nome de pessoa — ver _tours_with_identities_text),
    cacheado por hash do texto (parsear ~100 KB de Turtle por request seria o
    custo dominante da página)."""
    import hashlib
    from rdflib import Graph
    text = _tours_with_identities_text()
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    with _feed_lock:
        if _tours_graph_cache["digest"] != digest:
            _tours_graph_cache["graph"] = Graph().parse(data=text, format="turtle")
            _tours_graph_cache["digest"] = digest
        return _tours_graph_cache["graph"]


def _render_tour_index(tour_id):
    """index.html com meta/OG/JSON-LD/<article> do passeio — None se o
    tour não existe no catálogo."""
    import json
    import re
    from html import escape as h
    from rdflib import Namespace, RDF, URIRef

    PH = Namespace(PH_NS)
    SCHEMA = Namespace("https://schema.org/")
    DCT = Namespace("http://purl.org/dc/terms/")
    PROV = Namespace("http://www.w3.org/ns/prov#")

    g = _tours_graph()
    t = URIRef(PAS_NS + tour_id)
    if (t, RDF.type, PH.Tour) not in g:
        return None

    title = _tour_display_title(g, t)
    page_url = f"{SITE_URL}?tour={tour_id}"

    date = g.value(t, DCT.date)
    try:
        dt = datetime.fromisoformat(str(date)) if date else None
    except ValueError:
        dt = None
    date_label = f"{dt.day} de {_MONTHS_PT[dt.month - 1]} de {dt.year}" if dt else None

    narrative = str(g.value(t, DCT.description) or "").strip()
    img = g.value(t, SCHEMA.image)
    img_url = str(img) if img else None

    energy_line = None
    kj = g.value(t, PH.energyEstimate)
    if kj is not None:
        try:
            kj_val = float(kj)
        except (TypeError, ValueError):
            # Forma legada (IRI de QuantityValue) ou lixo — não derruba o
            # SSR do passeio inteiro por causa de um dado malformado.
            kj_val = None
        if kj_val is not None:
            intensity = _intensity_for(kj_val)
            energy_line = (f"{kj_val:.0f} quilojaules"
                           + (f" ({intensity})" if intensity else ""))
    route_ref = g.value(t, PH.linkRoute)
    route_url = g.value(route_ref, SCHEMA.url) if route_ref else None
    ig_url = g.value(t, PH.linkInstagram)
    authors = sorted(_person_name(g, p) for p in g.objects(t, PROV.wasAttributedTo))

    # Descrição pra <meta>/OG: primeiro parágrafo da narrativa (truncado),
    # senão um resumo do que houver.
    if narrative:
        first = re.split(r"\r?\n+", narrative)[0].strip()
        meta_desc = first if len(first) <= 200 else first[:197].rstrip() + "…"
    else:
        bits = [b for b in (date_label, energy_line) if b]
        meta_desc = ("Passeio do Pedal Hidrográfico"
                     + (" — " + " · ".join(bits) if bits else "."))

    # <article> que o crawler lê (e quem está sem JS).
    a = ['<article id="tour-article" class="tour-article">',
         f"  <h1>{h(title)}</h1>"]
    meta_bits = []
    if dt:
        meta_bits.append(f'<time datetime="{h(dt.isoformat())}">{h(date_label)}</time>')
    meta_bits.append("Pedal Hidrográfico")
    a.append('  <p class="tour-article-meta">' + " · ".join(meta_bits) + "</p>")
    if img_url:
        a.append(f'  <figure><img src="{h(img_url)}" alt="{h(title)}"/></figure>')
    for para in re.split(r"\r?\n+", narrative):
        if para.strip():
            a.append(f"  <p>{h(para.strip())}</p>")
    facts = []
    if route_url:
        facts.append(f'Rota: <a href="{h(str(route_url))}">{h(str(route_url))}</a>')
    if energy_line:
        facts.append(h(energy_line))
    if ig_url:
        facts.append(f'<a href="{h(str(ig_url))}">Post no Instagram</a>')
    if facts:
        a.append("  <p>" + "<br/>".join(facts) + "</p>")
    if authors:
        a.append(f"  <p>Alguns elaboradores: {h(', '.join(authors))}</p>")
    a.append(f'  <p><a href="{h(SITE_URL)}">← mapa do Pedal Hidrográfico</a></p>')
    a.append("</article>")
    article = "\n".join(a)

    jsonld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "mainEntityOfPage": page_url,
        "url": page_url,
        "inLanguage": "pt-BR",
        "publisher": {
            "@type": "Organization",
            "name": "Pedal Hidrográfico",
            "url": "https://pedalhidrografi.co/",
            "logo": {"@type": "ImageObject",
                     "url": f"{SITE_URL}logo-phidro-512.jpg"},
        },
    }
    if dt:
        jsonld["datePublished"] = dt.isoformat()
        jsonld["dateModified"] = dt.isoformat()
    if img_url:
        jsonld["image"] = [img_url]
    if meta_desc:
        jsonld["description"] = meta_desc
    if authors:
        jsonld["author"] = [{"@type": "Person", "name": n} for n in authors]
    # Escapa &/</> pra um tour com "</script>" no título/narrativa não
    # fechar a tag e injetar markup no <head> (crawlers/preview bots não
    # têm o CSP da página pra segurar isso). & primeiro, senão o <
    # e > que a gente escreve depois seriam re-escapados.
    jsonld_body = (json.dumps(jsonld, ensure_ascii=False)
                   .replace("&", "\\u0026")
                   .replace("<", "\\u003c")
                   .replace(">", "\\u003e"))
    jsonld_tag = ('<script type="application/ld+json">'
                  + jsonld_body + "</script>")

    html_text = (WEB / "index.html").read_text(encoding="utf-8")

    def attr(pattern, value, text):
        # lambda no replacement: o valor pode conter '\' e '\1' literais.
        return re.sub(pattern, lambda m: m.group(1) + value + m.group(2),
                      text, count=1)

    full_title = f"{title} — amora · Pedal Hidrográfico"
    html_text = re.sub(r"<title>.*?</title>",
                       lambda m: f"<title>{h(full_title)}</title>",
                       html_text, count=1, flags=re.S)
    html_text = attr(r'(<meta name="description" content=")[^"]*(")',
                     h(meta_desc), html_text)
    html_text = attr(r'(<link rel="canonical" href=")[^"]*(")',
                     h(page_url), html_text)
    html_text = attr(r'(<meta property="og:title" content=")[^"]*(")',
                     h(full_title), html_text)
    html_text = attr(r'(<meta property="og:description" content=")[^"]*(")',
                     h(meta_desc), html_text)
    html_text = attr(r'(<meta property="og:url" content=")[^"]*(")',
                     h(page_url), html_text)
    if img_url:
        html_text = attr(r'(<meta property="og:image" content=")[^"]*(")',
                         h(img_url), html_text)
        # As dimensões fixas são do ícone 512×512 — não valem pra arte.
        html_text = re.sub(
            r'\s*<meta property="og:image:(?:width|height)" content="[^"]*" />',
            "", html_text)
    html_text = html_text.replace("</head>", "    " + jsonld_tag + "\n  </head>", 1)
    html_text = html_text.replace("</body>", article + "\n</body>", 1)
    return html_text


@app.get("/<path:p>")
def web_files(p):
    """Estáticos de web/ — inclui ./data/{shapes,ontology,tours}.ttl e tudo
    o que não é mutável. Os mutáveis (uploads, data_graphs, photos/*) têm
    handlers próprios acima e nunca caem aqui."""
    if (WEB / p).is_file():
        resp = send_from_directory(WEB, p)
        if p.endswith(".ttl") or p.endswith(".json"):
            resp.headers["Cache-Control"] = "no-cache"
        return resp
    abort(404)


# NOTA: este handler NÃO usa @serialized (ao contrário de /upload-video e do
# Tour CRUD). O _state_lock global serializaria TAMBÉM a transferência do corpo
# (originais de vários MB) e as gravações de blob — fazendo um lote de N fotos
# subir estritamente em série. Aqui o trabalho é dividido por lock:
#  - transferência do corpo (Werkzeug faz o parse do multipart no 1º acesso a
#    request.form/files) e gravação dos 3 blobs no store: FORA de qualquer lock
#    (I/O — solta o GIL; sobrepõe entre requests concorrentes + com o cliente
#    mandando vários em voo);
#  - validação SHACL: sob _validate_lock (pyshacl não é thread-safe e é CPU-
#    bound — serializada à parte, sem travar o RMW);
#  - read-modify-write do catálogo: sob _state_lock (curto), com re-checagem
#    TOCTOU da colisão cross-type. Mesmo espírito do fetch RWGPS do Tour CRUD.
# Seguro porque validate_image_ttl só LÊ o snapshot cacheado (nunca o muta), as
# keys de blob são content-addressed por phash (idempotentes) e o upsert lê
# images.ttl fresco sob o lock.
@app.post("/upload-image")
def upload_image():
    # `ttl` pode vir como campo de formulário ou como arquivo. (O acesso a
    # request.form/files aqui dispara a transferência/parse do corpo inteiro —
    # de propósito FORA dos locks, pra sobrepor entre uploads concorrentes.)
    ttl_text = request.form.get("ttl")
    if not ttl_text:
        f = request.files.get("ttl")
        if f:
            ttl_text = f.read().decode("utf-8", errors="replace")
    if not ttl_text:
        return jsonify(error="ttl ausente"), 400

    # Validação FORA do _state_lock. O parse/merge (por-call, local) roda
    # concorrente; só a chamada pyshacl.validate() lá dentro serializa sob
    # _validate_lock (thread-safety) — compartilhado com vídeo/tour.
    try:
        ok, phash, errors = validate_image_ttl(ttl_text)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"parse: {e}"), 400
    if not ok:
        return jsonify(error="shacl", details=errors, phash=phash), 400

    # Variantes — pelo menos uma é obrigatória. Blobs gravados FORA do lock
    # (keys content-addressed por phash — idempotente).
    written = []
    for variant in ("original", "large", "thumb"):
        f = request.files.get(variant)
        if not f:
            continue
        # `large` e `thumb` são sempre re-encodadas em JPEG; `original`
        # preserva extensão (heic/png/jpg).
        if variant == "original":
            ext = (os.path.splitext(f.filename or "")[1].lstrip(".") or "jpg").lower()
            if ext not in ("jpg", "jpeg", "png", "heic", "heif"):
                ext = "jpg"
            if ext == "jpeg":
                ext = "jpg"
        else:
            ext = "jpg"
        key = f"photos/{phash}/{variant}.{ext}"
        # MIME por extensão; deixamos o store inferir se ausente.
        ct = {
            "jpg": "image/jpeg", "png": "image/png",
            "heic": "image/heic", "heif": "image/heif",
        }.get(ext)
        data = f.read()
        STORE.write_bytes(key, data, content_type=ct)
        written.append(f"{variant}.{ext}")
    if not written:
        return jsonify(error="nenhuma variante de imagem enviada"), 400

    def _cleanup_orphans():
        # Blobs já gravados sem triples = órfãos invisíveis. Limpa best-effort
        # (re-upload regrava as mesmas keys de qualquer jeito).
        try:
            STORE.delete_prefix(f"photos/{phash}/")
        except Exception as e2:  # noqa: BLE001
            print(f"[upload-image] aviso limpando órfãos de {phash}: {e2}")

    # Single-file mode: upsert no images.ttl, deduplicando por phash. Só o RMW do
    # catálogo é serializado (sob _state_lock); o timestamp da activity é gerado
    # aqui dentro pra garantir IRI única entre uploads concorrentes.
    from rdflib import RDF as _RDF, URIRef as _URIRef
    _img_uri = _URIRef(MED_NS + phash)
    _motion = _URIRef(PH_NS + "MotionImage")
    collision = False
    upload_local = None
    try:
        with _state_lock:
            # Re-checagem TOCTOU: a colisão cross-type foi checada na validação
            # FORA do lock — re-confere contra o catálogo ATUAL antes de gravar.
            if (_img_uri, _RDF.type, _motion) in _load_catalog():
                collision = True
            else:
                upload_local = _upload_filename()[:-len(".ttl")]   # phd:upload_TIMESTAMP
                audit_block  = _build_audit_ttl(upload_local, phash)
                upsert_image_in_uploads(ttl_text, phash, audit_block)
                _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        _cleanup_orphans()
        return jsonify(
            error=f"persistência ttl: {e}", phash=phash, files=written,
        ), 500
    if collision:
        _cleanup_orphans()
        return jsonify(
            error=f"colisão: med:{phash} já existe como VÍDEO (ph:MotionImage) — "
                  f"phash colidiu com um vhash.", phash=phash,
        ), 409
    print(f"[upload-image] phash={phash} files={written} activity={upload_local}")
    return jsonify(phash=phash, files=written, activity=upload_local, ok=True)


def validate_video_ttl(ttl_text):
    """Espelha validate_image_ttl pra ph:Video: verifica que tem exatamente
    1 ph:Video com IRI phd:video_<vhash16>, e dispara SHACL contra shapes+
    ontology+catálogo (catálogo é mesclado MENOS os triples do próprio vídeo
    em curso, pra que re-uploads não disparem violações de cardinalidade).
    Retorna (ok, vhash, errors)."""
    v = _load_validator()
    from rdflib import URIRef, Namespace
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    videos = list(data.subjects(RDFT, URIRef(PH_NS + "MotionImage")))
    if len(videos) != 1:
        return False, None, [
            f"TTL deve conter exatamente 1 ph:Video (achou {len(videos)})"
        ]
    video_iri = str(videos[0])
    # IRI opaco med:<hash> (tipo vem da CLASSE, não do prefixo).
    if not video_iri.startswith(MED_NS):
        return False, None, [
            f"IRI do Video deve começar com med: (atual: {video_iri})"
        ]
    vhash = video_iri[len(MED_NS):]
    if len(vhash) != 16 or not all(c in "0123456789abcdef" for c in vhash.lower()):
        return False, vhash, [f"vhash inválido na IRI (esperado 16 hex): {vhash}"]

    vid_uri = URIRef(video_iri)
    catalog = _load_catalog()
    # Guarda de colisão CROSS-TYPE: vhash igual a um phash existente viraria o
    # MESMO IRI. Rejeita antes de sobrescrever a foto.
    if (vid_uri, RDFT, URIRef(PH_NS + "StillImage")) in catalog:
        return False, vhash, [
            f"colisão: med:{vhash} já existe como FOTO (ph:StillImage) — "
            f"vhash colidiu com um phash. Não dá pra reusar o IRI."
        ]
    # Exclui o próprio sujeito + seus nós derivados (locationCreated).
    exclude = {vid_uri} | _derived_subjects(catalog, vid_uri)
    merged = data + v["ont"]
    for s, p, o in catalog:
        if s not in exclude:
            merged.add((s, p, o))
    with _validate_lock:   # pyshacl não é thread-safe (parser SPARQL) — ver _validate_lock
        conforms, results_graph, _txt = v["pyshacl"].validate(
            merged, shacl_graph=v["shapes"], inference="rdfs", advanced=True)
    if conforms:
        return True, vhash, []

    own_subjects = set(data.subjects())
    SH = Namespace("http://www.w3.org/ns/shacl#")
    errors = []
    for r in results_graph.subjects(SH.resultSeverity, SH.Violation):
        focus = next(results_graph.objects(r, SH.focusNode), None)
        if focus is None or focus in own_subjects:
            msg = next(results_graph.objects(r, SH.resultMessage), None)
            errors.append(str(msg) if msg else "(sem mensagem)")
    if not errors:
        return True, vhash, []
    return False, vhash, errors


@app.post("/upload-video")
@serialized
def upload_video():
    """Recebe um clipe já processado no browser:
      - `audio`     : opus dentro de webm (sempre presente, alta qualidade)
      - `video360`  : webm 360p sem trilha de áudio (opcional, audio-only mode)
      - `video720`  : webm 720p sem trilha de áudio (opcional, audio-only mode)
      - `ttl`       : TTL auto-suficiente com 1 ph:Video e seus metadados
      - `id`        : pHash de vídeo (16 hex)
    Valida com SHACL (ph:VideoShape), persiste os arquivos em `clips/<id>.*`
    e mescla os triples no único `data/uploads.ttl` (que serve imagens E
    vídeos — o tipo vem da CLASSE StillImage/MotionImage, não do IRI)."""
    ttl_text = request.form.get("ttl")
    if not ttl_text:
        f = request.files.get("ttl")
        if f:
            ttl_text = f.read().decode("utf-8", errors="replace")
    if not ttl_text:
        return jsonify(error="ttl ausente"), 400

    vid_id = (request.form.get("id") or "").strip().lower()
    if not vid_id or len(vid_id) != 16 or not all(c in "0123456789abcdef" for c in vid_id):
        return jsonify(error="id inválido (esperado vhash de 16 hex)"), 400

    # Audio é obrigatório (a SHACL VideoShape exige ph:audio).
    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify(error="audio ausente (sempre obrigatório)"), 400

    # Valida antes de gravar — evita lixo em disco se o TTL não bate com a id.
    # Wrap igual ao upload_image: um TTL malformado faz o parse de
    # validate_video_ttl levantar, e sem isto virava 500 em vez de 400 limpo.
    try:
        ok, vhash, errors = validate_video_ttl(ttl_text)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"parse: {e}"), 400
    if not ok and not vhash:
        return jsonify(error="; ".join(errors)), 400
    if vhash != vid_id:
        return jsonify(error=f"id (form) {vid_id} != vhash (ttl) {vhash}"), 400
    if not ok:
        return jsonify(error="SHACL violations", details=errors), 422

    # Grava: audio.webm sempre; webms só se vieram (audio-only mode); thumb
    # opcional (mas o app espera ele pra renderizar o marker como photo-style).
    written = []
    audio_key = f"clips/{vid_id}.audio.webm"
    STORE.write_bytes(audio_key, audio_file.read(), content_type="audio/webm")
    written.append(audio_key)
    thumb_file = request.files.get("thumb")
    if thumb_file:
        thumb_key = f"clips/{vid_id}.thumb.jpg"
        STORE.write_bytes(thumb_key, thumb_file.read(), content_type="image/jpeg")
        written.append(thumb_key)
    for form_field, key_suffix in (("video360", "360p.webm"), ("video720", "720p.webm")):
        f = request.files.get(form_field)
        if not f:
            continue
        key = f"clips/{vid_id}.{key_suffix}"
        STORE.write_bytes(key, f.read(), content_type="video/webm")
        written.append(key)

    # Persiste TTL em uploads.ttl — mesma file dos uploads de imagem. Dedup
    # por IRI (re-upload sobrescreve triples antigos do mesmo vhash).
    try:
        from rdflib import URIRef, Graph as RdfGraph
        vid_iri = URIRef(MED_NS + vid_id)
        existing_text = STORE.read_text(KEY_IMAGES) or ""
        catalog = RdfGraph()
        if existing_text:
            catalog.parse(data=existing_text, format="turtle")
        _purge_subject(catalog, vid_iri)   # vídeo + nós derivados (geo)
        catalog.parse(data=ttl_text, format="turtle")
        _route_new_persons(catalog)        # autora nova → identities.ttl
        _route_new_collections(catalog)    # lista nova inline → lists.ttl
        STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        # Limpa os blobs recém-gravados (órfãos sem triples) — best-effort.
        for key in written:
            try:
                STORE.delete(key)
            except Exception as e2:  # noqa: BLE001
                print(f"[upload-video] aviso limpando órfão {key}: {e2}")
        return jsonify(error=f"persistência ttl: {e}", id=vid_id, files=written), 500

    print(f"[upload-video] id={vid_id} files={written}")
    return jsonify(id=vid_id, files=written, ok=True)


def remove_video_from_uploads(vhash):
    """Lê os caminhos dos arquivos do vídeo, purga triples (vídeo + bnodes
    alcançáveis), persiste, e devolve (paths, n_triples) — pra que o caller
    delete os blobs no STORE."""
    existing = STORE.read_text(KEY_IMAGES)
    if not existing:
        return [], 0
    from rdflib import URIRef
    v = _load_validator()
    vid_iri = URIRef(MED_NS + vhash)
    catalog = v["Graph"]()
    catalog.parse(data=existing, format="turtle")
    SCHEMA = "https://schema.org/"
    paths = []
    for pred in (PH_NS + "audio", PH_NS + "video360p", PH_NS + "video720p",
                 SCHEMA + "thumbnail"):
        for o in catalog.objects(vid_iri, URIRef(pred)):
            paths.append(str(o))
    n = _purge_subject(catalog, vid_iri)
    STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))
    return paths, n


@app.post("/delete-video/<vhash>")
@serialized
def delete_video(vhash):
    vhash = (vhash or "").strip().lower()
    if not vhash or len(vhash) != 16 or not all(c in "0123456789abcdef" for c in vhash):
        return jsonify(error="vhash inválido"), 400
    try:
        paths, removed_triples = remove_video_from_uploads(vhash)
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"persistência ttl: {e}", vhash=vhash), 500
    removed_files = 0
    for rel in paths:
        # `rel` é relativo a web/clips/ (ex.: "audio/IMG_X.m4a", "IMG_X.360p.mp4").
        # Vem do TTL armazenado (que qualquer cliente pode ter escrito — não
        # há auth), então sanitiza: um valor tipo "../app.js" viraria
        # web/app.js, dentro do root do store, e seria apagado de verdade.
        rel = str(rel).strip()
        if (not rel or rel.startswith(("/", "\\")) or "\\" in rel
                or ".." in rel.split("/") or "://" in rel):
            print(f"[delete-video] caminho suspeito ignorado: {rel!r}")
            continue
        key = f"clips/{rel}"
        try:
            STORE.delete(key)
            removed_files += 1
        except Exception as e:  # noqa: BLE001
            print(f"[delete-video] aviso ao remover {key}: {e}")
    print(f"[delete-video] vhash={vhash} files={removed_files} triples={removed_triples}")
    return jsonify(vhash=vhash, files=removed_files, triples=removed_triples)


@app.post("/delete-image/<phash>")
@serialized
def delete_image(phash):
    phash = (phash or "").strip().lower()
    if len(phash) != 16 or not all(c in "0123456789abcdef" for c in phash):
        return jsonify(error="phash inválido (esperado 16 hex)"), 400
    prefix = f"photos/{phash}/"
    removed_files = len(STORE.list_keys(prefix)) if hasattr(STORE, "list_keys") else 0
    # Triples primeiro, blobs depois (mesma ordem do delete-video): se a
    # purga do TTL falhar, os arquivos ainda existem e o catálogo continua
    # consistente — um retry conserta. Na ordem inversa, uma falha deixava
    # markers apontando pra imagens já apagadas (404 permanente).
    try:
        removed_triples = remove_image_from_uploads(phash)
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        return jsonify(
            error=f"persistência ttl: {e}", phash=phash, files=0,
        ), 500
    try:
        STORE.delete_prefix(prefix)
    except Exception as e:  # noqa: BLE001
        print(f"[delete-image] erro removendo {prefix}: {e}")
    print(f"[delete-image] phash={phash} files={removed_files} triples={removed_triples}")
    return jsonify(phash=phash, files=removed_files, triples=removed_triples)


def _do_update_media(kind, hash_):
    """Handler compartilhado de /update-image e /update-video: patch de
    metadados por-predicado (mode=patch), SEM reenvio de blobs. `kind` =
    'image'|'video'. Body: `ttl` (predicados alterados + eventuais
    schema:Collection inline) + `remove` (CURIEs de predicados a limpar)."""
    from rdflib import URIRef
    hash_ = (hash_ or "").strip().lower()
    if len(hash_) != 16 or not all(c in "0123456789abcdef" for c in hash_):
        return jsonify(error=f"{kind} hash inválido (esperado 16 hex)"), 400
    ttl_text = request.form.get("ttl")
    if not ttl_text:
        f = request.files.get("ttl")
        if f:
            ttl_text = f.read().decode("utf-8", errors="replace")
    if not ttl_text:
        return jsonify(error="ttl ausente"), 400

    media_iri = MED_NS + hash_
    cls_local = "StillImage" if kind == "image" else "MotionImage"
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    if (URIRef(media_iri), RDFT, URIRef(PH_NS + cls_local)) not in _load_catalog():
        return jsonify(error=f"{kind} não encontrado: {hash_}"), 404

    try:
        remove_preds = _expand_remove_preds(request.form.get("remove", ""))
        result_ttl = synthesize_media_patch(media_iri, ttl_text, remove_preds)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"patch: {e}"), 400

    validator = validate_image_ttl if kind == "image" else validate_video_ttl
    try:
        ok, _hash, errors = validator(result_ttl)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"parse: {e}"), 400
    if not ok:
        return jsonify(error="shacl", details=errors), 400

    try:
        upsert_media_node(media_iri, result_ttl)
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"persistência ttl: {e}"), 500
    print(f"[update-{kind}] {hash_} remove={request.form.get('remove','')!r}")
    return jsonify(ok=True, **{("phash" if kind == "image" else "vhash"): hash_})


@app.post("/update-image/<phash>")
@serialized
def update_image(phash):
    return _do_update_media("image", phash)


@app.post("/update-video/<vhash>")
@serialized
def update_video(vhash):
    return _do_update_media("video", vhash)


@app.post("/assign-media-lists")
@serialized
def assign_media_lists():
    """Operação em lote de pertencimento a listas (galeria): adiciona/remove
    schema:isPartOf em várias mídias num único ciclo de lock. Body JSON:
    {iris:[...], add:[listIri...], remove:[listIri...], newLists:[{iri,name}...]}.
    Só toca phd:image_/phd:video_; add/remove/newLists só aceitam lst: (listas).
    Como isPartOf é a única aresta tocada (range schema:Collection, garantido
    pelas listas declaradas), o resultado é SHACL-válido por construção — não
    revalidamos cada nó (seria N validações no lote). As arestas isPartOf ficam
    em images.ttl; as Collections (defs de lista) vivem em lists.ttl."""
    from rdflib import URIRef, Literal
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="body JSON ausente/inválido"), 400
    iris = body.get("iris") or []
    add = body.get("add") or []
    remove = body.get("remove") or []
    new_lists = body.get("newLists") or []
    if not isinstance(iris, list) or not iris:
        return jsonify(error="iris vazio"), 400
    if not isinstance(add, list) or not isinstance(remove, list):
        return jsonify(error="add/remove devem ser listas"), 400

    LIST_PREFIX = LST_NS
    ISPARTOF = URIRef(SCHEMA_NS + "isPartOf")
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    COLLECTION = URIRef(SCHEMA_NS + "Collection")
    NAME = URIRef(SCHEMA_NS + "name")
    IMG_CLS = URIRef(PH_NS + "StillImage")
    VID_CLS = URIRef(PH_NS + "MotionImage")

    def _is_list(x):
        return isinstance(x, str) and x.startswith(LIST_PREFIX)
    def _is_media(x):
        # med:<16hex> — foto ou vídeo (o tipo vem da classe no catálogo).
        return isinstance(x, str) and x.startswith(MED_NS) and len(x[len(MED_NS):]) == 16
    if not all(_is_list(x) for x in add) or not all(_is_list(x) for x in remove):
        return jsonify(error="add/remove devem ser IRIs lst: (listas)"), 400
    for m in iris:
        if not _is_media(m):
            return jsonify(error=f"iri de mídia inválida: {m}"), 400

    v = _load_validator()
    Graph = v["Graph"]
    catalog = Graph()
    existing = STORE.read_text(KEY_IMAGES)
    if existing:
        catalog.parse(data=existing, format="turtle")
    # Listas (schema:Collection) vivem em lists.ttl — grafo à parte.
    lists_g = Graph()
    existing_lists = STORE.read_text(KEY_LISTS)
    if existing_lists:
        lists_g.parse(data=existing_lists, format="turtle")

    # Garante que as listas novas existam como schema:Collection em lists.ttl
    # (persistem como sujeitos à parte, iguais a pessoas em identities.ttl).
    lists_dirty = False
    for nl in new_lists:
        li = (nl or {}).get("iri")
        nm = (nl or {}).get("name")
        if not _is_list(li) or not nm:
            return jsonify(error=f"newList inválida: {nl}"), 400
        lu = URIRef(li)
        if (lu, RDFT, COLLECTION) not in lists_g:
            lists_g.add((lu, RDFT, COLLECTION))
            lists_g.add((lu, NAME, Literal(str(nm))))
            lists_dirty = True

    # Toda lista em `add` precisa existir como Collection (range de isPartOf).
    for li in add:
        if (URIRef(li), RDFT, COLLECTION) not in lists_g:
            return jsonify(error=f"lista inexistente (declare em newLists): {li}"), 400

    touched = 0
    for m in iris:
        mu = URIRef(m)
        if (mu, RDFT, IMG_CLS) not in catalog and (mu, RDFT, VID_CLS) not in catalog:
            continue   # mídia inexistente — pula (idempotente)
        for li in remove:
            catalog.remove((mu, ISPARTOF, URIRef(li)))
        for li in add:
            catalog.add((mu, ISPARTOF, URIRef(li)))
        touched += 1

    if lists_dirty:
        STORE.write_text(KEY_LISTS, lists_g.serialize(format="turtle"))
    STORE.write_text(KEY_IMAGES, catalog.serialize(format="turtle"))
    _invalidate_catalog()
    print(f"[assign-media-lists] iris={len(iris)} touched={touched} add={add} remove={remove}")
    return jsonify(ok=True, touched=touched)


@app.post("/update-person/<slug>")
@serialized
def update_person(slug):
    """Edita os metadados de uma pessoa em identities.ttl (fonte única).

    Pós-split, pessoas vivem SÓ em identities.ttl (tours/images apenas as
    referenciam). Form fields:
      - `alternateName` (obrigatório) — apelido/handle, o rótulo curto
      - `name` (opcional) — nome real (schema:name)
      - `url` (opcional) — página pessoal (schema:url)
      - `seeAlso` (opcional, repetível) — perfis/links relacionados
        (rdfs:seeAlso — Instagram, Mastodon, etc.; associa sem afirmar
        identidade, ao contrário de schema:sameAs)
    Reescreve só esses predicados; rdf:type e schema:mainEntityOfPage são
    preservados. url/seeAlso precisam ser http(s). Se a pessoa não existe mas é
    referenciada em algum catálogo, a definição é criada. O PersonShape é soft
    (não bloqueia). Sem routes.json, sem auth.
    """
    import re as _re
    from rdflib import URIRef, Literal
    slug = (slug or "").strip()
    if not slug or not all(c.isalnum() or c in "_-" for c in slug):
        return jsonify(error="slug inválido"), 400
    alt = (request.form.get("alternateName") or "").strip()
    real_name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    see_also = [u.strip() for u in request.form.getlist("seeAlso") if u.strip()]
    if not alt:
        return jsonify(error="alternateName ausente (apelido é obrigatório)"), 400
    if len(alt) > 200 or len(real_name) > 200:
        return jsonify(error="nome longo demais (máx. 200)"), 400
    for u in ([url] if url else []) + see_also:
        if not _re.match(r"^https?://", u):
            return jsonify(error=f"URL inválida (precisa http/https): {u}"), 400

    v = _load_validator()
    Graph = v["Graph"]
    person = URIRef(PES_NS + slug)
    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    # schema.org aparece nas duas formas (https/http) no acervo — trata ambas.
    PERSON_CLS = (URIRef(SCHEMA_NS + "Person"), URIRef("http://schema.org/Person"))
    def _sc(local):
        return (URIRef(SCHEMA_NS + local), URIRef("http://schema.org/" + local))
    ALT_P, NAME_P, URL_P = _sc("alternateName"), _sc("name"), _sc("url")
    SEEALSO = URIRef("http://www.w3.org/2000/01/rdf-schema#seeAlso")

    idg = Graph()
    text = _load_dump_text("identities.ttl")
    if text:
        idg.parse(data=text, format="turtle")
    defined = (any((person, RDFT, c) in idg for c in PERSON_CLS)
               or any((person, p, None) in idg for p in ALT_P))
    if not defined and (None, None, person) not in _load_catalog():
        # Nem definida em identities nem referenciada em lugar nenhum.
        return jsonify(error=f"pessoa desconhecida: {slug}"), 404

    def _clear(preds):
        for p in preds:
            for o in list(idg.objects(person, p)):
                idg.remove((person, p, o))
    _clear(ALT_P); idg.add((person, URIRef(SCHEMA_NS + "alternateName"), Literal(alt)))
    _clear(NAME_P)
    if real_name:
        idg.add((person, URIRef(SCHEMA_NS + "name"), Literal(real_name)))
    _clear(URL_P)
    if url:
        idg.add((person, URIRef(SCHEMA_NS + "url"), URIRef(url)))
    for o in list(idg.objects(person, SEEALSO)):
        idg.remove((person, SEEALSO, o))
    for u in see_also:
        idg.add((person, SEEALSO, URIRef(u)))
    if not any((person, RDFT, c) in idg for c in PERSON_CLS):
        idg.add((person, RDFT, URIRef(SCHEMA_NS + "Person")))
    STORE.write_text(KEY_IDENTITIES, idg.serialize(format="turtle"))
    _invalidate_catalog()
    print(f"[update-person] {slug} alt={alt!r} name={real_name!r} "
          f"url={bool(url)} seeAlso={len(see_also)}")
    return jsonify(ok=True, slug=slug, alternateName=alt, name=real_name,
                   url=url, seeAlso=see_also, files=["identities.ttl"])


@app.post("/upload-tour")
def upload_tour():
    """Cria/atualiza 1 ph:Tour em tours.ttl.

    Espera `ttl` (form field ou file) com exatamente 1 `pas:<slug> a ph:Tour`
    + opcionalmente declarações novas de `phd:assoc_*`, `phd:pessoa*`, etc.

    Dois modos (form field `mode`):
      - `replace` (padrão): o TTL é o estado COMPLETO do tour — purge-and-
        replace de todos os triples do IRI. Certo pra criação.
      - `patch`: merge-patch por predicado — só os predicados afirmados no
        TTL (mais os listados no form field `remove`, CURIEs/IRIs separados
        por vírgula) substituem os existentes; o resto do tour sobrevive
        intacto. Certo pra edição: o cliente não precisa round-tripar
        predicados que não conhece. Com `announcement`, o schema:image atual
        também é substituído pela URL fresca. O SHACL valida o estado final.

    Opcionalmente, `announcement` (file): salvo em
    `tour_assets/<tour_id>/announcement.<ext>` no store e injetado como
    `schema:image <URL>` no TTL antes de persistir.

    Depois de persistir, sincroniza routes.json: se o tour tem `ph:linkRoute`
    → RideWithGPS, busca a geometria e faz upsert da rota; senão remove a
    entrada órfã. O fetch (IO de rede) roda FORA do lock — por isso este
    handler não usa `@serialized` no corpo inteiro, só envolve a seção crítica
    (validação + escrita do tours.ttl) em `with _state_lock`.

    Sem auth — mesma política do resto da API.
    """
    ttl_text = request.form.get("ttl")
    if not ttl_text:
        f = request.files.get("ttl")
        if f:
            ttl_text = f.read().decode("utf-8", errors="replace")
    if not ttl_text:
        return jsonify(error="ttl ausente"), 400

    mode = (request.form.get("mode") or "replace").strip().lower()
    if mode not in ("replace", "patch"):
        return jsonify(error=f"mode inválido: {mode!r} (replace|patch)"), 400

    # Seção crítica: validação + announcement + escrita do tours.ttl, tudo
    # serializado. O fetch da rota acontece depois, sem o lock. O patch é
    # sintetizado aqui dentro (lê tours.ttl) pra não perder updates entre a
    # leitura do estado atual e a escrita do resultado.
    with _state_lock:
        if mode == "patch":
            ann = request.files.get("announcement")
            try:
                remove_preds = _expand_remove_preds(request.form.get("remove"))
                _tid, ttl_text = synthesize_tour_patch(
                    ttl_text, remove_preds,
                    replace_image=bool(ann and ann.filename))
            except ValueError as e:
                return jsonify(error=str(e)), 400
            except Exception as e:  # noqa: BLE001
                return jsonify(error=f"patch: {e}"), 400
        try:
            ok, tour_id, errors = validate_tour_ttl(ttl_text)
        except Exception as e:  # noqa: BLE001
            return jsonify(error=f"parse: {e}"), 400
        if not ok:
            return jsonify(error="shacl", details=errors, tour_id=tour_id), 400

        # Upload opcional do anúncio: salva no store e injeta `schema:image`.
        announcement_url = None
        f = request.files.get("announcement")
        if f and f.filename:
            ext = (os.path.splitext(f.filename or "")[1].lstrip(".") or "jpg").lower()
            if ext not in ("jpg", "jpeg", "png", "webp", "gif", "heic", "heif"):
                ext = "jpg"
            if ext == "jpeg":
                ext = "jpg"
            key = f"tour_assets/{tour_id}/announcement.{ext}"
            ct = {
                "jpg": "image/jpeg", "png": "image/png",
                "webp": "image/webp", "gif": "image/gif",
                "heic": "image/heic", "heif": "image/heif",
            }.get(ext, "application/octet-stream")
            try:
                STORE.write_bytes(key, f.read(), content_type=ct)
            except Exception as e:  # noqa: BLE001
                return jsonify(
                    error=f"persistência announcement: {e}", tour_id=tour_id,
                ), 500
            # URL ABSOLUTA obrigatoriamente: um caminho relativo
            # ("./tour_assets/…") injetado como IRI no TTL é resolvido pelo
            # rdflib contra o CWD do processo na re-serialização → vira
            # file:///… inutilizável.
            #
            # A ordem importa. `request.host_url` é o ÚLTIMO recurso porque ele
            # grava no catálogo o host pelo qual ESTE cliente chegou — e um
            # backend de desenvolvimento assa `http://localhost:8080/…` num
            # dado que depois sobe pra produção pelo `deploy-cloudrun.sh
            # --state` (foi o que aconteceu com o PH/96). Quem auto-hospeda
            # deve setar PUBLIC_BASE_URL com o host público de verdade.
            announcement_url = (
                STORE.public_url(key)
                or (PUBLIC_BASE_URL
                    and f"{PUBLIC_BASE_URL}/tour_assets/{tour_id}/announcement.{ext}")
                or (request.host_url.rstrip("/")
                    + f"/tour_assets/{tour_id}/announcement.{ext}"))
            # Injeta schema:image se ainda não estiver no TTL (cliente pode
            # ter posto um URL externo; respeitamos a escolha do cliente).
            # Checagem via triple (não substring): um TTL usando a IRI completa
            # `<https://schema.org/image>` passava no teste antigo de substring
            # `"schema:image" in ttl_text` e ganhava um image duplicado.
            from rdflib import Graph as _RdfGraph, URIRef as _URIRef
            _tour_uri = _URIRef(PAS_NS + tour_id)
            _img_preds = (_URIRef("https://schema.org/image"), _URIRef("http://schema.org/image"))
            try:
                _g = _RdfGraph().parse(data=ttl_text, format="turtle")
                _has_image = any((_tour_uri, p, None) in _g for p in _img_preds)
            except Exception:  # noqa: BLE001
                _has_image = "schema:image" in ttl_text  # fallback conservador
            if not _has_image:
                # IRI completa no subject: o TTL pode ser sintetizado pelo
                # mode=patch (serialização rdflib), que não garante o
                # prefixo pas: — a forma <...> é válida em qualquer doc.
                inject = (
                    f"\n# Imagem do anúncio (uploaded server-side)\n"
                    f"<{PAS_NS}{tour_id}> <https://schema.org/image> "
                    f"<{announcement_url}> .\n"
                )
                ttl_text = ttl_text + inject

        try:
            upsert_tour_in_tours_ttl(ttl_text, tour_id)
            _invalidate_catalog()
        except Exception as e:  # noqa: BLE001
            # Anúncio já gravado sem triples referenciando-o = órfão invisível.
            # Limpa best-effort (mesmo padrão do upload-image/upload-video).
            if f and f.filename:
                try:
                    STORE.delete(key)
                except Exception as e2:  # noqa: BLE001
                    print(f"[upload-tour] aviso limpando anúncio órfão de {tour_id}: {e2}")
            return jsonify(
                error=f"persistência ttl: {e}", tour_id=tour_id,
            ), 500

    # Fora do lock: sincroniza a geometria da rota (best-effort, IO de rede).
    # O try/except garante que NENHUMA falha aqui (import, storage, bug)
    # transforma um save bem-sucedido do tour em 500.
    try:
        route_status = _sync_tour_route(tour_id)
    except Exception as e:  # noqa: BLE001
        route_status = {"status": "error", "error": str(e)}
        print(f"[upload-tour] erro sincronizando routes.json: {e}")
    print(f"[upload-tour] tour_id={tour_id} announcement={announcement_url} "
          f"route={route_status.get('status')}")
    return jsonify(
        tour_id=tour_id, announcement_url=announcement_url,
        route=route_status, mode=mode, ok=True,
    )


@app.post("/delete-tour/<tour_id>")
@serialized
def delete_tour(tour_id):
    """Remove um ph:Tour (e seus bnodes) do tours.ttl + apaga seus assets
    (tour_assets/<id>/) do store. Não toca em pessoas/séries — git history
    preserva e elas podem ser referenciadas por outros tours."""
    tour_id = (tour_id or "").strip()
    if not tour_id or not all(c.isalnum() or c in "_-" for c in tour_id):
        return jsonify(error="tour_id inválido"), 400
    asset_prefix = f"tour_assets/{tour_id}/"
    removed_assets = len(STORE.list_keys(asset_prefix)) if hasattr(STORE, "list_keys") else 0
    # Triples primeiro, assets depois (mesma ordem do delete-image): se a
    # purga do TTL falhar, os assets ainda existem e `schema:image` continua
    # apontando pra algo válido — um retry conserta. Na ordem inversa, uma
    # falha deixava o tour com `schema:image` quebrado (assets já apagados)
    # até o próximo retry.
    try:
        removed_triples = remove_tour_from_tours_ttl(tour_id)
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        return jsonify(
            error=f"persistência ttl: {e}", tour_id=tour_id,
            assets=0,
        ), 500
    try:
        STORE.delete_prefix(asset_prefix)
    except Exception as e:  # noqa: BLE001
        print(f"[delete-tour] erro removendo {asset_prefix}: {e}")
    # Remove a entrada do tour de routes.json (sem IO de rede — lock curto).
    try:
        removed_routes = _remove_tour_route(tour_id)
    except Exception as e:  # noqa: BLE001
        removed_routes = 0
        print(f"[delete-tour] erro removendo rota de routes.json: {e}")
    print(f"[delete-tour] tour_id={tour_id} assets={removed_assets} "
          f"triples={removed_triples} routes={removed_routes}")
    return jsonify(tour_id=tour_id, assets=removed_assets,
                   triples=removed_triples, routes=removed_routes)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
