#!/usr/bin/env python3
"""Transforma um PERCURSO (.fit de /garmin/course/…) num pedal simulado ao
longo dele, pra tocar no simulador do Connect IQ.

É a entrada que faltava pra testar os campos com posição de verdade: o
aparelho simulado "pedala" a rota do passeio a velocidade constante, com um
registro por segundo. O radar do campo Pessoas mostra o traçado passando por
baixo; com a transmissão ligada, o "Garmin" aparece andando no mapa do amora.

    pip install garmin-fit-sdk
    curl -o ph.fit https://amora.pedalhidrografi.co/garmin/course/t/<slug>.fit
    python garmin/tools/course_to_ride.py ph.fit pedal.fit --speed 6

No simulador: Data Fields > Timer > Start Activity, depois
Simulation > FIT Data > Playback File…

O percurso não tem altitude: o pedal sai plano (`--alt`, 740 m por padrão),
então a energia do Quilojaules aqui é só rolamento + arrasto. `--speed` é em
m/s (6 ≈ 22 km/h; 30 faz 26 km passarem em 15 min, pra ver o radar andar).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fit_course import FIT_EPOCH_OFFSET  # noqa: E402
from garmin_fit_sdk import Decoder, Stream  # noqa: E402
from speedup_fit import write_activity  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("course")
    ap.add_argument("dst")
    ap.add_argument("--speed", type=float, default=6.0, help="m/s (padrão 6)")
    ap.add_argument("--alt", type=float, default=740.0, help="altitude constante, m")
    a = ap.parse_args()
    if a.speed <= 0:
        ap.error("--speed precisa ser > 0")

    msgs, _errors = Decoder(Stream.from_file(a.course)).read()
    pts = [(r["position_lat"], r["position_long"], float(r["distance"]))
           for r in msgs.get("record_mesgs", [])
           if r.get("position_lat") is not None and r.get("distance") is not None]
    if len(pts) < 2:
        sys.exit("o percurso não tem pontos com posição e distância")

    out, j = [], 0
    total = pts[-1][2]
    d = 0.0
    while True:
        d = min(d, total)
        while j < len(pts) - 2 and pts[j + 1][2] < d:
            j += 1
        (la0, lo0, d0), (la1, lo1, d1) = pts[j], pts[j + 1]
        f = (d - d0) / (d1 - d0) if d1 > d0 else 0.0
        f = max(0.0, min(1.0, f))
        out.append({"lat": round(la0 + (la1 - la0) * f), "lng": round(lo0 + (lo1 - lo0) * f),
                    "dist": d, "alt": a.alt, "power": None, "hr": None, "cad": None})
        if d >= total:
            break
        d += a.speed

    n, dist = write_activity(a.dst, out, int(time.time()) - FIT_EPOCH_OFFSET)
    print(f"{a.dst}: {n} registros ({n / 60:.1f} min no simulador), {dist / 1000:.1f} km a "
          f"{a.speed:g} m/s ({a.speed * 3.6:.0f} km/h)")


if __name__ == "__main__":
    main()
