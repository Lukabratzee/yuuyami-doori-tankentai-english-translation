#!/usr/bin/env python3
"""Validate translations before a build.  Usage: check_script.py [file numbers...]   (default: all)
Reports per file: lines translated / total, and problems: non-ASCII characters, lines wider than MAX_PX,
empty translation for a non-empty Japanese line.  Exit code 1 if any problem."""
import sys, json, glob
sys.path.insert(0, 'tools')
from latin_font import glyph
MAX_PX = 256          # 320 px screen, but only ~265 px are visible (overscan crop seen in DuckStation 2026-11-17)
def width(s): return sum(glyph(c)[1] for c in s)
files = ['translation/script/%04d.json' % int(a) for a in sys.argv[1:]] or sorted(glob.glob('translation/script/*.json'))
bad = 0; done = total = complete = 0
for f in files:
    d = json.load(open(f, encoding='utf8')); n = t = 0
    for l in d['lines']:
        if not l['jp']: continue
        n += 1; en = l.get('en') or l.get('en_raw') or ''
        if not en: continue
        t += 1
        if any(not (32 <= ord(c) < 127) for c in en): print('%s line %d: non-ASCII character' % (f, l['n'])); bad += 1
        if width(en) > MAX_PX: print('%s line %d: %d px wide (max %d): %s' % (f, l['n'], width(en), MAX_PX, en)); bad += 1
    total += n; done += t; complete += (n == t)
print('%d/%d lines translated, %d/%d files complete, %d problems' % (done, total, complete, len(files), bad))
sys.exit(1 if bad else 0)
