#!/bin/sh
# Make a release patch from the original dump and your English build:  tools/make_patch.sh "<original>.bin" build/ydt_en.bin
# Needs xdelta3 (brew install xdelta / apt install xdelta3).  Output: patches/YDT-EN-<date>.xdelta  (never commit it; attach it to a GitHub Release)
set -e
[ $# -eq 2 ] || { echo "usage: $0 original.bin english.bin"; exit 2; }
command -v xdelta3 >/dev/null || { echo "xdelta3 not found"; exit 1; }
dir="$(cd "$(dirname "$0")/.." && pwd)/patches"; mkdir -p "$dir"; out="$dir/YDT-EN-$(date +%Y%m%d).xdelta"
echo "encoding (a few minutes; output appears at the end) -> $out"
# big source window because the archive grows and everything after it shifts by whole sectors
xdelta3 -e -9 -B 1073741824 -s "$1" "$2" "$out"
xdelta3 -d -s "$1" "$out" "${TMPDIR:-/tmp}/ydt_verify.bin" && cmp "${TMPDIR:-/tmp}/ydt_verify.bin" "$2" && echo "patch verified: $out ($(du -h "$out" | cut -f1))"
rm -f "${TMPDIR:-/tmp}/ydt_verify.bin"
echo "target CRC32 (give this in the release notes):"; python3 - "$2" <<'P'
import sys, zlib
c = 0
with open(sys.argv[1], 'rb') as f:
    for b in iter(lambda: f.read(1 << 24), b''): c = zlib.crc32(b, c)
print('%08x' % c)
P
