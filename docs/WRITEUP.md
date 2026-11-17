# How the Yuuyami Doori Tankentai English build works

夕闇通り探検隊 (Yuuyami Doori Tankentai, PlayStation, Spike, 1999, SLPS-02274). This document explains how the game's text
and menu graphics were found, how they are replaced, and how anyone can edit the translation and rebuild the disc.
Everything here was worked out from the retail disc image; no EXE patch, emulator trick or runtime hook is used in the
final build. **The English is a raw first pass** (see [Quality and limits](#9-quality-and-limits)).

Contents: 1 Short version, 2 Disc layout, 3 Finding the text, 4 The ACD scene format, 5 Replacing the text, 6 Menus (pictures),
7 Rebuilding the disc, 8 Editing the translation, 9 Quality and limits, 10 Reproducing from scratch, 11 Testing log, 12 Open items.

---

## 1. Short version

- The game stores no text strings. Each scene file ("ACD") contains its own **hand-drawn glyph tiles** and the dialogue is a
  list of tile indices. Searching for Shift-JIS finds nothing.
- Because the glyph tiles travel with each scene, **translating means swapping the scene's font for a Latin one and
  re-indexing the text**. The game's renderer already draws proportional text from a per-glyph width table, so English
  fits without touching the EXE.
- Scene files get bigger, so the archive `DATA/FILELINK.FLB` is rebuilt and the CD image is re-laid-out (later files moved by
  whole sectors, ISO directory records patched, EDC/ECC recomputed). The game follows the new tables without complaint.
- Menus, title screen, memory-card messages and the notebook are **pictures** (`EAS` image sets). They are redrawn at the
  same size, in place.
- The extracted Japanese lives in `translation/script/NNNN.json` (one file per unique scene, 1,234 files, 87,028 lines).
  Editing `en` (or `en_raw`) in those files and running one command re-inserts everything.

## 2. Disc layout

Reference dump: `Yuuyami Doori Tankentai (Japan).bin`, CRC32 `9d2b1afe`, SHA-1 `a6025151bddbf2c48157f0f5b91a27e03301a6f9`
(MODE2/2352, 307,677 sectors). ISO9660 holds only a few files:

| file | size | notes |
|---|---|---|
| `SLPS_022.74` | 468,992 B | main EXE, load 0x80010000. **Never modified.** |
| `DATA/FILELINK.FLB` | 556,816,800 B, LBA 254 | everything else: scenes, graphics, sound. **The only file that changes.** |
| `DATA/XALINK.XA`, `OPEN.STR`, `ROGO.STR` | | audio/movies; only *moved* (sector-exact) when the FLB grows |

`FILELINK.FLB` is a directory tree, not a flat archive (`tools/flb.py` documents the header). It has 15,735 leaf files. Leaves
are named by their position, e.g. `d009/d004/f051` = directory 9, sub-directory 4, file 51. Leaf types by magic bytes:
EVD (events), ACD (scene data with text), EAS (image sets), SEL, pBAV (sound banks), QVD, LSD, TIM, and a few others.

## 3. Finding the text

1. **Shift-JIS search failed.** Known character names (直樹, くるみ, サンゴ) appear nowhere as byte strings, in the EXE or the
   archive.
2. **A RAM dump during dialogue** showed 16x16 4bpp glyph bitmaps in RAM (copied there from the scene file) and a VRAM cache
   at (832,0) that the renderer uploads the needed glyphs to. So the text is drawn from bitmaps shipped with each scene.
3. Searching the archive leaves for those bitmaps located the **ACD** files, and rendering their glyph tiles and text records
   as an image (`tools/acd_render.py`) proved the layout.
4. Menus were checked the same way: the EXE and every system directory contain no UI text; the menu words are bitmaps inside
   `EAS` files (section 6). Only the memory-card *save title* (shown in the PlayStation memory card manager) is real text
   in `d000`, and it is deliberately left alone.

## 4. The ACD scene format

Three variants carry text: `ACD\0 1.20`, `ACD  1.20` (text only; the opening scene uses it) and a few `ACD  1.10`.
`tools/acd.py` parses and rebuilds all of them. Key points (see its docstring for the full field list):

- Header: magic, size fields, a table of section offsets and counts.
- **Sequence table** (at 0x50, 16 bytes each): for each timed "beat" of the scene, ranges into the other sections and a
  duration in frames. Text is referenced from here by record index. A range may start or end mid-line (a line revealed in two
  steps).
- **Text section**: 4-byte records `u16 glyph index, u8 ?, u8 delay`. Glyph `0xFFFF` ends a line; byte 3 is frames to wait
  after the character (2 normally; on the terminator, the hold time). Durations are the sum over the range, so **timing
  comes from the data, not from the player's reading speed**.
- **Metrics section**: 4 bytes per glyph (`font group, x offset, advance width`). This is why proportional English works.
- **Glyph tiles**: a 16-colour palette (index 15 = transparent, 14 = white, low = dark) then 128-byte tiles, low nibble = left
  pixel. A file's font is a few groups, each kana first, then the kanji that file uses. Files whose font is too small for the Latin
  glyph set (102 unique files in the full build) get the new font appended to the end of the leaf.

The same scene can appear at many paths (3,169 instances, 1,234 unique files, by content hash). The tools work on the unique
file and apply it to every path. `work/acd_index.json` maps file number to its paths.

## 5. Replacing the text

`tools/acd.py rebuild(d, lines, glyph)` does, for each scene file:

1. take the English lines (one per Japanese line; same count and order, because the sequence table points at line ranges),
2. build a Latin font containing only the characters used (`tools/latin_font.py`, DejaVu Sans Condensed 11, 1px dark fringe, ink
   drawn with high palette index) and its advance widths,
3. write new text records, keeping each character's delay and each beat's duration,
4. re-point the sequence table and fix all section offsets and counts,
5. return the new leaf (usually larger) plus a flag for "font appended".

Constraints this imposes on translators (enforced by `tools/check_script.py`):

- **Exactly one English line per Japanese line**, same order. Lines are shown on a timer, one or two at a time.
- **Width <= 256 px.** The screen is 320 px but only about 265 px are visible (overscan crop, found by an English line being
  clipped in DuckStation). Roughly 40-44 characters.
- **Printable ASCII only** (the Latin font has no accents or curly quotes).
- A file is only built into the game if **every** non-empty line in it has English (otherwise it is left in Japanese).

### Why no EXE patch was needed
The renderer reads each scene's own font, metrics and text records. Nothing in the EXE assumes full-width glyphs for dialogue,
so there is no hook point to add. The "hook" is purely the data: the ACD leaf and the archive tables that locate it.

## 6. Menus: EAS image sets

Title screen, Yes/No, notebook topics, rumor names, Settings page, help captions, save/memory-card messages, button labels,
the fiction disclaimer and the town-map labels are all pre-drawn images in 348 `EAS 1.00` leaves. `tools/eas.py` documents
the format. Essentials:

- Header 0x38, then a table of 20-byte entries (id, origin, width, height, bpp 4 or 8, **end** offset of pixels).
- **Row stride = image byte size / height** (rows are padded; assuming width/2 skews pictures). 4bpp: low nibble = left pixel.
- Palettes differ per image; the tool works in palette *indices*. The notebook pencil is drawn with **subtractive blending**
  (high index = darker) which is why the first redraws came out as faint dots.
- Every English image is rendered **at the same pixel size as the original**, in place, so the file never changes size and
  nothing needs to move.

`translation/ui/eas_text.json` (50 leaves, about 450 images) maps `leaf -> image number -> {text, style}`. **Do not hand-edit it:**
it is generated by `tools/mk_ui.py`, which also finds shared buttons (OK, Cancel, Map...) by pixel hash across every leaf.
Styles (`tools/eas.py: styled_rows`): `hand` (pencil, keeps the slant, `segs` places option words where the original words were
so the game's highlight boxes line up), `cap`, `help`, `msg`, `msgdark`, `save`, `btn`, `ramp`, `auto` (map labels: background
from the border pixels, ink from brightness percentiles, slant inferred), and `_disclaimer` for the full-screen notice.
`tools/eas_sheet.py <leaf> out.png A-B [scale]` draws a contact sheet so you can see an image set.

Not translated: the staff credits (`d011/f001-2`; mostly names), the notebook date header (it reuses the kanji for Monday/Sunday
as "month/day", so changing it would break the weekday display). The ~65 street-name captions on the per-area map close-ups
(`d002/f543-578`, images 15-18) are redrawn at tiny sizes and are guesses.

## 7. Rebuilding the disc

`python3 tools/build_disc.py en build/ydt_en.bin`

1. Walk every ACD leaf; for each unique file with a complete translation, `rebuild()` it.
2. Apply `translation/ui/eas_text.json` to the EAS leaves (same size, in place).
3. `tools/flb_rebuild.py`: rewrite `FILELINK.FLB` with the changed leaves. Offsets in the nested group tables are recomputed.
   **Gate:** with no replacements the output is byte-identical to the original.
4. `tools/isobuild.py`: write a new MODE2/2352 image. XA and STR files are moved by whole sectors to follow the larger FLB;
   the ISO directory records and primary volume descriptor (volume size) are patched; **EDC and ECC are regenerated** for every
   rewritten sector (`tools/psx_sector.py`, verified against original sectors).
5. Output: `ydt_en.bin` plus a `.cue` (single data track).

Current build: 309,764 sectors (+2,087 over the original). Quality control, run after every build:
`work/qc` (compiled from `tools/disc_qc.c`) checks sync, MSF header, EDC/ECC for Form 1 and Form 2 sectors (0 bad on the last
build); `tools/fscheck.py <new> <orig>` walks both ISO9660 filesystems and confirms only `FILELINK.FLB` differs.

## 8. Editing the translation

The raw files are `translation/en/NNNN.json` (English; published) and, locally after `setup.py`, `translation/script/NNNN.json` (same
plus the Japanese; never published). The local form is:

```json
{ "file": 1079, "paths": ["d009/d001/f059"], "variant": "ACD 1.20",
  "lines": [ {"n": 0, "jp": "...", "en_raw": "first-pass English", "en": ""} ] }
```

- `en_raw` is the machine first pass. **`en` is for the human pass**: the build uses `en` if non-empty, otherwise `en_raw`.
- Do not change `n`, `jp`, `paths`, or the number/order of lines.
- Choice prompts are a single line `Option A / Option B  continuation` (keep the ` / `).
- Rumor system messages are two-line and share their second line between files (`obtained!` / `solved!`), so line 1 carries the
  rumor name.
- Names: `translation/glossary/names.json`.

### Finding context for a line
- `python3 tools/context.py index` writes `translation/context/INDEX.tsv` (English only): per file, its **scene group** (archive directory;
  files in one group were authored together and play roughly in file order), position in the group, line count, how many
  choices, which glossary characters appear, and the first English line.
- `python3 tools/context.py view 1079` shows a file as JP / English with its previous and next file.
- `python3 tools/context.py book d008/d012` prints a whole scene group in order as Markdown, the easiest way to read a scene.
- **To find where a line is in the game:** `tools/build_idtest.py` / `tools/build_disc.py test` build discs in which every line
  displays its own ID (`[437-04]`: hex file number, line number; 0x437 = 1079). Play to the scene and read the IDs.
  We do **not** have a map from files to named in-game locations or days; the scene group is the best structural hint.

### Commands
```
python3 tools/tm.py fill                    # copy existing English onto identical Japanese lines (never overwrites)
python3 tools/check_script.py [N ...]       # ASCII, 256 px, completeness; exit 1 on problems
python3 tools/build_disc.py en build/ydt_en.bin
work/qc build/ydt_en.bin                    # sector QC (compile tools/disc_qc.c first)
python3 tools/fscheck.py build/ydt_en.bin "<original>.bin"
```
For batch work, `tools/batch.py export A B` prints untranslated lines as `FFFF:NN<TAB>Japanese` and `batch.py apply FILE` writes
`FFFF:NN<TAB>English` back (and to every identical Japanese line). `tools/seq.py` pairs a plain English list with export keys by
position and refuses a count mismatch.

## 9. Quality and limits

- **The Japanese was recovered by identifying glyph pictures, not decoded from text.** 3,391 unique tiles were clustered by
  ink mask into 2,354 groups (`tools/glyphtable.py`) and labelled by eye from contact sheets (first 1,280 by frequency, then
  context checks; corrections in `translation/tables/glyph_fixes.tsv`). The final script has no unidentified (`〓`) glyphs, but
  some are **best guesses**: kana look-alikes share labels (り/リ, か/カ/力, が/ガ, 一/ー, 口/ロ) and the 1,074 rarest kanji labels
  (`glyph_labels_1280_2353.txt`, all marked `?`) were never individually verified. A nonsensical kanji in a line is probably a
  mislabelled glyph; log it in `translation/notes/glyph-suspects.md` and fix the table.
- **The English is a literal first pass**, 87,028 lines all filled (27,217 unique Japanese lines). Expect stiff or
  over-literal phrasing, flat tone, lines that are fragments because the Japanese splits sentences across timed lines, and
  occasional misreadings from the glyph issue above. Names and places are provisional (see the glossary).
- Mid-sentence capitals on continuation lines are mostly intentional (new sentences, not continuations).
- Visible width is a conservative 256 px, so some lines are shorter-worded than they might need to be.

## 10. Reproducing from scratch

You need your own dump matching the CRC above. **No game data is in the public repository**, and neither is the Japanese script.

```
python3 tools/setup.py "<dump>.bin"       # verifies CRC, extracts, indexes, regenerates the Japanese script, imports translation/en
export YDT_DISC="<dump>.bin"
python3 tools/build_disc.py en build/ydt_en.bin
```
What `setup.py` does: `iso_extract.py` (ISO files to `extract/`), `flb.py tree` (leaf list), `mk_index.py` (file numbering by content
hash), `dump_script.py` (decode every scene's text with the glyph table), `en_import.py` (merge English by line number, refusing
lines whose Japanese hash differs). The glyph table is `translation/tables/glyph_hashes.tsv`: the md5 of each 128-byte glyph tile
mapped to a character, so it carries labels but no bitmaps. Tested from a clean checkout: the regenerated script and the built disc
image are **byte-identical** to the maintainer's.

Published: `translation/en/` (English plus a Japanese-line hash per line). Not published: `translation/script/` (the Japanese),
`extract/`, `work/`, `build/`, patches in the repo. Releases carry an xdelta patch against the verified dump (`docs/PATCHING.md`).

Requirements: Python 3, `numpy`, `pillow`; `gcc` for `disc_qc.c`. Fonts: DejaVu Sans / Sans Condensed / Sans Bold.
The maintainer-only step of rebuilding the hash table from clustered tiles (`glyphtable.py rebuild`) needs `work/glyphs/clusters.pkl`.

## 11. Testing log

Emulator: DuckStation (macOS). Hold keys about 0.3 s (taps are missed): arrows d-pad, L circle, K cross, I triangle, J square,
Return start, Tab fast-forward. Always use *System > Close Game Without Saving*.

- Test build A (IDs in place, nothing moved): text/font format confirmed.
- Test build B (everything resized, FLB +17.6 MB, XA/STR moved 8,594 sectors): opening movie, title, opening scene fine.
  Proves the game follows the FLB tables and ISO directory.
- Full English build: opening scene and subtitles, a walk through early town scenes (including the dog-tying sequence),
  pause menu, notebook (topics, all 44 rumor names, Settings with options and help text), button prompts, town map labels,
  title date, fiction disclaimer. Found and fixed: a clipped line (width limit), unreadable notebook ink (subtractive
  blending), vertical streaks in the disclaimer (texture copy).
- **Only part of the game has been played.** Not yet seen in-game: memory-card and save messages, save/purify prompts, HUD
  weekday glyphs, walk-start labels, the later chapters. Rare crashes or overflow in unvisited scenes cannot be ruled out; the
  static checks (width, ASCII, completeness, sector QC) pass for every file.

## 12. Open items

- Verify the unseen screens; translate staff credits and notebook date header if wanted; polish phrasing; verify the rare glyphs.
- Human translation pass over everything (the point of publishing the raw files).
- Another group (dothacktranslate) announced a human translation of this game; see `docs/PRIOR-WORK.md`.
- Release patch (xdelta) still to be generated and attached to a GitHub Release.
