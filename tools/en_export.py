#!/usr/bin/env python3
"""translation/script/*.json (local, contains Japanese)  ->  translation/en/NNNN.json (English only, safe to publish).
Each line keeps its number n and h = first 8 hex digits of md5(Japanese line), so a later import can tell whether the
Japanese it was written against is still the same line.  Blank-Japanese lines are omitted."""
import json, glob, os, hashlib
os.makedirs('translation/en', exist_ok=True); n = 0
for f in sorted(glob.glob('translation/script/*.json')):
    d = json.load(open(f, encoding='utf8'))
    out = {'file': d['file'], 'paths': d['paths'], 'lines': [
        {'n': l['n'], 'h': hashlib.md5(l['jp'].encode('utf8')).hexdigest()[:8], 'en_raw': l.get('en_raw', ''), **({'en': l['en']} if l.get('en') else {})}
        for l in d['lines'] if l['jp'].strip() or l.get('en_raw')]}
    json.dump(out, open('translation/en/%04d.json' % d['file'], 'w', encoding='utf8'), ensure_ascii=False, indent=0); n += len(out['lines'])
print('exported', n, 'lines to translation/en/')
