#!/usr/bin/env python3
"""Extract ISO9660 files from a MODE2/2352 PS1 .bin. Usage: iso_extract.py <bin> <outdir> [--skip-big]
Form1 files -> 2048 bytes/sector. XA/STR (form2 interleaved) are listed but skipped."""
import sys, os, struct, json
SEC=2352
def rd(f,lba,n=1):
    out=b''
    for i in range(n):
        f.seek((lba+i)*SEC+24); out+=f.read(2048)
    return out
def walk(f,lba,size,path,res):
    d=rd(f,lba,(size+2047)//2048); i=0
    while i<len(d):
        l=d[i]
        if l==0:
            i=(i//2048+1)*2048; continue
        e=d[i:i+l]; elba,=struct.unpack('<I',e[2:6]); esz,=struct.unpack('<I',e[10:14]); fl=e[25]; nl=e[32]; name=e[33:33+nl]
        i+=l
        if name in(b'\0',b'\1'): continue
        name=name.decode('ascii').split(';')[0]
        if fl&2: walk(f,elba,esz,path+name+'/',res)
        else: res.append({'path':path+name,'lba':elba,'size':esz})
bin_,out=sys.argv[1],sys.argv[2]
with open(bin_,'rb') as f:
    pvd=rd(f,16); root=pvd[156:190]
    rl,=struct.unpack('<I',root[2:6]); rs,=struct.unpack('<I',root[10:14])
    res=[]; walk(f,rl,rs,'',res)
    for r in res:
        ext=r['path'].rsplit('.',1)[-1]
        r['extracted']=ext not in('XA','STR')
        if r['extracted']:
            p=os.path.join(out,r['path']); os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
            with open(p,'wb') as o:
                left=r['size']; lba=r['lba']
                while left>0:
                    n=min(512,(left+2047)//2048); b=rd(f,lba,n); o.write(b[:left]); left-=len(b); lba+=n
        print(r)
    json.dump(res,open(os.path.join(out,'layout.json'),'w'),indent=1)
