#!/usr/bin/env python3
"""Batch helper for the translation pass.
  batch.py export A B        print untranslated lines of files A..B (first occurrence of each unique jp line only),
                             format  FFFF:NN<TAB>japanese
  batch.py apply FILE        read  FFFF:NN<TAB>english  lines, write them to en_raw (and to every identical jp line
                             in the whole script via translation memory), then report width problems
"""
import json, sys, glob, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def path(n): return os.path.join(ROOT, 'translation/script/%04d.json' % n)
def load(n): return json.load(open(path(n)))
def save(n, d): json.dump(d, open(path(n), 'w'), ensure_ascii=False, indent=1)
def export(a, b):
    seen = set()
    for n in range(a, b + 1):
        if not os.path.exists(path(n)): continue
        d = load(n); out = []
        for l in d['lines']:
            if l['jp'].strip() and not l.get('en_raw') and l['jp'] not in seen:
                seen.add(l['jp']); out.append('%04d:%02d\t%s' % (n, l['n'], l['jp']))
        if out: print('# file %04d' % n); print('\n'.join(out))
def apply(fn):
    got = {}
    for ln in open(fn, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln or ln.startswith('#'): continue
        k, _, en = ln.partition('\t')
        got[k] = en
    bad = [k for k, v in got.items() if not v.strip()]
    files = {}
    for k, en in got.items():
        n, i = k.split(':'); files.setdefault(int(n), {})[int(i)] = en
    jpmap = {}
    for n, m in files.items():
        d = load(n)
        for l in d['lines']:
            if l['n'] in m:
                l['en_raw'] = m[l['n']]; jpmap[l['jp']] = m[l['n']]
        save(n, d)
    print('applied', len(got), 'lines to', len(files), 'files; empty:', bad)
    return jpmap
if __name__ == '__main__':
    if sys.argv[1] == 'export': export(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == 'apply': apply(sys.argv[2])
