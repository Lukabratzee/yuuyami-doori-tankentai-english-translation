# Applying and making patches

## Players
You need the reference dump: Japan release, MODE2/2352 `.bin` (307,677 sectors of 2,352 bytes = 723,656,304 bytes), **CRC32 `9d2b1afe`**,
SHA-1 `a6025151bddbf2c48157f0f5b91a27e03301a6f9`. (Check with `crc32`, 7-Zip, or `python3 tools/setup.py` which verifies it.)

```
xdelta3 -d -s "Yuuyami Doori Tankentai (Japan).bin" YDT-EN-YYYYMMDD.xdelta ydt_en.bin
```
GUI tools that apply xdelta patches (xdelta UI, Delta Patcher) work too. Copy the original `.cue`, edit its `FILE` line to
the new `.bin` name. The patched image should have CRC32 as stated in the release notes. Wrong CRC = wrong source dump or a
corrupted patch.

## Building it yourself (no patch needed)
```
python3 tools/setup.py "<your dump>.bin"                 # once: extracts, indexes, regenerates the Japanese script, imports translation/en
export YDT_DISC="<your dump>.bin"
python3 tools/check_script.py
python3 tools/build_disc.py en build/ydt_en.bin          # about a minute
```
This produces exactly the same disc image as the release patch for the same `translation/en` (verified byte-for-byte).

## Maintainers: making a release patch
```
tools/make_patch.sh "<original>.bin" build/ydt_en.bin    # needs xdelta3; verifies by re-applying; prints the target CRC32
```
Attach `patches/*.xdelta` to a GitHub Release, never to the repo. Put the source CRC32, target CRC32 and the commit
hash in the release notes and mark it "machine-translated first pass". Do not publish the `.bin`.
