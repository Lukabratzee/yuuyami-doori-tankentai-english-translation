import struct,sys,hashlib
def rd(path):
    f=open(path,'rb')
    def sec(l): f.seek(l*2352+24); return f.read(2048)
    return f,sec
def walk(sec,lba,size,path,out):
    data=b''.join(sec(lba+i) for i in range((size+2047)//2048))[:size]
    p=0
    while p<len(data):
        n=data[p]
        if n==0: p=(p//2048+1)*2048; continue
        ext=struct.unpack('<I',data[p+2:p+6])[0]; sz=struct.unpack('<I',data[p+10:p+14])[0]; fl=data[p+25]; nl=data[p+32]; nm=data[p+33:p+33+nl]
        p+=n
        if nm in (b'\x00',b'\x01'): continue
        nm=nm.decode('latin1')
        if fl&2: walk(sec,ext,sz,path+nm+'/',out)
        else: out[path+nm]=(ext,sz)
res={}
for tag,pth in (('orig',__import__('os').environ.get('YDT_DISC','../Yuuyami Doori Tankentai (Japan)/Yuuyami Doori Tankentai (Japan).bin')),('new','build/ydt_en.bin')):
    f,sec=rd(pth); pvd=sec(16)
    vs=struct.unpack('<I',pvd[80:84])[0]
    root=pvd[156:190]; ext,sz=struct.unpack('<I',root[2:6])[0],struct.unpack('<I',root[10:14])[0]
    out={}; walk(sec,ext,sz,'/',out)
    import os
    tot=os.path.getsize(pth)//2352
    print(tag,'volsize',vs,'image sectors',tot,'files',len(out))
    h={}
    for k,(e,s) in out.items():
        m=hashlib.md5()
        for i in range((s+2047)//2048):
            d=sec(e+i); m.update(d if (i+1)*2048<=s else d[:s-i*2048])
        h[k]=(e,s,m.hexdigest())
    res[tag]=h
o,n=res['orig'],res['new']
print('missing in new',[k for k in o if k not in n],'extra',[k for k in n if k not in o])
for k in o:
    if k in n and o[k][2]!=n[k][2]: print('CHANGED',k,o[k][:2],'->',n[k][:2])
# overlap check
iv=sorted((e,e+(s+2047)//2048,k) for k,(e,s,_) in n.items())
for a,b in zip(iv,iv[1:]):
    if a[1]>b[0]: print('OVERLAP',a,b)
