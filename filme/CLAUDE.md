# Filme — working notes for Claude

A ~4 min retrospective video of Pedal Hidrográfico, edited in CapCut from amora's media.
Read [README.md](README.md) for the structure, tool list and recipes, and
[DIARIO.md](DIARIO.md) for what was done and decided. This file is the short list of
things that are easy to get wrong.

## Where to work

- The tools run from `~/Movies/amora-capcut-tools/`, **not** from this folder: the repo lives on
  a network share that drops mid-session. `filme/ferramentas/` is a snapshot — after changing a
  tool, copy it back here (`cp ~/Movies/amora-capcut-tools/*.py filme/ferramentas/`).
- Never keep anything you need in the session scratchpad. A reboot wiped it once and took the
  3D map renderer and every cache with it (the renderer was later rebuilt from the session log).
- Media, renders, audio and CapCut projects stay out of the repo (it is public, and they are
  large). No people's names, e-mail addresses or ledger contents in anything committed here.

## Editing a CapCut project

Projects live in `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`:
`bicicultura-pedalhidro` (16:9) and `bicicultura-pedalhidro-4x5` (portrait). The portrait one
was generated from the 16:9 one by `make_4x5.py` and then **edited by hand** (clips moved, a scene
shortened by 2 s): never run `make_4x5.py --refaz` on it again — that would wipe those edits.
Each project has its own soundtrack files (`-247s` for 16:9, `-4x5-v2` for portrait).

- **Only write while CapCut is closed.** Check with
  `ps -axo comm | grep -i -E 'capcut|jianying'`. Never quit it yourself — ask.
- The draft is `draft_info.json` plus three identical copies (`template-2.tmp`, and both files
  again under `Timelines/<id>/`). Write all four; `cmp` them afterwards.
- Back up the project folder (zip) before every write. Dry-run first.
- Every tool verifies itself by undoing its change in memory and requiring the result to equal
  the original draft. Keep that pattern in new tools; it is what catches unintended edits.
- Preserve what the person editing set by hand — volumes, mutes, positions, label wording.
  Add or extend; do not regenerate what already exists unless asked.
- You cannot see CapCut's output. Say so in every report, and name the timestamps worth
  checking. `capcut_layout.py` models placement (validated against a real export for position,
  scale, crop and rotation) and `previa45.py` draws contact sheets, but compound clips are
  unreadable to it and labels are drawn in a stand-in font.
- Cloning a segment means cloning its material and every `extra_material_refs` entry with new
  ids. Track order in the list must match each segment's `track_render_index`.

## Things the timeline depends on

- **60 BPM grid.** Cuts sit on whole seconds. The metronome and all music generators read the
  timeline from the draft, so re-render audio after the timeline moves.
- **File-name prefixes are an interface:** `1110-intro`, `1110-mural-10s-60bpm` and
  `1110-numeros-10s` are how the audio tools find the map, the wall and the stats matrix, and
  how `make_4x5.py` swaps in the portrait renders. Keep the prefix when re-rendering.
- **Step times are shared by both aspect ratios** (wall: 1, 3, 5, 7, 9 s; matrix: 4 and 7 s), so
  one soundtrack serves both projects.
- When extending audio that is already mixed, splice (`estende.py`) instead of re-rendering:
  the generators normalise the whole file, so a full re-render shifts the level of everything.

## Taste, as stated by the person editing

- Music: neutral and contemplative — not cute, not upbeat, not "spacey", not optimistic or
  pessimistic. Enough structure to tell where the film is and how much is left, and no more.
- Stats matrix: IBM Plex Mono, text only (no borders, no colour bars).
- Opening map in portrait: a single map, not a split view.
- Ask before big stylistic swings; show a still or a short sample first.

## Sources

- Tour data: `https://amora.pedalhidrografi.co/data/tours.ttl` and `images.ttl` (public).
  Stats follow `web/censo.html` — change the numbers there and here together.
- Everything the projects read lives in `~/Movies/2026-bicicultura/video-pedalhidro/` (see its
  `LEIAME.md`). Moving or renaming it breaks both projects until they are re-pointed with
  `religar.py`.
- The original-quality videos carry two names each (hash-only and tour-prefixed hard links); the
  tools read tour and date from the file name, so the projects use the prefixed one.
- CapCut rejects amora's 720p WebM files ("unsupported media"); convert them to MP4 first.
- Soft edges are a rectangle mask per clip with feather 0.05 and round corner 0.05 (values taken
  from a mask the editor made by hand). New masks are 95 % of the clip, with the clip scaled up
  to compensate. Compound clips have none.
- The colourful basemap covers only the metropolitan region. Beyond it the portrait map continues
  the same look with colours computed from elevation and slope, learned from the covered pixels.
