#!/usr/bin/env python3
"""FLB 2.00 archive reader (Yuuyami Doori Tankentai, DATA/FILELINK.FLB).

Header (little endian):
  00 'FLB\\x90'  04 '2.00'  08 u32 entry_table_off  0C u32 group_table_off  10 u32 data_off
  14 u32 n_entries  18 u32 n_groups
entry table: n_entries x (u32 value, u32 id).  id>>24: 0/1 = file (value = offset in data section, 1 = last file),
             2/3 = sub-directory (value = index into group table, 3 = last).  id&0xffffff looks like a name hash.
group table: n_groups x (u32 offset_in_data, u32 n_entries, u32 n_groups, u32 size); each group is itself an FLB.
File sizes are implicit: up to the next file/group offset.

Usage: flb.py tree <flb>            print every leaf: path, absolute offset, size, id, magic
       flb.py extract <flb> <out>   write leaves to <out>/<path>.bin plus index.json
"""
import sys, os, struct, mmap, json
MAGIC = b'FLB\x90'
def parse(m, base, size, path, out):
    etab, gtab, data, ne, ng = struct.unpack('<5I', m[base+8:base+0x1c])
    ents = [struct.unpack('<II', m[base+etab+i*8: base+etab+i*8+8]) for i in range(ne)]
    grps = [struct.unpack('<4I', m[base+gtab+i*16: base+gtab+i*16+16]) for i in range(ng)]
    files = [(v, i, eid) for i, (v, eid) in enumerate(ents) if (eid >> 24) < 2]
    bounds = sorted(set([v for v, _, _ in files] + [g[0] for g in grps] + [size - data]))
    for v, i, eid in files:
        c = [b for b in bounds if b > v]; nxt = min(c) if c else v
        off = base + data + v; sz = nxt - v; p = path + ['f%03d' % i]
        if m[off:off+4] == MAGIC: parse(m, off, sz, p, out)
        else: out.append({'path': '/'.join(p), 'off': off, 'size': sz, 'id': eid, 'magic': m[off:off+8]})
    for v, eid in ents:
        if (eid >> 24) >= 2:
            go, gne, gng, gsz = grps[v]; off = base + data + go; p = path + ['d%03d' % v]
            if m[off:off+4] == MAGIC: parse(m, off, gsz, p, out)
            else: out.append({'path': '/'.join(p), 'off': off, 'size': gsz, 'id': eid, 'magic': m[off:off+8]})
    return out
def tree(path):
    f = open(path, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    return m, parse(m, 0, len(m), [], [])
def mname(b):
    return b[:3].decode() if b[:3].isalpha() or b[:4] == b'pBAV' else ('TIM' if b[:4] == b'\x10\0\0\0' else 'raw')
if __name__ == '__main__':
    m, leaves = tree(sys.argv[2])
    if sys.argv[1] == 'tree':
        for l in leaves: print('%-28s off %09x size %9d id %08x %-4s %s' % (l['path'], l['off'], l['size'], l['id'], mname(l['magic']), l['magic'].hex()))
    elif sys.argv[1] == 'extract':
        out = sys.argv[3]
        for l in leaves:
            p = os.path.join(out, l['path'] + '.' + mname(l['magic']).lower()); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(m[l['off']:l['off']+l['size']]); l['magic'] = l['magic'].hex(); l['file'] = p
        json.dump(leaves, open(os.path.join(out, 'index.json'), 'w'), indent=0)
