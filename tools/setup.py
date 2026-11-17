#!/usr/bin/env python3
"""One-time setup from YOUR OWN disc dump.   Usage: python3 tools/setup.py "<path to your .bin>"
 1. checks size + CRC32 of the dump (Japan release, CRC32 9d2b1afe)
 2. extracts the ISO files to extract/            (git-ignored; never commit or share)
 3. indexes the archive -> work/flb_tree.txt, work/acd_index.json
 4. dumps the Japanese script to translation/script/NNNN.json from the dump's own glyphs (glyph table: translation/tables/glyph_hashes.tsv)
 5. imports the English in translation/en/ into those files (en_import.py)
Afterwards:  export YDT_DISC="<your .bin>"; python3 tools/build_disc.py en build/ydt_en.bin"""
import sys, os, zlib, subprocess
CRC, SIZE = 0x9d2b1afe, 307677 * 2352
if len(sys.argv) != 2: sys.exit(__doc__)
bin_ = sys.argv[1]
if os.path.getsize(bin_) != SIZE: sys.exit('size %d != expected %d: this is not the MODE2/2352 Japan dump (SLPS-02274)' % (os.path.getsize(bin_), SIZE))
c = 0
with open(bin_, 'rb') as f:
    while True:
        b = f.read(1 << 24)
        if not b: break
        c = zlib.crc32(b, c)
if c != CRC: sys.exit('CRC32 %08x != %08x: not the reference dump (redump Japan, SLPS-02274)' % (c, CRC))
print('dump OK (CRC32 %08x)' % c)
def run(*a, out=None):
    print('+', ' '.join(a)); r = subprocess.run([sys.executable] + list(a), stdout=open(out, 'w') if out else None)
    if r.returncode: sys.exit('failed: ' + ' '.join(a))
for d in ('extract', 'work', 'build'): os.makedirs(d, exist_ok=True)
run('tools/iso_extract.py', bin_, 'extract')
run('tools/flb.py', 'tree', 'extract/DATA/FILELINK.FLB', out='work/flb_tree.txt')
run('tools/mk_index.py')
run('tools/dump_script.py')
run('tools/en_import.py')
print('\nDone. Build with:  YDT_DISC="%s" python3 tools/build_disc.py en build/ydt_en.bin' % bin_)
