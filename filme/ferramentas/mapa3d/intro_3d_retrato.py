#!/usr/bin/env python3
"""A abertura "todas as rotas" em 3D pra tela em RETRATO (1080×1350), com a câmera podendo olhar pra qualquer ponto cardeal.
Mesma técnica do intro_3d.py (mapa drapeado no relevo FABDEM, rotas desenhadas na textura, rótulos retos na tela); muda:
  - AZ: pra onde a câmera olha, em graus a partir do norte (0 norte, 270 oeste, 315 noroeste…). O relevo e a textura são montados
    com o norte em cima e REAMOSTRADOS numa grade girada; a câmera continua olhando "pra cima" dessa grade.
  - o retângulo de chão é o MESMO do vídeo deitado (todas as 120 rotas); o que sobra de tela mostra mais terreno em volta.
  - sem título; letras maiores (tela de celular).
Variáveis: AZ, PITCH (graus em relação ao horizonte), EX (exagero), ZOOM, PAN_R / PAN_F (km: desloca a mira pra direita / pra frente),
LARGURA_KM (largura de chão vista; substitui o ZOOM), ESTICA_V (estica o chão na vertical), M_ALVO, LW, OUT_W, OUT_H, HOLD, DRAW.
  intro_3d_retrato.py <dir> --still 12 --png saida.png        intro_3d_retrato.py <dir> --out x.mp4"""
import argparse, hashlib, math, os, subprocess, sys, textwrap, time
os.environ["STRETCH"] = "1.459"                       # a vista da v4b (o retângulo de chão)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R, view_all as V
Image.MAX_IMAGE_PIXELS = None
W, H, SS = int(os.environ.get("OUT_W", 1080)), int(os.environ.get("OUT_H", 1350)), 2
SW, SH = W * SS, H * SS
FOV_V = 1.0
AZ = float(os.environ.get("AZ", 0))                    # pra onde a câmera olha, em graus a partir do norte, sentido horário
PITCH = float(os.environ.get("PITCH", 35.0)); EX = float(os.environ.get("EX", 2.0)); ZOOM = float(os.environ.get("ZOOM", 1.0))
M_ALVO = float(os.environ.get("M_ALVO", 20.0))                                          # m por px de textura
Z_REF = 771.0
TOTAL, NVIS = 20.0, 10
HOLD = float(os.environ.get("HOLD", 0.0)); DRAW = float(os.environ.get("DRAW", 1.0))
NLAB = 4
BG = (27, 27, 27)
LW = float(os.environ.get("LW", 1.0))
KV = float(os.environ.get("ESTICA_V", 1.0))            # estica o chão na vertical da tela (1/0,7 = corta 15 % em cima e embaixo e estica); letras e bolinha não esticam
VSS, LARGURA_M = 2, 4.0
F_NUM, F_NOME, QUEBRA = 38, 25, 24                     # px finais das letras; caracteres por linha do nome


class Cena:
    def __init__(self, S, flat=False):
        self.S = S
        self.box = w, s, e, n = V.bbox(V.vista(S))
        assert abs(w + 46.957) < 2e-3 and abs(s + 23.905) < 2e-3 and abs(e + 46.266) < 2e-3 and abs(n + 23.386) < 2e-3, self.box
        p = math.radians(PITCH); self.sp, self.cp = math.sin(p), math.cos(p)
        self.F = (SH / 2) / math.tan(math.radians(FOV_V) / 2); self.z0 = Z_REF
        self.lat0, self.lon0 = (n + s) / 2, (e + w) / 2
        self.gla, self.glo = 1 / 110570.0, 1 / (111320.0 * math.cos(math.radians(self.lat0)))   # graus por metro
        A = math.radians(AZ); self.sa, self.ca = math.sin(A), math.cos(A)
        # câmera: (r, f) = metros à direita e à frente do centro do retângulo
        # enquadra as ROTAS (não os cantos do retângulo): todo ponto de toda rota cabe na tela, com 5 % de folga
        pts = np.array([(la, lo) for r_ in V.visiveis(S)[0] for la, lo in r_["latlngs"]], float)
        x, y = (pts[:, 1] - self.lon0) / self.glo, (pts[:, 0] - self.lat0) / self.gla                                    # (leste, norte) em m
        r, f = x * self.ca - y * self.sa, x * self.sa + y * self.ca
        r0, f0 = (r.max() + r.min()) / 2, (f.max() + f.min()) / 2                    # centra a câmera nas ROTAS (não no retângulo): sobra menos borda
        r0 += float(os.environ.get("PAN_R", 0)) * 1000; f0 += float(os.environ.get("PAN_F", 0)) * 1000   # desloca a mira (km pra direita / pra frente)
        self.lon0 += (r0 * self.ca + f0 * self.sa) * self.glo; self.lat0 += (-r0 * self.sa + f0 * self.ca) * self.gla
        r, f = r - r0, f - f0; self._rf = (r, f)
        self.D = 1.05 * float(np.max(np.maximum(self.F * np.abs(r) / (SW / 2) - f * self.cp, self.F * KV * np.abs(f * self.sp) / (SH / 2) - f * self.cp))) / ZOOM
        if os.environ.get("LARGURA_KM"): self.D = float(os.environ["LARGURA_KM"]) * 1000 * self.F / SW        # largura de chão vista, em km (manda no zoom)
        def alcance(Y, zp):                                                        # m à frente do centro em que o raio da linha Y bate no plano zp
            dz = (zp - self.z0) * EX
            return (Y * (self.D - dz * self.sp) - self.F * dz * self.cp) / (self.F * self.sp - Y * self.cp)
        longe = max(alcance(SH / 2 / KV, 600.0), alcance(SH / 2 / KV, 1300.0)); perto = -min(alcance(-SH / 2 / KV, 0.0), alcance(-SH / 2 / KV, self.z0))
        meia = (SW / 2) * (self.D + longe * self.cp) / self.F                       # meia largura visível lá no fundo
        self.longe, self.perto, self.lado = longe + 2500.0, perto + 2500.0, meia + 2500.0
        # textura de chão (norte em cima): a caixa que contém o retângulo que a câmera enxerga
        en = [(r * self.ca + f * self.sa, -r * self.sa + f * self.ca) for r, f in ((-self.lado, self.longe), (self.lado, self.longe), (-self.lado, -self.perto), (self.lado, -self.perto))]
        self.tb = (self.lon0 + min(x for x, _ in en) * self.glo, self.lat0 + min(y for _, y in en) * self.gla,
                   self.lon0 + max(x for x, _ in en) * self.glo, self.lat0 + max(y for _, y in en) * self.gla)                 # W S E N
        x0, y0 = R.merc(self.tb[3], self.tb[0], 0); x1, y1 = R.merc(self.tb[1], self.tb[2], 0)
        self.GW = int(round((self.tb[2] - self.tb[0]) / self.glo / M_ALVO)); self.zt = math.log2(self.GW / (x1 - x0)); f = 2 ** self.zt
        self.tox, self.toy = x0 * f, y0 * f; self.GH = int(round((y1 - y0) * f))
        self.m = 156543.03 * math.cos(math.radians(self.lat0)) / 2 ** self.zt       # m por px
        self.ugc, self.vgc = self.uvg(self.lat0, self.lon0)                         # o centro do retângulo, em px de chão
        self.TW, self.TH = int(round(2 * self.lado / self.m)), int(round((self.longe + self.perto) / self.m))                  # textura da câmera
        self.uc, self.vc = self.TW / 2, self.longe / self.m
        zg = self.dem() if not flat else np.full((self.GH, self.GW), self.z0, np.float32)
        self.zg = zg; self.z = self.pra_camera(zg, float(self.z0))

    def uvg(self, lat, lon):                                                        # chão (norte em cima)
        x, y = R.merc(lat, lon, self.zt); return x - self.tox, y - self.toy

    def uv(self, lat, lon):                                                         # textura da câmera: u pra direita, v pra perto
        ug, vg = self.uvg(lat, lon); e_, n_ = ug - self.ugc, -(vg - self.vgc)
        return self.uc + e_ * self.ca - n_ * self.sa, self.vc - (e_ * self.sa + n_ * self.ca)

    def pra_camera(self, arr, fundo):                                               # reamostra uma grade de chão na grade da câmera (gira AZ)
        from scipy.ndimage import affine_transform
        ca, sa = self.ca, self.sa; M = [[ca, sa], [-sa, ca]]
        off = (self.vgc - self.uc * sa - self.vc * ca + 0.5 * (ca + sa) - 0.5, self.ugc - self.uc * ca + self.vc * sa + 0.5 * (ca - sa) - 0.5)
        return affine_transform(arr.astype(np.float32), M, offset=off, output_shape=(self.TH, self.TW), order=1, mode="constant", cval=fundo)

    def _chave(self): return hashlib.md5(repr((tuple(round(v, 5) for v in self.tb), self.GW, self.GH)).encode()).hexdigest()[:10]

    def dem(self):
        p = f"{self.S}/dem-{self._chave()}.npy"
        if os.path.exists(p): return np.load(p)
        from osgeo import gdal
        from scipy.ndimage import map_coordinates
        gdal.UseExceptions(); gdal.SetConfigOption("GDAL_HTTP_USERAGENT", "Mozilla/5.0 (map-render-poc)")
        w, s, e, n = self.tb; urls = []
        for la in range(math.floor(s), math.floor(n) + 1):
            for lo in range(math.floor(w), math.floor(e) + 1):
                nome = f"{'S' if la < 0 else 'N'}{abs(la):02d}{'W' if lo < 0 else 'E'}{abs(lo):03d}_FABDEM_V1-2.tif"
                try: gdal.Open("/vsicurl/https://fabdem.pedalhidrografi.co/" + nome); urls.append("/vsicurl/https://fabdem.pedalhidrografi.co/" + nome)
                except Exception as ex: print(f"DEM: sem o tile {nome} (fica 0 m): {str(ex)[:60]}")
        res = 1 / 3600; W_, N_ = w - 0.01, n + 0.01
        nx, ny = int(round((e + 0.01 - W_) / res)), int(round((N_ - (s - 0.01)) / res))
        ds = gdal.Warp("", gdal.BuildVRT("", urls), format="MEM", outputBounds=(W_, N_ - ny * res, W_ + nx * res, N_), width=nx, height=ny,
                       resampleAlg="bilinear", srcNodata=-9999, dstNodata=-9999)
        a = ds.ReadAsArray().astype(np.float32); ruim = ~np.isfinite(a) | (a < -500)
        print(f"DEM {a.shape} de {len(urls)} tile(s), sem dado: {ruim.mean():.1%}, faixa {a[~ruim].min():.0f}..{a[~ruim].max():.0f} m")
        a[ruim] = 0.0
        s_ = 256 * 2 ** self.zt
        lon = (np.arange(self.GW) + 0.5 + self.tox) / s_ * 360 - 180
        lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (np.arange(self.GH) + 0.5 + self.toy) / s_))))
        z = map_coordinates(a, np.meshgrid((N_ - lat) / res - 0.5, (lon - W_) / res - 0.5, indexing="ij"), order=1, mode="nearest").astype(np.float32)
        np.save(p, z); return z

    def proj(self, u, v, z=None):
        u = np.atleast_1d(np.asarray(u, float)); v = np.atleast_1d(np.asarray(v, float))
        if z is None:
            from scipy.ndimage import map_coordinates
            z = map_coordinates(self.z, [np.clip(v - 0.5, 0, self.TH - 1), np.clip(u - 0.5, 0, self.TW - 1)], order=1, mode="nearest")
        dx, dy, dz = (u - self.uc) * self.m, (self.vc - v) * self.m, (z - self.z0) * EX
        depth = self.D + dy * self.cp - dz * self.sp
        return SW / 2 + self.F * dx / depth, SH / 2 - KV * self.F * (dy * self.sp + dz * self.cp) / depth

    def mapa(self):
        TW = self.TW; idx = np.full((SH, SW), -1, np.int32); ymin = np.full(SW, SH, np.int32)
        cols = np.arange(SW); Xc = cols + 0.5 - SW / 2; xp = np.arange(TW) + 0.5
        for tv in range(self.TH - 1, -1, -1):                                       # do mais perto pro mais longe, com horizonte por coluna
            dy = (self.vc - (tv + 0.5)) * self.m; d0 = self.D + dy * self.cp
            u = self.uc + Xc * d0 / (self.F * self.m); ok = (u >= 0.5) & (u <= TW - 0.5)
            dz = (np.interp(u, xp, self.z[tv]) - self.z0) * EX
            top = np.maximum(np.floor(SH / 2 - KV * self.F * (dy * self.sp + dz * self.cp) / (d0 - dz * self.sp)).astype(np.int32), 0)
            m = ok & (top < ymin)
            if not m.any(): continue
            ui = np.clip(u.astype(np.int32), 0, TW - 1) + tv * TW
            for k in range(int((ymin[m] - top[m]).max())):
                r = top + k; mk = m & (r < ymin); idx[r[mk], cols[mk]] = ui[mk]
            ymin[m] = top[m]
        return idx

    def base(self):
        p = f"{self.S}/tex-{self._chave()}-d.png"
        if os.path.exists(p): im = Image.open(p).convert("RGBA")
        else:
            GW, GH = self.GW, self.GH; tz = min(16, round(self.zt)); f = 2 ** (tz - self.zt)
            x0, y0, x1, y1 = self.tox * f, self.toy * f, (self.tox + GW) * f, (self.toy + GH) * f
            tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
            big = Image.new("RGBA", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (0, 0, 0, 0))
            jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]; os.makedirs(f"{self.S}/tiles", exist_ok=True)
            with ThreadPoolExecutor(8) as ex:
                for (x, y), t in zip(jobs, ex.map(lambda j: R.tile(R.TOPO, tz, j[0], j[1], f"{self.S}/tiles"), jobs)):
                    if t: big.paste(t, ((x - tx0) * 256, (y - ty0) * 256))
            topo = big.resize((GW, GH), Image.LANCZOS, box=(x0 - tx0 * 256, y0 - ty0 * 256, x1 - tx0 * 256, y1 - ty0 * 256))
            # fora da cobertura do mapa-base: relevo sombreado discreto tirado do próprio DEM (em vez de um vazio), com a borda esfumada
            from scipy.ndimage import gaussian_filter
            zs = gaussian_filter(self.zg, 1.5); gy_, gx_ = np.gradient(zs, self.m)
            cob = np.asarray(topo.getchannel("A"), np.float32) / 255.0 > 0.5; rgb = np.asarray(topo.convert("RGB"), np.float32); mar = self.zg <= 1.0
            # Fora da cobertura do mapa colorido, CONTINUA o mapa colorido: a cor dele é função da altitude (faixas de 1 m) escurecida pela
            # declividade — 77 % da variância só com a altitude. A regra é aprendida nos pixels cobertos e aplicada no resto (mar incluso).
            decl = np.hypot(gx_, gy_); zi = np.clip(np.round(self.zg).astype(np.int32), -5, 2100) + 5
            si = np.digitize(decl, [0.02, 0.04, 0.07, 0.10, 0.15, 0.20, 0.30, 0.45, 0.70]).astype(np.int32); NZ, NS_ = 2106, 10
            chave = (zi * NS_ + si)[cob]; n2 = np.bincount(chave, minlength=NZ * NS_).astype(np.float32)
            lut2 = np.stack([np.bincount(chave, weights=rgb[:, :, k][cob], minlength=NZ * NS_) for k in range(3)], 1) / np.maximum(n2, 1)[:, None]
            n1 = np.bincount(zi[cob], minlength=NZ).astype(np.float32)
            lut1 = np.stack([np.bincount(zi[cob], weights=rgb[:, :, k][cob], minlength=NZ) for k in range(3)], 1) / np.maximum(n1, 1)[:, None]
            bons = np.nonzero(n1 >= 50)[0]                                           # altitudes sem amostra: a mais próxima que tem
            lut1 = lut1[bons[np.abs(np.arange(NZ)[:, None] - bons[None, :]).argmin(1)]]
            esc = np.array([(rgb[cob][si[cob] == j].mean() if (si[cob] == j).any() else np.nan) for j in range(NS_)]); esc = esc / esc[0]
            esc = np.where(np.isfinite(esc), esc, np.nanmin(esc))                    # quanto cada faixa de declividade escurece
            lut2 = lut2.reshape(NZ, NS_, 3); pouco = n2.reshape(NZ, NS_) < 30
            lut2[pouco] = (lut1[:, None, :] * esc[None, :, None])[pouco]
            fundo = lut2[zi, si] * R.TOPO_OPACITY + np.array(BG, np.float32) * (1 - R.TOPO_OPACITY)
            a = np.clip((gaussian_filter(cob.astype(np.float32), 40) - 0.5) * 2, 0, 1)[:, :, None]                                  # some pra dentro da borda
            mix = (rgb * R.TOPO_OPACITY + np.array(BG, np.float32) * (1 - R.TOPO_OPACITY)) * a + fundo * (1 - a)
            im = Image.fromarray(np.clip(mix, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
            veu = Image.new("RGBA", im.size, (255, 255, 255, 0)); veu.putalpha(self.viario()); im.alpha_composite(veu); im.save(p)
        rgb = np.asarray(im.convert("RGB"))
        cam = np.stack([np.clip(self.pra_camera(rgb[:, :, k], float(BG[k])), 0, 255) for k in range(3)], axis=2).astype(np.uint8)
        return Image.fromarray(cam, "RGB").convert("RGBA")

    def viario(self):
        from osgeo import ogr, gdal
        gdal.SetConfigOption("GDAL_HTTP_USERAGENT", "Mozilla/5.0 (map-render-poc)"); gdal.SetConfigOption("CPL_VSIL_CURL_CACHE_SIZE", "268435456")
        ds = ogr.Open("/vsicurl/https://fabdem.pedalhidrografi.co/viario/south-america-viario.fgb"); ly = ds.GetLayer(0)   # ds tem que ficar vivo
        w, s, e, n = (float(v) for v in self.tb); ly.SetSpatialFilterRect(w, s, e, n)
        im = Image.new("L", (self.GW * VSS, self.GH * VSS), 0); d = ImageDraw.Draw(im); s_ = 256 * 2 ** self.zt; k = 0
        for ft in ly:
            g = ft.GetGeometryRef()
            if g is None: continue
            for part in ([g] if g.GetGeometryType() in (ogr.wkbLineString, ogr.wkbLineString25D) else [g.GetGeometryRef(i) for i in range(g.GetGeometryCount())]):
                pts = part.GetPoints()
                if pts and len(pts) > 1:
                    d.line([(((c[0] + 180) / 360 * s_ - self.tox) * VSS, ((1 - math.asinh(math.tan(math.radians(c[1]))) / math.pi) / 2 * s_ - self.toy) * VSS) for c in pts], fill=255, width=1)
            k += 1
        fator = min(1.0, LARGURA_M / (self.m / VSS)); print(f"viário: {k} vias; fator {fator:.2f}")
        return im.reduce(VSS).point(lambda a: int(a * fator))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--still", nargs="*", type=float); ap.add_argument("--png"); ap.add_argument("--out")
    a = ap.parse_args(); S = a.dir; t0 = time.time()
    c = Cena(S); w, s, e, n = c.box
    print(f"olhando pra {AZ:g}° · inclinação {PITCH:g}° · exagero {EX:g}× · zoom {ZOOM:g} · textura {c.TW}×{c.TH} ({c.m:.1f} m/px; chão W{c.tb[0]:.3f} S{c.tb[1]:.3f} E{c.tb[2]:.3f} N{c.tb[3]:.3f}); câmera a {c.D / 1000:.0f} km")
    for nome, (la, lo) in dict(NO=(n, w), NE=(n, e), SO=(s, w), SE=(s, e)).items():
        x, y = c.proj(*c.uv(la, lo), z=np.array([c.z0])); print(f"  canto {nome}: tela {float(x[0]) / SS:6.0f}, {float(y[0]) / SS:6.0f}  (quadro {W}×{H})")
    base = c.base(); idx = c.mapa(); vazio = idx < 0; flatidx = np.where(vazio, 0, idx)
    print(f"mapa de visibilidade pronto ({time.time() - t0:.0f} s); pixels sem chão: {vazio.mean():.2%}")
    def renderiza(tex_rgb):
        out = np.asarray(tex_rgb).reshape(-1, 3)[flatidx]; out[vazio] = BG; return Image.fromarray(out, "RGB")
    rs, fora = V.visiveis(S); assert len(rs) == 120, len(rs); rs = rs[::-1]
    fps = 30; nfr = round(TOTAL * fps); N = len(rs); Dt = (TOTAL - HOLD) / (N - 1 + DRAW)
    fb = ImageFont.truetype(f"{S}/plex-mono-700.ttf", F_NUM * SS); fn = ImageFont.truetype(f"{S}/plex-mono-600.ttf", F_NOME * SS)
    md = ImageDraw.Draw(Image.new("RGBA", (8, 8))); T = []
    for i, r in enumerate(rs):
        tex = [c.uv(la, lo) for la, lo in r["latlngs"]]; cum = [0.0]
        for j in range(1, len(tex)): cum.append(cum[-1] + math.dist(tex[j], tex[j - 1]))
        sx, sy = c.proj([p[0] for p in tex], [p[1] for p in tex])
        num = r.get("number") or {}; linhas = ([(f"{num['source']} {num['value']}", fb)] if num.get("source") else [])
        nome = textwrap.wrap(r["name"], QUEBRA)
        if len(nome) > 2: nome = nome[:2]; nome[1] = nome[1][:QUEBRA - 1].rstrip() + "…"
        linhas += [(l, fn) for l in nome]
        tw = max(md.textlength(l, font=f) for l, f in linhas); hs = [int(f.size * 1.18) for _, f in linhas]; th = sum(hs); g = 14 * SS
        itop, ibot = int(np.argmin(sy)), int(np.argmax(sy)); my = (sy.min() + sy.max()) / 2 - th / 2; cands = []
        for k in range(4):
            o = g + k * (th + g) * 0.6
            cands += [(sx[itop] - tw / 2, sy.min() - th - o), (sx[ibot] - tw / 2, sy.max() + o), (sx.max() + o, my), (sx.min() - tw - o, my),
                      (sx.max() + o, sy.min() - th - o), (sx.min() - tw - o, sy.min() - th - o), (sx.max() + o, sy.max() + o), (sx.min() - tw - o, sy.max() + o)]
        esc = None
        for cx, cy in cands:
            lx = min(max(cx, 14 * SS), SW - tw - 14 * SS); ly = min(max(cy, 10 * SS), SH - th - 10 * SS)
            box = (lx - g, ly - g / 2, lx + tw + g, ly + th + g / 2)
            bate = any(not (box[2] < ob[0] or box[0] > ob[2] or box[3] < ob[1] or box[1] > ob[3]) for ob in [O["box"] for O in T[-(NLAB - 1):]])
            if esc is None or not bate:
                esc = (lx, ly, box)
                if not bate: break
        T.append(dict(pts=tex, cum=cum, a=i * Dt, linhas=linhas, hs=hs, lx=esc[0], ly=esc[1], box=esc[2]))
    fim = T[-1]["a"] + DRAW * Dt; print(f"{N} rotas, uma a cada {Dt:.3f} s")
    def frame(i):
        t = (i + 1) / fps; tc = min(t, fim)
        vis = [(r, max(0.0, min(1.0, 1 - (tc - r["a"] - DRAW * Dt) / ((NVIS - DRAW) * Dt)))) for r in T if r["a"] < tc]; vis = [(r, al) for r, al in vis if al > 0]
        tex = base.copy(); lay = Image.new("RGBA", tex.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); pontas = []
        for r, al in vis:
            A = int(255 * al); sub, ponta = R.partial(r["pts"], r["cum"], R.ease((tc - r["a"]) / (DRAW * Dt)))
            R.stroke(d, sub, (0, 0, 0, A), round((7 + 6 * al) * SS * LW)); R.stroke(d, sub, (255, 240, 60, A), round((3 + 4 * al) * SS * LW))
            if t - r["a"] < DRAW * Dt: pontas.append(ponta)
        tex.alpha_composite(lay); im = renderiza(tex.convert("RGB")).convert("RGBA")
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for pu, pv in pontas:
            x, y = c.proj(pu, pv); x, y = float(x[0]), float(y[0]); q = 8 * SS
            d.ellipse((x - q, y - q, x + q, y + q), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=3 * SS)
        for r, _ in vis:
            al = max(0.0, min(1.0, 1 - (tc - r["a"] - DRAW * Dt) / ((NLAB - DRAW) * Dt)))
            if al <= 0: continue
            A = int(255 * al); y = r["ly"]
            for (l, f), hh in zip(r["linhas"], r["hs"]):
                d.text((r["lx"], y), l, font=f, fill=(255, 255, 255, A), stroke_width=4 * SS, stroke_fill=(0, 0, 0, A)); y += hh
        im.alpha_composite(lay); return im.convert("RGB").resize((W, H), Image.LANCZOS)
    if a.still is not None:
        for t in a.still: frame(round(t * fps) - 1).save(a.png or f"{S}/retrato-az{AZ:g}-p{PITCH:g}-{t:05.2f}.png")
        return
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for i in range(nfr):
        ff.stdin.write(frame(i).tobytes())
        if i % 100 == 0: print(f"quadro {i}/{nfr} ({time.time() - t0:.0f} s)", flush=True)
    ff.stdin.close(); sys.exit(ff.wait())


if __name__ == "__main__":
    main()
