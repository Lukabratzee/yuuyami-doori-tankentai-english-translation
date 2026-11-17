"""Write into a file inside a MODE2/2352 image by logical offset, tracking dirty sectors; finish() regenerates EDC/ECC."""
import mmap
from psx_sector import fix_form1
class Disc:
    def __init__(s, path):
        s.f = open(path, 'r+b'); s.m = mmap.mmap(s.f.fileno(), 0); s.dirty = set()
    def read(s, lba, off, n):
        out = bytearray()
        while n:
            sec, o = lba + off // 2048, off % 2048; k = min(n, 2048 - o)
            out += s.m[sec*2352+24+o: sec*2352+24+o+k]; off += k; n -= k
        return bytes(out)
    def write(s, lba, off, data):
        i = 0
        while i < len(data):
            sec, o = lba + off // 2048, off % 2048; k = min(len(data) - i, 2048 - o)
            p = sec*2352+24+o
            if s.m[p:p+k] != data[i:i+k]: s.m[p:p+k] = data[i:i+k]; s.dirty.add(sec)
            off += k; i += k
    def finish(s):
        for sec in sorted(s.dirty):
            b = bytearray(s.m[sec*2352:(sec+1)*2352]); s.m[sec*2352:(sec+1)*2352] = fix_form1(b)
        s.m.flush(); n = len(s.dirty); s.dirty = set(); return n
