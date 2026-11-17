"""MODE2/2352 Form 1 sector EDC/ECC regeneration (same algorithm as ECM/cdrtools)."""
F=[0]*256; B=[0]*256; EDC=[0]*256
for i in range(256):
    j=((i<<1)^(0x11D if i&0x80 else 0))&0xFF; F[i]=j; B[i^j]=i
    e=i
    for _ in range(8): e=(e>>1)^(0xD8018001 if e&1 else 0)
    EDC[i]=e
def edc(data):
    e=0
    for b in data: e=(e>>8)^EDC[(e^b)&0xFF]
    return e
def _ecc(src,major_count,minor_count,major_mult,minor_inc):
    size=major_count*minor_count; out=bytearray(major_count*2)
    for major in range(major_count):
        idx=(major>>1)*major_mult+(major&1); a=b=0
        for _ in range(minor_count):
            t=src[idx]; idx+=minor_inc
            if idx>=size: idx-=size
            a=F[a^t]; b^=t
        a=B[F[a]^b]; out[major]=a; out[major+major_count]=a^b
    return out
def fix_form1(sec):
    """sec: bytearray(2352) with new user data at [24:2072]; rewrites EDC and ECC in place."""
    e=edc(sec[16:2072]); sec[2072:2076]=e.to_bytes(4,'little')
    src=bytearray(4)+sec[16:2076]            # header zeroed for mode 2
    p=_ecc(src,86,24,2,86); sec[2076:2248]=p
    q=_ecc(src+p,52,43,86,88); sec[2248:2352]=q
    return sec
def selftest(binpath, lba=30):
    with open(binpath,'rb') as f:
        f.seek(lba*2352); s=bytearray(f.read(2352))
    return fix_form1(bytearray(s))==s
