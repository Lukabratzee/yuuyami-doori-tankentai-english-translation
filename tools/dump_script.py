#!/usr/bin/env python3
"""Dump the Japanese script: translation/script/NNNN.json, one per unique text file (index from work/acd_index.json).
Each line: {"n": line no, "jp": text ('〓' = glyph not identified yet), "en_raw": "", "en": ""}.  Existing en/en_raw are kept."""
import sys, os, json, hashlib, mmap, collections
sys.path.insert(0, 'tools')
from acd import *; import glyphtable
t2c, unc, t2k = glyphtable.load()
index = json.load(open('work/acd_index.json')); p2i = {p: int(k) for k, v in index.items() for p in v}
os.makedirs('translation/script', exist_ok=True); st = collections.Counter(); seen = set(); uniq = set()
for path, o, d, a in acds():
    fi = p2i[path]
    if fi in seen: continue
    seen.add(fi); n = a.nglyphs(); tl = [a.tile(g) for g in range(n)]; out = 'translation/script/%04d.json' % fi
    old = {l['n']: l for l in json.load(open(out, encoding='utf8'))['lines']} if os.path.exists(out) else {}
    lines = []
    for i, (crs, term) in enumerate(split_lines(a.text())):
        jp = ''.join(t2c.get(tl[g], '〓') if g < n else '〓' for g, _, _ in crs)
        e = {'n': i, 'jp': jp, 'en_raw': old.get(i, {}).get('en_raw', ''), 'en': old.get(i, {}).get('en', '')}
        lines.append(e); st['lines'] += 1; st['chars'] += len(jp); st['unknown'] += jp.count('〓'); st['empty'] += not jp; uniq.add(jp)
    json.dump({'file': fi, 'paths': index[str(fi)], 'variant': a.magic.decode('latin1').replace('\x00', '0'), 'lines': lines},
              open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
st['files'] = len(seen); st['unique_lines'] = len(uniq); print(dict(st))
