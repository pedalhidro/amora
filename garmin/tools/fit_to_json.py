#!/usr/bin/env python3
"""Extrai de um .fit de ATIVIDADE as séries que o campo Quilojaules lê no
aparelho — distância acumulada, altitude, potência e tempo, uma amostra por
`record` — num JSON pro garmin/tools/kj_parity.mjs.

    pip install garmin-fit-sdk
    python garmin/tools/fit_to_json.py pedal.fit > pedal.json
"""
import json
import sys

from garmin_fit_sdk import Decoder, Stream


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    msgs, errors = Decoder(Stream.from_file(sys.argv[1])).read()
    if errors:
        print(f"avisos do decodificador: {errors[:3]}", file=sys.stderr)
    t0 = None
    out = {"s": [], "h": [], "p": [], "t": [], "laps": []}
    for r in msgs.get("record_mesgs", []):
        s = r.get("distance")
        h = r.get("enhanced_altitude", r.get("altitude"))
        ts = r.get("timestamp")
        if s is None or ts is None:
            continue
        if t0 is None:
            t0 = ts
        out["s"].append(round(float(s), 2))
        out["h"].append(None if h is None else round(float(h), 2))
        out["p"].append(r.get("power"))
        out["t"].append(round((ts - t0).total_seconds(), 1))
    for lap in msgs.get("lap_mesgs", []):
        if lap.get("start_time") is not None and t0 is not None:
            out["laps"].append(round((lap["start_time"] - t0).total_seconds(), 1))
    ses = (msgs.get("session_mesgs") or [{}])[0]
    out["session"] = {k: ses.get(k) for k in
                      ("total_distance", "total_ascent", "total_work", "avg_power")}
    json.dump(out, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
