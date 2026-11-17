"""Write a new MODE2/2352 image where DATA/FILELINK.FLB is replaced by a (possibly larger) file.
Files after it on the disc (XALINK.XA, STR movies) are moved by whole sectors; directory records and PVD are patched."""
import numpy as np, struct, mmap, os
from psx_sector import F, B, EDC, fix_form1
FLB_LBA, FLB_SECS, DATA_DIR_LBA, PVD_LBA = 254, 271884, 23, 16
Fn = np.array(F, np.uint8); Bn = np.array(B, np.uint8); En = np.array(EDC, np.uint32)
def bcd(v): return ((v // 10) << 4) | (v % 10)
def msf(lba):
    a = lba + 150; return bytes([bcd(a // 4500), bcd(a // 75 % 60), bcd(a % 75)])
def _ecc(src, major_count, minor_count, major_mult, minor_inc):
    n = src.shape[0]; size = major_count * minor_count; out = np.zeros((n, major_count * 2), np.uint8)
    for major in range(major_count):
        idx = (major >> 1) * major_mult + (major & 1); a = np.zeros(n, np.uint8); b = np.zeros(n, np.uint8)
        for _ in range(minor_count):
            t = src[:, idx]; idx += minor_inc
            if idx >= size: idx -= size
            a = Fn[a ^ t]; b ^= t
        a = Bn[Fn[a] ^ b]; out[:, major] = a; out[:, major + major_count] = a ^ b
    return out
def make_form1(lba0, data, last=False):
    """data: bytes, multiple of 2048 -> np array (n,2352) of finished sectors starting at lba0"""
    n = len(data) // 2048; s = np.zeros((n, 2352), np.uint8)
    s[:, 1:11] = 0xFF; s[:, 15] = 2; s[:, 18] = 8; s[:, 22] = 8
    for i in range(n): s[i, 12:15] = np.frombuffer(msf(lba0 + i), np.uint8)
    if last: s[n-1, 18] = 0x89; s[n-1, 22] = 0x89
    s[:, 24:2072] = np.frombuffer(data, np.uint8).reshape(n, 2048)
    e = np.zeros(n, np.uint32)
    for c in range(16, 2072): e = (e >> 8) ^ En[(e ^ s[:, c]) & 0xFF]
    s[:, 2072:2076] = e.astype('<u4').view(np.uint8).reshape(n, 4)
    src = np.zeros((n, 2064), np.uint8); src[:, 4:] = s[:, 16:2076]
    p = _ecc(src, 86, 24, 2, 86); s[:, 2076:2248] = p
    s[:, 2248:2352] = _ecc(np.concatenate([src, p], 1), 52, 43, 86, 88)
    return s
def build(orig_path, flb_path, out_path, log=print):
    of = open(orig_path, 'rb'); om = mmap.mmap(of.fileno(), 0, access=mmap.ACCESS_READ); total = len(om) // 2352
    ff = open(flb_path, 'rb'); fm = mmap.mmap(ff.fileno(), 0, access=mmap.ACCESS_READ); size = len(fm)
    nsec = max(FLB_SECS, (size + 2047) // 2048); delta = nsec - FLB_SECS
    with open(out_path, 'wb') as out:
        head = bytearray(om[:FLB_LBA * 2352])
        # DATA directory
        s = bytearray(head[DATA_DIR_LBA*2352:(DATA_DIR_LBA+1)*2352]); i = 24
        while s[i]:
            l = s[i]; name = bytes(s[i+33:i+33+s[i+32]])
            if name.startswith(b'FILELINK'): s[i+10:i+14] = struct.pack('<I', size); s[i+14:i+18] = struct.pack('>I', size)
            elif name not in (b'\0', b'\1'):
                lba = struct.unpack_from('<I', s, i+2)[0] + delta; s[i+2:i+6] = struct.pack('<I', lba); s[i+6:i+10] = struct.pack('>I', lba)
            i += l
        head[DATA_DIR_LBA*2352:(DATA_DIR_LBA+1)*2352] = fix_form1(s)
        s = bytearray(head[PVD_LBA*2352:(PVD_LBA+1)*2352]); vs = struct.unpack_from('<I', s, 24+80)[0] + delta
        s[24+80:24+84] = struct.pack('<I', vs); s[24+84:24+88] = struct.pack('>I', vs)
        head[PVD_LBA*2352:(PVD_LBA+1)*2352] = fix_form1(s); out.write(head)
        # FLB: copy leading sectors that are unchanged, regenerate the rest
        same = 0; CH = 1 << 20
        while same < min(size, FLB_SECS * 2048):
            a = fm[same:same+CH]; b = b''.join(om[(FLB_LBA + (same + k) // 2048) * 2352 + 24:(FLB_LBA + (same + k) // 2048) * 2352 + 2072] for k in range(0, len(a), 2048))[:len(a)]
            if a != b: break
            same += len(a)
        keep = same // 2048
        if delta == 0: keep = min(keep, FLB_SECS - 1)
        out.write(om[FLB_LBA*2352:(FLB_LBA + keep)*2352]); log('unchanged FLB sectors copied:', keep, 'regenerating:', nsec - keep, 'delta:', delta)
        N = 4096
        for s0 in range(keep, nsec, N):
            n = min(N, nsec - s0); data = fm[s0*2048:(s0+n)*2048]; data += bytes(n*2048 - len(data))
            out.write(make_form1(FLB_LBA + s0, data, last=(s0 + n == nsec)).tobytes())
        # tail (XA + STR): move whole raw sectors, rewrite header address
        tail0 = FLB_LBA + FLB_SECS
        for s0 in range(tail0, total, 8192):
            n = min(8192, total - s0); blk = np.frombuffer(om[s0*2352:(s0+n)*2352], np.uint8).reshape(n, 2352).copy()
            if delta:
                for i in range(n): blk[i, 12:15] = np.frombuffer(msf(s0 + i + delta), np.uint8)
            out.write(blk.tobytes())
    return size, delta
