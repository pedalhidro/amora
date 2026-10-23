"""
activitypub.py — o amora como conta do fediverso (ActivityPub), fase só-leitura.

Monta os documentos ActivityStreams 2.0 (JSON-LD) que o `backend/main.py`
serve: WebFinger, o ator, a outbox, os Notes dos passeios e o nodeinfo. Funções
puras — recebem os fatos já extraídos do catálogo (`_tour_facts` do main.py) e
devolvem dicts; quem fala HTTP e lê o catálogo é o main.py (mesma divisão do
`rwgps.py`).

Escolhas que não se desfazem depois que houver seguidores:
  • O `id` do ator é `<SITE_URL>ap/actor` e o de um passeio é
    `<SITE_URL>passeio/<slug8>`. Mastodon & cia exigem que o `id` de um objeto
    more no MESMO host que o serviu — o 303 de id.pedalhidrografi.co pro amora
    não serve, então os IRIs `id.…` entram só como `seeAlso`. O slug8 (não o
    legível) porque é a identidade imutável do passeio.
  • A conta é `@<AP_USERNAME>@<host do SITE_URL>` (default
    `@amora@amora.pedalhidrografi.co`).

Ainda NÃO há entrega (POST pros seguidores), assinatura HTTP nem tratamento
de Follow — a inbox só registra no log. A chave pública só aparece no ator
quando `AP_PRIVATE_KEY` (PEM) está no ambiente.
"""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlsplit

AS_CONTEXT = "https://www.w3.org/ns/activitystreams"
SECURITY_CONTEXT = "https://w3id.org/security/v1"
PUBLIC = AS_CONTEXT + "#Public"
AS_MIME = "application/activity+json"
JRD_MIME = "application/jrd+json"

# Termos fora do vocabulário AS que os servidores entendem (Mastodon e
# derivados): hashtag, sensível, PropertyValue dos campos do perfil,
# descoberta. `seeAlso` liga o objeto ao IRI dereferenciável do recurso.
_EXTRA_CONTEXT = {
    "Hashtag": "as:Hashtag",
    "sensitive": "as:sensitive",
    "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
    "toot": "http://joinmastodon.org/ns#",
    "discoverable": "toot:discoverable",
    "indexable": "toot:indexable",
    "schema": "http://schema.org#",
    "PropertyValue": "schema:PropertyValue",
    "value": "schema:value",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "seeAlso": {"@id": "rdfs:seeAlso", "@type": "@id"},
}
CONTEXT = [AS_CONTEXT, SECURITY_CONTEXT, _EXTRA_CONTEXT]

HASHTAGS = ("PedalHidrografico",)
OUTBOX_PAGE_SIZE = 20
# Trecho da narrativa no post — o resto fica na página do passeio.
NARRATIVE_MAX = 500


@dataclass(frozen=True)
class Config:
    site_url: str            # com barra final (SITE_URL do main.py)
    username: str = "amora"
    public_key_pem: str | None = None

    @property
    def domain(self):
        return urlsplit(self.site_url).hostname or ""

    @property
    def handle(self):
        return f"{self.username}@{self.domain}"

    @property
    def actor_id(self):
        return f"{self.site_url}ap/actor"

    @property
    def inbox(self):
        return f"{self.site_url}ap/inbox"

    @property
    def outbox(self):
        return f"{self.site_url}ap/outbox"

    @property
    def followers(self):
        return f"{self.site_url}ap/followers"

    @property
    def following(self):
        return f"{self.site_url}ap/following"

    def tour_note_id(self, tour_id):
        return f"{self.site_url}passeio/{tour_id}"


def public_key_from_private(pem):
    """PEM da chave pública a partir da privada (PKCS#1 ou PKCS#8). Aceita o
    PEM numa linha só com `\\n` literais (como cabe num .env). None se o
    `cryptography` faltar ou a chave não parsear — o ator sai sem chave."""
    if not pem:
        return None
    try:
        from cryptography.hazmat.primitives import serialization
        key = serialization.load_pem_private_key(
            pem.replace("\\n", "\n").encode("ascii"), password=None)
        return key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")
    except Exception as e:  # noqa: BLE001
        print(f"[activitypub] AP_PRIVATE_KEY inválida ({e}) — ator sem chave")
        return None


def wants_activitystreams(accept, fmt=""):
    """True quando o pedido é de ActivityStreams: `?format=as` ou um Accept
    com `application/activity+json` ou `application/ld+json` com o profile do
    AS (é o que Mastodon, Pixelfed & cia mandam). Browser nunca pede isso."""
    if (fmt or "").lower() in ("as", "ap", "activity", "activitystreams"):
        return True
    for part in (accept or "").lower().split(","):
        media, *params = [p.strip() for p in part.split(";")]
        q = next((p[2:] for p in params if p.startswith("q=")), "1")
        try:
            if float(q) <= 0:
                continue   # q=0 = "não aceito"
        except ValueError:
            pass
        if media == AS_MIME:
            return True
        if media == "application/ld+json" and any(
                "activitystreams" in p for p in params):
            return True
    return False


def _iso(dt):
    """datetime → ISO 8601 em UTC com Z. Naive = UTC (convenção do backend)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def published_of(facts, now=None):
    """Instante de publicação do Note de um passeio: a data do passeio, nunca
    no futuro (um passeio anunciado antes de acontecer sai com o agora). A
    fase de entrega vai gravar o instante do anúncio e passar a usá-lo."""
    dt = facts.get("dt")
    if dt is None:
        return None
    now = now or datetime.now(timezone.utc)
    aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return _iso(min(aware, now))


def webfinger(cfg, resource):
    """JRD da conta (RFC 7033) — None se `resource` não é esta conta. Aceita
    `acct:amora@host` e o próprio id do ator."""
    r = (resource or "").strip()
    if r.lower() not in (f"acct:{cfg.handle}".lower(), cfg.actor_id.lower()):
        return None
    return {
        "subject": f"acct:{cfg.handle}",
        "aliases": [cfg.actor_id, cfg.site_url],
        "links": [
            {"rel": "self", "type": AS_MIME, "href": cfg.actor_id},
            {"rel": "http://webfinger.net/rel/profile-page",
             "type": "text/html", "href": cfg.site_url},
        ],
    }


def actor(cfg):
    """O ator (perfil da conta). `Person` e não `Organization` de propósito:
    é o tipo que todo servidor do fediverso aceita seguir (o Pixelfed é o
    mais restritivo)."""
    site = escape(cfg.site_url)
    doc = {
        "@context": CONTEXT,
        "id": cfg.actor_id,
        "type": "Person",
        "preferredUsername": cfg.username,
        "name": "Pedal Hidrográfico",
        "summary": (
            "<p>Coletivo de ciclismo urbano que pedala pelos rios, córregos e "
            "morros de São Paulo. Aqui saem os passeios do coletivo; o acervo "
            f'(rotas, fotos, vídeos) está em <a href="{site}">{site}</a>.</p>'
            "<p>Esta conta só publica — fale com a gente pelo site.</p>"),
        "url": cfg.site_url,
        "inbox": cfg.inbox,
        "outbox": cfg.outbox,
        "followers": cfg.followers,
        "following": cfg.following,
        "endpoints": {"sharedInbox": cfg.inbox},
        "manuallyApprovesFollowers": False,
        "discoverable": True,
        "indexable": True,
        "icon": {"type": "Image", "mediaType": "image/jpeg",
                 "url": f"{cfg.site_url}logo-phidro-512.jpg"},
        "attachment": [
            {"type": "PropertyValue", "name": "Site",
             "value": f'<a href="{site}" rel="me">{site}</a>'},
            {"type": "PropertyValue", "name": "Licença",
             "value": '<a href="https://creativecommons.org/licenses/by-sa/4.0/">'
                      "CC BY-SA 4.0</a>"},
        ],
        "tag": [],
    }
    if cfg.public_key_pem:
        doc["publicKey"] = {"id": f"{cfg.actor_id}#main-key",
                            "owner": cfg.actor_id,
                            "publicKeyPem": cfg.public_key_pem}
    return doc


def _trim(text, limit):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def _hashtag(cfg, name):
    return {"type": "Hashtag", "name": f"#{name}", "href": cfg.site_url}


def tour_note(cfg, facts, art_url=None, now=None):
    """Note de um passeio. `facts` = `_tour_facts` do main.py; `art_url` = a
    arte em tamanho de exibição (variante web), absoluta."""
    note_id = cfg.tour_note_id(facts["id"])
    lines = [f"<p>{escape(facts['title'])}</p>"]
    when = facts.get("date_label")
    if when:
        dep = facts.get("departed")
        if dep is not None:
            when += f", saída às {dep.hour}h{dep.minute:02d}"
        lines.append(f"<p>{escape(when)}</p>")
    paragraphs = facts.get("paragraphs") or []
    if paragraphs:
        lines.append(f"<p>{escape(_trim(paragraphs[0], NARRATIVE_MAX))}</p>")
    metrics = [m for m in (
        facts.get("energy_line"),
        facts.get("total") and f"{facts['total']} de passeio",
        facts.get("attendees") and f"{facts['attendees']} pessoas",
    ) if m]
    if metrics:
        lines.append(f"<p>{escape(' · '.join(metrics))}</p>")
    page = escape(facts["page_url"])
    lines.append(f'<p><a href="{page}">{page}</a></p>')
    lines.append("<p>" + " ".join(
        f'<a href="{escape(cfg.site_url)}" class="mention hashtag" rel="tag">'
        f"#<span>{escape(h)}</span></a>" for h in HASHTAGS) + "</p>")
    content = "".join(lines)

    note = {
        "@context": CONTEXT,
        "id": note_id,
        "type": "Note",
        "attributedTo": cfg.actor_id,
        "to": [PUBLIC],
        "cc": [cfg.followers],
        "url": facts["page_url"],
        "content": content,
        "contentMap": {"pt": content},
        "sensitive": False,
        "attachment": [],
        "tag": [_hashtag(cfg, h) for h in HASHTAGS],
        "seeAlso": facts["iri"],
    }
    published = published_of(facts, now)
    if published:
        note["published"] = published
    if art_url:
        media_type = (mimetypes.guess_type(urlsplit(art_url).path)[0]
                      or "image/jpeg")
        note["attachment"].append({
            "type": "Document", "mediaType": media_type, "url": art_url,
            "name": f"Arte de anúncio do passeio {facts['title']}",
        })
    return note


def create_of(cfg, note):
    """Create que embrulha um Note (item da outbox)."""
    obj = {k: v for k, v in note.items() if k != "@context"}
    act = {"id": f"{note['id']}#create", "type": "Create",
           "actor": cfg.actor_id, "to": note["to"], "cc": note["cc"],
           "object": obj}
    if "published" in note:
        act["published"] = note["published"]
    return act


def outbox(cfg, notes, page=None):
    """OrderedCollection da outbox (mais recentes primeiro). Sem `page`: só o
    cabeçalho com o link pra 1ª página; com `page` (1, 2, …): a página."""
    total = len(notes)
    if page is None:
        doc = {"@context": CONTEXT, "id": cfg.outbox,
               "type": "OrderedCollection", "totalItems": total}
        if total:
            last = (total + OUTBOX_PAGE_SIZE - 1) // OUTBOX_PAGE_SIZE
            doc["first"] = f"{cfg.outbox}?page=1"
            doc["last"] = f"{cfg.outbox}?page={last}"
        return doc
    start = (page - 1) * OUTBOX_PAGE_SIZE
    chunk = notes[start:start + OUTBOX_PAGE_SIZE]
    doc = {"@context": CONTEXT, "id": f"{cfg.outbox}?page={page}",
           "type": "OrderedCollectionPage", "partOf": cfg.outbox,
           "orderedItems": [create_of(cfg, n) for n in chunk]}
    if start + OUTBOX_PAGE_SIZE < total:
        doc["next"] = f"{cfg.outbox}?page={page + 1}"
    if page > 1:
        doc["prev"] = f"{cfg.outbox}?page={page - 1}"
    return doc


def empty_collection(collection_id):
    """Coleção vazia (seguidores/seguindo enquanto não há Follow)."""
    return {"@context": CONTEXT, "id": collection_id,
            "type": "OrderedCollection", "totalItems": 0, "orderedItems": []}


def nodeinfo_links(cfg):
    return {"links": [{
        "rel": "http://nodeinfo.diaspora.software/ns/schema/2.1",
        "href": f"{cfg.site_url}nodeinfo/2.1",
    }]}


def nodeinfo(local_posts):
    return {
        "version": "2.1",
        "software": {"name": "amora", "version": "0",
                     "repository": "https://github.com/pedalhidro/amora",
                     "homepage": "https://amora.pedalhidrografi.co/"},
        "protocols": ["activitypub"],
        "services": {"inbound": [], "outbound": ["rss2.0"]},
        "openRegistrations": False,
        "usage": {"users": {"total": 1, "activeMonth": 1, "activeHalfyear": 1},
                  "localPosts": local_posts},
        "metadata": {"nodeName": "Pedal Hidrográfico"},
    }
