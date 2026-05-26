# Photos-RDF — Design Notes

Notes accumulated across the design of the photos/tours RDF substrate:
[ontology.ttl](ontology.ttl), [shapes.ttl](shapes.ttl), [data/initial-data.ttl](data/initial-data.ttl),
[data/tours.ttl](data/tours.ttl), [build-tours.py](build-tours.py), [upload-form.html](upload-form.html).

## 1. Vocabulary strategy

**Reuse external vocabularies first; mint `ph:` only for project-specific concepts.**
Per `CLAUDE.md`. Order of preference, when a concept fits multiple:

1. PROV-O (primary — per stored memory `[[feedback_ontology_prov_preference]]`)
2. schema.org (secondary)
3. Dublin Core (`dcterms:`) for bibliographic / file metadata
4. QUDT for quantities & units
5. NFO for file hashes
6. EXIF for camera metadata
7. GeoSPARQL for spatial primitives (currently only `schema:GeoCoordinates` is used)

Project-minted `ph:` classes & properties:

- **Classes:** `ph:Tour` (`⊑ prov:Activity, schema:Event`), `ph:Image`
  (`⊑ prov:Entity, schema:ImageObject`), `ph:Association` (reification of
  Tour↔EventSeries membership), `ph:RouteReference` (URL + provider).
- **Object properties:** `ph:capturedDuring` (Image → Tour, `⊑ prov:wasGeneratedBy`),
  `ph:linkRoute`, `ph:inSeriesEdition`, `ph:inEventSeries`, `ph:energyEstimate`.
- **Datatype properties:** `ph:linkInstagram`, `ph:countAttendee`,
  `ph:countNewcomer`, `ph:sequenceInSeries`, `ph:intensityClassification`,
  `ph:mediaCount`, `ph:anonymized`, `ph:compressed`.
- **Reusable instances:** `ph:rwgps`, `ph:strava` declared as
  `schema:Organization` so route references can use `schema:provider`.

**Deprecated but retained** (with `owl:deprecated true` + `owl:equivalentProperty`):
`ph:linkRWGPS`, `ph:EventSeriesSequenceNumber`, `ph:estimate_quilojoules`.
Old data keeps validating; new data should use the successors.

### Naming conventions

- Classes: `PascalCase`.
- Properties: `lowerCamelCase`.
- Avoid baking units into property names (`ph:estimate_quilojoules` → `ph:energyEstimate`; unit lives in `qudt:hasUnit`).
- Avoid snake_case (legacy artefact — being phased out).

## 2. Shapes & validation

Shapes are organized as one `sh:NodeShape` per concept, with `sh:property` blocks for each constraint.

**Severities:**
- `sh:Violation` — must hold (date format, GPS presence, valid IRIs, route reference).
- `sh:Warning` — encouraged but not required (attribution, license, camera metadata, optional flags).

**Cross-property constraint (SPARQL).** `ph:EnergyEstimateShape` validates that
`ph:intensityClassification` matches the bucket implied by `qudt:numericValue` (kJ):

| Range (kJ)  | Label         |
| ----------- | ------------- |
| 0 ≤ x < 150 | De boa        |
| 150 ≤ x < 300 | Ok          |
| 300 ≤ x < 500 | Endorfinado |
| 500 ≤ x < 1000 | Frito      |
| x ≥ 1000    | Insano        |
| x < 0       | invalid (rejected via separate `sh:minInclusive 0`) |

Scoped to the energy-estimate context via `sh:targetObjectsOf ph:energyEstimate`,
not on every `qudt:QuantityValue` (so other quantities aren't subject to the rule).

**License is an IRI**, not a string (`sh:nodeKind sh:IRI`). Use the canonical
Creative Commons URL.

**Auto-detected booleans:** `ph:anonymized` and `ph:compressed` are optional
warnings. Only emit `true` — absence implies `false`; tidies the TTL.

### Validation pipeline gotcha

`pyshacl.validate(..., ont_graph=ont)` makes axioms available for inference but
**does not expose instance triples in `ont` to `sh:class` checks**. The fix is
to merge `data + ont` and pass the merged graph as `data_graph`:

```python
merged = data + ont
pyshacl.validate(merged, shacl_graph=shapes, inference='rdfs', advanced=True)
```

This was discovered when `ph:rwgps` (declared as `schema:Organization` only in
`ontology.ttl`) wasn't being recognized by `ph:RouteReferenceShape`'s
`schema:provider` class check. Going forward, **any project-wide validation
script should always pass the merged graph.**

## 3. Data graphs

### IRI schemes

- Tours: `phd:tour_<eH>` where eH is the integer "ever" counter from the CSV.
- Persons: `phd:pessoa<Capitalized>` (slugified, accents stripped). The original
  nickname/full name lives in `schema:alternateName`.
- Images: `phd:image_<phash16>` — uses the full 16-hex perceptual hash as the
  IRI suffix. **Near-duplicate uploads share an IRI**, which is the clustering
  behavior described in `CLAUDE.md`.
- Series: `phd:PH`, `phd:BP`, `phd:S` (Suados), `phd:BT` (Trips/Bondes).
- Associations: `phd:assoc_<series>_<n>` (one per (series, sequence) pair).
- Providers: `ph:rwgps`, `ph:strava` (vocabulary-level instances).

### Reification of series membership

`schema:organizer` was being misused as `Tour → Association`. Fixed by:

1. Inventing `ph:inSeriesEdition` (Tour → Association).
2. Inventing `ph:inEventSeries` (Association → EventSeries) and
   `ph:sequenceInSeries` (Association → integer).
3. Leaving `schema:organizer` available for the actual organizing person/org
   (currently unfilled).

A Tour can have multiple series memberships (e.g. PH-83 was also BP-3) — the
Association reification carries the per-series sequence number cleanly.

### Photo provenance

- **Attribution**: `prov:wasAttributedTo` (the author — cartographer/copywriter/
  artist roles all funneled to the same predicate based on the CSV's 🗺️📝🎨
  columns).
- **Upload provenance**: `pav:providedBy` (who actually uploaded). Often the
  same person as the author; data file has them separate.

## 4. Build pipeline (build-tours.py)

Converts a TSV dump of the spreadsheet (`data/tours.csv`) into `data/tours.ttl`.
Reproducible: `python3 build-tours.py`.

**Sentinels treated as "no value":** `''`, `-`, `n/a`, `?`, `sumiu`, `#DIV/0!`,
`#REF!`, `#N/A`.

**Number parsing**: strips comma thousand separators (`1,700` → `1700`).

**Dates**: assumes São Paulo timezone (`-03:00`); writes `xsd:dateTime`.

**Routes**: only emits `ph:linkRoute` when the URL host matches
`ridewithgps.com` or `strava.com`. Provider derived from URL host.

**Intensity classification**: computed automatically from kJ value using the same
bucket table the SHACL rule enforces.

**Persons**: nicknames slugged → `phd:pessoa<Name>`, deduped across the dataset,
declared with `schema:alternateName` carrying the raw nickname.

**Series titles**: hardcoded guesses (`Pedais Hidrográficos Regulares`,
`Bicipassarinhadas`, `Pedais Hidrográficos Suados`, `Bondes / Trips`) — update
in the script if better titles emerge.

## 5. Upload form (upload-form.html)

Browser-only, dependency-light, but loads several modules from CDN at runtime
(see deps below). Needs HTTP (the catalog fetch breaks on `file://`).

```
python3 -m http.server -d research/photos-rdf 8000
# → http://localhost:8000/upload-form.html
```

### CDN dependencies

| Lib | Purpose |
|-----|---------|
| `exifr` | EXIF parsing (date, GPS, bearing, focal length) |
| `n3` | Turtle parsing (loads `data/tours.ttl` + `data/initial-data.ttl` for the catalog) |
| `tom-select` | Searchable, multi-select dropdown with on-the-fly creation for people |
| `jszip` | Build the update-kit ZIP |

All four are tolerated as missing: form degrades to manual entry if any CDN is
unreachable.

### Perceptual hash (pHash)

Switched from SHA-256 to a Hacker-Factor-style **pHash** so near-duplicates
cluster naturally:

1. Decode → 32×32 grayscale
2. Separable 2D DCT
3. Top-left 8×8 low-frequency block
4. Median of 63 (excluding DC)
5. Bit = `coef > median` → 64 bits → 16 hex

Hamming distance ≤ `PHASH_DUP_THRESHOLD` (default **5**) → reject the upload
as a duplicate. Threshold is tunable at the top of the module script. The
notice that fires names both files and the distance, so users can calibrate.

### Tour auto-detection

When a photo's date is set (manually or from EXIF), the form picks the tour
whose start time falls in `[photo − 2h, photo + 12h]`. Ties broken by closest
start. Two ways the detection gets locked:

1. If a default tour was set in the Padrões panel, the card's
   `skipAutoDetect` flag is true from the start.
2. If the user picks a tour manually after the fact, `skipAutoDetect` flips on
   via the select's `change` event.

Programmatic `select.value = …` does **not** fire `change` — so the
auto-detector setting the value doesn't accidentally lock itself.

### Card lifecycle

- Single picker (`#files`) at the bottom of the page (below `#cards`), so it
  naturally moves down as cards accumulate.
- Each pick **appends** to the existing set; **Limpar todas as fotos** clears.
- `pickerBusy` flag re-entry-guards the change handler against browsers that
  fire `change` twice on a single dialog (Safari quirk).
- `clearNotices()` at the start of each pick so stale messages from prior
  uploads don't bleed into the new batch.
- Per-card **remove (×) button** destroys Tom Select instances, revokes the
  thumbnail's object URL, and removes the card from `cards[]`.

### Notices placement

Live inside the upload-zone fieldset, next to the file picker (not at the top
of the document) — so the message about a pick is adjacent to the picker that
caused it.

### Update kit ZIP

```
update.ttl
photos/<phash>/original.<ext|jpg>
photos/<phash>/large.jpg     ≤ 500 KB
photos/<phash>/thumb.jpg     256 px
```

`large.jpg` and `thumb.jpg` are always (re)generated from the cached
`ImageBitmap` (one decode pass per photo). `original` depends on the per-card
toggles:

- `Comprimir` → 500 KB compressed JPEG (re-encoded)
- `Anonimizar` (alone) → re-encoded JPEG, EXIF stripped as a side effect
- Neither → raw file bytes, original extension preserved

Compression loop tries quality 0.85 → 0.3 at progressively smaller max
dimensions (2400 → 500 px) until the blob fits the 500 KB target.

### Defaults panel

Single panel on the upload zone with:

- Tour (overrides auto-detect if set)
- Autoras (multi-select, can create new persons)
- Quem subiu (multi-select, can create new persons)
- Licença
- Anonimizar / Comprimir checkboxes

Defaults apply at card creation time. Changing the defaults after cards exist
does not retroactively touch them — re-upload to re-apply.

**Person mint propagation.** When a user types a new person in any
person-select (defaults panel or any card), `mintPerson()` adds the option to
**every** existing person-select in the page via a shared `personSelects[]`
registry. The new person is emitted as `phd:pessoaX a schema:Person ;
schema:alternateName "..."` at the top of the generated Turtle when used.

### UI strings & code identifiers

- Portuguese in UI labels, messages, and form copy.
- English in code identifiers, comments-when-needed, and TTL property names.

## 6. Cross-cutting conventions

- IRIs over string literals when the value is dereferenceable (licenses,
  provider URLs, route references).
- Datetimes always carry timezone (`-03:00` for SP).
- Numbers strip thousand separators before emission.
- Default license: `CC BY-SA 4.0`.
- Booleans only emit when `true` (omit-default convention to keep TTL terse).

## 7. Known limitations & open questions

- **`pav:providedBy` warning fires on every backfilled tour** (102/102). The CSV has no provider column; we either need to drop the requirement from `TourShape` or treat 🗺️ (cartographer) as the provider too.
- **6 tours lack a route URL.** The shape was relaxed from Violation to Warning to accommodate them; if a tour genuinely has no published route, this is fine.
- **One tour (#84 "SESC Consolação")** has no series membership (`PH=n/a`). Intentional per the spreadsheet.
- **#41 series swap?** `phd:assoc_PH_1` points to `phd:BP` and `phd:assoc_BP_1` to `phd:PH`. Possibly a data error in the original spreadsheet; the converter doesn't second-guess.
- **Series titles for `PH-S` and `BT`** are guesses — confirm with the user.
- **pHash on low-variance images** (uniform gray, dark frames) is dominated by floating-point noise. In practice this matters only for synthetic/edge-case inputs.
- **Form requires HTTP.** Catalog fetch (`./data/tours.ttl`) breaks under `file://` — documented above. Could be bypassed by pre-baking the catalog into the HTML at build time if a fully offline mode is needed.
