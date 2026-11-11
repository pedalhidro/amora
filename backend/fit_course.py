"""Codificador de PERCURSO no formato FIT (Garmin) — sem dependências.

Usado por `garmin.py` (`GET /garmin/course/<tipo>/<id>.fit`): o app do relógio
baixa o arquivo com `HTTP_RESPONSE_CONTENT_TYPE_FIT` e entrega à navegação
nativa; o mesmo arquivo serve pro "Exportar pro Garmin" do site (o Garmin
Connect importa .fit de percurso).

Só FIT, não GPX: o Forerunner 955 não aceita rota GPX baixada por um app
Connect IQ (o Edge 1040 aceita os dois) — ver garmin/README.md.

Estrutura (a de um percurso exportado por RideWithGPS/Garmin Connect):
    file_id (type=course) · course (nome, esporte) · lap (resumo) ·
    event timer start · record × N (posição, distância, [altitude], tempo) ·
    course_point × M (POIs) · event timer stop_disable_all

Os instantes são SINTÉTICOS (velocidade constante `speed_mps`): o FIT de
percurso exige timestamp por ponto e o aparelho usa isso só no "parceiro
virtual". Altitude é opcional — rotas salvas do amora não têm elevação no
estado salvo (o aparelho então não mostra perfil de subida); rotas do
RideWithGPS trazem `<ele>` no GPX.

O layout dos campos segue o Profile.xlsx do FIT SDK; a conferência é feita
decodificando a saída com o `garmin-fit-sdk` oficial (garmin/tools/).
"""
from __future__ import annotations

import math
import struct
import time

# Segundos entre a época Unix e a época FIT (1989-12-31T00:00:00Z).
FIT_EPOCH_OFFSET = 631065600
SEMICIRCLES_PER_DEG = 2 ** 31 / 180.0

# Tipos-base FIT (byte do tipo na definição, formato struct, tamanho, inválido).
_ENUM = (0x00, "B", 1)
_UINT8 = (0x02, "B", 1)
_UINT16 = (0x84, "H", 2)
_SINT32 = (0x85, "i", 4)
_UINT32 = (0x86, "I", 4)
_UINT32Z = (0x8C, "I", 4)
_STRING = 0x07

# Números globais das mensagens.
MESG_FILE_ID, MESG_LAP, MESG_RECORD, MESG_EVENT = 0, 19, 20, 21
MESG_COURSE, MESG_COURSE_POINT = 31, 32

FILE_TYPE_COURSE = 6
MANUFACTURER_DEVELOPMENT = 255
SPORT_CYCLING = 2
EVENT_TIMER = 0
EVENT_TYPE_START = 0
EVENT_TYPE_STOP_DISABLE_ALL = 9

# course_point.type — só os valores antigos do enum, que todo aparelho conhece.
CP_GENERIC, CP_SUMMIT, CP_VALLEY, CP_WATER, CP_FOOD = 0, 1, 2, 3, 4
CP_DANGER, CP_FIRST_AID = 5, 9

# Símbolos Garmin que o editor do amora grava nos POIs (`sym` do GPX) →
# tipo do ponto de percurso. O que não casar vira "genérico".
_SYM_TO_CP = (
    ("summit", CP_SUMMIT), ("water", CP_WATER), ("drinking", CP_WATER),
    ("restaurant", CP_FOOD), ("food", CP_FOOD), ("pizza", CP_FOOD),
    ("fast food", CP_FOOD), ("bar", CP_FOOD), ("convenience", CP_FOOD),
    ("shopping", CP_FOOD), ("danger", CP_DANGER), ("skull", CP_DANGER),
    ("medical", CP_FIRST_AID), ("first aid", CP_FIRST_AID),
    ("pharmacy", CP_FIRST_AID), ("valley", CP_VALLEY),
)

MAX_RECORDS = 10000        # teto de pontos do traçado (decimação uniforme)
MAX_COURSE_POINTS = 200    # limite prático dos aparelhos
NAME_MAX_BYTES = 47        # + NUL


_CRC_TABLE = (0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400)


def crc16(data: bytes, crc: int = 0) -> int:
    """CRC-16 do FIT (tabela de nibbles do SDK)."""
    for b in data:
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[b & 0xF]
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[(b >> 4) & 0xF]
    return crc


def _haversine(lat1, lon1, lat2, lon2):
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _semi(deg: float) -> int:
    v = int(round(deg * SEMICIRCLES_PER_DEG))
    return max(-2 ** 31 + 1, min(2 ** 31 - 1, v))


def _fit_string(s: str, max_bytes: int = NAME_MAX_BYTES) -> bytes:
    """UTF-8 truncado em fronteira de caractere + NUL final."""
    raw = (s or "").encode("utf-8")
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
        while raw and (raw[-1] & 0xC0) == 0x80:   # byte de continuação solto
            raw = raw[:-1]
        if raw and raw[-1] >= 0xC0:               # líder sem continuação
            raw = raw[:-1]
    return raw + b"\x00"


class _Writer:
    """Acumula mensagens de definição + dados (little-endian, sem compressão
    de timestamp). Um tipo local por mensagem global."""

    def __init__(self):
        self.buf = bytearray()
        self._fmt = {}

    def define(self, local: int, global_num: int, fields):
        """fields: [(nº do campo, tipo-base | ('s', tamanho))]."""
        self.buf += struct.pack("<BBBHB", 0x40 | local, 0, 0, global_num, len(fields))
        fmt = "<B"
        for num, typ in fields:
            if isinstance(typ, tuple) and typ[0] == "s":
                size = typ[1]
                self.buf += struct.pack("<BBB", num, size, _STRING)
                fmt += f"{size}s"
            else:
                code, f, size = typ
                self.buf += struct.pack("<BBB", num, size, code)
                fmt += f
        self._fmt[local] = fmt

    def data(self, local: int, *values):
        self.buf += struct.pack(self._fmt[local], local, *values)

    def finish(self) -> bytes:
        header = struct.pack("<BBHI4s", 14, 0x10, 2132, len(self.buf), b".FIT")
        header += struct.pack("<H", crc16(header))
        body = header + bytes(self.buf)
        return body + struct.pack("<H", crc16(body))


def _cp_type(sym: str) -> int:
    s = (sym or "").lower()
    for needle, t in _SYM_TO_CP:
        if needle in s:
            return t
    return CP_GENERIC


def encode_course(name, latlngs, pois=None, elevations=None, speed_mps=4.2,
                  created=None, min_spacing_m=10.0) -> bytes:
    """Monta o .fit de um percurso de bicicleta.

    `latlngs`: [[lat, lng], …] (≥ 2 pontos). `pois`: [{lat, lng, name, sym}].
    `elevations`: lista paralela a `latlngs` (m; None onde faltar) — só entra
    no arquivo se TODOS os pontos tiverem altitude. `created`: epoch Unix
    (default: agora). `min_spacing_m`: espaçamento mínimo entre pontos
    gravados (0 = todos). Levanta ValueError com traçado inválido."""
    pts = [(float(p[0]), float(p[1])) for p in (latlngs or [])
           if isinstance(p, (list, tuple)) and len(p) >= 2
           and math.isfinite(float(p[0])) and math.isfinite(float(p[1]))
           and abs(float(p[0])) <= 90 and abs(float(p[1])) <= 180]
    eles = None
    if elevations is not None and len(elevations) == len(latlngs or []) \
            and len(pts) == len(elevations) \
            and all(isinstance(e, (int, float)) and math.isfinite(e) for e in elevations):
        eles = [float(e) for e in elevations]
    if len(pts) < 2:
        raise ValueError("percurso precisa de pelo menos 2 pontos")

    # Distância acumulada sobre a geometria CHEIA (a decimação não a encurta).
    dist = [0.0]
    for i in range(1, len(pts)):
        dist.append(dist[-1] + _haversine(pts[i - 1][0], pts[i - 1][1],
                                          pts[i][0], pts[i][1]))
    total = dist[-1]
    if total <= 0:
        raise ValueError("percurso de comprimento zero")

    # Desbaste: um GPX do RideWithGPS traz um ponto a cada ~2 m (10 km = 5 mil
    # pontos, ~95 kB pelo Bluetooth do celular). Mantém um ponto a cada
    # `min_spacing_m` de arco — corta uma esquina em no máximo ~2 m.
    idx = [0]
    for i in range(1, len(pts) - 1):
        if dist[i] - dist[idx[-1]] >= min_spacing_m:
            idx.append(i)
    idx.append(len(pts) - 1)
    if len(idx) > MAX_RECORDS:
        stride = (len(idx) - 1) / (MAX_RECORDS - 1)
        idx = [idx[j] for j in sorted({round(i * stride) for i in range(MAX_RECORDS)})]

    speed = max(0.5, float(speed_mps))
    t0 = int(created if created is not None else time.time()) - FIT_EPOCH_OFFSET
    t0 = max(1, t0)

    def ts(d):
        return t0 + int(round(d / speed))

    w = _Writer()

    w.define(0, MESG_FILE_ID, [(0, _ENUM), (1, _UINT16), (2, _UINT16),
                               (3, _UINT32Z), (4, _UINT32)])
    w.data(0, FILE_TYPE_COURSE, MANUFACTURER_DEVELOPMENT, 1, (t0 & 0xFFFFFFFF) or 1, t0)

    cname = _fit_string(name or "amora")
    w.define(1, MESG_COURSE, [(4, _ENUM), (5, ("s", len(cname)))])
    w.data(1, SPORT_CYCLING, cname)

    end_t = ts(total)
    elapsed_ms = max(1, (end_t - t0) * 1000)
    w.define(2, MESG_LAP, [(253, _UINT32), (2, _UINT32), (3, _SINT32), (4, _SINT32),
                           (5, _SINT32), (6, _SINT32), (7, _UINT32), (8, _UINT32),
                           (9, _UINT32)])
    w.data(2, end_t, t0, _semi(pts[0][0]), _semi(pts[0][1]),
           _semi(pts[-1][0]), _semi(pts[-1][1]), elapsed_ms, elapsed_ms,
           int(round(total * 100)))

    w.define(3, MESG_EVENT, [(253, _UINT32), (0, _ENUM), (1, _ENUM), (4, _UINT8)])
    w.data(3, t0, EVENT_TIMER, EVENT_TYPE_START, 0)

    if eles is not None:
        w.define(4, MESG_RECORD, [(253, _UINT32), (0, _SINT32), (1, _SINT32),
                                  (5, _UINT32), (2, _UINT16)])
        for i in idx:
            alt = int(round((eles[i] + 500.0) * 5.0))
            w.data(4, ts(dist[i]), _semi(pts[i][0]), _semi(pts[i][1]),
                   int(round(dist[i] * 100)), max(0, min(0xFFFE, alt)))
    else:
        w.define(4, MESG_RECORD, [(253, _UINT32), (0, _SINT32), (1, _SINT32),
                                  (5, _UINT32)])
        for i in idx:
            w.data(4, ts(dist[i]), _semi(pts[i][0]), _semi(pts[i][1]),
                   int(round(dist[i] * 100)))

    # POIs → pontos de percurso, presos ao vértice mais próximo do traçado.
    cps = []
    for p in (pois or []):
        try:
            la, lo = float(p.get("lat")), float(p.get("lng"))
        except (TypeError, ValueError, AttributeError):
            continue
        if not (math.isfinite(la) and math.isfinite(lo)):
            continue
        best_i, best_d = 0, float("inf")
        for i, (a, b) in enumerate(pts):
            # equiretangular: basta pra achar o vértice mais próximo
            dd = (a - la) ** 2 + ((b - lo) * math.cos(math.radians(la))) ** 2
            if dd < best_d:
                best_i, best_d = i, dd
        cps.append((dist[best_i], la, lo, str(p.get("name") or "").strip(),
                    _cp_type(p.get("sym") or p.get("type") or "")))
    cps.sort(key=lambda c: c[0])
    cps = cps[:MAX_COURSE_POINTS]
    if cps:
        size = max(len(_fit_string(c[3], 31)) for c in cps)
        w.define(5, MESG_COURSE_POINT, [(254, _UINT16), (1, _UINT32), (2, _SINT32),
                                        (3, _SINT32), (4, _UINT32), (5, _ENUM),
                                        (6, ("s", size))])
        for n, (d, la, lo, nm, typ) in enumerate(cps):
            w.data(5, n, ts(d), _semi(la), _semi(lo), int(round(d * 100)), typ,
                   _fit_string(nm, 31).ljust(size, b"\x00"))

    w.data(3, end_t, EVENT_TIMER, EVENT_TYPE_STOP_DISABLE_ALL, 0)
    return w.finish()
