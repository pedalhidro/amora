#!/usr/bin/env python3
"""Converte data/tours.csv em web/data/tours.ttl seguindo shapes.ttl."""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO_ROOT = ROOT.parent.parent
CSV_PATH = ROOT / 'data' / 'tours.csv'
TTL_PATH = REPO_ROOT / 'web' / 'data' / 'tours.ttl'

# Sentinels treated as "no value"
BLANK = {'', '-', 'n/a', 'N/A', '?', 'sumiu', '#DIV/0!', '#REF!', '#N/A'}

def blank(v): return (v or '').strip() in BLANK

def to_int(v):
    if blank(v): return None
    try: return int(v.replace(',', '').strip())
    except ValueError: return None

def to_dec(v):
    if blank(v): return None
    try: return float(v.replace(',', '').strip())
    except ValueError: return None

DT_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})')

def to_xsd_datetime(v):
    if blank(v): return None
    m = DT_RE.match(v.strip())
    if not m: return None
    return f'{m.group(1)}T{m.group(2)}:00-03:00'

DUR_RE = re.compile(r'^(\d{1,3}):(\d{1,2})(?::(\d{1,2}))?$')

def to_xsd_duration(v):
    """'1:00' / '0:52' / '2:35:30' → 'PT1H0M0S' / 'PT0H52M0S' / 'PT2H35M30S'.
    Anything else (including '100%' garbage from misaligned cells) → None."""
    if blank(v): return None
    m = DUR_RE.match(v.strip())
    if not m: return None
    h  = int(m.group(1))
    mn = int(m.group(2))
    sc = int(m.group(3) or 0)
    if mn >= 60 or sc >= 60: return None
    return f'PT{h}H{mn}M{sc}S'

HHMM_RE = re.compile(r'^(\d{1,2}):(\d{2})$')

def parse_hhmm(v):
    """'20:35' → (20, 35); rejeita coisas tipo '20:00:00', '100%', '?'."""
    if blank(v): return None
    m = HHMM_RE.match(v.strip())
    if not m: return None
    h, mn = int(m.group(1)), int(m.group(2))
    if h >= 24 or mn >= 60: return None
    return (h, mn)

def combine_date_time(date_str, hm, day_offset=0):
    """date_str='2024-09-09', hm=(20, 35), day_offset=0|1 → '2024-09-09T20:35:00-03:00'.
    day_offset=1 desloca pro dia seguinte (caso Chegada cruze meia-noite)."""
    from datetime import date as Date, timedelta
    y, m, d = (int(x) for x in date_str.split('-'))
    base = Date(y, m, d) + timedelta(days=day_offset)
    return f'{base.isoformat()}T{hm[0]:02d}:{hm[1]:02d}:00-03:00'

def slug(name):
    s = re.sub(r'[^a-z0-9]', '', name.strip().lower())
    return s

def cap(s):
    return s[:1].upper() + s[1:] if s else s

def split_people(v):
    if blank(v): return []
    out = []
    for part in v.split(','):
        s = slug(part)
        if s and s != 'na':
            out.append(s)
    return out

def is_url(s): return s.startswith(('http://', 'https://'))

def turtle_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

def intensity_for(kj):
    if kj is None: return None
    if kj < 0:    return None  # caller should skip
    if kj < 150:  return 'De boa'
    if kj < 300:  return 'Ok'
    if kj < 500:  return 'Endorfinado'
    if kj < 1000: return 'Frito'
    return 'Insano'

def main():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter='\t'))
    header, data = rows[0], rows[1:]

    persons   = set()
    assocs    = {}   # (series, num) -> phd:assoc_<series>_<num>
    tour_ttls = []
    missing_route = []
    missing_attrib = []

    for r in data:
        # pad short rows
        while len(r) < 35: r.append('')

        eh    = r[1].strip()
        nome  = r[6].strip()
        dt    = to_xsd_datetime(r[0])
        if blank(eh) or blank(nome) or not dt:
            continue

        tour_id = f'phd:tour_{eh}'
        props   = ['a ph:Tour',
                   f'dcterms:title "{turtle_escape(nome)}"',
                   f'dcterms:date "{dt}"^^xsd:dateTime']

        # series memberships
        for col, series in [(2,'PH'), (3,'BP'), (4,'S'), (5,'BT')]:
            n = to_int(r[col])
            if n is None: continue
            key = (series, n)
            assocs.setdefault(key, f'phd:assoc_{series}_{n}')
            props.append(f'ph:inSeriesEdition {assocs[key]}')

        # rota — emite ph:linkRoute com provedor (RWGPS ou Strava)
        rota = (r[15] or '').strip().strip('"').strip()
        provider = None
        if is_url(rota):
            if 'ridewithgps.com' in rota: provider = 'ph:rwgps'
            elif 'strava.com'   in rota: provider = 'ph:strava'
        if provider:
            props.append(
                'ph:linkRoute [\n'
                '        a ph:RouteReference ;\n'
                f'        schema:url <{rota}> ;\n'
                f'        schema:provider {provider}\n'
                '    ]'
            )
        else:
            missing_route.append((eh, nome))

        # Instagram post
        ig = (r[14] or '').strip()
        if is_url(ig) and 'instagram.com' in ig:
            props.append(f'ph:linkInstagram "{turtle_escape(ig)}"^^xsd:anyURI')

        # head-counts
        n_pres = to_int(r[21])
        if n_pres is not None and n_pres >= 0:
            props.append(f'ph:countAttendee {n_pres}')
        n_new = to_int(r[22])
        if n_new is not None and n_new >= 0:
            props.append(f'ph:countNewcomer {n_new}')

        # energia (kJ anunciado)
        kj = to_dec(r[24])
        if kj is not None and kj >= 0:
            cls = intensity_for(kj)
            kj_lit = f'{kj:g}'
            props.append(
                'ph:energyEstimate [\n'
                '        a qudt:QuantityValue ;\n'
                f'        qudt:numericValue "{kj_lit}"^^xsd:decimal ;\n'
                '        qudt:hasUnit unit:KiloJ ;\n'
                f'        ph:intensityClassification "{cls}"\n'
                '    ]'
            )

        # energia medida (kJ med. — col 25) → ph:measuredEnergy.
        kj_meas = to_dec(r[25])
        if kj_meas is not None and kj_meas >= 0:
            kj_meas_lit = f'{kj_meas:g}'
            props.append(
                'ph:measuredEnergy [\n'
                '        a qudt:QuantityValue ;\n'
                f'        qudt:numericValue "{kj_meas_lit}"^^xsd:decimal ;\n'
                '        qudt:hasUnit unit:KiloJ\n'
                '    ]'
            )

        # atribuição (🗺️ + 📝 + 🎨 → prov:wasAttributedTo)
        attribs = set()
        for col in (11, 12, 13):
            for s in split_people(r[col]):
                attribs.add(s)
                persons.add(s)
        if attribs:
            for s in sorted(attribs):
                props.append(f'prov:wasAttributedTo phd:pessoa{cap(s)}')
        else:
            missing_attrib.append((eh, nome))

        # mídias coletadas
        midias = to_int(r[34])
        if midias is not None and midias > 0:
            props.append(f'ph:mediaCount {midias}')

        # Tempo de movimento (col 28, 'Tempo Mov') → ph:movingDuration.
        mov = to_xsd_duration(r[28])
        if mov:
            props.append(f'ph:movingDuration "{mov}"^^xsd:duration')

        # Partida (col 19) / Chegada (col 20) → ph:departedAt / ph:arrivedAt.
        # São hora-do-dia (HH:MM); combinamos com a data de `Data-hora`. Se a
        # Chegada parecer anterior à Partida (cruzou meia-noite), avança 1 dia.
        # Sem Partida, usa Horário (col 18) como referência pra wrap-detection.
        date_only = dt[:10]  # 'YYYY-MM-DD' a partir de dt 'YYYY-MM-DDT…'
        partida = parse_hhmm(r[19])
        chegada = parse_hhmm(r[20])
        if partida:
            props.append(
                f'ph:departedAt "{combine_date_time(date_only, partida)}"^^xsd:dateTime'
            )
        if chegada:
            ref = partida or parse_hhmm(r[18])  # Horário planejado como fallback
            wrap = 1 if (ref and (chegada[0]*60 + chegada[1]) < (ref[0]*60 + ref[1])) else 0
            props.append(
                f'ph:arrivedAt "{combine_date_time(date_only, chegada, wrap)}"^^xsd:dateTime'
            )

        body = ' ;\n    '.join(props)
        tour_ttls.append(f'{tour_id}\n    {body} .\n')

    # output
    prefixes = '''\
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix pav:     <http://purl.org/pav/> .
@prefix ph:      <https://pedalhidrografi.co/terms#> .
@prefix phd:     <https://pedalhidrografi.co/data/> .
@prefix prov:    <http://www.w3.org/ns/prov#> .
@prefix qudt:    <http://qudt.org/schema/qudt/> .
@prefix schema:  <https://schema.org/> .
@prefix unit:    <http://qudt.org/vocab/unit/> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
'''

    series_block = '''
# Séries
phd:PH a schema:EventSeries ; dcterms:title "Pedais Hidrográficos Regulares" .
phd:BP a schema:EventSeries ; dcterms:title "Bicipassarinhadas" .
phd:S  a schema:EventSeries ; dcterms:title "Pedais Hidrográficos Suados" .
phd:BT a schema:EventSeries ; dcterms:title "Bondes / Trips" .
'''

    persons_block = '\n# Pessoas\n' + ''.join(
        f'phd:pessoa{cap(p)} a schema:Person ; schema:alternateName "{p}" .\n'
        for p in sorted(persons)
    )

    assocs_block = '\n# Associações (filiação a série)\n' + ''.join(
        f'phd:assoc_{s}_{n} a ph:Association ;\n'
        f'    ph:inEventSeries phd:{s} ;\n'
        f'    ph:sequenceInSeries {n} .\n'
        for (s, n) in sorted(assocs.keys())
    )

    tours_block = '\n# Passeios\n' + '\n'.join(tour_ttls)

    TTL_PATH.write_text(prefixes + series_block + persons_block + assocs_block + tours_block)

    print(f'✓ {len(tour_ttls)} passeios, {len(assocs)} associações, {len(persons)} pessoas → {TTL_PATH.relative_to(REPO_ROOT)}')
    if missing_route:
        print(f'⚠ {len(missing_route)} passeios sem RideWithGPS (falham linkRWGPS):',
              ', '.join(f'#{eh}' for eh, _ in missing_route[:10]),
              '…' if len(missing_route) > 10 else '')
    if missing_attrib:
        print(f'⚠ {len(missing_attrib)} passeios sem atribuição (falham prov:wasAttributedTo):',
              ', '.join(f'#{eh}' for eh, _ in missing_attrib[:10]))

if __name__ == '__main__':
    main()
