#!/usr/bin/env python3
"""Translation memory.  tm.py fill  -> copy en_raw/en between lines whose Japanese is identical (never overwrites).
                        tm.py stats -> progress numbers."""
import sys, json, glob, collections
files = sorted(glob.glob('translation/script/*.json')); data = {f: json.load(open(f, encoding='utf8')) for f in files}
tm = {}
for d in data.values():
    for l in d['lines']:
        if l['jp'] and l.get('en_raw') and l['jp'] not in tm: tm[l['jp']] = l['en_raw']
if sys.argv[1] == 'fill':
    n = 0
    for f, d in data.items():
        ch = False
        for l in d['lines']:
            if l['jp'] and not l.get('en_raw') and l['jp'] in tm: l['en_raw'] = tm[l['jp']]; n += 1; ch = True
        if ch: json.dump(d, open(f, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('filled', n, 'lines from', len(tm), 'known translations')
else:
    tot = sum(1 for d in data.values() for l in d['lines'] if l['jp']); done = sum(1 for d in data.values() for l in d['lines'] if l['jp'] and l.get('en_raw'))
    uniq = len({l['jp'] for d in data.values() for l in d['lines'] if l['jp']})
    print('lines %d/%d, unique Japanese lines %d, translated unique %d' % (done, tot, uniq, len(tm)))
