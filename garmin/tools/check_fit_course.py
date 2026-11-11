#!/usr/bin/env python3
"""Confere o codificador de percurso (backend/fit_course.py) com um parser
INDEPENDENTE: o garmin-fit-sdk oficial. Um round-trip pelo próprio escritor
não provaria nada.

    python -m venv .venv && .venv/bin/pip install garmin-fit-sdk
    .venv/bin/python garmin/tools/check_fit_course.py [arquivo.fit]

Sem argumento, gera um percurso sintético (com POIs e altitude) e outro sem
altitude, e confere campo a campo. Com um arquivo, só decodifica e resume.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
import fit_course  # noqa: E402
from garmin_fit_sdk import Decoder, Stream  # noqa: E402


def decode(data: bytes):
    # check_integrity() consome o stream: um Decoder pra conferir, outro pra ler.
    dec = Decoder(Stream.from_byte_array(bytearray(data)))
    assert dec.is_fit(), "cabeçalho FIT inválido"
    assert dec.check_integrity(), "CRC/tamanho inválido"
    msgs, errors = Decoder(Stream.from_byte_array(bytearray(data))).read()
    assert not errors, errors
    return msgs


def summarize(msgs):
    for k, v in msgs.items():
        print(f"  {k}: {len(v)}")
    print("  file_id:", msgs["file_id_mesgs"][0])
    print("  course:", msgs["course_mesgs"][0])
    print("  lap:", msgs["lap_mesgs"][0])
    print("  record[0]:", msgs["record_mesgs"][0])
    print("  record[-1]:", msgs["record_mesgs"][-1])
    for cp in msgs.get("course_point_mesgs", []):
        print("  course_point:", cp)
    for ev in msgs.get("event_mesgs", []):
        print("  event:", ev)


def main():
    if len(sys.argv) > 1:
        summarize(decode(Path(sys.argv[1]).read_bytes()))
        return
    # ~3 km em zigue-zague na zona oeste de SP, 1 ponto a cada ~25 m.
    pts = [[-23.5505 + 0.0002 * i, -46.6833 + 0.00012 * i + 0.0003 * math.sin(i / 5)]
           for i in range(140)]
    eles = [740 + 12 * math.sin(i / 20) for i in range(len(pts))]
    pois = [
        {"lat": pts[40][0], "lng": pts[40][1], "name": "Bica d'água", "sym": "Drinking Water"},
        {"lat": pts[100][0] + 0.0001, "lng": pts[100][1],
         "name": "Padaria São João — café", "sym": "Restaurant"},
        {"lat": pts[10][0], "lng": pts[10][1], "name": "Cuidado: trilho", "sym": "Danger Area"},
    ]
    for label, ele in (("com altitude", eles), ("sem altitude", None)):
        data = fit_course.encode_course("PH 114 · Tietê acima", pts, pois, ele,
                                        created=1_800_000_000, min_spacing_m=0)
        msgs = decode(data)
        print(f"{label}: {len(data)} bytes")
        summarize(msgs)
        fid = msgs["file_id_mesgs"][0]
        assert fid["type"] == "course", fid
        assert msgs["course_mesgs"][0]["name"] == "PH 114 · Tietê acima"
        assert msgs["course_mesgs"][0]["sport"] == "cycling"
        recs = msgs["record_mesgs"]
        assert len(recs) == len(pts)
        semi = 180 / 2 ** 31
        for r, p in zip(recs, pts):
            assert abs(r["position_lat"] * semi - p[0]) < 1e-6
            assert abs(r["position_long"] * semi - p[1]) < 1e-6
        d = [r["distance"] for r in recs]
        assert d[0] == 0 and all(b >= a for a, b in zip(d, d[1:]))
        t = [r["timestamp"] for r in recs]
        assert all(b >= a for a, b in zip(t, t[1:]))
        lap = msgs["lap_mesgs"][0]
        assert abs(lap["total_distance"] - d[-1]) < 0.02
        if ele is not None:
            assert all(abs(r["altitude"] - e) < 0.11 for r, e in zip(recs, eles))
        else:
            assert "altitude" not in recs[0] and "enhanced_altitude" not in recs[0]
        cps = msgs["course_point_mesgs"]
        assert [c["type"] for c in cps] == ["danger", "water", "food"], cps
        assert [c["name"] for c in cps][1] == "Bica d'água"
        assert all(b["distance"] >= a["distance"] for a, b in zip(cps, cps[1:]))
        evs = msgs["event_mesgs"]
        assert evs[0]["event_type"] == "start" and evs[-1]["event_type"] == "stop_disable_all"
    print("OK")


if __name__ == "__main__":
    main()
