#!/usr/bin/env python3
"""PoC 7: a abertura "todas as rotas" (v4b) em 3D, como o modo 3D do cameratopo: o mapa drapeado
sobre o relevo (FABDEM), sem iluminação extra, câmera olhando pro norte.

  câmera: campo de visão VERTICAL de 1°, inclinada 45° em relação ao horizonte, exagero vertical 2×
  vista:  o mesmo retângulo de chão da v4b (o esticão horizontal de lá some: a inclinação de 45°
          encurta o norte–sul por sen 45° e o retângulo passa a caber em 16:9 com geometria real)

As rotas são desenhadas na TEXTURA (ficam deitadas no relevo); rótulos e a bolinha da ponta ficam
retos, na tela, na posição projetada (com a elevação).

  intro_3d.py <dir> --check            → números de conferência + all3d-flat.jpg / all3d-relevo.jpg
  intro_3d.py <dir> --still 0.6 9      → quadros de conferência
  intro_3d.py <dir> --out x.mp4
"""
import argparse, math, os, subprocess, sys, textwrap, time
os.environ["STRETCH"] = "1.459"                       # a vista da v4b
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R, view_all as V
Image.MAX_IMAGE_PIXELS = None

W, H, SS = R.W, R.H, R.SS
SW, SH = W * SS, H * SS
FOV_V = 1.0
PITCH = float(os.environ.get("PITCH", 30.0))
EX = float(os.environ.get("EX", 2.0))
ZOOM = float(os.environ.get("ZOOM", 1.15))     # aproximação além do enquadramento "os 4 cantos cabem"
TAG = f"p{PITCH:g}-e{EX:g}-z{ZOOM:g}"   #                      # graus, graus em relação ao horizonte, exagero
TW = 4096                                              # largura da textura (px)
PAD_EW = 0.03          # folga leste/oeste da textura; norte/sul saem da geometria da câmera
Z_REF = 771.0         # m: altura do planalto (mediana do retângulo da v4b) — o enquadramento é feito nela
#                # folga da textura além do retângulo da v4b
TOTAL, NVIS = 20.0, 10
HOLD = float(os.environ.get("HOLD", 0.8)); DRAW = float(os.environ.get("DRAW", 1.5))
NLAB = 5               # rótulos: só nas 5 rotas mais recentes (10 rótulos de uma vez viram poluição)
TITULO = ["resumo audiovisual sistemático", "de mídias gravadas em passeios", "do pedal hidrográfico", "entre 2024 e 2026"]
TIT_FONT = os.path.expanduser("~/Library/Fonts/COOPBL.TTF")   # Cooper Black
TIT_PX, TIT_X, TIT_Y, TIT_FADE = 40, 50, 30, 0.6        # px finais; canto de cima-esquerda (acima da rota mais ao norte)
BG = (27, 27, 27)
LW = 0.65              # engrossa as rotas na textura (a inclinação as afina na vertical)
VSS, LARGURA_M = 3, 4.0                                # viário: superamostragem sobre a textura; largura real


class Cena:
    def __init__(self, S, flat=False):
        self.S = S
        v2 = V.vista(S)
        self.box = w, s, e, n = V.bbox(v2)             # retângulo de chão da v4b
        assert abs(w + 46.957) < 2e-3 and abs(s + 23.905) < 2e-3 and abs(e + 46.266) < 2e-3 and abs(n + 23.386) < 2e-3, self.box
        p = math.radians(PITCH)
        self.sp, self.cp = math.sin(p), math.cos(p)
        self.F = (SH / 2) / math.tan(math.radians(FOV_V) / 2)
        self.z0 = Z_REF
        self._grade(0.05, 0.05)                        # grade provisória, só pra achar a distância da câmera
        self._camera()
        # até onde a câmera enxerga ao norte e ao sul: raio do topo do quadro num plano alto, raio da base no nível do mar
        def alcance(Y, zp):
            dz = (zp - self.z0) * EX
            return (Y * (self.D - dz * self.sp) - self.F * dz * self.cp) / (self.F * self.sp - Y * self.cp)
        norte = max(alcance(SH / 2, 600.0), alcance(SH / 2, 1300.0))      # m ao norte do centro
        sul = -min(alcance(-SH / 2, 0.0), alcance(-SH / 2, self.z0))      # m ao sul do centro
        meio = (self.vc_m)                                                 # (em metres, calculado em _camera)
        dh = n - s
        graus = 1 / 110570.0
        pad_n = max(0.03, ((norte * graus) - dh / 2) / dh + 0.03)
        pad_s = max(0.03, ((sul * graus) - dh / 2) / dh + 0.03)
        self._grade(pad_n, pad_s)
        self._camera()
        self.z = self.dem() if not flat else np.full((self.TH, TW), self.z0, np.float32)

    def _grade(self, pad_n, pad_s):
        w, s, e, n = self.box
        dw, dh = (e - w), (n - s)
        self.tb = (w - PAD_EW * dw, s - pad_s * dh, e + PAD_EW * dw, n + pad_n * dh)       # textura: W S E N
        x0, y0 = R.merc(self.tb[3], self.tb[0], 0); x1, y1 = R.merc(self.tb[1], self.tb[2], 0)
        self.zt = math.log2(TW / (x1 - x0))
        f = 2 ** self.zt
        self.tox, self.toy = x0 * f, y0 * f
        self.TH = int(round((y1 - y0) * f))
        self.m = 156543.03 * math.cos(math.radians((n + s) / 2)) / 2 ** self.zt           # metros por px de textura

    def _camera(self):
        w, s, e, n = self.box
        (u_w, v_n), (u_e, v_s) = self.uv(n, w), self.uv(s, e)
        self.uc, self.vc = (u_w + u_e) / 2, (v_n + v_s) / 2
        self.vc_m = self.vc * self.m
        D = 0.0
        for cu_, cv_ in ((u_w, v_n), (u_e, v_n), (u_w, v_s), (u_e, v_s)):                  # os 4 cantos, no plano z0, cabem
            dx, dy = (cu_ - self.uc) * self.m, (self.vc - cv_) * self.m
            D = max(D, self.F * abs(dx) / (SW / 2) - dy * self.cp, self.F * abs(dy * self.sp) / (SH / 2) - dy * self.cp)
        self.D = D / ZOOM

    def uv(self, lat, lon):
        x, y = R.merc(lat, lon, self.zt)
        return x - self.tox, y - self.toy

    def dem(self):
        p = f"{self.S}/dem-{TAG}-{TW}-{self.TH}.npy"
        if os.path.exists(p):
            return np.load(p)
        from osgeo import gdal
        from scipy.ndimage import map_coordinates
        gdal.UseExceptions()
        gdal.SetConfigOption("GDAL_HTTP_USERAGENT", "Mozilla/5.0 (map-render-poc)")
        w, s, e, n = self.tb
        urls = []
        for la in range(math.floor(s), math.floor(n) + 1):
            for lo in range(math.floor(w), math.floor(e) + 1):
                nome = f"{'S' if la < 0 else 'N'}{abs(la):02d}{'W' if lo < 0 else 'E'}{abs(lo):03d}_FABDEM_V1-2.tif"
                try:
                    gdal.Open("/vsicurl/https://fabdem.pedalhidrografi.co/" + nome)
                    urls.append("/vsicurl/https://fabdem.pedalhidrografi.co/" + nome)
                except Exception as ex:
                    print(f"DEM: sem o tile {nome} (fica 0 m): {str(ex)[:60]}")
        res = 1 / 3600
        W_, N_ = w - 0.01, n + 0.01
        nx, ny = int(round((e + 0.01 - W_) / res)), int(round((N_ - (s - 0.01)) / res))
        vrt = gdal.BuildVRT("", urls)
        ds = gdal.Warp("", vrt, format="MEM", outputBounds=(W_, N_ - ny * res, W_ + nx * res, N_), width=nx, height=ny,
                       resampleAlg="bilinear", srcNodata=-9999, dstNodata=-9999)
        a = ds.ReadAsArray().astype(np.float32)
        ruim = ~np.isfinite(a) | (a < -500)
        print(f"DEM {a.shape} de {len(urls)} tile(s), sem dado: {ruim.mean():.1%}, faixa {a[~ruim].min():.0f}..{a[~ruim].max():.0f} m")
        a[ruim] = 0.0                                                                      # mar / sem dado = 0 m
        s_ = 256 * 2 ** self.zt
        lon = (np.arange(TW) + 0.5 + self.tox) / s_ * 360 - 180
        lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (np.arange(self.TH) + 0.5 + self.toy) / s_))))
        col = (lon - W_) / res - 0.5
        row = (N_ - lat) / res - 0.5
        z = map_coordinates(a, np.meshgrid(row, col, indexing="ij"), order=1, mode="nearest").astype(np.float32)
        np.save(p, z)
        return z

    def proj(self, u, v, z=None):
        """textura (u, v) → tela superamostrada (x, y), com a elevação (exagerada) do ponto."""
        u = np.atleast_1d(np.asarray(u, float)); v = np.atleast_1d(np.asarray(v, float))
        if z is None:
            from scipy.ndimage import map_coordinates
            z = map_coordinates(self.z, [np.clip(v - 0.5, 0, self.TH - 1), np.clip(u - 0.5, 0, TW - 1)], order=1, mode="nearest")
        dx, dy, dz = (u - self.uc) * self.m, (self.vc - v) * self.m, (z - self.z0) * EX
        depth = self.D + dy * self.cp - dz * self.sp
        return SW / 2 + self.F * dx / depth, SH / 2 - self.F * (dy * self.sp + dz * self.cp) / depth

    def mapa(self):
        """Pra cada pixel da tela (superamostrada), o índice do pixel de textura que ele enxerga (−1 = nada).
        Varre as linhas da textura da mais próxima (sul) pra mais distante (norte), com horizonte por coluna."""
        idx = np.full((SH, SW), -1, np.int32)
        ymin = np.full(SW, SH, np.int32)
        cols = np.arange(SW)
        Xc = cols + 0.5 - SW / 2
        xp = np.arange(TW) + 0.5
        for tv in range(self.TH - 1, -1, -1):
            dy = (self.vc - (tv + 0.5)) * self.m
            d0 = self.D + dy * self.cp
            u = self.uc + Xc * d0 / (self.F * self.m)                    # coluna da tela → u (profundidade do plano z0)
            ok = (u >= 0.5) & (u <= TW - 0.5)
            zc = np.interp(u, xp, self.z[tv])
            dz = (zc - self.z0) * EX
            sy = SH / 2 - self.F * (dy * self.sp + dz * self.cp) / (d0 - dz * self.sp)
            top = np.floor(sy).astype(np.int32)
            top = np.maximum(top, 0)
            m = ok & (top < ymin)
            if not m.any():
                continue
            ui = np.clip(u.astype(np.int32), 0, TW - 1) + tv * TW
            span = int((ymin[m] - top[m]).max())
            for k in range(span):
                r = top + k
                mk = m & (r < ymin)
                idx[r[mk], cols[mk]] = ui[mk]
            ymin[m] = top[m]
        return idx

    # ── textura de base: topografia + viário ──
    def base(self):
        p = f"{self.S}/tex3d-{TAG}-{TW}-{self.TH}.png"
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
        tz = min(16, round(self.zt))
        f = 2 ** (tz - self.zt)
        x0, y0, x1, y1 = self.tox * f, self.toy * f, (self.tox + TW) * f, (self.toy + self.TH) * f
        tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
        big = Image.new("RGBA", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (0, 0, 0, 0))
        jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
        os.makedirs(f"{self.S}/tiles", exist_ok=True)
        with ThreadPoolExecutor(8) as ex:
            for (x, y), im in zip(jobs, ex.map(lambda j: R.tile(R.TOPO, tz, j[0], j[1], f"{self.S}/tiles"), jobs)):
                if im:
                    big.paste(im, ((x - tx0) * 256, (y - ty0) * 256))
        topo = big.resize((TW, self.TH), Image.LANCZOS, box=(x0 - tx0 * 256, y0 - ty0 * 256, x1 - tx0 * 256, y1 - ty0 * 256))
        im = Image.new("RGBA", topo.size, BG + (255,))
        topo.putalpha(topo.getchannel("A").point(lambda a: int(a * R.TOPO_OPACITY)))
        im.alpha_composite(topo)
        veu = Image.new("RGBA", im.size, (255, 255, 255, 0))
        veu.putalpha(self.viario())
        im.alpha_composite(veu)
        im.save(p)
        return im

    def viario(self):
        from osgeo import ogr, gdal
        gdal.SetConfigOption("GDAL_HTTP_USERAGENT", "Mozilla/5.0 (map-render-poc)")
        gdal.SetConfigOption("CPL_VSIL_CURL_CACHE_SIZE", "268435456")
        ds = ogr.Open("/vsicurl/https://fabdem.pedalhidrografi.co/viario/south-america-viario.fgb")
        ly = ds.GetLayer(0)
        w, s, e, n = self.tb
        ly.SetSpatialFilterRect(w, s, e, n)
        im = Image.new("L", (TW * VSS, self.TH * VSS), 0)
        d = ImageDraw.Draw(im)
        s_ = 256 * 2 ** self.zt
        k = 0
        for ft in ly:
            g = ft.GetGeometryRef()
            if g is None:
                continue
            parts = [g] if g.GetGeometryType() in (ogr.wkbLineString, ogr.wkbLineString25D) else [g.GetGeometryRef(i) for i in range(g.GetGeometryCount())]
            for part in parts:
                pts = part.GetPoints()
                if pts and len(pts) > 1:
                    d.line([(((c[0] + 180) / 360 * s_ - self.tox) * VSS,
                             ((1 - math.asinh(math.tan(math.radians(c[1]))) / math.pi) / 2 * s_ - self.toy) * VSS) for c in pts], fill=255, width=1)
            k += 1
        fator = min(1.0, LARGURA_M / (self.m / VSS))
        print(f"viário: {k} vias; fator {fator:.2f}")
        return im.reduce(VSS).point(lambda a: int(a * fator))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir"); ap.add_argument("--still", nargs="*", type=float); ap.add_argument("--out"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    S = a.dir
    t0 = time.time()
    c = Cena(S)
    w, s, e, n = c.box
    print(f"{PITCH:g}° · exagero {EX:g}× · textura {TW}×{c.TH} (lat {c.tb[1]:.3f}..{c.tb[3]:.3f}), {c.m:.1f} m/px; z0 {c.z0:.0f} m; câmera a {c.D / 1000:.0f} km, foco {c.F:.0f} px")
    if a.check:
        flat = Cena(S, flat=True)
        for nome, (la, lo) in dict(NO=(n, w), NE=(n, e), SO=(s, w), SE=(s, e)).items():
            x, y = flat.proj(*flat.uv(la, lo))
            print(f"  canto {nome} (chão plano): tela {float(x[0]) / SS:7.1f}, {float(y[0]) / SS:7.1f}  (quadro 0..{W} × 0..{H})")
        for nome, (la, lo) in {"Pico do Jaraguá": (-23.4563, -46.7663), "Marginal Tietê (Cebolão)": (-23.5215, -46.7445),
                               "Serra do Mar, baixada (Cubatão)": (-23.89, -46.42), "Cratera de Colônia (centro)": (-23.87, -46.706)}.items():
            u, v = c.uv(la, lo)
            zz = float(c.z[int(v), int(u)])
            (x1, y1), (x0, y0) = c.proj(u, v), flat.proj(u, v)
            print(f"  {nome}: {zz:.0f} m → tela {float(x1[0]) / SS:.0f}, {float(y1[0]) / SS:.0f}; em relação ao plano: {(float(y1[0]) - float(y0[0])) / SS:+.1f} px (negativo = sobe)")
    base = c.base()
    idx = c.mapa()
    vazio = idx < 0
    flatidx = np.where(vazio, 0, idx)
    print(f"mapa de visibilidade pronto ({time.time() - t0:.0f} s); pixels sem chão: {vazio.mean():.2%}")

    def renderiza(tex_rgb):
        out = np.asarray(tex_rgb).reshape(-1, 3)[flatidx]
        out[vazio] = BG
        return Image.fromarray(out, "RGB")

    if a.check:
        renderiza(base.convert("RGB")).resize((W, H), Image.LANCZOS).save(f"{S}/all3d-{TAG}-relevo.jpg", quality=90)
        fl = Cena(S, flat=True)
        i2 = fl.mapa(); v2 = i2 < 0
        o = np.asarray(base.convert("RGB")).reshape(-1, 3)[np.where(v2, 0, i2)]; o[v2] = BG
        Image.fromarray(o, "RGB").resize((W, H), Image.LANCZOS).save(f"{S}/all3d-{TAG}-flat.jpg", quality=90)
        return

    rs, fora = V.visiveis(S)
    assert len(rs) == 120, len(rs)
    rs = rs[::-1]
    fps = 30
    nfr = round(TOTAL * fps)
    N = len(rs)
    Dt = (TOTAL - HOLD) / (N - 1 + DRAW)
    fb = ImageFont.truetype(f"{S}/plex-mono-700.ttf", 30 * SS)
    fn = ImageFont.truetype(f"{S}/plex-mono-600.ttf", 21 * SS)
    md = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    from PIL import ImageFilter, ImageChops
    ft = ImageFont.truetype(TIT_FONT, TIT_PX * SS)
    tit_h = int(TIT_PX * SS * 1.18)
    tit_box = (0, 0, TIT_X * SS + max(md.textlength(l, font=ft) for l in TITULO) + 30 * SS, TIT_Y * SS + tit_h * len(TITULO) + 22 * SS)
    # título: branco com SOMBRA preta (sem contorno) — pré-renderizado uma vez
    tit = Image.new("RGBA", (int(tit_box[2]) + 20 * SS, int(tit_box[3]) + 20 * SS), (0, 0, 0, 0))
    td = ImageDraw.Draw(tit)
    for k, l in enumerate(TITULO):
        td.text((TIT_X * SS + 4 * SS, TIT_Y * SS + k * tit_h + 4 * SS), l, font=ft, fill=(0, 0, 0, 235))
    tit = tit.filter(ImageFilter.GaussianBlur(2.2 * SS))
    td = ImageDraw.Draw(tit)
    for k, l in enumerate(TITULO):
        td.text((TIT_X * SS + 3 * SS, TIT_Y * SS + k * tit_h + 3 * SS), l, font=ft, fill=(0, 0, 0, 255))      # núcleo firme da sombra
    tit = tit.filter(ImageFilter.GaussianBlur(0.8 * SS))
    td = ImageDraw.Draw(tit)
    for k, l in enumerate(TITULO):
        td.text((TIT_X * SS, TIT_Y * SS + k * tit_h), l, font=ft, fill=(255, 255, 255, 255))
    T = []
    for i, r in enumerate(rs):
        tex = [c.uv(la, lo) for la, lo in r["latlngs"]]
        cum = [0.0]
        for j in range(1, len(tex)):
            cum.append(cum[-1] + math.dist(tex[j], tex[j - 1]))
        sx, sy = c.proj([p[0] for p in tex], [p[1] for p in tex])
        num = r.get("number") or {}
        linhas = ([(f"{num['source']} {num['value']}", fb)] if num.get("source") else [])
        nome = textwrap.wrap(r["name"], 32)
        if len(nome) > 2:
            nome = nome[:2]; nome[1] = nome[1][:31].rstrip() + "…"
        linhas += [(l, fn) for l in nome]
        tw = max(md.textlength(l, font=f) for l, f in linhas)
        hs = [int(f.size * 1.18) for _, f in linhas]
        th = sum(hs)
        g = 14 * SS
        itop, ibot = int(np.argmin(sy)), int(np.argmax(sy))
        my = (sy.min() + sy.max()) / 2 - th / 2
        cands = []
        for k in range(4):
            o = g + k * (th + g) * 0.6
            cands += [(sx[itop] - tw / 2, sy.min() - th - o), (sx[ibot] - tw / 2, sy.max() + o), (sx.max() + o, my), (sx.min() - tw - o, my),
                      (sx.max() + o, sy.min() - th - o), (sx.min() - tw - o, sy.min() - th - o), (sx.max() + o, sy.max() + o), (sx.min() - tw - o, sy.max() + o)]
        esc = None
        for cx, cy in cands:
            lx = min(max(cx, 14 * SS), SW - tw - 14 * SS); ly = min(max(cy, 10 * SS), SH - th - 10 * SS)
            box = (lx - g, ly - g / 2, lx + tw + g, ly + th + g / 2)
            bate = any(not (box[2] < ob[0] or box[0] > ob[2] or box[3] < ob[1] or box[1] > ob[3]) for ob in [O["box"] for O in T[-(NLAB - 1):]] + [tit_box])
            if esc is None or not bate:
                esc = (lx, ly, box)
                if not bate:
                    break
        T.append(dict(pts=tex, cum=cum, a=i * Dt, linhas=linhas, hs=hs, lx=esc[0], ly=esc[1], box=esc[2]))
    fim = T[-1]["a"] + DRAW * Dt
    print(f"{N} rotas, uma a cada {Dt:.3f} s")

    def frame(i):
        t = (i + 1) / fps
        tc = min(t, fim)
        vis = [(r, max(0.0, min(1.0, 1 - (tc - r["a"] - DRAW * Dt) / ((NVIS - DRAW) * Dt)))) for r in T if r["a"] < tc]
        vis = [(r, al) for r, al in vis if al > 0]
        tex = base.copy()
        lay = Image.new("RGBA", tex.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        pontas = []
        for r, al in vis:                                             # rotas: na textura (deitadas no relevo)
            A = int(255 * al)
            sub, ponta = R.partial(r["pts"], r["cum"], R.ease((tc - r["a"]) / (DRAW * Dt)))
            R.stroke(d, sub, (0, 0, 0, A), round((7 + 6 * al) * SS * LW))
            R.stroke(d, sub, (255, 240, 60, A), round((3 + 4 * al) * SS * LW))
            if t - r["a"] < DRAW * Dt:
                pontas.append(ponta)
        tex.alpha_composite(lay)
        im = renderiza(tex.convert("RGB")).convert("RGBA")
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for pu, pv in pontas:                                         # bolinha e rótulos: retos, na tela
            x, y = c.proj(pu, pv)
            x, y = float(x[0]), float(y[0])
            q = 8 * SS
            d.ellipse((x - q, y - q, x + q, y + q), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=3 * SS)
        for r, _ in vis:
            al = max(0.0, min(1.0, 1 - (tc - r["a"] - DRAW * Dt) / ((NLAB - DRAW) * Dt)))
            if al <= 0:
                continue
            A = int(255 * al)
            y = r["ly"]
            for (l, f), hh in zip(r["linhas"], r["hs"]):
                d.text((r["lx"], y), l, font=f, fill=(255, 255, 255, A), stroke_width=4 * SS, stroke_fill=(0, 0, 0, A))
                y += hh
        im.alpha_composite(lay)
        al = min(1.0, t / TIT_FADE)
        if os.environ.get("SEM_TITULO"):
            pass
        elif al >= 1:
            im.alpha_composite(tit)
        else:
            tt = tit.copy(); tt.putalpha(tit.getchannel("A").point(lambda v: int(v * al)))
            im.alpha_composite(tt)
        return im.convert("RGB").resize((W, H), Image.LANCZOS)

    if a.still is not None:
        for t in a.still:
            frame(round(t * fps) - 1).save(f"{S}/all3d-{TAG}-{t:05.2f}.jpg", quality=88)
        return
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out],
                          stdin=subprocess.PIPE)
    for i in range(nfr):
        ff.stdin.write(frame(i).tobytes())
        if i % 100 == 0:
            print(f"quadro {i}/{nfr} ({time.time() - t0:.0f} s)", flush=True)
    ff.stdin.close(); sys.exit(ff.wait())


if __name__ == "__main__":
    main()
