# Contributing

You can help by translating, testing, or fixing tools. You need your own copy of the game (Japan, CRC32 `9d2b1afe`), Python 3
with `numpy` and `pillow`, and an emulator (DuckStation works well). Nobody needs to read Japanese to test.

## 1. Set up (once)
```
git clone <this repo> && cd <repo>
python3 tools/setup.py "/path/to/Yuuyami Doori Tankentai (Japan).bin"
export YDT_DISC="/path/to/Yuuyami Doori Tankentai (Japan).bin"
```
`setup.py` verifies your dump, extracts it into `extract/` (git-ignored), regenerates the Japanese script into
`translation/script/` (git-ignored; **never commit it**) and imports `translation/en/` into it. If it reports
`MISMATCH` lines, your Japanese differs from the one the English was written against (see "Mismatches").

## 2. Translate
The translation lives in `translation/en/NNNN.json`:
```json
{"file": 1079, "paths": ["d009/d001/f059"], "lines": [{"n": 4, "h": "1a2b3c4d", "en_raw": "first-pass English", "en": "your edit"}]}
```
- Edit **`en`** (human pass). If `en` is present and non-empty the build uses it, otherwise `en_raw`. Never change `n` or `h`.
- To read the Japanese beside the English, work in your local `translation/script/NNNN.json` (same line numbers) or use
  `python3 tools/context.py view NNNN` and `python3 tools/context.py book d008/d012` (a whole scene group in order).
- After editing a local script file, run `python3 tools/en_export.py` to write your changes back to `translation/en/`
  (this rewrites every file; `git diff` shows only what you changed). Or edit `translation/en/` directly and run
  `python3 tools/en_import.py` to sync your local script.
- Find who/where: `translation/context/INDEX.tsv` gives the **scene group** (the archive directory; scenes in one group were
  authored together and play roughly in file order), the characters in each file, and the first line.

### Hard constraints (the build and `tools/check_script.py` enforce them)
1. **One English line per Japanese line, same order.** Lines are timed by the data; you cannot add or remove lines. If a
   Japanese sentence is split over two lines, split the English across the same two lines (fragments are fine).
2. **At most 256 px wide** (about 40-44 characters). The screen is 320 px but ~265 px are visible. Narrow letters fit more.
3. **Printable ASCII only**: no curly quotes, em dashes, accents; use `...`, `-`, `'`, `"`.
4. A file is built in only if every non-empty line has English.
5. Choice prompts are one line: `Option A / Option B  continuation` (keep the ` / `).
6. Rumor system messages are two-line and share their second line between files (`obtained!` / `solved!`), so line 1 carries the
   rumor name. Messages are matched by exact Japanese, so identical Japanese lines should usually get identical English
   (`python3 tools/tm.py fill` copies English onto identical Japanese lines; it never overwrites).

### Style
Natural, plain English for what the Japanese says; late-1990s junior-high kids, short casual lines, contractions. No embellishment.
Names/places: `translation/glossary/names.json` (provisional; propose changes in a PR, then replace consistently). US spelling.
Keep `...` `!` `?` roughly as in the source.

### Mismatches and wrong kanji
The Japanese was recovered by recognising glyph pictures, so some characters are wrong (look-alike kana, rare kanji). If a
Japanese line makes no sense, the glyph is probably mislabelled: open an Issue with the file/line and what you think it should
be. Maintainers fix `translation/tables/glyph_fixes.tsv`; fixing a glyph changes the Japanese hash `h` of affected lines, which
is why `en_import.py` refuses to apply English to a changed line unless you pass `--force`.

## 3. Build and test
```
python3 tools/check_script.py                  # ASCII, width, completeness
python3 tools/build_disc.py en build/ydt_en.bin
```
Boot `build/ydt_en.bin` (original `.cue` renamed). Always close the emulator without saving states over your own saves.

### Finding a line in the game
`python3 tools/build_disc.py test build/ydt_ids.bin` builds a disc where every line shows `[FFF-LL]`: **hex** file number and
line number (`[437-04]` = file 0x437 = 1079, line 4). Play to the scene, read the IDs, then edit that file.

### Menu and map graphics
Menu text is drawn into pictures. They are defined in `tools/mk_ui.py` (text, style, which image) and drawn by `tools/eas.py`.
Run `python3 tools/mk_ui.py` after editing, then rebuild. `tools/eas_sheet.py <leaf> out.png A-B` renders a contact sheet
so you can see which images exist. Everything is redrawn at the original pixel size.

## 4. Pull request
- Commit only `translation/en/`, `translation/ui/`, glossary, tables, tools or docs. **Never** commit the disc, `extract/`,
  `work/`, `build/`, `translation/script/` (Japanese) or patches/screenshots that show the game's copyrighted material beyond
  what is needed for a bug report.
- Say which files/scenes you covered and whether you tested them in-game.
- Large rewrites of a scene are fine; keep unrelated changes out of the same PR.

## Quality-check checklist for a scene
- Reads naturally aloud? Consistent names? Jokes/wordplay explained or adapted?
- Fits 256 px (`check_script.py`)? Choice lines keep ` / `?
- Played in the emulator at least once, text not clipped or overlapping?
