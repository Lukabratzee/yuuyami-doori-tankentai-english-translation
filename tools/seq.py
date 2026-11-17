#!/usr/bin/env python3
"""seq.py EXPORT ENGLISH OUT.tsv
EXPORT: output of batch.py export. ENGLISH: '# file NNNN' headers, then one english line per exported line, in order.
Pairs them positionally (counts must match per file) and writes keyed TSV; also prints jp|en pairs to stdout if -v."""
import sys
exp,eng,out=sys.argv[1:4]
def parse(p,keyed):
    d={};cur=None
    for ln in open(p,encoding='utf-8').read().split('\n'):
        if ln.startswith('# file '): cur=ln[7:].strip(); d[cur]=[]; continue
        if cur is None or ln=='' : continue
        d[cur].append(ln.split('\t',1) if keyed else ln)
    return d
E=parse(exp,True); G=parse(eng,False); ok=True; rows=[]
for f,items in E.items():
    g=G.get(f,[])
    if len(g)!=len(items):
        print(f'MISMATCH {f}: export {len(items)} vs english {len(g)}'); ok=False; continue
    for (k,jp),en in zip(items,g): rows.append(f'{k}\t{en}')
    if '-v' in sys.argv:
        for (k,jp),en in zip(items,g): print(k,jp,'|',en)
if ok: open(out,'w',encoding='utf-8').write('\n'.join(rows)+'\n'); print('ok',len(rows))
else: sys.exit(1)
