#!/usr/bin/env python3
"""Context helper for translators.
  context.py index            -> translation/context/INDEX.tsv  (one row per script file: where it lives, who/what is in it; English only, publishable)
  context.py view N [N ...]   -> reading view of script file(s): JP | raw EN | final EN, with neighbours listed
  context.py book GROUP       -> whole scene group in order (GROUP like d008/d012; see INDEX.tsv column 'group'),
                                 as Markdown on stdout: the best way to read a scene start to finish
Scene groups: files that live in the same archive directory were authored together (one event, one day segment or one
area), and the game plays them in roughly file order, so neighbours give the surrounding conversation."""
import sys, json, glob, os, collections
S = 'translation/script'
def load(n): return json.load(open('%s/%04d.json' % (S, n), encoding='utf8'))
def group(d): return '/'.join(d['paths'][0].split('/')[:-1])
def allfiles(): return [json.load(open(f, encoding='utf8')) for f in sorted(glob.glob(S + '/*.json'))]
names = [(g['jp'].split(' / ')[0], g['en']) for g in json.load(open('translation/glossary/names.json'))]
def who(d):
    t = '\n'.join(l['jp'] for l in d['lines']); return [e for j, e in names if len(j) > 1 and j in t]
def kind(l):
    if ' / ' in l['jp'] or '　／　' in l['jp']: return 'choice'
    return ''
if sys.argv[1] == 'index':
    fs = allfiles(); g = collections.defaultdict(list)
    for d in fs: g[group(d)].append(d['file'])
    os.makedirs('translation/context', exist_ok=True)
    with open('translation/context/INDEX.tsv', 'w', encoding='utf8') as o:
        o.write('file\tgroup\tpos_in_group\tgroup_size\tlines\tchoices\tnames\tother_paths\tfirst_en\n')
        for d in fs:
            ls = [l for l in d['lines'] if l['jp'].strip()]
            first = ls[0] if ls else {'jp': '', 'en_raw': ''}; m = g[group(d)]
            o.write('\t'.join([str(d['file']), group(d), str(m.index(d['file']) + 1), str(len(m)), str(len(d['lines'])),
                str(sum(kind(l) == 'choice' for l in ls)), ','.join(who(d)), ';'.join(d['paths'][1:]),
                (first.get('en') or first.get('en_raw', ''))[:40]]) + '\n')
    print('wrote translation/context/INDEX.tsv', len(fs), 'files,', len(g), 'groups')
elif sys.argv[1] == 'view':
    for a in sys.argv[2:]:
        d = load(int(a)); m = [x for x in glob.glob(S + '/*.json')]
        gp = group(d); sib = sorted(int(os.path.basename(f)[:4]) for f in m if group(json.load(open(f))) == gp)
        i = sib.index(d['file'])
        print('=== file %04d  %s  (%s)  group %s: %d of %d, previous %s, next %s' % (d['file'], ', '.join(d['paths']), d['variant'],
              gp, i + 1, len(sib), sib[i-1] if i else '-', sib[i+1] if i + 1 < len(sib) else '-'))
        print('names in this file:', ', '.join(who(d)) or '-')
        for l in d['lines']:
            if l['jp'].strip(): print('%3d  %s\n     %s%s' % (l['n'], l['jp'], l.get('en_raw', ''), '' if not l.get('en') else '\n  >> ' + l['en']))
else:
    gp = sys.argv[2]; fs = [d for d in allfiles() if group(d) == gp]
    print('# Scene group %s (%d files)\n' % (gp, len(fs)))
    for d in fs:
        print('## file %04d (%s)  names: %s\n' % (d['file'], ', '.join(d['paths']), ', '.join(who(d)) or '-'))
        for l in d['lines']:
            if l['jp'].strip(): print('- %s  \n  **%s**' % (l['jp'], l.get('en') or l.get('en_raw', '')))
        print()
