#!/usr/bin/env python3
"""Importa `ph:linkActivity` (a URL da gravação GPS) a partir da planilha do censo.

`ph:linkActivity` estava em **0 de 109** passeios, e é ele que destrava o
pós-passeio: sem a URL da gravação, `ph:departedAt`, `ph:arrivedAt`,
`ph:movingDuration` e `ph:measuredEnergy` não têm de onde ser reconstruídos.

A planilha do censo já tem essas URLs, curadas à mão — este script só as traz
pro catálogo, que é onde elas passam a ser úteis (e duráveis: ninguém precisa
refazer o casamento nunca mais).

**Como casa planilha → passeio.** A chave é a URL da ROTA, não a data e muito
menos o número da edição:

- **rota** (`ph:linkRoute` → `schema:url` → `/routes/<id>`): exata e inequívoca.
  Cobre a maioria.
- **data exata**: pros passeios sem rota na planilha. Tentada ANTES de alargar
  a janela — alargar direto pra ±1 dia faz o pedal VIZINHO entrar como
  candidato e o casamento vira ambíguo (foi o que aconteceu com o BP/1
  "Represa do Guarapiranga", de 2024-11-20, contra o PH/14 do dia 19).
- **data ±1 dia**: só se a data exata não achar nada (algumas linhas da
  planilha caem na véspera).
- Rota reusada por dois passeios diferentes (acontece — a mesma rota volta a
  ser pedalada) é desempatada pela data.

Nada de casar por NÚMERO de edição: a numeração colide de propósito no acervo
(existe um "28 Lavapés Aclimação 2" e um "35 Braço Morto do Tietê" que são
eventos distintos dos PH/28 e PH/35 do catálogo).

Escreve por `POST /upload-tour` com `mode=patch` — o backend é o único escritor
legítimo do catálogo, e o patch preserva todo predicado que este script não
conhece.

    python scripts/import-activities-censo.py --tsv <arquivo>              # dry-run
    python scripts/import-activities-censo.py --tsv <arquivo> --apply
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import rdflib

REPO = Path(__file__).resolve().parents[1]
TOURS = REPO / "web" / "data" / "tours.ttl"

PH = rdflib.Namespace("https://id.pedalhidrografi.co/terms#")
DCT = rdflib.Namespace("http://purl.org/dc/terms/")
SCHEMA = rdflib.Namespace("https://schema.org/")

SERVIDOR_PADRAO = "https://amora.pedalhidrografi.co"

# A gravação: uma ATIVIDADE do Strava ou um TRIP do RideWithGPS. Repare que
# `strava.com/routes/...` e `ridewithgps.com/routes/...` são ROTAS PLANEJADAS,
# não gravações — a planilha tem as duas coisas, e confundi-las gravaria uma
# rota no lugar da gravação.
RE_ATIVIDADE = re.compile(r"https://(?:www\.strava\.com/activities/\d+|ridewithgps\.com/trips/\d+)")
RE_ROTA = re.compile(r"https://(?:ridewithgps\.com|www\.strava\.com)/routes/(\d+)")

TTL = """@prefix ph: <https://id.pedalhidrografi.co/terms#> .
@prefix pas: <https://id.pedalhidrografi.co/passeio/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

pas:{slug} a ph:Tour ;
    ph:linkActivity "{url}"^^xsd:anyURI .
"""


def carregar_planilha(caminho: Path) -> list[dict]:
    linhas = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        campos = linha.split("\t")
        act = RE_ATIVIDADE.search(linha)
        rota = RE_ROTA.search(linha)
        linhas.append({
            "data": campos[0][:10],
            "titulo": campos[6] if len(campos) > 6 else "",
            "atividade": act.group(0) if act else None,
            "rota": rota.group(1) if rota else None,
        })
    return linhas


def indexar_catalogo(g):
    por_rota, por_data, meta = defaultdict(list), defaultdict(list), {}
    for t in g.subjects(rdflib.RDF.type, PH.Tour):
        data = str(g.value(t, DCT.date))[:10]
        por_data[data].append(t)
        ed = g.value(t, PH.inSeriesEdition)
        meta[t] = {
            "data": data,
            "titulo": str(g.value(t, DCT.title) or ""),
            "edicao": str(ed).split("/passeio/")[-1] if ed else "—",
            "tem": g.value(t, PH.linkActivity) is not None,
        }
        r = g.value(t, PH.linkRoute)
        if r is not None:
            u = g.value(r, SCHEMA.url)
            if u is not None:
                m = re.search(r"/routes/(\d+)", str(u))
                if m:
                    por_rota[m.group(1)].append(t)
    return por_rota, por_data, meta


def casar(linha, por_rota, por_data, meta):
    """Devolve (passeio, como) ou (None, motivo)."""
    base = datetime.date.fromisoformat(linha["data"])

    if linha["rota"]:
        cands = por_rota.get(linha["rota"], [])
        if len(cands) == 1:
            return cands[0], "rota"
        if len(cands) > 1:
            # Mesma rota pedalada mais de uma vez — desempata pela data.
            perto = [c for c in cands
                     if abs((datetime.date.fromisoformat(meta[c]["data"]) - base).days) <= 1]
            if len(perto) == 1:
                return perto[0], "rota+data"

    # Data EXATA primeiro. Alargar direto pra ±1 traria o pedal vizinho junto.
    exatos = por_data.get(linha["data"], [])
    if len(exatos) == 1:
        return exatos[0], "data"
    if len(exatos) > 1:
        return None, "dois passeios na mesma data"

    vizinhos = []
    for dd in (-1, 1):
        vizinhos += por_data.get((base + datetime.timedelta(days=dd)).isoformat(), [])
    if len(vizinhos) == 1:
        return vizinhos[0], "data±1"
    return None, "sem passeio correspondente" if not vizinhos else "ambíguo na janela de ±1 dia"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tsv", type=Path, required=True, help="planilha do censo (TSV)")
    ap.add_argument("--apply", action="store_true", help="grava (default: só mostra)")
    ap.add_argument("--servidor", default=os.environ.get("PHIDRO_SERVER", SERVIDOR_PADRAO))
    ap.add_argument("--force", action="store_true",
                    help="sobrescreve ph:linkActivity já existente")
    a = ap.parse_args()

    g = rdflib.Graph()
    g.parse(TOURS, format="turtle")
    por_rota, por_data, meta = indexar_catalogo(g)
    linhas = carregar_planilha(a.tsv)

    com_atividade = [l for l in linhas if l["atividade"]]
    casados, falhas, pulados = {}, [], []
    for l in com_atividade:
        t, como = casar(l, por_rota, por_data, meta)
        if t is None:
            falhas.append((l, como))
            continue
        if t in casados:
            falhas.append((l, f"passeio já casado com outra linha ({casados[t][1]})"))
            continue
        if meta[t]["tem"] and not a.force:
            pulados.append((t, l))
            continue
        casados[t] = (l["atividade"], como)

    print(f"planilha: {len(linhas)} linhas, {len(com_atividade)} com gravação")
    print(f"casaram:  {len(casados)}   não casaram: {len(falhas)}   "
          f"já tinham (pulados): {len(pulados)}\n")

    for t, (url, como) in sorted(casados.items(), key=lambda kv: meta[kv[0]]["data"]):
        m = meta[t]
        print(f"  {m['data']}  {m['edicao']:8} {como:9} {m['titulo'][:34]:36} {url}")

    if falhas:
        print(f"\n  NÃO CASARAM ({len(falhas)}) — precisam de olho humano:")
        for l, motivo in falhas:
            print(f"    {l['data']}  {l['titulo'][:38]:40} → {motivo}")

    if not a.apply:
        print(f"\n{len(casados)} gravações a importar. Rode com --apply pra gravar.")
        return

    import urllib.error
    import urllib.request

    ok = 0
    for t, (url, _) in casados.items():
        slug = str(t).rsplit("/", 1)[-1]
        ttl = TTL.format(slug=slug, url=url)
        body, headers = multipart({"ttl": ttl, "mode": "patch"})
        req = urllib.request.Request(f"{a.servidor.rstrip('/')}/upload-tour",
                                     data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    ok += 1
                else:
                    print(f"  ✗ {slug}: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"  ✗ {slug}: HTTP {e.code}: {e.read().decode()[:160]}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {slug}: {e}")
    print(f"\n✓ {ok}/{len(casados)} gravações importadas via {a.servidor}")


def multipart(campos: dict[str, str]) -> tuple[bytes, dict]:
    bnd = "----phidroimport" + os.urandom(8).hex()
    partes = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
              for k, v in campos.items()]
    partes.append(f"--{bnd}--\r\n")
    return "".join(partes).encode("utf-8"), {
        "Content-Type": f"multipart/form-data; boundary={bnd}"}


if __name__ == "__main__":
    main()
