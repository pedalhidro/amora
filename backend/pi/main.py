"""
Pedal Hidrográfico — backend Flask.

Mesmo código serve dois alvos:

  STORAGE_BACKEND=local (padrão)  — Pi/dev: estado mutável no filesystem
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
  STORAGE_EMULATOR_HOST   p/ rodar contra fake-gcs-server localmente
                          (https://github.com/fsouza/fake-gcs-server)
"""
import functools
import json
import os
import threading
from pathlib import Path

from datetime import datetime, timezone
from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory

from storage import make_store_from_env

# ── Caminhos ─────────────────────────────────────────────────────────────
# WEB é o filesystem read-only do container/repo: HTML/JS/CSS/icons + os
# TTLs estáticos (shapes, ontology, tours). Resolve em duas tentativas:
#   1. Pi/dev: backend/pi/main.py → repo_root/web ( parents[2] / "web" )
#   2. Container: /app/main.py    → /app/web      ( parent  / "web" )
# `os.environ.get(k, default)` avalia `default` SEMPRE — não dá pra confiar
# em parents[2] cru porque dá IndexError no container.
def _default_web_path():
    here = Path(__file__).resolve()
    try:
        repo_layout = here.parents[2] / "web"
        if repo_layout.is_dir():
            return repo_layout
    except IndexError:
        pass
    return here.parent / "web"

WEB = Path(os.environ.get("PHIDRO_WEB") or _default_web_path()).resolve()
DATA_DIR      = WEB / "data"
SHAPES_PATH   = DATA_DIR / "shapes.ttl"
ONTOLOGY_PATH = DATA_DIR / "ontology.ttl"

# Store = estado mutável. Em modo local, raiz = PHIDRO_WEB (mesma layout
# que o Pi: data/uploads.ttl, photos/<phash>/...); em modo gcs, raiz é o
# bucket GCS. Os "keys" são strings relativas, mesmas em ambos os modos.
STORE = make_store_from_env(WEB)

# Keys de estado mutável (usados como `STORE.read_text(...)` etc.)
KEY_UPLOADS  = "data/uploads.ttl"
KEY_MANIFEST = "data/data_graphs.ttl"
KEY_TOURS    = "data/tours.ttl"
# routes.json é pré-bakado por scripts/build-routes.py mas também é atualizado
# incrementalmente aqui (upsert/remove de 1 rota por upload/delete de tour).
# Vira estado mutável: servido bucket-first, com o arquivo bakeado no
# container/repo como seed/fallback. Em modo local o root do STORE é `web/`,
# então isto grava o MESMO `web/routes.json` que o script — sem divergência.
KEY_ROUTES   = "routes.json"

# Credenciais do RideWithGPS pra buscar a geometria das rotas (privadas/
# unlisted exigem auth; públicas funcionam sem). Lidas de `os.environ` por
# `rwgps.decorate_rwgps`; carregamos o `.env` do repo best-effort pra que o
# Pi/dev local pegue as mesmas chaves que o build-routes.py usa.
try:  # python-dotenv é dep do build-routes; pode faltar no container slim.
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(WEB.parent / ".env")
except Exception:  # noqa: BLE001
    pass

VOID_NS = "http://rdfs.org/ns/void#"

PH_NS  = "https://pedalhidrografi.co/terms#"
PHD_NS = "https://pedalhidrografi.co/data/"

# Limite por requisição. Um upload de vídeo manda 360p + 720p (webm) +
# áudio + thumb num único multipart, então o teto precisa acomodar a soma.
# Override via env pra hosts com clipes mais longos.
MAX_PER_UPLOAD = int(os.environ.get("MAX_UPLOAD_BYTES") or (256 * 1024 * 1024))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_PER_UPLOAD

# Compressão transparente (gzip/brotli) — routes.json sai de ~2 MB pra
# ~210 KB e app.js de ~280 KB pra ~90 KB. Import best-effort (mesmo
# espírito do load do .env): um Pi que ainda não rodou pip install
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
          "(pip install -r backend/pi/requirements.txt)")


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


def serialized(fn):
    """Serializa o handler inteiro sob `_state_lock` (validação + escrita)."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with _state_lock:
            return fn(*args, **kwargs)
    return wrapper


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


def _invalidate_catalog():
    global _catalog_cache
    _catalog_cache = None


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


def _load_catalog():
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    v = _load_validator()
    Graph = v["Graph"]
    catalog = Graph()
    manifest_text = STORE.read_text(KEY_MANIFEST)
    if manifest_text is None:
        _catalog_cache = catalog
        return catalog
    manifest = Graph().parse(
        data=manifest_text, format="turtle", publicID=MANIFEST_BASE)
    from rdflib import URIRef
    pred = URIRef(VOID_NS + "dataDump")
    loaded = 0
    for _s, _p, o in manifest.triples((None, pred, None)):
        url = str(o)
        fname = url[len(MANIFEST_BASE):] if url.startswith(MANIFEST_BASE) \
                else url.rsplit("/", 1)[-1]
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


def validate_image_ttl(ttl_text):
    """Verifica que o TTL contém exatamente 1 ph:Image e satisfaz as shapes.
    Retorna (ok, phash, errors). `errors` traz só violations (warnings passam)
    cujo focusNode está no TTL recebido — ruído do catálogo (passeios velhos
    com warnings, etc.) não bloqueia o upload."""
    v = _load_validator()
    from rdflib import URIRef, Namespace
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    images = list(data.subjects(RDFT, URIRef(PH_NS + "Image")))
    if len(images) != 1:
        return False, None, [
            f"TTL deve conter exatamente 1 ph:Image (achou {len(images)})"
        ]
    image_iri = str(images[0])
    if not image_iri.startswith(PHD_NS + "image_"):
        return False, None, [
            f"IRI da Image deve começar com phd:image_ (atual: {image_iri})"
        ]
    phash = image_iri[len(PHD_NS + "image_"):]
    # phash é um pHash de 64 bits → exatamente 16 hex. Espelha o check do
    # video (len==16) pra que um cliente não consiga cunhar diretórios
    # photos/<phash>/ de tamanho arbitrário nem poluir o catálogo.
    if len(phash) != 16 or not all(c in "0123456789abcdef" for c in phash.lower()):
        return False, phash, [f"phash inválido na IRI (esperado 16 hex): {phash}"]

    # Mescla data + ontology + catálogo, MAS exclui triples do catálogo cujo
    # subject é a imagem em curso (ou bnodes alcançáveis a partir dela). Sem
    # isso, re-upload da mesma foto sobrepõe os triples antigos aos novos, e
    # SHACL flagra cardinalidade > 1 em `dcterms:date` etc.
    from rdflib import BNode
    img_uri = URIRef(image_iri)
    catalog = _load_catalog()
    # Coleta bnodes alcançáveis a partir da imagem (hash, locationCreated, …).
    img_bnodes = set()
    queue = [img_uri]
    while queue:
        cur = queue.pop()
        for _s, _p, o in catalog.triples((cur, None, None)):
            if isinstance(o, BNode) and o not in img_bnodes:
                img_bnodes.add(o)
                queue.append(o)
    exclude = img_bnodes | {img_uri}
    merged = data + v["ont"]
    for s, p, o in catalog:
        if s not in exclude:
            merged.add((s, p, o))
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


def _build_audit_ttl(upload_local, phash):
    """Bloco PROV server-side anexado ao TTL do upload."""
    ts = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    ts = ts.replace("+00:00", "Z")
    return (
        "\n# Registro de envio (provenance) — adicionado server-side.\n"
        "@prefix prov: <http://www.w3.org/ns/prov#> .\n"
        "@prefix ph:   <https://pedalhidrografi.co/terms#> .\n"
        "@prefix phd:  <https://pedalhidrografi.co/data/> .\n"
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .\n"
        "\n"
        f"phd:{upload_local} a ph:Upload ;\n"
        f"    prov:startedAtTime \"{ts}\"^^xsd:dateTime ;\n"
        f"    prov:generated phd:image_{phash} .\n"
    )


# Base estável e hierárquica para o manifesto. rdflib usa isto como o
# resolvido para `<>` e para `<tours.ttl>` etc., e na hora de serializar com
# `base=` essas URIs voltam a ser relativas — mantendo o arquivo limpo no
# disco. Precisa ser hierárquica (URN não serve por causa do RFC 3986).
MANIFEST_BASE = "https://pedalhidrografi.co/.manifest/"
MANIFEST_SEED = """\
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix void:    <http://rdfs.org/ns/void#> .

<> a void:Dataset ;
    dcterms:title "Pedal Hidrográfico — grafos de dados"@pt ;
    void:dataDump <tours.ttl> .
"""


def _load_manifest():
    """Devolve o Graph do manifesto; cria o esqueleto se faltando."""
    v = _load_validator()
    Graph = v["Graph"]
    g = Graph()
    text = STORE.read_text(KEY_MANIFEST)
    if text is not None:
        g.parse(data=text, format="turtle", publicID=MANIFEST_BASE)
    else:
        g.parse(data=MANIFEST_SEED, format="turtle", publicID=MANIFEST_BASE)
    return g


def _save_manifest(g):
    import re
    out = g.serialize(format="turtle", base=MANIFEST_BASE)
    out = re.sub(r'^@base\s+<[^>]*>\s*\.\s*\n', '', out, count=1, flags=re.MULTILINE)
    STORE.write_text(KEY_MANIFEST, out)


def _manifest_root():
    """O sujeito `<>` resolvido contra a base opaca."""
    from rdflib import URIRef
    return URIRef(MANIFEST_BASE)


def _manifest_uri(filename):
    from rdflib import URIRef
    return URIRef(MANIFEST_BASE + filename)


def register_upload_in_manifest(filename):
    """Adiciona `<> void:dataDump <filename>` ao manifesto (idempotente)."""
    from rdflib import URIRef
    g = _load_manifest()
    triple = (_manifest_root(), URIRef(VOID_NS + "dataDump"), _manifest_uri(filename))
    if triple not in g:
        g.add(triple)
        _save_manifest(g)
        _invalidate_catalog()


def unregister_upload_in_manifest(filename):
    """Remove a linha `void:dataDump <filename>` do manifesto."""
    if not STORE.exists(KEY_MANIFEST):
        return False
    from rdflib import URIRef
    g = _load_manifest()
    triple = (None, URIRef(VOID_NS + "dataDump"), _manifest_uri(filename))
    n = 0
    for s, p, o in list(g.triples(triple)):
        g.remove((s, p, o))
        n += 1
    if n:
        _save_manifest(g)
        _invalidate_catalog()
    return n > 0


def _purge_subject(graph, root):
    """Apaga triples cujo subject é `root` e bnodes alcançáveis a partir dele."""
    from rdflib import BNode
    seen, queue = set(), [root]
    while queue:
        cur = queue.pop()
        for _s, _p, o in graph.triples((cur, None, None)):
            if isinstance(o, BNode) and o not in seen:
                seen.add(o)
                queue.append(o)
    removed = 0
    for bn in seen:
        for s, p, o in list(graph.triples((bn, None, None))):
            graph.remove((s, p, o))
            removed += 1
    for s, p, o in list(graph.triples((root, None, None))):
        graph.remove((s, p, o))
        removed += 1
    return removed


PROV_GEN_URI = "http://www.w3.org/ns/prov#generated"


def upsert_image_in_uploads(image_ttl, phash, audit_ttl):
    """Mescla os blocos da imagem + da activity no único `uploads.ttl`,
    sobrescrevendo qualquer dado prévio para essa mesma imagem."""
    v = _load_validator()
    Graph = v["Graph"]
    from rdflib import URIRef
    image_iri = URIRef(PHD_NS + "image_" + phash)
    catalog = Graph()
    existing = STORE.read_text(KEY_UPLOADS)
    if existing:
        catalog.parse(data=existing, format="turtle")
    # 1) Tira da imagem (+ bnodes de hash/loc).
    _purge_subject(catalog, image_iri)
    # 2) Tira qualquer ph:Upload activity que tenha gerado essa imagem.
    for s in list(catalog.subjects(URIRef(PROV_GEN_URI), image_iri)):
        _purge_subject(catalog, s)
    # 3) Mescla os novos blocos (imagem + nova activity).
    catalog += Graph().parse(data=image_ttl + audit_ttl, format="turtle")
    STORE.write_text(KEY_UPLOADS, catalog.serialize(format="turtle"))


def remove_image_from_uploads(phash):
    """Remove triples da imagem + da sua activity de envio. Retorna nº de triples."""
    existing = STORE.read_text(KEY_UPLOADS)
    if not existing:
        return 0
    v = _load_validator()
    from rdflib import URIRef
    image_iri = URIRef(PHD_NS + "image_" + phash)
    catalog = v["Graph"]()
    catalog.parse(data=existing, format="turtle")
    n = _purge_subject(catalog, image_iri)
    for s in list(catalog.subjects(URIRef(PROV_GEN_URI), image_iri)):
        n += _purge_subject(catalog, s)
    STORE.write_text(KEY_UPLOADS, catalog.serialize(format="turtle"))
    return n


# ── Tour upserts ─────────────────────────────────────────────────────────
# Mesma mecânica de validação/merge das imagens, mas pra phd:tour_<id>
# e gravando em tours.ttl em vez de uploads.ttl. Pra dar suporte ao form
# upload_tour.html, que cria/edita 1 tour por vez.

def validate_tour_ttl(ttl_text):
    """Verifica que o TTL contém exatamente 1 ph:Tour e satisfaz TourShape.

    Retorna (ok, tour_id, errors). `tour_id` é o sufixo após `phd:tour_`.
    """
    v = _load_validator()
    from rdflib import URIRef, Namespace, BNode
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    tours = list(data.subjects(RDFT, URIRef(PH_NS + "Tour")))
    if len(tours) != 1:
        return False, None, [
            f"TTL deve conter exatamente 1 ph:Tour (achou {len(tours)})"
        ]
    tour_iri = str(tours[0])
    if not tour_iri.startswith(PHD_NS + "tour_"):
        return False, None, [
            f"IRI do Tour deve começar com phd:tour_ (atual: {tour_iri})"
        ]
    tour_id = tour_iri[len(PHD_NS + "tour_"):]
    if not tour_id:
        return False, tour_id, ["IRI do Tour vazio"]
    # Mesmo charset que delete_tour exige. Sem isso, um IRI completo tipo
    # <https://pedalhidrografi.co/data/tour_../x> passa (a forma full-IRI
    # aceita "/" e "."), e o tour_id vira componente de path no store
    # (tour_assets/<id>/...) — traversal pra qualquer lugar sob web/ — além
    # de criar tours que o delete-tour depois recusa.
    if not all(c.isalnum() or c in "_-" for c in tour_id):
        return False, None, [
            f"tour_id inválido (apenas [A-Za-z0-9_-]): {tour_id!r}"
        ]

    # Mescla com ontology + catálogo (excluindo o próprio tour pra evitar
    # cardinalidade falsa por sobreposição de re-upload).
    tour_uri = URIRef(tour_iri)
    catalog = _load_catalog()
    tour_bnodes = set()
    queue = [tour_uri]
    while queue:
        cur = queue.pop()
        for _s, _p, o in catalog.triples((cur, None, None)):
            if isinstance(o, BNode) and o not in tour_bnodes:
                tour_bnodes.add(o)
                queue.append(o)
    exclude = tour_bnodes | {tour_uri}
    merged = data + v["ont"]
    for s, p, o in catalog:
        if s not in exclude:
            merged.add((s, p, o))

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
    tour_iri = URIRef(PHD_NS + "tour_" + tour_id)
    catalog = Graph()
    existing = _load_dump_text("tours.ttl")
    if existing:
        catalog.parse(data=existing, format="turtle")
    _purge_subject(catalog, tour_iri)
    # Mescla os novos blocos (tour + eventual associação/pessoa nova).
    catalog += Graph().parse(data=tour_ttl, format="turtle")
    STORE.write_text(KEY_TOURS, catalog.serialize(format="turtle"))


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
    tour_iri = URIRef(PHD_NS + "tour_" + tour_id)
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
        meta = rwgps.tour_entry_from_graph(g, _URIRef(PHD_NS + "tour_" + tour_id))
    except Exception:  # noqa: BLE001
        return None
    return meta["id"] if meta else None


def _sync_tour_route(tour_id, tour_ttl):
    """Sincroniza a entrada de routes.json do tour `tour_id` com o estado atual.

    • Se o TTL do tour tem `ph:linkRoute` → RideWithGPS: busca a geometria
      (fora do lock) e faz upsert da entrada (keyed por tourIri).
    • Senão (sem linkRoute): remove qualquer entrada existente daquele tour.

    Best-effort: o caller (upload_tour) envolve a chamada em try/except — o
    tour já foi salvo no tours.ttl; uma falha aqui só significa que a
    geometria não entrou (re-rodar build-routes.py conserta). Retorna um
    dict de status pro handler reportar ao form.
    """
    import rwgps
    from rdflib import Graph as _RdfGraph, URIRef as _URIRef

    tour_iri = PHD_NS + "tour_" + tour_id
    try:
        g = _RdfGraph().parse(data=tour_ttl, format="turtle")
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

    # Fetch da geometria FORA do lock (IO de rede, pode demorar).
    entry = rwgps.build_route_entry(meta)

    with _state_lock:
        # Re-checa sob o lock: o tour ainda existe e ainda aponta pra MESMA
        # rota? Se não (deletado ou re-editado durante o fetch), descarta —
        # o estado vigente já foi/será sincronizado por quem o mudou.
        if _current_tour_route_id(tour_id) != entry["id"]:
            return {"status": "stale", "rwgpsId": entry["id"]}
        payload = _load_routes_payload()
        payload["routes"] = [r for r in payload["routes"] if r.get("tourIri") != tour_iri]
        payload["routes"].append(entry)
        _write_routes_payload(payload["routes"])

    if entry.get("latlngs"):
        return {"status": "ok", "rwgpsId": entry["id"], "points": len(entry["latlngs"])}
    return {"status": "fetch_failed", "rwgpsId": entry["id"], "error": entry.get("error")}


def _remove_tour_route(tour_id):
    """Remove a entrada de routes.json do tour (chamado no delete-tour).
    Retorna nº de entradas removidas. Sob lock curto (sem IO de rede)."""
    tour_iri = PHD_NS + "tour_" + tour_id
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
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/data/<filename>")
def get_data_ttl(filename):
    """Handler único pra /data/*.ttl — bucket-first, container fallback.

    Inclui os mutáveis (uploads.ttl, data_graphs.ttl) e os estáticos
    overrideables (shapes.ttl, ontology.ttl, tours.ttl). Quando o arquivo
    não existe em nenhum dos dois lugares, devolve um seed razoável pros
    dois mutáveis ou 404 pros demais.
    """
    # O converter padrão do Flask bloqueia "/" mas não um ".." solto —
    # `DATA_DIR / ".."` é um diretório existente e o read_text estourava
    # IsADirectoryError → 500 feio. Só servimos *.ttl de nome simples.
    if not filename.endswith(".ttl") or "/" in filename or ".." in filename:
        abort(404)
    text = _load_dump_text(filename)
    if text is None:
        if filename == "uploads.ttl":
            text = ""             # catálogo vazio — válido
        elif filename == "data_graphs.ttl":
            text = MANIFEST_SEED  # manifesto mínimo
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


# URL pública canônica — usada no feed RSS (links absolutos). Override por
# env pra quem servir o app em outro domínio.
SITE_URL = (os.environ.get("PUBLIC_BASE_URL")
            or "https://amora.pedalhidrografi.co").rstrip("/") + "/"

# Cache do XML do feed, chaveado pelo hash do tours.ttl — parsear 100 KB de
# Turtle por request seria caro no Pi; assim só re-renderiza quando o
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


def _build_feed_xml(tours_text):
    from email.utils import format_datetime
    from xml.sax.saxutils import escape
    from rdflib import Graph, Namespace, RDF

    PH = Namespace(PH_NS)
    SCHEMA = Namespace("https://schema.org/")
    DCT = Namespace("http://purl.org/dc/terms/")

    g = Graph().parse(data=tours_text, format="turtle")
    tours = []
    for t in g.subjects(RDF.type, PH.Tour):
        date = g.value(t, DCT.date)
        try:
            dt = datetime.fromisoformat(str(date)) if date else None
        except ValueError:
            dt = None
        tours.append((dt, t))
    tours.sort(key=lambda x: (x[0] is not None, x[0] or datetime.min), reverse=True)

    items = []
    for dt, t in tours[:50]:
        title = str(g.value(t, DCT.title) or t).strip()
        ig = g.value(t, PH.linkInstagram)
        link = str(ig) if ig else SITE_URL

        parts = []
        att, new = g.value(t, PH.countAttendee), g.value(t, PH.countNewcomer)
        if att is not None:
            parts.append(f"{att} participantes" + (f" ({new} novat@s)" if new else ""))
        energy = g.value(t, PH.energyEstimate)
        if energy is not None:
            from rdflib import Namespace as _NS
            QUDT = _NS("http://qudt.org/schema/qudt/")
            kj = g.value(energy, QUDT.numericValue)
            intensity = g.value(energy, PH.intensityClassification)
            if kj is not None:
                parts.append(f"{float(kj):.0f} kJ" + (f" ({intensity})" if intensity else ""))
        moving = _fmt_moving_duration(g.value(t, PH.movingDuration) or "")
        if moving:
            parts.append(f"{moving} em movimento")
        media = g.value(t, PH.mediaCount)
        if media is not None:
            parts.append(f"{media} mídias no acervo")
        desc = " · ".join(parts) or "Passeio do Pedal Hidrográfico."
        img = g.value(t, SCHEMA.image)
        if img:
            desc += f'<br/><img src="{escape(str(img))}" alt=""/>'

        items.append(
            "    <item>\n"
            f"      <title>{escape(title)}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid isPermaLink=\"false\">{escape(str(t))}</guid>\n"
            + (f"      <pubDate>{format_datetime(dt)}</pubDate>\n" if dt else "")
            + f"      <description>{escape(desc)}</description>\n"
            "    </item>"
        )

    newest = next((dt for dt, _ in tours if dt), None)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>amora — pedais do Pedal Hidrográfico</title>\n"
        f"    <link>{escape(SITE_URL)}</link>\n"
        "    <description>Passeios do coletivo de ciclismo urbano Pedal "
        "Hidrográfico na Grande São Paulo — rotas, fotos e histórias.</description>\n"
        "    <language>pt-br</language>\n"
        f"    <atom:link href=\"{escape(SITE_URL)}feed.xml\" rel=\"self\" "
        "type=\"application/rss+xml\"/>\n"
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
    text = _load_dump_text("tours.ttl") or ""
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    with _feed_lock:
        if _feed_cache["digest"] != digest:
            _feed_cache["xml"] = _build_feed_xml(text)
            _feed_cache["digest"] = digest
        xml = _feed_cache["xml"]
    return _conditional(Response(xml, mimetype="application/rss+xml",
                                 headers={"Cache-Control": "no-cache"}))


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


@app.post("/upload-image")
@serialized
def upload_image():
    # `ttl` pode vir como campo de formulário ou como arquivo.
    ttl_text = request.form.get("ttl")
    if not ttl_text:
        f = request.files.get("ttl")
        if f:
            ttl_text = f.read().decode("utf-8", errors="replace")
    if not ttl_text:
        return jsonify(error="ttl ausente"), 400

    try:
        ok, phash, errors = validate_image_ttl(ttl_text)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"parse: {e}"), 400
    if not ok:
        return jsonify(error="shacl", details=errors, phash=phash), 400

    # Variantes — pelo menos uma é obrigatória.
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

    # Single-file mode: upsert no web/data/uploads.ttl, deduplicando por phash.
    # O nome da activity ainda inclui timestamp pra ser único como IRI; o
    # "ph:Upload" antigo da mesma imagem é removido pelo upsert. Git history
    # do uploads.ttl preserva o histórico de quem-fez-o-quê-quando.
    try:
        upload_local = _upload_filename()[:-len(".ttl")]   # phd:upload_TIMESTAMP
        audit_block  = _build_audit_ttl(upload_local, phash)
        upsert_image_in_uploads(ttl_text, phash, audit_block)
        register_upload_in_manifest("uploads.ttl")          # idempotente
    except Exception as e:  # noqa: BLE001
        # Blobs já gravados sem triples = órfãos invisíveis. Limpa
        # best-effort (re-upload regrava as mesmas keys de qualquer jeito).
        try:
            STORE.delete_prefix(f"photos/{phash}/")
        except Exception as e2:  # noqa: BLE001
            print(f"[upload-image] aviso limpando órfãos de {phash}: {e2}")
        return jsonify(
            error=f"persistência ttl: {e}", phash=phash, files=written,
        ), 500
    print(f"[upload-image] phash={phash} files={written} activity={upload_local}")
    return jsonify(phash=phash, files=written, activity=upload_local, ok=True)


def validate_video_ttl(ttl_text):
    """Espelha validate_image_ttl pra ph:Video: verifica que tem exatamente
    1 ph:Video com IRI phd:video_<vhash16>, e dispara SHACL contra shapes+
    ontology+catálogo (catálogo é mesclado MENOS os triples do próprio vídeo
    em curso, pra que re-uploads não disparem violações de cardinalidade).
    Retorna (ok, vhash, errors)."""
    v = _load_validator()
    from rdflib import URIRef, Namespace, BNode
    data = v["Graph"]().parse(data=ttl_text, format="turtle")

    RDFT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    videos = list(data.subjects(RDFT, URIRef(PH_NS + "Video")))
    if len(videos) != 1:
        return False, None, [
            f"TTL deve conter exatamente 1 ph:Video (achou {len(videos)})"
        ]
    video_iri = str(videos[0])
    if not video_iri.startswith(PHD_NS + "video_"):
        return False, None, [
            f"IRI do Video deve começar com phd:video_ (atual: {video_iri})"
        ]
    vhash = video_iri[len(PHD_NS + "video_"):]
    if len(vhash) != 16 or not all(c in "0123456789abcdef" for c in vhash.lower()):
        return False, vhash, [f"vhash inválido na IRI (esperado 16 hex): {vhash}"]

    vid_uri = URIRef(video_iri)
    catalog = _load_catalog()
    vid_bnodes = set()
    queue = [vid_uri]
    while queue:
        cur = queue.pop()
        for _s, _p, o in catalog.triples((cur, None, None)):
            if isinstance(o, BNode) and o not in vid_bnodes:
                vid_bnodes.add(o)
                queue.append(o)
    exclude = vid_bnodes | {vid_uri}
    merged = data + v["ont"]
    for s, p, o in catalog:
        if s not in exclude:
            merged.add((s, p, o))
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
    vídeos — namespaces de IRI distinguem: phd:image_ vs phd:video_)."""
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
        from rdflib import URIRef, BNode, Graph as RdfGraph
        vid_iri = URIRef(PHD_NS + f"video_{vid_id}")
        existing_text = STORE.read_text(KEY_UPLOADS) or ""
        catalog = RdfGraph()
        if existing_text:
            catalog.parse(data=existing_text, format="turtle")
        to_remove_subjects = {vid_iri}
        queue = [vid_iri]
        while queue:
            cur = queue.pop()
            for _s, _p, o in list(catalog.triples((cur, None, None))):
                if isinstance(o, BNode) and o not in to_remove_subjects:
                    to_remove_subjects.add(o)
                    queue.append(o)
        for subj in to_remove_subjects:
            for triple in list(catalog.triples((subj, None, None))):
                catalog.remove(triple)
        catalog.parse(data=ttl_text, format="turtle")
        STORE.write_text(KEY_UPLOADS, catalog.serialize(format="turtle"))
        register_upload_in_manifest("uploads.ttl")  # idempotente
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
    existing = STORE.read_text(KEY_UPLOADS)
    if not existing:
        return [], 0
    from rdflib import URIRef
    v = _load_validator()
    vid_iri = URIRef(PHD_NS + "video_" + vhash)
    catalog = v["Graph"]()
    catalog.parse(data=existing, format="turtle")
    SCHEMA = "https://schema.org/"
    paths = []
    for pred in (PH_NS + "audio", PH_NS + "video360p", PH_NS + "video720p",
                 SCHEMA + "thumbnail"):
        for o in catalog.objects(vid_iri, URIRef(pred)):
            paths.append(str(o))
    n = _purge_subject(catalog, vid_iri)
    STORE.write_text(KEY_UPLOADS, catalog.serialize(format="turtle"))
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


@app.post("/upload-tour")
def upload_tour():
    """Cria/atualiza 1 ph:Tour em tours.ttl.

    Espera `ttl` (form field ou file) com exatamente 1 `phd:tour_<id> a ph:Tour`
    + opcionalmente declarações novas de `phd:assoc_*`, `phd:pessoa*`, etc.

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

    # Seção crítica: validação + announcement + escrita do tours.ttl, tudo
    # serializado. O fetch da rota acontece depois, sem o lock.
    with _state_lock:
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
            # Fallback local: URL ABSOLUTA baseada em como o cliente chegou
            # aqui (request.host_url). Um caminho relativo ("./tour_assets/…")
            # injetado como IRI no TTL é resolvido pelo rdflib contra o CWD
            # do processo na re-serialização → vira file:///… inutilizável.
            announcement_url = STORE.public_url(key) or (
                request.host_url.rstrip("/")
                + f"/tour_assets/{tour_id}/announcement.{ext}")
            # Injeta schema:image se ainda não estiver no TTL (cliente pode
            # ter posto um URL externo; respeitamos a escolha do cliente).
            # Checagem via triple (não substring): um TTL usando a IRI completa
            # `<https://schema.org/image>` passava no teste antigo de substring
            # `"schema:image" in ttl_text` e ganhava um image duplicado.
            from rdflib import Graph as _RdfGraph, URIRef as _URIRef
            _tour_uri = _URIRef(PHD_NS + f"tour_{tour_id}")
            _img_preds = (_URIRef("https://schema.org/image"), _URIRef("http://schema.org/image"))
            try:
                _g = _RdfGraph().parse(data=ttl_text, format="turtle")
                _has_image = any((_tour_uri, p, None) in _g for p in _img_preds)
            except Exception:  # noqa: BLE001
                _has_image = "schema:image" in ttl_text  # fallback conservador
            if not _has_image:
                inject = (
                    f"\n# Imagem do anúncio (uploaded server-side)\n"
                    f'phd:tour_{tour_id} <https://schema.org/image> <{announcement_url}> .\n'
                )
                ttl_text = ttl_text + inject

        try:
            upsert_tour_in_tours_ttl(ttl_text, tour_id)
            _invalidate_catalog()
        except Exception as e:  # noqa: BLE001
            return jsonify(
                error=f"persistência ttl: {e}", tour_id=tour_id,
            ), 500

    # Fora do lock: sincroniza a geometria da rota (best-effort, IO de rede).
    # O try/except garante que NENHUMA falha aqui (import, storage, bug)
    # transforma um save bem-sucedido do tour em 500.
    try:
        route_status = _sync_tour_route(tour_id, ttl_text)
    except Exception as e:  # noqa: BLE001
        route_status = {"status": "error", "error": str(e)}
        print(f"[upload-tour] erro sincronizando routes.json: {e}")
    print(f"[upload-tour] tour_id={tour_id} announcement={announcement_url} "
          f"route={route_status.get('status')}")
    return jsonify(
        tour_id=tour_id, announcement_url=announcement_url,
        route=route_status, ok=True,
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
    try:
        STORE.delete_prefix(asset_prefix)
    except Exception as e:  # noqa: BLE001
        print(f"[delete-tour] erro removendo {asset_prefix}: {e}")
    try:
        removed_triples = remove_tour_from_tours_ttl(tour_id)
        _invalidate_catalog()
    except Exception as e:  # noqa: BLE001
        return jsonify(
            error=f"persistência ttl: {e}", tour_id=tour_id,
            assets=removed_assets,
        ), 500
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
