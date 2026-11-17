# Findings: where the text lives (2026-11-15)

Status: **text format located and proven by rendering** (see `work/samples/f281_text.png`). Glyph-to-character mapping not done yet.

## Disc
- `disc` = `../Yuuyami Doori Tankentai (Japan)/*.bin` — SHA-1 `a6025151bddbf2c48157f0f5b91a27e03301a6f9`, CRC32 `9d2b1afe` (matches the CRC listed for the Japan release).
- Files: `SLPS_022.74` (468,992 B, SHA-1 `1b2eee02e9ae542620be83a142532dc39c468886`, load 0x80010000, entry 0x8001210C), `SYSTEM.CNF`,
  `DATA/FILELINK.FLB` (556,816,800 B, LBA 254), `DATA/XALINK.XA`, `DATA/OPEN.STR`, `DATA/ROGO.STR`.
- EXE library strings date PsyQ libs to 1997–98 (`sys.c 1.140 1998/01/12`) → likely PsyQ 4.x; exact compiler still to identify.

## FILELINK.FLB — directory tree, not flat archives
See `tools/flb.py` docstring for the header. An FLB is a directory: entries are files or sub-directories (each a nested FLB).
`flb.py tree` yields **15,735 leaves**. Leaf types by magic:

| magic | count | guess |
|---|---|---|
| `EVD 1.02` | 5517 | event/script data |
| `ACD 1.20` / `ACD  1.10` / `ACD  1.20` | 3555 / 1857 / 116 | **scene data incl. dialogue text + font** |
| `SEL` | 1125 | ? |
| `pBAV` | 1120 | VAB sound banks |
| `QVD 1.00` | 541 | ? |
| `EAS 1.00` | 348 | ? |
| `LSD` | 199 | ? |
| TIM | 161 | graphics |
| `PFD`, `XAL`, raw | few | |

## Why Shift-JIS searches found nothing
Dialogue is **not character-encoded at all**. Each `ACD 1.20` file carries its own 16x16 4bpp anti-aliased glyph tiles
(hand-written style font) and the text is a list of **indices into that file's own tile set**. The game copies the tiles
to RAM (seen at 0x8015F54C in `ram_dump1.bin`) and uploads the glyphs it needs to a VRAM cache at (832,0).

## ACD 1.20 layout (from `d007/d000/f281`, 123,380 B)
```
00  'ACD\0' '1.20'
08  u32 ?(0x1e1f4)   0C u32 0x50 (header size)
10  u32 sec_off[10]
38  u16 count[12]
```
| sec | record | count field | meaning (so far) |
|---|---|---|---|
| 0 | 8 B | count[1] | ? |
| 1 | 8 B | count[2] | ? (animation frames/positions?) |
| 2 | 4 B (u16 0, u16 n) | count[3] | ? per-line value |
| **3** | **4 B: u16 glyph, u8 ?, u8 flag** | count[4] | **dialogue text**. `glyph=0xFFFF` ends a line. flag `02` on normal chars, `00` on last char of a line |
| 5 | 4 B | count[6] | ? |
| 7 | 12 B (u32 off, u16, u16, u32) | | image table |
| 8 | 8 B | count[9] | palette refs? |
| **9** | | count[8] = glyph count? | 32-byte 16-colour CLUT (grey ramp) then 128-byte glyph tiles (low nibble = left pixel, 0xF = background), then other graphics |

Glyph tile `g` = `sec_off[9] + 0x20 + g*128`. Tile order starts with kana in a fixed order, then the kanji that file uses.

## Scale (unique ACD 1.20 files only)
1,250 unique files, 1,135 with text; **~79,000 lines / ~793,000 text records**.
Counting `count[8]` tiles per file gives 40,843 distinct tiles — far too many for distinct characters, so either count[8] is
not purely the glyph count or the same character has many drawn variants. **Open question #1.**

## Open questions / next steps
1. Glyph identity: dedupe tiles (exact, then fuzzy), label each unique glyph once (vision/OCR), build per-file index→character tables → real Japanese text.
2. Meaning of text record bytes 2–3, section 2, and how EVD scripts reference lines (speaker, choices).
3. ACD 1.10 layout; where menu/UI text lives (EXE overlays in d000?).
4. For English: replace each file's tile set with Latin glyphs and re-index. 16-px cells → want half-width or VWF (renderer in EXE; decomp target).

---
# Update 2026-11-15 (evening): format corrections, rebuild pipeline, two test builds

## Corrections to the ACD 1.20 notes above
- **Glyph count is `count[6]`**, not count[8]. Font start = `sec_off[9] + u32 at sec4[0]` (0x20 or 0x40, not always 0x20).
- **sec 5 = per-glyph metrics**, 4 B each: `u16 font group, u8 x offset, u8 advance width` → the game already draws
  proportional text. No variable-width hack should be needed for English.
- A file's font can hold several groups, each sorted kana-then-kanji, so one character may appear more than once.
- **0x50: sequence table**, `count[0]` x 16 B: `u16 sec0 start, u16 n, u16 sec2 start, u16 n, u16 text start, u16 text count,
  u16 duration, u16 has_text`. Text is referenced from here by record index. A range can start or end mid-line (~0.4%: a
  line revealed in two steps).
- Text record byte 3 = delay in frames after the character (2 normal); on the `FFFF` terminator it is the hold time.
  Sequence duration = sum of byte 3 over its range, so line timing is fixed by the data, not by the player.
- FLB: group table `size` excludes the child's own header; header +0x1C = data size; +0x20 = DOS date/time (1999-08-30).
- Real totals: 3,285 unique glyph tiles, 20,828 unique lines (89,665 line instances in 1,216 files; 1,135 unique files).

## Tools added
| tool | does |
|---|---|
| `tools/acd.py` | parse ACD; `rebuild(d, lines, glyph)` re-encodes text with a new font, re-points the sequence table, keeps durations |
| `tools/latin_font.py` | Latin glyph tiles (DejaVu Sans 11) in game format + advance widths |
| `tools/flb_rebuild.py` | rebuild FILELINK.FLB with resized leaves. **Gate: empty replacement set → byte-identical FLB (passes)** |
| `tools/isobuild.py`, `psx_sector.py`, `discio.py` | write the image, move XA/STR, patch directory + PVD, regenerate EDC/ECC (checked against original sectors) |
| `tools/build_idtest.py` | Build A |
| `tools/build_disc.py test|en` | Build B / real English build from `translation/script/NNNN.json` |

## Test builds (in `build/`) — NOT yet run in an emulator
- **A `ydt_idtest`**: nothing moves, same sizes. Each line shows `FFF-LL` (file index from `work/acd_index.json`, line no.).
  Answers: is the text/font format right?
- **B `ydt_testB`**: every line becomes `[FFF-LL] The quick brown fox jumps.`; FLB grows 9.9 MB, XA/STR move 4,839 sectors.
  Answers: does the game follow the FLB tables and file system when things move? Does long text fit/wrap? Does a font
  appended to the end of a file work (154 files with small fonts use that path)?

## Still open
- Glyph → character table (3,285 tiles). Tesseract is useless on this hand-drawn font; plan is to transcribe a 1,341-line
  covering set by eye (`work/glyphs/lines.pkl`) and derive the table by alignment.
- ACD 1.10 files, menu/UI text, EVD scripts, speaker names.

---
# Update 2026-11-15 18:40 — emulator tests (DuckStation, macOS), both builds PASS on the opening scene

- **Three ACD variants carry text**, not one (see `tools/acd.py` docstring): `ACD\0 1.20`, `ACD  1.20` (text-only; the
  opening scene uses these) and a few `ACD  1.10`. First test showed Japanese because only the first was patched.
  Totals now: 1,234 unique text files (3,169 instances), 3,391 unique glyph tiles, 27,857 unique lines.
- **Palette direction**: index 15 = transparent, 14 = white, low = dark. First test font was inverted (hollow dotted letters).
  `latin_font.py` fixed: ink high, 1px dark fringe.
- **Build A** (`ydt_idtest`, in place): opening scene shows `427-06`, `427-07`… → text + font format confirmed.
- **Build B** (`ydt_testB`, +17.6 MB FLB, XA/STR moved 8,594 sectors, 2,008 files with font appended): opening movie plays,
  title menu works, opening scene shows `[437-04] The quick brown fox jumps.` centred, crisp, proportional, timing normal.
  → the game follows the FLB tables and the ISO directory; resizing text and appending fonts is safe. No EXE patch needed
  for dialogue. Only the first ~1 minute of a new game was watched; nothing else is verified yet.
- **Still Japanese**: title menu ("start from beginning", save date), memory-card messages, the pink hint text seen while
  walking around school (source not located — not in an ACD text section, or was already in RAM from the old save state).
- DuckStation notes: default keys work with a ~0.3 s hold (taps are missed): arrows = d-pad, L = circle, Return = start,
  Tab = fast-forward. Always use *System → Close Game Without Saving* so the Dec-2025 resume state is kept. The emulator
  showed a "saved memory card" toast on reset; no in-game save was made.

---
# Update 2026-11-15 19:10 — Japanese script dumped; first real English line shown in-game

- **Glyph table**: tiles clustered by ink mask (2,354 clusters, `work/glyphs/clusters.pkl`), ordered by frequency. The first
  1,280 clusters are labelled (`translation/tables/glyph_labels_0000_1279.txt`, read from contact sheets in
  `work/glyphs/sheets2/`), then every doubtful one was checked against decoded lines; corrections in
  `translation/tables/glyph_fixes.tsv`. Coverage: 99.3% of characters; 2,198 characters (in ~1,440 unique lines) still
  show as `〓`. Clusters 1280–2353 (sheets c08–c14) are unlabelled rare kanji/variants.
- Known weakness: kana look-alikes (り/リ, か/カ/力, が/ガ, 一/ー, ０/Ｏ…) and same-shape variants share a label. Good enough to
  read and translate; not a clean transcription.
- **Script**: `tools/dump_script.py` → `translation/script/NNNN.json` (1,234 files, 87,028 non-empty lines, 27,287 unique).
  Re-running it keeps existing `en_raw`/`en`.
- **Translation tooling**: `tools/tm.py` (translation memory), `tools/check_script.py` (ASCII + 296 px width),
  `docs/TRANSLATOR-HANDOFF.md` (instructions for the bulk pass), `translation/glossary/names.json` (seed, provisional).
- **Translated so far**: files 437, 1063, 1079 by hand (205 lines); translation memory then filled 29,799 repeated lines
  (mostly "..." and stock replies). 46 files complete → built into `build/ydt_en.bin`.
- **Tested**: `ydt_en` boots; the opening scene (file 1079) plays in English with correct timing. Test-build IDs are hex:
  `[437-04]` on screen = file 0x437 = 1079.
- Line width budget measured: 44 average characters ≈ 261 px; limit set to 296 px.
