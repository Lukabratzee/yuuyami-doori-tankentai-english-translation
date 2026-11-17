"""Rebuild FILELINK.FLB with some leaves replaced (sizes may change).  See flb.py for the format.
rebuild_to_file(src_mmap, repl{abs_offset: bytes}, out_path) -> new size.  With repl={} the output is byte-identical."""
import struct, bisect
MAGIC = b'FLB\x90'
def _node(m, base, total, repl, keys):
    """returns list of byte chunks for the node occupying m[base:base+total]"""
    lo = bisect.bisect_left(keys, base)
    if lo >= len(keys) or keys[lo] >= base + total: return [m[base:base+total]]
    if m[base:base+4] != MAGIC:
        assert keys[lo] == base, 'replacement not at a leaf start'
        return [repl[base]]
    etab, gtab, data, ne, ng = struct.unpack('<5I', m[base+8:base+0x1c])
    hdr = bytearray(m[base:base+data])
    ents = [struct.unpack_from('<II', hdr, etab + i*8) for i in range(ne)]
    grps = [struct.unpack_from('<4I', hdr, gtab + i*16) for i in range(ng)]
    items = [(v, 'f', i) for i, (v, eid) in enumerate(ents) if (eid >> 24) < 2] + [(g[0], 'g', i) for i, g in enumerate(grps)]
    items.sort()
    assert not items or items[0][0] == 0, 'data section does not start with first child'
    bounds = sorted(set(v for v, _, _ in items)) + [total - data]
    chunks = [hdr]; pos = 0; newoff = {}
    for v, kind, i in items:
        nxt = bounds[bisect.bisect_right(bounds, v)]
        if (v, kind) in newoff: continue
        sub = _node(m, base + data + v, nxt - v, repl, keys); ln = sum(len(c) for c in sub)
        newoff[(v, kind)] = (pos, ln - (nxt - v)); chunks += sub; pos += ln
    for i, (v, eid) in enumerate(ents):
        if (eid >> 24) < 2: struct.pack_into('<I', hdr, etab + i*8, newoff[(v, 'f')][0])
    for i, (go, gne, gng, gsz) in enumerate(grps):
        struct.pack_into('<I', hdr, gtab + i*16, newoff[(go, 'g')][0]); struct.pack_into('<I', hdr, gtab + i*16 + 12, gsz + newoff[(go, 'g')][1])
    old = struct.unpack_from('<I', hdr, 0x1c)[0]
    struct.pack_into('<I', hdr, 0x1c, old + (pos - (total - data)))
    chunks[0] = bytes(hdr)
    return chunks
def rebuild_to_file(m, repl, out_path):
    keys = sorted(repl); chunks = _node(m, 0, len(m), repl, keys); n = 0
    with open(out_path, 'wb') as f:
        for c in chunks: f.write(c); n += len(c)
    return n
