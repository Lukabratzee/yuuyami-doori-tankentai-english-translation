#!/usr/bin/env python3
"""Build a patched disc image.  Usage: build_disc.py test|en <out.bin>
 test: every line becomes '[FFF-LL] The quick brown fox jumps.' (resized text, rebuilt FLB, moved XA/STR)
 en:   lines come from translation/script/<idx>.json ('en' or 'en_raw'); untranslated files are left untouched"""
import sys, os, json, hashlib, mmap, time, collections
sys.path.insert(0, 'tools')
from acd import *; from latin_font import glyph; import flb_rebuild, isobuild
ORIG = os.environ.get('YDT_DISC', '../Yuuyami Doori Tankentai (Japan)/Yuuyami Doori Tankentai (Japan).bin')   # your dump (set YDT_DISC)
mode, outp = sys.argv[1], sys.argv[2]
f = open(FLB, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
index = {p: int(k) for k, v in json.load(open('work/acd_index.json')).items() for p in v}; byhash = {}; repl = {}; st = collections.Counter()
t = time.time()
for path, o, s, fid, mg in leaves('ACD'):
    d = m[o:o+s]
    a = has_text(d)
    if not a: continue
    tx = a.text()
    h = hashlib.md5(d).hexdigest()
    if h not in byhash:
        fi = index.get(path); L = split_lines(tx); new = None
        if mode == 'test': new = [('[%03X-%02X] The quick brown fox jumps.' % (fi, i)) if crs else '' for i, (crs, _) in enumerate(L)]
        else:
            p = 'translation/script/%04d.json' % fi
            if os.path.exists(p):
                e = json.load(open(p))['lines']; new = [(x.get('en') or x.get('en_raw') or '') for x in e]
                if len(new) != len(L) or not all(new[i] or not L[i][0] for i in range(len(L))): new = None; st['incomplete'] += 1
        byhash[h] = rebuild(d, new, glyph) if new else None
    if byhash[h]: repl[o] = byhash[h][0]; st['files'] += 1; st['appended_font'] += byhash[h][1]
if mode == 'en' and os.path.exists('translation/ui/eas_text.json'):      # UI images: same-size, in-place redraw
    import eas
    ui = json.load(open('translation/ui/eas_text.json'))
    for path, o, s, fid, mg in leaves('EAS'):
        if path in ui: repl[o] = eas.patch(m[o:o+s], ui[path]); st['ui_images'] += len(ui[path])
print(dict(st), 'rebuilt ACDs in %.0fs' % (time.time() - t)); t = time.time()
n = flb_rebuild.rebuild_to_file(m, repl, 'build/FILELINK.FLB'); print('new FLB', n, 'was', len(m), '%.0fs' % (time.time() - t)); t = time.time()
size, delta = isobuild.build(ORIG, 'build/FILELINK.FLB', outp); print('image written, sector delta', delta, '%.0fs' % (time.time() - t))
open(outp[:-4] + '.cue', 'w').write('FILE "%s" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n' % os.path.basename(outp))
