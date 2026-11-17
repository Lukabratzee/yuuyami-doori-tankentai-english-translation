#!/usr/bin/env python3
"""Write work/acd_index.json: {file number: [leaf paths]} for every ACD leaf that has dialogue, numbered in order of first
appearance by content hash.  The numbers are the NNNN of translation/script/NNNN.json, so this must reproduce exactly."""
import sys, json, hashlib, mmap
sys.path.insert(0, 'tools'); from acd import *
f = open(FLB, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ); idx = {}; order = []
for path, o, s, fid, mg in leaves('ACD'):
    d = m[o:o+s]
    if not has_text(d): continue
    h = hashlib.md5(d).hexdigest()
    if h not in idx: idx[h] = {'idx': len(order), 'paths': []}; order.append(h)
    idx[h]['paths'].append(path)
json.dump({v['idx']: v['paths'] for v in idx.values()}, open('work/acd_index.json', 'w'), indent=0)
print(len(order), 'unique text files')
