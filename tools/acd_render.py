#!/usr/bin/env python3
"""Render the text section of an ACD 1.20 file using its own embedded glyph tiles (proof of the text format).
Usage: acd_render.py <file.acd> <out.png> [max_lines]"""
import sys, struct
from PIL import Image
d = open(sys.argv[1], 'rb').read()
offs = struct.unpack('<10I', d[0x10:0x38]) + (len(d),)
cnt = struct.unpack('<12H', d[0x38:0x50])
text = d[offs[3]:offs[4]]; font = offs[9] + 0x20
recs = [struct.unpack('<HBB', text[i:i+4]) for i in range(0, len(text), 4)]
lines, cur = [], []
for g, a, b in recs:
    if g == 0xffff: lines.append(cur); cur = []
    else: cur.append(g)
if cur: lines.append(cur)
lines = lines[:int(sys.argv[3]) if len(sys.argv) > 3 else 40]
W = max(len(l) for l in lines) * 16 + 4; img = Image.new('L', (W, len(lines) * 18 + 2), 255)
for y, l in enumerate(lines):
    for x, g in enumerate(l):
        t = d[font + g*128: font + g*128 + 128]
        px = bytes(v for b in t for v in ((b & 15) * 17, (b >> 4) * 17))
        img.paste(Image.frombytes('L', (16, 16), px), (2 + x*16, 2 + y*18))
img.resize((img.width*2, img.height*2), Image.NEAREST).save(sys.argv[2])
print(len(recs), 'records', len(lines), 'lines; glyph count field', cnt[8], 'max glyph', max(g for l in lines for g in l))
