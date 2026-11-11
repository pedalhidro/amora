#!/usr/bin/env python3
"""Acelera um .fit de atividade pra testar os campos de dados no simulador.

O simulador do Connect IQ toca um .fit em tempo real, sem avançar: pra ver o
que o campo mostra aos 10 min (ou aos 300 kJ) seria preciso esperar. Este
script regrava a atividade com 1 registro a cada `--factor` originais e os
instantes de 1 em 1 segundo — um pedal de 2 h passa em 6 min com --factor 20.

    pip install garmin-fit-sdk
    python garmin/tools/speedup_fit.py pedal.fit rapido.fit --factor 20
    python garmin/tools/speedup_fit.py pedal.fit trecho.fit --factor 10 --skip-min 10 --max-min 60

No simulador: Simulation > FIT Data > Playback File…

O que muda e o que não:
  • distância e altitude ficam as do pedal — é o que o modelo de kJ lê, então
    a energia do MODELO sai igual à do pedal de verdade;
  • a velocidade aparece `factor` vezes maior;
  • a potência é a média da janela × `factor`, pra a energia MEDIDA (∫P·dt)
    também bater com a do pedal (o número de watts em si fica absurdo).
`--skip-min` corta o começo (a distância recomeça do zero); `--max-min`
limita a duração, em minutos do pedal ORIGINAL.
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fit_course import (  # noqa: E402
    FIT_EPOCH_OFFSET, _ENUM, _SINT32, _UINT8, _UINT16, _UINT32, _UINT32Z, _Writer,
)
from garmin_fit_sdk import Decoder, Stream  # noqa: E402

MESG_FILE_ID, MESG_SESSION, MESG_LAP, MESG_RECORD = 0, 18, 19, 20
MESG_EVENT, MESG_ACTIVITY = 21, 34
SINT32_INVALID = 0x7FFFFFFF


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--factor", type=int, default=20, help="aceleração (padrão 20)")
    ap.add_argument("--skip-min", type=float, default=0, help="pula os primeiros N min do pedal")
    ap.add_argument("--max-min", type=float, default=0, help="usa no máximo N min do pedal (0 = tudo)")
    a = ap.parse_args()
    if a.factor < 1:
        ap.error("--factor precisa ser ≥ 1")

    msgs, errors = Decoder(Stream.from_file(a.src)).read()
    recs = [r for r in msgs.get("record_mesgs", [])
            if r.get("timestamp") is not None and r.get("distance") is not None]
    if len(recs) < 2:
        sys.exit("o .fit não tem registros com distância")
    t_first = recs[0]["timestamp"]
    lo = a.skip_min * 60
    hi = lo + a.max_min * 60 if a.max_min else float("inf")
    recs = [r for r in recs if lo <= (r["timestamp"] - t_first).total_seconds() <= hi]
    if len(recs) < 2 * a.factor:
        sys.exit("sobrou pedal de menos nesse recorte")

    d0 = recs[0]["distance"]
    out = []
    last_alt = None
    for i in range(0, len(recs), a.factor):
        win = recs[i:i + a.factor]
        r = win[-1]                     # estado no FIM da janela
        alt = r.get("enhanced_altitude", r.get("altitude"))
        if alt is None:
            alt = last_alt if last_alt is not None else 0.0
        last_alt = alt
        powers = [w["power"] for w in win if w.get("power") is not None]
        power = round(sum(powers) / len(powers) * a.factor) if powers else None
        out.append({
            "lat": r.get("position_lat"), "lng": r.get("position_long"),
            "dist": float(r["distance"]) - float(d0), "alt": float(alt),
            "power": power, "hr": r.get("heart_rate"), "cad": r.get("cadence"),
        })

    t0 = int(recs[0]["timestamp"].timestamp()) - FIT_EPOCH_OFFSET
    n = len(out)
    t_end = t0 + n - 1
    total = out[-1]["dist"]
    elapsed_ms = max(1, (n - 1) * 1000)

    w = _Writer()
    w.define(0, MESG_FILE_ID, [(0, _ENUM), (1, _UINT16), (2, _UINT16), (3, _UINT32Z), (4, _UINT32)])
    w.data(0, 4, 255, 1, (t0 & 0xFFFFFFFF) or 1, t0)              # type 4 = activity
    w.define(1, MESG_EVENT, [(253, _UINT32), (0, _ENUM), (1, _ENUM), (4, _UINT8)])
    w.data(1, t0, 0, 0, 0)                                         # timer start
    # timestamp, lat, long, altitude, distance, enhanced_speed, power, hr, cadence
    w.define(2, MESG_RECORD, [(253, _UINT32), (0, _SINT32), (1, _SINT32), (2, _UINT16),
                              (5, _UINT32), (73, _UINT32), (7, _UINT16), (3, _UINT8), (4, _UINT8)])
    prev = 0.0
    for k, r in enumerate(out):
        speed = max(0.0, r["dist"] - prev)                         # m por registro = m/s
        prev = r["dist"]
        w.data(2, t0 + k,
               r["lat"] if r["lat"] is not None else SINT32_INVALID,
               r["lng"] if r["lng"] is not None else SINT32_INVALID,
               max(0, min(0xFFFE, round((r["alt"] + 500.0) * 5.0))),
               round(r["dist"] * 100), round(speed * 1000),
               min(65000, r["power"]) if r["power"] is not None else 0xFFFF,
               min(254, r["hr"]) if r["hr"] is not None else 0xFF,
               min(254, r["cad"]) if r["cad"] is not None else 0xFF)
    w.data(1, t_end, 0, 4, 0)                                      # timer stop_all
    summary = [(254, _UINT16), (253, _UINT32), (0, _ENUM), (1, _ENUM), (2, _UINT32),
               (7, _UINT32), (8, _UINT32), (9, _UINT32)]
    w.define(3, MESG_LAP, summary)
    w.data(3, 0, t_end, 9, 1, t0, elapsed_ms, elapsed_ms, round(total * 100))    # lap / stop
    w.define(4, MESG_SESSION, summary + [(5, _ENUM), (6, _ENUM), (25, _UINT16), (26, _UINT16)])
    w.data(4, 0, t_end, 8, 1, t0, elapsed_ms, elapsed_ms, round(total * 100), 2, 0, 0, 1)
    w.define(5, MESG_ACTIVITY, [(253, _UINT32), (0, _UINT32), (1, _UINT16), (2, _ENUM),
                                (3, _ENUM), (4, _ENUM)])
    w.data(5, t_end, elapsed_ms, 1, 0, 26, 1)                      # manual / activity / stop
    Path(a.dst).write_bytes(w.finish())

    mins = (recs[-1]["timestamp"] - recs[0]["timestamp"]).total_seconds() / 60
    print(f"{a.dst}: {n} registros ({n / 60:.1f} min no simulador) = {mins:.0f} min de pedal, "
          f"{total / 1000:.1f} km, ×{a.factor}"
          + (f"; avisos do decodificador: {errors[:2]}" if errors else ""))


if __name__ == "__main__":
    main()
