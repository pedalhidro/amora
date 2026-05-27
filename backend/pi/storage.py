"""
Storage abstraction para o backend Pedal Hidrográfico.

Roteia ESTADO MUTÁVEL (catálogos TTL + variantes de imagem) por trás de
uma interface comum:

  StateStore.read_text(key)              → str | None
  StateStore.write_text(key, txt, ct=…)  → None
  StateStore.write_bytes(key, b, ct=…)   → None
  StateStore.delete(key)                 → None
  StateStore.delete_prefix(prefix)       → None
  StateStore.exists(key)                 → bool
  StateStore.public_url(key)             → str | None
      (None = sirva via Flask; URL = HTTP redirect)

Dois backends:
  LocalStateStore(root_dir)   — Pi / dev: lê e grava no filesystem
  GCSStateStore(bucket_name)  — Cloud Run: lê e grava num bucket público

Keys são relativos ao estado (p.ex. "data/uploads.ttl",
"photos/abc123.../large.jpg"). NUNCA começam com "/".

Estado mutável (ambos backends):
  data/uploads.ttl                    catálogo de imagens uploaded
  data/data_graphs.ttl                manifesto void:Dataset
  photos/<phash>/<variant>.<ext>      variantes por imagem

Estado estático (sempre servido pelo Flask a partir do container):
  data/shapes.ttl, data/ontology.ttl, data/tours.ttl
  index.html, app.js, style.css, lib/*, …
"""
from __future__ import annotations

from pathlib import Path


class StateStore:
    def read_text(self, key: str) -> str | None:
        raise NotImplementedError

    def write_text(self, key: str, text: str, content_type: str = "text/turtle") -> None:
        raise NotImplementedError

    def write_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def delete_prefix(self, prefix: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def public_url(self, key: str) -> str | None:
        return None

    def list_keys(self, prefix: str) -> list[str]:
        raise NotImplementedError


class LocalStateStore(StateStore):
    """Filesystem-backed store — Pi e dev local."""

    def __init__(self, root_dir: str | Path):
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _p(self, key: str) -> Path:
        # Bloqueia escape do root via "../" — defesa em profundidade.
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError(f"key escapa do root: {key}")
        return p

    def read_text(self, key):
        p = self._p(key)
        if not (p.exists() and p.is_file() and p.stat().st_size > 0):
            return None
        return p.read_text()

    def write_text(self, key, text, content_type="text/turtle"):
        p = self._p(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def write_bytes(self, key, data, content_type=None):
        p = self._p(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def delete(self, key):
        p = self._p(key)
        if p.is_file():
            p.unlink()

    def delete_prefix(self, prefix):
        p = self._p(prefix)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    try:
                        f.unlink()
                    except OSError:
                        pass
            # Remove diretórios vazios depois (deepest first)
            for d in sorted(p.rglob("*"), key=lambda x: -len(str(x))):
                if d.is_dir():
                    try:
                        d.rmdir()
                    except OSError:
                        pass
            try:
                p.rmdir()
            except OSError:
                pass

    def exists(self, key):
        return self._p(key).exists()

    def list_keys(self, prefix):
        p = self._p(prefix)
        if not p.is_dir():
            return []
        out = []
        for f in p.rglob("*"):
            if f.is_file():
                rel = f.relative_to(self.root)
                out.append(str(rel).replace("\\", "/"))
        return out


class GCSStateStore(StateStore):
    """Google Cloud Storage-backed store — Cloud Run."""

    def __init__(self, bucket_name: str):
        # Import lazy: a lib gcs é pesada e só faz sentido no modo cloud.
        from google.cloud import storage  # type: ignore

        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)
        self.bucket_name = bucket_name

    # MIME guessing — só pros conteúdos que servimos por static (raro,
    # quase tudo vira redirect para o GCS público).
    @staticmethod
    def _ct_for(key: str) -> str:
        if key.endswith(".ttl"):
            return "text/turtle; charset=utf-8"
        if key.endswith(".json"):
            return "application/json"
        if key.endswith(".jpg") or key.endswith(".jpeg"):
            return "image/jpeg"
        if key.endswith(".png"):
            return "image/png"
        if key.endswith(".heic") or key.endswith(".heif"):
            return "image/heic"
        return "application/octet-stream"

    def read_text(self, key):
        # IMPORTANTE: usar get_blob() (que faz HEAD + popula a generation)
        # ao invés de bucket.blob() + download_as_text(). Sem isso, a SDK
        # do google-cloud-storage pode devolver um snapshot stale do conteúdo
        # — observado empiricamente em produção (Cloud Run): mesmo bucket,
        # mesma chave, gcloud storage cat retornava 205KB, mas
        # blob.download_as_text() retornava 232KB de uma versão anterior.
        # `get_blob` ancora a generation antes do download e elimina o bug.
        blob = self._bucket.get_blob(key)
        if blob is None:
            return None
        return blob.download_as_text()

    def write_text(self, key, text, content_type="text/turtle; charset=utf-8"):
        blob = self._bucket.blob(key)
        blob.upload_from_string(text, content_type=content_type)

    def write_bytes(self, key, data, content_type=None):
        blob = self._bucket.blob(key)
        blob.upload_from_string(
            data, content_type=content_type or self._ct_for(key)
        )

    def delete(self, key):
        blob = self._bucket.blob(key)
        if blob.exists():
            blob.delete()

    def delete_prefix(self, prefix):
        for blob in self._client.list_blobs(self.bucket_name, prefix=prefix):
            try:
                blob.delete()
            except Exception:
                pass

    def exists(self, key):
        return self._bucket.blob(key).exists()

    def public_url(self, key):
        # Bucket é uniform-access + publicly readable; servir via redirect
        # é muito mais eficiente que streamar via Flask.
        return f"https://storage.googleapis.com/{self.bucket_name}/{key}"

    def list_keys(self, prefix):
        return [b.name for b in self._client.list_blobs(self.bucket_name, prefix=prefix)]


def make_store_from_env(default_local_root: str | Path) -> StateStore:
    """Constrói o store apropriado a partir de variáveis de ambiente.

    STORAGE_BACKEND=gcs  →  GCSStateStore(GCS_BUCKET)
    STORAGE_BACKEND=local (default)  →  LocalStateStore(default_local_root)
    """
    import os

    backend = (os.environ.get("STORAGE_BACKEND") or "local").lower()
    if backend == "gcs":
        bucket = os.environ.get("GCS_BUCKET")
        if not bucket:
            raise RuntimeError("STORAGE_BACKEND=gcs requer GCS_BUCKET")
        return GCSStateStore(bucket)
    if backend == "local":
        return LocalStateStore(default_local_root)
    raise RuntimeError(f"STORAGE_BACKEND inválido: {backend}")
