#!/usr/bin/env python3
"""Teste dos endpoints /garmin/… (backend/garmin.py) com o test client do
Flask, sobre uma CÓPIA temporária do estado do repo — nada é escrito em web/
e nenhuma rede é usada (o fetch do RideWithGPS é trocado por uma falha, que
é o caminho de fallback).

    pip install -r backend/requirements.txt garmin-fit-sdk
    python garmin/tools/test_backend.py

O catálogo do repo não tem passeio futuro, então um passeio ganha uma data
daqui a 3 dias pra exercitar "próximos passeios" e o glance.
"""
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FUTURE_TOUR = "pas:74d4aa50"            # PH 111, rota no RideWithGPS
FUTURE_SLUG = "ano-novo-guarani-na-tekoa-yvypora"


def build_state(tmp: Path):
    (tmp / "data").mkdir()
    for name in ("tours.ttl", "identities.ttl", "ontology.ttl", "shapes.ttl",
                 "tour-iri-map.json"):
        shutil.copy(REPO / "web" / "data" / name, tmp / "data" / name)
    for name in ("routes.json", "saved_routes.json", "llms.txt"):
        shutil.copy(REPO / "web" / name, tmp / name)
    ttl = (tmp / "data" / "tours.ttl").read_text(encoding="utf-8")
    start = ttl.index(f"{FUTURE_TOUR} a ph:Tour")
    when = (datetime.now(timezone(timedelta(hours=-3))) + timedelta(days=3)) \
        .replace(hour=8, minute=30, second=0, microsecond=0)
    head, tail = ttl[:start], ttl[start:]
    tail, n = re.subn(r'dcterms:date "[^"]+"', f'dcterms:date "{when.isoformat()}"',
                      tail, count=1)
    assert n == 1, "não achou a data do passeio de teste"
    (tmp / "data" / "tours.ttl").write_text(head + tail, encoding="utf-8")
    return when


def main():
    tmp = Path(tempfile.mkdtemp(prefix="amora-garmin-test-"))
    try:
        when = build_state(tmp)
        os.environ.update(PHIDRO_WEB=str(tmp), PHIDRO_NO_WARMUP="1",
                          STORAGE_BACKEND="local")
        sys.path.insert(0, str(REPO / "backend"))
        import main as backend
        import rwgps
        rwgps.http_get = lambda url, accept=None: (503, "")   # sem rede no teste
        c = backend.app.test_client()

        # ── lista ────────────────────────────────────────────────────────
        r = c.get("/garmin/list")
        assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
        body = r.get_json()
        assert [i["id"] for i in body["next"]] == [FUTURE_SLUG], body["next"]
        assert f"{when.day}/{when.month} · 8h30" in body["next"][0]["s"], body["next"][0]
        assert FUTURE_SLUG not in [i["id"] for i in body["recent"]]
        assert len(body["recent"]) == 6 and "sent" not in body
        assert all(set(i) == {"k", "id", "n", "s"} for i in body["recent"] + body["routes"])
        assert len(r.data) < 4000, len(r.data)
        g = c.get("/garmin/list?glance=1").get_json()
        assert g["next"]["id"] == FUTURE_SLUG and len(json.dumps(g)) < 300

        # ── ficha ────────────────────────────────────────────────────────
        t = c.get(f"/garmin/item/t/{FUTURE_SLUG}").get_json()
        assert t["kj"] == 279 and t["band"] == "Ok" and t["place"] == "Museu Indigena"
        assert 2 <= len(t["pts"]) <= 60 and t["km"] > 5
        assert c.get("/garmin/item/t/74d4aa50").get_json()["id"] == FUTURE_SLUG  # slug8
        route_slug = body["routes"][0]["id"]
        ri = c.get(f"/garmin/item/r/{route_slug}").get_json()
        assert ri["k"] == "r" and ri["fit"].endswith(f"/r/{route_slug}.fit")
        assert c.get("/garmin/item/r/nao-existe").status_code == 404
        assert c.get("/garmin/item/x/qualquer").status_code == 404

        # ── percurso FIT ─────────────────────────────────────────────────
        for url, min_recs in ((ri["fit"], 2), (t["fit"], 50)):
            f = c.get(url)
            assert f.status_code == 200 and f.mimetype == "application/vnd.ant.fit"
            assert f.data[8:12] == b".FIT"
            assert f.headers["ETag"]
            try:
                from garmin_fit_sdk import Decoder, Stream
            except ImportError:
                print("  (garmin-fit-sdk ausente: percurso não decodificado)")
                continue
            assert Decoder(Stream.from_byte_array(bytearray(f.data))).check_integrity()
            msgs, errs = Decoder(Stream.from_byte_array(bytearray(f.data))).read()
            assert not errs and msgs["file_id_mesgs"][0]["type"] == "course"
            assert len(msgs["record_mesgs"]) >= min_recs
        assert c.get("/garmin/course/r/nao-existe.fit").status_code == 404

        # ── freio do RideWithGPS ─────────────────────────────────────────
        # Passeios com rota no RideWithGPS: a geometria cheia é buscada lá.
        import garmin
        rw = [r for r in json.loads((tmp / "routes.json").read_text())["routes"]
              if r.get("provider") == "rwgps" and r.get("latlngs") and r.get("slug")]
        assert len(rw) >= 3
        calls = []
        gpx = ('<gpx><trk><trkseg>' + ''.join(
            f'<trkpt lat="{-23.5 - i * 1e-4}" lon="-46.6"><ele>{760 + i}</ele></trkpt>'
            for i in range(300)) + '</trkseg></trk></gpx>')

        def fake_get(url, accept=None):
            calls.append(url)
            return (200, gpx)
        rwgps.http_get = fake_get
        garmin._geom_cache.clear()
        garmin._rwgps_gate[0] = 0.0
        fit = lambda slug: c.get(f"/garmin/course/t/{slug}.fit")  # noqa: E731
        full = fit(rw[0]["slug"])                 # 1º pedido: busca no RideWithGPS
        assert full.status_code == 200 and len(calls) == 1
        assert fit(rw[0]["slug"]).data[14:] != b"" and len(calls) == 1      # cache
        held = fit(rw[1]["slug"])                 # outra rota, em seguida: freio
        assert held.status_code == 200 and len(calls) == 1
        garmin._rwgps_gate[0] = 0.0               # passou o intervalo
        assert fit(rw[1]["slug"]).status_code == 200 and len(calls) == 2
        rwgps.http_get = lambda url, accept=None: (calls.append(url), (503, ""))[1]
        garmin._rwgps_gate[0] = 0.0
        assert fit(rw[2]["slug"]).status_code == 200 and len(calls) == 3    # falhou
        garmin._rwgps_gate[0] = 0.0
        assert fit(rw[2]["slug"]).status_code == 200 and len(calls) == 3    # não insiste

        # ── pareamento + envio ───────────────────────────────────────────
        send = lambda **kw: c.post("/garmin/send", json=kw)  # noqa: E731
        assert send(code="xx", k="r", id=route_slug).status_code == 400
        assert send(code="abc123", k="r", id="nao-existe").status_code == 404
        first = send(code="AB-C 12O", k="r", id=route_slug).get_json()
        assert first == {"ok": True, "seen": False, "name": body["routes"][0]["n"]}
        # Um GET com o código lê os envios mas NÃO grava nada (não registra).
        sent = c.get("/garmin/list?code=abc120").get_json()["sent"]
        assert [i["id"] for i in sent] == [route_slug]
        assert send(code="abc120", k="r", id=route_slug).get_json()["seen"] is False
        assert c.get("/garmin/list?code=zzzzzz").get_json()["sent"] == []
        queue = json.loads((tmp / "garmin_queue.json").read_text())
        assert set(queue["codes"]) == {"abc120"} and not queue["codes"]["abc120"]["seen"]
        # O aparelho abre o app (POST com o código): agora ele fica "visto".
        sent = c.post("/garmin/list", json={"code": "ABC 120"}).get_json()
        assert [i["id"] for i in sent["sent"]] == [route_slug] and sent["next"]
        again = send(code="abc120", k="t", id=FUTURE_SLUG).get_json()
        assert again["seen"] is True
        sent = c.post("/garmin/list", json={"code": "abc120"}).get_json()["sent"]
        assert [i["id"] for i in sent] == [FUTURE_SLUG, route_slug]   # mais novo primeiro
        send(code="abc120", k="r", id=route_slug)                      # reenvio não duplica
        assert len(c.get("/garmin/list?code=abc120").get_json()["sent"]) == 2
        assert "sent" not in c.post("/garmin/list", json={}).get_json()

        # ── ao vivo ──────────────────────────────────────────────────────
        tok_a, tok_b = "a" * 32, "b" * 32
        assert c.post("/garmin/live", json={}).get_json() == {"n": 0, "p": []}
        for tok, name, lat in ((tok_a, "Ana", -23.55), (tok_b, "Bia", -23.56)):
            assert c.post("/live-location", json={"id": tok, "name": name, "lat": lat,
                                                  "lng": -46.63}).status_code == 200
        live = c.post("/garmin/live", json={"id": tok_a})
        assert tok_a not in live.get_data(as_text=True) and tok_b not in live.get_data(as_text=True)
        lj = live.get_json()
        assert lj["n"] == 1 and lj["p"][0][:3] == ["Bia", -23.56, -46.63] and lj["p"][0][3] <= 2
        assert c.post("/garmin/live").get_json()["n"] == 2   # sem corpo: todo mundo
        print("OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
