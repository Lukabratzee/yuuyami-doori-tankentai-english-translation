"""ACD scene files (Yuuyami Doori Tankentai): parse, iterate, rebuild with new text + font.

Three variants, same idea, slightly different headers:
  'ACD\\0' '1.20'  header 0x50, 10 section offsets at 0x10, 12 u16 counts at 0x38, graphics = section 9   (scenes with sprites)
  'ACD '   '1.20'  same layout (text-only files; u32 at 0x08 is not the file size)
  'ACD '   '1.10'  header 0x44,  8 section offsets at 0x10, 10 u16 counts at 0x30, graphics = section 7
Common: sequence table right after the header (count[0] x 16 B: u16 s0,n0,s2,n2, text_start, text_count, duration, flag)
  section 3 = text records (u16 glyph | 0xFFFF end of line, u8 0, u8 delay)      count[4]
  section 4 = font descriptor (u32 offset of glyph tiles inside the graphics section, ...)
  section 5 = glyph metrics (u16 group, u8 x offset, u8 advance)                 count[6] = glyph count
  glyph tile g = graphics_section + font_offset + g*128   (16x16, 4bpp, 0xF background)
"""
import struct, mmap, hashlib
FLB = 'extract/DATA/FILELINK.FLB'; TREE = 'work/flb_tree.txt'
def leaves(kind=None):
    for l in open(TREE):
        p = l.split()
        if kind is None or p[7] == kind: yield p[0], int(p[2], 16), int(p[4]), int(p[6], 16), p[8]
class ACD:
    def __init__(s, d):
        s.d = d; s.magic = d[:8]
        if d[4:8] == b'1.20': s.hdr, s.nsec, s.cnt_off, s.ncnt = 0x50, 10, 0x38, 12
        elif d[4:8] == b'1.10': s.hdr, s.nsec, s.cnt_off, s.ncnt = 0x44, 8, 0x30, 10
        else: raise ValueError('unknown ACD version %r' % d[:8])
        s.gfx = s.nsec - 1
        s.offs = struct.unpack_from('<%dI' % s.nsec, d, 0x10) + (len(d),)
        s.cnt = struct.unpack_from('<%dH' % s.ncnt, d, s.cnt_off)
    def sec(s, i): return s.d[s.offs[i]:s.offs[i+1]]
    def text(s):
        t = s.sec(3); return [struct.unpack_from('<HBB', t, i) for i in range(0, len(t) - 3, 4)]
    def nglyphs(s): return s.cnt[6]
    def fontbase(s): return s.offs[s.gfx] + struct.unpack_from('<I', s.sec(4), 0)[0]
    def tile(s, g):
        o = s.fontbase() + g*128; return s.d[o:o+128]
    def metrics(s):
        t = s.sec(5); return [struct.unpack_from('<HBB', t, i) for i in range(0, len(t) - 3, 4)]
    def seqs(s): return [struct.unpack_from('<HH', s.d, s.hdr + i*16 + 8) for i in range(s.cnt[0])]
def has_text(d):
    if d[:3] != b'ACD' or len(d) < 0x50: return None
    try:
        a = ACD(d)
        ok = a.cnt[4] and len(a.sec(3)) == a.cnt[4]*4 and len(a.sec(4)) >= 20 and len(a.sec(5)) == a.cnt[6]*4 and a.fontbase() + a.nglyphs()*128 <= len(d)
        return a if ok else None
    except Exception: return None
def acds(unique=True):
    """yield (path, abs_offset, bytes, ACD) for every ACD leaf that has dialogue text"""
    f = open(FLB, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ); seen = set()
    for path, o, s, fid, mg in leaves('ACD'):
        d = m[o:o+s]; a = has_text(d)
        if not a: continue
        if unique:
            h = hashlib.md5(d).digest()
            if h in seen: continue
            seen.add(h)
        yield path, o, d, a
def split_lines(tx):
    """records -> list of lines; each line = (char_records, terminator_record_or_None)"""
    lines, cur = [], []
    for r in tx:
        if r[0] == 0xffff: lines.append((cur, r)); cur = []
        else: cur.append(r)
    if cur: lines.append((cur, None))
    return lines
def rebuild(d, new_lines, glyph):
    """New ACD with every dialogue line replaced by new_lines[i] (one string per original line).
    glyph(ch) -> (128-byte tile, advance).  Display time of every sequence is preserved.  Returns (bytes, font_was_appended)."""
    a = ACD(d); tx = a.text(); lines = split_lines(tx)
    assert len(new_lines) == len(lines), (len(new_lines), len(lines))
    chars = sorted(set(''.join(new_lines))); cmap = {c: i for i, c in enumerate(chars)}
    M, N = a.nglyphs(), len(chars)
    seqs = a.seqs(); marks = set()
    for st, n in seqs: marks.add(st); marks.add(st + n)
    out = bytearray(); newpos = {}; old = 0
    for (crs, term), s in zip(lines, new_lines):
        k, n = len(crs), len(s)
        cuts = [0] + sorted(j for j in range(1, k) if old + j in marks) + [k]; ncuts = [0]
        for j in cuts[1:-1]:                                   # a line revealed in two steps: break after a space
            t = round(j * n / k) if k else 0
            sp = [i + 1 for i, ch in enumerate(s) if ch == ' ']
            if sp: t = min(sp, key=lambda x: abs(x - t))
            ncuts.append(max(ncuts[-1], min(n, t)))
        ncuts.append(n)
        for seg in range(len(cuts) - 1):
            o0, o1, n0, n1 = cuts[seg], cuts[seg+1], ncuts[seg], ncuts[seg+1]
            newpos[old + o0] = len(out) // 4
            total = sum(c for _, _, c in crs[o0:o1]); m = n1 - n0
            for i in range(m):
                out += struct.pack('<HBB', cmap[s[n0 + i]], 0, min(255, total * (i + 1) // m - total * i // m))
        newpos[old + k] = len(out) // 4
        if term is not None: out += struct.pack('<HBB', *term)
        old += k + (1 if term is not None else 0)
    newpos[old] = len(out) // 4
    hdr = bytearray(d[:a.offs[0]])
    for i, (st, n) in enumerate(seqs):
        if st not in newpos or st + n not in newpos: raise ValueError('sequence %d text range (%d,%d) unmapped' % (i, st, n))
        struct.pack_into('<HH', hdr, a.hdr + i*16 + 8, newpos[st], newpos[st + n] - newpos[st])
    met = bytearray(a.sec(5)); sec4 = bytearray(a.sec(4)); gfx = bytearray(a.sec(a.gfx))
    tiles = b''.join(glyph(c)[0] for c in chars)
    if N > M: met += bytes(4 * (N - M))
    for c, i in cmap.items(): met[i*4+2] = 0; met[i*4+3] = glyph(c)[1]
    if N <= M:
        fo = struct.unpack_from('<I', sec4, 0)[0]; gfx[fo:fo+len(tiles)] = tiles; appended = False
    else:
        while len(gfx) % 4: gfx += b'\0'
        struct.pack_into('<I', sec4, 0, len(gfx)); struct.pack_into('<H', sec4, 8, N); struct.pack_into('<H', sec4, 14, N)
        gfx += tiles; appended = True
    secs = [a.sec(i) for i in range(a.nsec)]; secs[3] = bytes(out); secs[4] = bytes(sec4); secs[5] = bytes(met); secs[a.gfx] = bytes(gfx)
    body = bytearray(); offs = []
    for s in secs: offs.append(len(hdr) + len(body)); body += s
    while (len(hdr) + len(body)) % 4: body += b'\0'
    cnt = list(a.cnt); cnt[4] = len(out) // 4; cnt[6] = max(M, N)
    struct.pack_into('<%dI' % a.nsec, hdr, 0x10, *offs); struct.pack_into('<%dH' % a.ncnt, hdr, a.cnt_off, *cnt)
    if struct.unpack_from('<I', hdr, 8)[0] == len(d): struct.pack_into('<I', hdr, 8, len(hdr) + len(body))
    return bytes(hdr + body), appended
