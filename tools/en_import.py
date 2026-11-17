#!/usr/bin/env python3
"""translation/en/NNNN.json  ->  translation/script/NNNN.json  (fills en_raw / en, matched by line number n).
A line whose Japanese hash differs from the one the English was written against is NOT applied and is reported
(your glyph table or disc differs); use --force to apply anyway.   Usage: en_import.py [--force]"""
import json, glob, sys, hashlib
force = '--force' in sys.argv; bad = applied = 0
for f in sorted(glob.glob('translation/en/*.json')):
    e = json.load(open(f, encoding='utf8')); p = 'translation/script/%04d.json' % e['file']
    d = json.load(open(p, encoding='utf8')); by = {l['n']: l for l in d['lines']}
    for x in e['lines']:
        l = by.get(x['n'])
        if l is None or (hashlib.md5(l['jp'].encode('utf8')).hexdigest()[:8] != x['h'] and not force):
            bad += 1
            if bad <= 20: print('MISMATCH file %04d line %d: Japanese differs from the one translated' % (e['file'], x['n']))
            continue
        l['en_raw'] = x['en_raw']; l['en'] = x.get('en', ''); applied += 1
    json.dump(d, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('applied', applied, 'lines;', bad, 'mismatches')
sys.exit(1 if bad else 0)
