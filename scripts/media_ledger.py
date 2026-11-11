#!/usr/bin/env python3
"""Livro-razão da sincronização de mídia (acervo do Drive / Fotos → amora).

Responde a pergunta que faltava pra dizer "o amora REFLETE o acervo": pra cada
arquivo de origem, o que foi feito dele?

    ingested   subiu, e virou med:<hash>
    duplicate  já estava lá (qual mídia, a quantos bits)
    held       parece uma mídia que foi APAGADA no amora — não sobe sem alguém liberar
    excluded   uma pessoa decidiu que não sobe
    (notas)    sem GPS, erro de decode… — reavaliadas a cada rodada

Três regras de projeto:

1. **Fica FORA dos catálogos e fora do git.** `.sync-state/` é gitignored e por
   máquina: o repo é público e os nomes de arquivo carregam nome de gente. E
   se o registro morasse nas triples da mídia, apagar a mídia apagaria o
   registro — e a foto removida por privacidade subiria de novo na rodada
   seguinte.

2. **A sincronização é só aditiva.** Apagou no amora → respeitado (nunca
   re-sobe). Sumiu na origem → relatado, nunca propagado.

3. **Falha fechada.** Sem livro, `--apply` não roda (um clone novo ou um
   worktree começa com `.sync-state/` vazio e re-subiria tudo que já foi
   apagado). O primeiro uso pede `--iniciar-livro`.

Dois arquivos em `.sync-state/` (ou `$PHIDRO_SYNC_STATE`):

  media-ledger.jsonl   uma linha por decisão, só acrescenta; a última linha de
                       cada origem é o estado dela.
  media-seen.json      todo hash que o amora JÁ TEVE. "Lápide" = já teve e não
                       tem mais = foi apagado. Antes de subir qualquer coisa a
                       ingestão compara com as lápides (Hamming mais largo que
                       o da dedup: o custo de errar pra menos é republicar uma
                       foto apagada; pra mais, uma revisão humana).

Chave da origem: `drive:<item-id>` (o id do arquivo no Google Drive, lido do
xattr que o Drive for Desktop expõe — sobrevive a renomear/mover pasta) ou
`photos:<uuid>` (Fotos da Apple). Caminho, tamanho e mtime vão como DADO, nunca
como chave: as pastas do acervo são renomeadas.

Uso:

    media_ledger.py status             # por pasta: pendente / subiu / duplicata / …
    media_ledger.py status --json F
    media_ledger.py semear             # lápides do que foi apagado ANTES do livro
    media_ledger.py retidos            # o que está "held", pra decidir
    media_ledger.py liberar  <origem>  # held → pode subir na próxima rodada
    media_ledger.py excluir  <origem>  # nunca sobe
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = Path(os.environ.get("PHIDRO_SYNC_STATE") or REPO / ".sync-state")
LEDGER = STATE_DIR / "media-ledger.jsonl"
SEEN = STATE_DIR / "media-seen.json"

# Desfechos que encerram o assunto: o arquivo não é relido nas próximas rodadas.
TERMINAIS = {"ingested", "duplicate", "excluded"}
# Notas: ficam no livro pra explicar o "pendente", mas são reavaliadas sempre
# (um original "sem GPS" na fase 1 ainda é candidato da fase 2).
NOTAS = {"held", "released", "skipped", "error"}

# A dedup contra o catálogo vivo usa Hamming ≤ 5 (PHASH_DUP_THRESHOLD). Contra
# as LÁPIDES a régua é mais larga: o mesmo original dá até 8 bits de diferença
# entre aparelhos, e a recompressão do WhatsApp soma em cima.
LAPIDE_HAMMING = 10

XATTR_DRIVE_ID = b"com.google.drivefs.item-id#S"
RE_HASH = re.compile(r"^[0-9a-f]{16}$")


def agora() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


# ═════════════════════════════════════════════════════════════════════════
# 1. Identidade da origem
# ═════════════════════════════════════════════════════════════════════════

_libc = None


def _getxattr(caminho: str, nome: bytes) -> bytes | None:
    """getxattr(2) via ctypes — o `os.getxattr` do Python não existe no macOS.
    Lê só o atributo estendido: não abre nem materializa o arquivo."""
    global _libc
    if _libc is None:
        _libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    buf = ctypes.create_string_buffer(256)
    p = os.fsencode(caminho)
    if sys.platform == "darwin":
        _libc.getxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        n = _libc.getxattr(p, nome, buf, len(buf), 0, 0)
    else:
        _libc.getxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                                   ctypes.c_size_t]
        n = _libc.getxattr(p, nome, buf, len(buf))
    return buf.raw[:n] if n > 0 else None


def drive_item_id(caminho) -> str | None:
    """O id do arquivo no Google Drive (estável a renomear/mover), ou None se o
    arquivo não vive num volume do Drive for Desktop."""
    try:
        v = _getxattr(str(caminho), XATTR_DRIVE_ID)
    except OSError:
        return None
    if not v:
        return None
    s = v.decode("utf-8", "replace").strip("\x00").strip()
    return s or None


def chave_drive(caminho) -> str | None:
    i = drive_item_id(caminho)
    return f"drive:{i}" if i else None


def chave_photos(uuid: str) -> str:
    return f"photos:{uuid}"


# ═════════════════════════════════════════════════════════════════════════
# 2. O livro (JSONL, só acrescenta)
# ═════════════════════════════════════════════════════════════════════════

class LivroAusente(Exception):
    pass


class Livro:
    def __init__(self, caminho: Path = LEDGER, criar: bool = False):
        self.caminho = Path(caminho)
        self.ultimo: dict[str, dict] = {}      # origem → última linha
        self.terminal: dict[str, dict] = {}    # origem → último desfecho terminal
        self.liberados: set[str] = set()
        self.midias: dict[str, str | None] = {}   # hash que o livro já viu no amora → kind
        if not self.caminho.exists():
            if not criar:
                raise LivroAusente(str(self.caminho))
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            self.caminho.touch()
        with self.caminho.open(encoding="utf-8") as f:
            for n, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    self._aplica(json.loads(linha))
                except (ValueError, KeyError) as e:
                    raise SystemExit(f"livro corrompido em {self.caminho}:{n}: {e}")

    def _aplica(self, r: dict) -> None:
        src = r["src"]
        self.ultimo[src] = r
        o = r["outcome"]
        if o in ("ingested", "duplicate") and r.get("media"):
            self.midias[r["media"]] = r.get("kind")
        if o in TERMINAIS:
            self.terminal[src] = r
            self.liberados.discard(src)
        elif o == "released":
            self.liberados.add(src)
            self.terminal.pop(src, None)       # liberar desfaz um "excluded"

    def registra(self, src: str, outcome: str, **campos) -> dict | None:
        """Acrescenta uma linha (fsync na hora: o registro tem que sobreviver a
        um Ctrl-C logo depois do 200 do servidor). Notas repetidas — mesmo
        desfecho e mesmo motivo da última linha — não são regravadas, senão
        cada rodada engordaria o livro com os mesmos "sem GPS"."""
        assert outcome in TERMINAIS | NOTAS, outcome
        ant = self.ultimo.get(src)
        if (outcome in NOTAS and ant and ant.get("outcome") == outcome
                and ant.get("reason") == campos.get("reason")
                and ant.get("media") == campos.get("media")):
            return None
        r = {"src": src, "outcome": outcome, "at": agora(),
             **{k: v for k, v in campos.items() if v is not None}}
        with self.caminho.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._aplica(r)
        return r


LOCK = STATE_DIR / "ingest.lock"


def _pid_vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def trava_escritor() -> None:
    """Uma ingestão com --apply por vez, nesta máquina. Cada uma decide com um
    RETRATO do catálogo tirado no começo; duas ao mesmo tempo não se enxergam —
    a cópia do zap de uma sobrescreveria o original que a outra acabou de subir
    (o /upload-image é purge-and-replace). Trava por pid: se o dono morreu, a
    trava velha é ignorada."""
    import atexit
    if LOCK.exists():
        try:
            d = json.loads(LOCK.read_text(encoding="utf-8"))
            pid = int(d.get("pid"))
        except (ValueError, TypeError, OSError):
            d, pid = {}, None
        if pid and pid != os.getpid() and _pid_vivo(pid):
            raise SystemExit(
                f"\noutra ingestão com --apply está rodando (pid {pid}, desde {d.get('desde')}):\n"
                f"  {d.get('cmd')}\nEspere ela terminar — duas ao mesmo tempo se atropelam.")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({"pid": os.getpid(), "desde": agora(),
                                "cmd": " ".join(sys.argv)}), encoding="utf-8")

    def _solta():
        try:
            if json.loads(LOCK.read_text(encoding="utf-8")).get("pid") == os.getpid():
                LOCK.unlink()
        except (OSError, ValueError):
            pass
    atexit.register(_solta)


def abre_livro(apply: bool, iniciar: bool) -> Livro | None:
    """A porta de entrada das ingestões. Dry-run sem livro segue (não grava
    nada mesmo); `--apply` sem livro PARA, a não ser com `--iniciar-livro`.
    Com `--apply` também toma a trava de escritor único."""
    if apply:
        trava_escritor()
    try:
        return Livro(criar=apply and iniciar)
    except LivroAusente as e:
        if apply:
            raise SystemExit(
                f"\nlivro-razão não encontrado: {e}\n"
                "Sem ele não dá pra saber o que já subiu nem o que foi APAGADO no amora —\n"
                "e a ingestão re-subiria mídia removida. Se este é mesmo o primeiro uso\n"
                "nesta máquina: rode `scripts/media_ledger.py semear` e depois a ingestão\n"
                "com --iniciar-livro. Se o livro existe em outra cópia do repo, copie o\n"
                "diretório .sync-state/ de lá.")
        return None


# ═════════════════════════════════════════════════════════════════════════
# 3. Hashes já vistos e lápides
# ═════════════════════════════════════════════════════════════════════════

class Vistos:
    """Todo hash que o amora já teve: {hash: {kind, first, last, via}}."""

    def __init__(self, caminho: Path = SEEN):
        self.caminho = Path(caminho)
        self.h: dict[str, dict] = {}
        self.semeado: str | None = None     # quando o `semear` rodou aqui (None = nunca)
        if self.caminho.exists():
            d = json.loads(self.caminho.read_text(encoding="utf-8"))
            self.h = d.get("hashes", {})
            self.semeado = d.get("semeado")

    def nota(self, h: str, kind: str | None, via: str, presente: bool) -> None:
        if not RE_HASH.match(h):
            return
        e = self.h.setdefault(h, {"kind": kind, "first": agora(), "via": via})
        if kind and not e.get("kind"):
            e["kind"] = kind
        if presente:
            e["last"] = agora()

    def atualiza(self, por_classe: dict[str, set[str]]) -> None:
        """Anota o catálogo vivo ({'StillImage': {...}, 'MotionImage': {...}})."""
        for classe, kind in (("StillImage", "image"), ("MotionImage", "video")):
            for h in por_classe.get(classe, ()):
                self.nota(h, kind, "catalogo", presente=True)

    def lapides(self, por_classe: dict[str, set[str]]) -> dict[str, dict]:
        vivos = set().union(*por_classe.values()) if por_classe else set()
        return {h: e for h, e in self.h.items() if h not in vivos}

    def salva(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.caminho.with_suffix(".tmp")
        tmp.write_text(json.dumps({"semeado": self.semeado, "hashes": self.h},
                                  ensure_ascii=False, indent=0, sort_keys=True),
                       encoding="utf-8")
        os.replace(tmp, self.caminho)


def lapide_proxima(h: str, kind: str, lapides: dict[str, dict]) -> tuple[str, int] | None:
    """A lápide mais próxima de `h` dentro de LAPIDE_HAMMING, do mesmo tipo
    (lápide de tipo desconhecido compara com os dois)."""
    melhor = None
    for t, e in lapides.items():
        if e.get("kind") not in (None, kind):
            continue
        d = hamming(h, t)
        if d <= LAPIDE_HAMMING and (melhor is None or d < melhor[1]):
            melhor = (t, d)
    return melhor


def hashes_com_geo(g) -> set[str]:
    """Hashes das mídias do catálogo (grafo rdflib) que têm coordenada."""
    import rdflib
    med = "https://id.pedalhidrografi.co/midia/"
    out = set()
    for m in g.subjects(rdflib.URIRef("https://schema.org/locationCreated"), None):
        m = str(m)
        if m.startswith(med):
            out.add(m[len(med):].removeprefix("image_").removeprefix("video_").lower())
    return out


def prepara(por_classe: dict[str, set[str]], grava: bool,
            livro: "Livro | None" = None) -> dict[str, dict]:
    """Passo comum das ingestões: anota nos vistos o catálogo vivo E toda mídia
    que o livro registrou (uma foto que subiu e foi apagada antes da rodada
    seguinte nunca apareceria num retrato do catálogo), e devolve as lápides.
    `grava=False` (dry-run) não toca o disco.

    Com `grava=True` (--apply) exige que o `semear` já tenha rodado nesta
    máquina: sem a semente não há lápide nenhuma do que foi apagado antes de o
    livro existir, e a ingestão republicaria essas mídias."""
    v = Vistos()
    if grava and not v.semeado:
        raise SystemExit(
            f"\nlápides não semeadas nesta máquina ({v.caminho}).\n"
            "Rode antes: python scripts/media_ledger.py semear\n"
            "(lista o que já foi apagado no amora, pra ingestão não re-subir).")
    v.atualiza(por_classe)
    if livro is not None:
        for h, kind in livro.midias.items():
            v.nota(h, kind, "livro", presente=False)
    if grava:
        v.salva()
    return v.lapides(por_classe)


# ═════════════════════════════════════════════════════════════════════════
# 4. Semente: o que foi apagado ANTES de o livro existir
# ═════════════════════════════════════════════════════════════════════════

def _hashes_de_blobs(linhas) -> tuple[set[str], set[str]]:
    fotos, clipes = set(), set()
    for l in linhas:
        m = re.search(r"photos/([0-9a-f]{16})/", l)
        if m:
            fotos.add(m.group(1))
            continue
        m = re.search(r"clips/([0-9a-f]{16})\.", l)
        if m:
            clipes.add(m.group(1))
    return fotos, clipes


def semear(servidor: str, bucket: str | None, projeto: str) -> None:
    """Toda mídia cujos BLOBS já existiram e que não está mais no catálogo foi
    apagada (ou é órfã de um envio que falhou — vira lápide do mesmo jeito: na
    dúvida, revisão humana). Fontes:

      · web/photos/<hash>/ e web/clips/<hash>.* locais (o que já passou por
        esta máquina);
      · o bucket, com TODAS as versões dos objetos (Object Versioning guarda
        os apagados por 90 dias) — só a listagem, nada é baixado.

    Os catálogos em si não servem de fonte histórica: images.ttl nunca foi
    versionado no git."""
    I = _carrega("ingest-drive.py")
    por_classe = I.hashes_no_servidor(servidor)
    vivos = set().union(*por_classe.values())
    v = Vistos()
    v.atualiza(por_classe)
    antes = len(v.lapides(por_classe))

    fotos, clipes = set(), set()
    web = REPO / "web"
    if (web / "photos").is_dir():
        fotos |= {d for d in os.listdir(web / "photos") if RE_HASH.match(d)}
    if (web / "clips").is_dir():
        clipes |= _hashes_de_blobs(f"clips/{f}" for f in os.listdir(web / "clips"))[1]
    print(f"local:  {len(fotos)} fotos, {len(clipes)} clipes com nome de hash")

    if bucket:
        for pref in ("photos", "clips"):
            try:
                out = subprocess.run(
                    ["gcloud", "storage", "ls", "--all-versions",
                     f"gs://{bucket}/{pref}/**", "--project", projeto],
                    capture_output=True, text=True, check=True, timeout=900).stdout
            except (OSError, subprocess.SubprocessError) as e:
                raise SystemExit(f"não consegui listar gs://{bucket}/{pref} ({e}).\n"
                                 "Rode com --sem-bucket pra semear só com o que há local.")
            f2, c2 = _hashes_de_blobs(out.splitlines())
            fotos |= f2
            clipes |= c2
        print(f"+bucket (todas as versões): {len(fotos)} fotos, {len(clipes)} clipes")

    for h in fotos - vivos:
        v.nota(h, "image", "semente", presente=False)
    for h in clipes - vivos:
        v.nota(h, "video", "semente", presente=False)
    v.semeado = agora()
    v.salva()
    lap = v.lapides(por_classe)
    n_i = sum(1 for e in lap.values() if e.get("kind") == "image")
    print(f"\ncatálogo vivo: {len(por_classe['StillImage'])} fotos + "
          f"{len(por_classe['MotionImage'])} vídeos")
    print(f"lápides: {len(lap)} ({n_i} fotos, {len(lap) - n_i} vídeos) — eram {antes} antes de semear")
    print(f"→ {SEEN}")


# ═════════════════════════════════════════════════════════════════════════
# 5. status — o amora reflete o acervo?
# ═════════════════════════════════════════════════════════════════════════

def _carrega(nome: str):
    """Importa um script vizinho de nome com hífen (como os outros fazem)."""
    mod = nome.replace("-", "_").removesuffix(".py")
    if mod in sys.modules:
        return sys.modules[mod]
    spec = importlib.util.spec_from_file_location(mod, Path(__file__).with_name(nome))
    m = importlib.util.module_from_spec(spec)
    sys.modules[mod] = m
    spec.loader.exec_module(m)
    return m


def estado_da_origem(src: str | None, livro: Livro | None, vivos: set[str]) -> tuple[str, dict | None]:
    """(estado, linha) de uma origem:
    sem-id | pendente | subiu | duplicata | apagada-no-amora | retida | excluida"""
    if src is None:
        return "sem-id", None
    if livro is None:
        return "pendente", None
    t = livro.terminal.get(src)
    if t:
        if t["outcome"] == "excluded":
            return "excluida", t
        if t.get("media") and t["media"] not in vivos:
            return "apagada-no-amora", t
        return ("subiu" if t["outcome"] == "ingested" else "duplicata"), t
    u = livro.ultimo.get(src)
    if u and u["outcome"] == "held" and src not in livro.liberados:
        return "retida", u
    return "pendente", u


ORDEM = ["subiu", "duplicata", "pendente", "retida", "apagada-no-amora", "excluida",
         "sem-id", "fora-de-escopo"]

# O que as ingestões sabem subir. Áudio e formatos que o backend não aceita
# como `original` ficam "fora de escopo" — senão o pendente nunca chegaria a 0.
EXT_INGERIVEL = {".jpg", ".jpeg", ".png", ".heic", ".heif",
                 ".mp4", ".mov", ".m4v", ".avi", ".webm", ".3gp", ".mkv"}


def status(acervo: str, servidor: str, saida_json: Path | None) -> None:
    A = _carrega("audit-captura.py")
    I = _carrega("ingest-drive.py")
    por_classe = I.hashes_no_servidor(servidor)
    vivos = set().union(*por_classe.values())
    try:
        livro = Livro()
    except LivroAusente:
        livro = None
    lap = prepara(por_classe, grava=False, livro=livro)

    pastas = A.ler_acervo(Path(acervo), quieto=True)
    passeios, _ = A.carregar_catalogos(servidor)
    A.casar(passeios, pastas)
    por_pasta = {p.pasta.nome: p for p in passeios if p.pasta}

    total = Counter()
    motivos = Counter()
    fora = Counter()
    linhas, vistos_src = [], set()
    for pa in pastas:
        arquivos = [c for c, _ in pa.originais_paths] + [c for c, _ in pa.whatsapp_paths]
        if not arquivos:
            continue
        c = Counter()
        for caminho in arquivos:
            src = chave_drive(caminho)
            if src:
                vistos_src.add(src)
            est, r = estado_da_origem(src, livro, vivos)
            if est in ("pendente", "sem-id") and caminho.suffix.lower() not in EXT_INGERIVEL:
                est = "fora-de-escopo"
                fora[caminho.suffix.lower()] += 1
            c[est] += 1
            if est == "pendente" and r and r.get("reason"):
                motivos[r["reason"]] += 1
        total.update(c)
        p = por_pasta.get(pa.nome)
        linhas.append({"pasta": pa.nome, "passeio": p.edicao if p else None,
                       "arquivos": len(arquivos), **{k: c.get(k, 0) for k in ORDEM}})

    sumiu = []
    if livro:
        sumiu = [r for s, r in livro.ultimo.items()
                 if s.startswith("drive:") and s not in vistos_src]

    n = sum(total.values())
    print("═" * 72)
    print(f"  O AMORA REFLETE O ACERVO?  {n} arquivos de mídia em {len(linhas)} pastas")
    print("═" * 72)
    if livro is None:
        print("  (livro-razão ainda não existe nesta máquina — tudo conta como pendente)")
    rot = {"subiu": "subiu pro amora", "duplicata": "já estava lá (duplicata)",
           "pendente": "PENDENTE (sem desfecho)", "retida": "RETIDA (parece mídia apagada)",
           "apagada-no-amora": "apagada no amora (respeitado)", "excluida": "excluída à mão",
           "sem-id": "sem id do Drive (não rastreável)",
           "fora-de-escopo": "fora de escopo (áudio / formato que o amora não aceita)"}
    for k in ORDEM:
        if total.get(k):
            print(f"  {total[k]:6}  {rot[k]}")
    if fora:
        print("          " + ", ".join(f"{q} {e}" for e, q in fora.most_common()))
    if motivos:
        print("\n  pendentes com nota:")
        for m, q in motivos.most_common(8):
            print(f"    {q:6}  {m}")
    print(f"\n  lápides conhecidas (mídia que o amora já teve e não tem mais): {len(lap)}")
    if sumiu:
        print(f"\n  ORIGEM SUMIU — {len(sumiu)} arquivos com registro no livro que não estão mais no acervo")
        print("  (só relatado: nada é apagado no amora por causa disso)")
        for r in sumiu[:10]:
            print(f"    {r.get('outcome'):10} {r.get('path', r['src'])[:56]}")

    pend = sorted((l for l in linhas if l["pendente"] or l["retida"]),
                  key=lambda l: -(l["pendente"] + l["retida"]))
    if pend:
        print(f"\n  PASTAS COM PENDÊNCIA — {len(pend)}")
        for l in pend[:25]:
            print(f"    {l['pendente']:5} pend {l['retida']:3} ret  de {l['arquivos']:4}  "
                  f"{(l['passeio'] or 'sem passeio'):13} {l['pasta'][:38]}")
        if len(pend) > 25:
            print(f"    … e mais {len(pend) - 25}")
    if saida_json:
        saida_json.write_text(json.dumps(
            {"gerado": agora(), "total": dict(total), "lapides": len(lap),
             "pastas": linhas, "origem_sumiu": sumiu}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\n→ {saida_json}")


def retidos() -> None:
    livro = Livro()
    rs = [r for s, r in livro.ultimo.items()
          if r["outcome"] == "held" and s not in livro.liberados]
    if not rs:
        print("nada retido.")
        return
    print(f"{len(rs)} arquivos retidos — parecem mídia que foi apagada no amora:\n")
    for r in rs:
        print(f"  {r['src']}\n      {r.get('path', '')}\n      hash {r.get('hash')} ~ lápide "
              f"{r.get('media')} ({r.get('dist')} bits)\n")
    print("liberar <origem> = pode subir na próxima rodada · excluir <origem> = nunca sobe")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("status", "semear"):
        s = sub.add_parser(nome)
        s.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER",
                                                            "https://amora.pedalhidrografi.co"))
        if nome == "status":
            s.add_argument("--acervo", default=os.environ.get("BIBLIOTECA_DIR"),
                           help="raiz do acervo (padrão: o do audit-captura.py)")
            s.add_argument("--json", type=Path)
        else:
            s.add_argument("--bucket", default=os.environ.get("GCS_BUCKET", "phidro-state"))
            s.add_argument("--projeto", default=os.environ.get("GCP_PROJECT", "pedal-hidrografico"))
            s.add_argument("--sem-bucket", action="store_true",
                           help="só as fontes locais (sem gcloud)")
    sub.add_parser("retidos")
    for nome in ("liberar", "excluir"):
        s = sub.add_parser(nome)
        s.add_argument("origem", help="drive:<id> ou photos:<uuid>")
        s.add_argument("--motivo")
    a = ap.parse_args()

    if a.cmd == "status":
        status(a.acervo or _carrega("audit-captura.py").ACERVO_PADRAO,
               a.servidor.rstrip("/"), a.json)
    elif a.cmd == "semear":
        semear(a.servidor.rstrip("/"), None if a.sem_bucket else a.bucket, a.projeto)
    elif a.cmd == "retidos":
        retidos()
    else:
        livro = Livro()
        if a.origem not in livro.ultimo:
            sys.exit(f"origem desconhecida no livro: {a.origem}")
        ant = livro.ultimo[a.origem]
        livro.registra(a.origem, "released" if a.cmd == "liberar" else "excluded",
                       reason=a.motivo or "decisão manual", path=ant.get("path"),
                       hash=ant.get("hash"))
        print(f"{a.origem}: {'liberada' if a.cmd == 'liberar' else 'excluída'}")


if __name__ == "__main__":
    main()
