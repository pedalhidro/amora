"""Vista fixa das rotas do amora na região de São Paulo (a de Oakland fica de fora).

Parte do enquadramento de TODAS as rotas, corta 1/3 de baixo e 1/3 da direita, e depois encosta as
bordas de cima e da esquerda nas rotas (TL_PAD px). Como sobra mais à esquerda que em cima, o mapa é
ESTICADO na horizontal (kx > 1) pra preencher 16:9 — distorção consentida.

Coordenadas de tela (superamostradas): x = (mx - ox) * kx, y = my - oy, com (mx, my) = Mercator em px
no zoom zv."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
W, H, SS = R.W, R.H, R.SS
MARGIN = 0.05
KEEP = 2 / 3            # fração da vista "todas as rotas" que fica (a partir do canto de cima-esquerda)
BOTTOM_LAT = -23.905    # borda de baixo: logo abaixo da Cratera de Colônia (centro ~-23.87, raio ~1,8 km)
STRETCH = float(os.environ.get("STRETCH", 1.147))         # esticão horizontal (o mesmo da versão anterior); a borda direita sai dele
TL_PAD = 50             # px finais entre a borda de cima/esquerda e a rota mais ao norte/oeste
MIN_DENTRO = 0.3        # rota com menos que isso dentro do quadro sai da animação


def rotas(S):
    r = [e for e in json.load(open(f"{S}/../routes.json"))["routes"] if e.get("latlngs")]
    dentro = [e for e in r if -25 < e["latlngs"][0][0] < -22 and -48 < e["latlngs"][0][1] < -45]
    fora = [e for e in r if e not in dentro]
    return sorted(dentro, key=lambda e: e["dateMs"]), fora


def vista(S):
    rs, _ = rotas(S)
    xs = [R.merc(la, lo, 0)[0] for e in rs for la, lo in e["latlngs"]]
    ys = [R.merc(la, lo, 0)[1] for e in rs for la, lo in e["latlngs"]]
    Z = math.log2(min(W * (1 - 2 * MARGIN) / (max(xs) - min(xs)), H * (1 - 2 * MARGIN) / (max(ys) - min(ys))))
    f = 2 ** (Z + math.log2(SS))
    cx, cy = (min(xs) + max(xs)) / 2 * f, (min(ys) + max(ys)) / 2 * f
    ox, oy = cx - W * SS / 2, cy - H * SS / 2
    xr, yb = ox + W * SS * KEEP, oy + H * SS * KEEP            # bordas direita e de baixo depois do corte
    x0, y0 = min(xs) * f - TL_PAD * SS * KEEP, min(ys) * f - TL_PAD * SS * KEEP
    yb = R.merc(BOTTOM_LAT, 0, 0)[1] * f                       # borda de baixo fixada pela cratera
    ky = H * SS / (yb - y0)
    zv = math.log2(f) + math.log2(ky)                          # o zoom passa a ser o da escala vertical
    return dict(Z=zv - math.log2(SS), zv=zv, ox=x0 * ky, oy=y0 * ky, kx=STRETCH)


def xy(la, lo, v):
    mx, my = R.merc(la, lo, v["zv"])
    return (mx - v["ox"]) * v["kx"], my - v["oy"]


def lonlat(sx, sy, v):
    s = 256 * 2 ** v["zv"]
    px, py = sx / v["kx"] + v["ox"], sy + v["oy"]
    return px / s * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / s))))


def bbox(v):
    w, n = lonlat(0, 0, v); e, s = lonlat(W * SS, H * SS, v)
    return w, s, e, n


def visiveis(S, v=None):
    """(rotas que entram na animação, rotas da região que ficaram fora do quadro)"""
    v = v or vista(S)
    rs, _ = rotas(S)
    ok, fora = [], []
    for e in rs:
        n = sum(1 for la, lo in e["latlngs"] if (lambda p: 0 <= p[0] <= W * SS and 0 <= p[1] <= H * SS)(xy(la, lo, v)))
        (ok if n / len(e["latlngs"]) >= MIN_DENTRO else fora).append(e)
    return ok, fora


def mosaico(url, v, cache):
    """Tiles do zoom inteiro mais próximo cobrindo a vista, reamostrados (com o esticão) pro quadro."""
    tz = min(16, round(v["zv"]))
    f = 2 ** (tz - v["zv"])
    x0, y0 = v["ox"] * f, v["oy"] * f
    x1, y1 = (v["ox"] + W * SS / v["kx"]) * f, (v["oy"] + H * SS) * f
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    big = Image.new("RGBA", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (0, 0, 0, 0))
    jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
    with ThreadPoolExecutor(8) as ex:
        for (x, y), im in zip(jobs, ex.map(lambda j: R.tile(url, tz, j[0], j[1], cache), jobs)):
            if im:
                big.paste(im, ((x - tx0) * 256, (y - ty0) * 256))
    return big.resize((W * SS, H * SS), Image.LANCZOS, box=(x0 - tx0 * 256, y0 - ty0 * 256, x1 - tx0 * 256, y1 - ty0 * 256))


def chave(v):
    return f"{v['Z']:.3f}-{v['kx']:.3f}"


if __name__ == "__main__":
    S = sys.argv[1]
    v = vista(S); ok, fora = visiveis(S, v)
    w, s, e, n = bbox(v)
    mpp = 156543.03 * math.cos(math.radians((n + s) / 2)) / 2 ** v["Z"]
    print(f"zoom {v['Z']:.2f} (vertical), esticão horizontal {v['kx']:.3f}; bbox W{w:.3f} S{s:.3f} E{e:.3f} N{n:.3f}; m/px {mpp:.1f} (vert.) / {mpp / v['kx']:.1f} (horiz.); "
          f"{len(ok)} rotas dentro; {len(fora)} fora:")
    for x in fora:
        print("   ", x["date"], (x.get("number") or {}).get("source", ""), (x.get("number") or {}).get("value", ""), "|", x["name"][:50])
