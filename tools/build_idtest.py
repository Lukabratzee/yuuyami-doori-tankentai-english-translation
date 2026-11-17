#!/usr/bin/env python3
"""Build A: in-place 'ID build'. Every dialogue line is replaced (same length) by '<file idx>-<line no>' in a Latin font.
Nothing moves and no size changes, so this isolates one question: is the text/font format understood?
Usage: build_idtest.py <out.bin>   (out.bin must already be a copy of the original image)"""
import sys, struct, json, hashlib, collections
sys.path.insert(0, 'tools')
from acd import *; from latin_font import glyph; from discio import Disc
FLB_LBA = 254
disc = Disc(sys.argv[1]); index = {}; order = []; stats = collections.Counter()
f = open(FLB, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
for path, o, s, fid, mg in leaves('ACD'):
    d = m[o:o+s]
    a = has_text(d)
    if not a: continue
    tx = a.text()
    h = hashlib.md5(d).hexdigest()
    if h not in index: index[h] = {'idx': len(order), 'paths': []}; order.append(h)
    fi = index[h]['idx']; index[h]['paths'].append(path)
    # new strings, one per line, same number of characters as the original
    lines, cur = [], 0
    for g, b, c in tx:
        if g == 0xffff: lines.append(cur); cur = 0
        else: cur += 1
    if cur: lines.append(cur)
    strs = [('%03X-%02X' % (fi, ln)).ljust(k)[:k] for ln, k in enumerate(lines)]
    chars = sorted(set(''.join(strs)))
    M = a.nglyphs()
    if len(chars) > M: stats['skipped_small_font'] += 1; continue
    cmap = {ch: i for i, ch in enumerate(chars)}
    met = bytearray(a.sec(5)); font = bytearray()
    for ch, i in cmap.items():
        t, adv = glyph(ch); font += t; met[i*4+2] = 0; met[i*4+3] = adv
    txt = bytearray(a.sec(3)); it = iter(''.join(strs))
    for r in range(len(tx)):
        if tx[r][0] != 0xffff: struct.pack_into('<H', txt, r*4, cmap[next(it)])
    disc.write(FLB_LBA, o + a.offs[3], bytes(txt)); disc.write(FLB_LBA, o + a.offs[5], bytes(met)); disc.write(FLB_LBA, o + a.fontbase(), bytes(font))
    stats['patched_files'] += 1; stats['lines'] += len(lines)
stats['dirty_sectors'] = disc.finish()
json.dump({v['idx']: v['paths'] for v in index.values()}, open('work/acd_index.json', 'w'), indent=0)
print(dict(stats), 'unique', len(order))
