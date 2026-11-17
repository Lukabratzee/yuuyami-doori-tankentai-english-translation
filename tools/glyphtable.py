"""Glyph tile -> character table, keyed by a hash of the tile bitmap so no game data is needed to ship it.
translation/tables/glyph_hashes.tsv:  md5[:16] of the 128-byte tile <TAB> cluster index <TAB> character
(clusters = tiles with the same ink mask; labels were read by eye from contact sheets, corrections in glyph_fixes.tsv;
glyph_labels_*.txt / glyph_fixes.tsv remain the human-editable source, `glyphtable.py rebuild` regenerates the tsv from them
when work/glyphs/clusters.pkl exists, i.e. only on the maintainer's machine).
load() -> (tile2char, uncertain set, tile2cluster); the dicts accept raw 128-byte tiles."""
import hashlib, os, sys
H = lambda t: hashlib.md5(t).hexdigest()[:16]
class TileMap(dict):
    def get(s, t, default=None): return dict.get(s, H(t), default)
    def __getitem__(s, t): return dict.__getitem__(s, H(t))
    def __contains__(s, t): return dict.__contains__(s, H(t))
def load():
    t2c, t2k = TileMap(), TileMap()
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'translation/tables/glyph_hashes.tsv'), encoding='utf8'):
        if line.startswith('#') or not line.strip(): continue
        h, k, lab = (line.rstrip('\n').split('\t') + [''])[:3]
        dict.__setitem__(t2k, h, int(k))
        if lab: dict.__setitem__(t2c, h, lab)
    return t2c, set(), t2k
def rebuild():
    import pickle, glob
    c = pickle.load(open('work/glyphs/clusters.pkl', 'rb')); labels = []
    for f in sorted(glob.glob('translation/tables/glyph_labels_*.txt')):
        for line in open(f, encoding='utf8'): labels += [x for x in line.rstrip('\n').split(' ') if x != '']
    for line in open('translation/tables/glyph_fixes.tsv', encoding='utf8'):
        if line.strip() and not line.startswith('#'):
            i, lab = line.rstrip('\n').split('\t'); i = int(i)
            while len(labels) <= i: labels.append('')
            labels[i] = lab
    with open('translation/tables/glyph_hashes.tsv', 'w', encoding='utf8') as o:
        o.write('# md5[:16] of the 128-byte glyph tile\tcluster index\tcharacter (empty = unlabelled)\n')
        for i, tiles in enumerate(c['clusters']):
            lab = labels[i] if i < len(labels) else ''
            if lab.endswith('?') and len(lab) > 1: lab = lab[:-1]
            for t in tiles: o.write('%s\t%d\t%s\n' % (H(t), i, lab))
if __name__ == '__main__' and sys.argv[1:] == ['rebuild']: rebuild()
