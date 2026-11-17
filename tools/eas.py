#!/usr/bin/env python3
"""EAS 1.00 image sets (system/UI graphics).  Layout worked out 2026-11-16:
 00 'EAS\\x90' '1.00'   08 u32 0x38   0C.. u32 section offsets; [0x1C] = palette section, [0x20] = pixel data base,
 [0x24] = palette bytes, [0x28] = pixel bytes, 0x2C u16 image count.
 0x38: u32 0, then image table, 20 B each: u16 id, u16 ?, u16 origin_x, u16 origin_y, u16 w, u16 h, u32 bpp (4|8),
       u32 END offset of this image's pixels (start = previous end).  4bpp rows are w/2 bytes, low nibble = left pixel.
Usage: eas.py montage <flb leaf path e.g. d004/f000> <out.png> [preview]   greyscale contact sheet with image numbers;
       'preview' applies translation/ui/eas_text.json first.  build_disc.py applies the same file to the disc."""
import sys, struct, mmap
from PIL import Image, ImageDraw
def images(d):
    n = struct.unpack_from('<H', d, 0x2c)[0]; base = struct.unpack_from('<I', d, 0x20)[0]; prev = 0; out = []
    for i in range(n):
        iid, a, ox, oy, w, h, bpp, end = struct.unpack_from('<6H2I', d, 0x3c + i*20)
        out.append({'i': i, 'id': iid, 'w': w, 'h': h, 'bpp': bpp, 'off': base + prev, 'size': end - prev}); prev = end
    return out
def indices(d, im):
    """-> list of rows of palette indices.  Row stride is size // h (rows are padded; do not assume w/2)."""
    w, h, raw = im['w'], im['h'], d[im['off']:im['off'] + im['size']]; stride = im['size'] // h if h else 0
    if im['bpp'] == 8: return [list(raw[y*stride:y*stride + w]) for y in range(h)]
    return [[(raw[y*stride + x//2] >> (4*(x & 1))) & 15 for x in range(w)] for y in range(h)]
def decode(d, im):
    k = 17 if im['bpp'] == 4 else 1
    return Image.frombytes('L', (im['w'], im['h']), bytes(v * k for r in indices(d, im) for v in r))
def encode(im, rows):
    """rows of indices -> pixel bytes of exactly im['size'] (same stride/padding as the original)"""
    h, w = im['h'], im['w']; stride = im['size'] // h; out = bytearray(im['size'])
    for y in range(h):
        for x in range(w):
            if im['bpp'] == 8: out[y*stride + x] = rows[y][x]
            else: out[y*stride + x//2] |= (rows[y][x] & 15) << (4*(x & 1))
    return bytes(out)
def text_rows(d, im, s):
    """Draw s centred in the image box, reusing the image's own colours: background = top-left pixel,
    fill = most common other index, outline = second most common.  Heuristic; check the result in-game."""
    from collections import Counter
    from PIL import ImageFont
    rows = indices(d, im); bg = rows[0][0]; c = Counter(v for r in rows for v in r if v != bg).most_common(2)
    fill = c[0][0] if c else (bg ^ 15); edge = c[1][0] if len(c) > 1 else bg
    w, h = im['w'], im['h']; size = min(12, h - 2)
    while size > 6:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
        if f.getlength(s) <= w - 2: break
        size -= 1
    m = Image.new('1', (w, h), 0); ImageDraw.Draw(m).text((w // 2, h // 2), s, font=f, fill=1, anchor='mm')
    ink = [[m.getpixel((x, y)) for x in range(w)] for y in range(h)]; out = [[bg]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if ink[y][x]: out[y][x] = fill
            elif any(0 <= x+dx < w and 0 <= y+dy < h and ink[y+dy][x+dx] for dx in (-1, 0, 1) for dy in (-1, 0, 1)): out[y][x] = edge
    return out
# ---- styled text (2026-11-17): eas_text.json values may be {"t": text, "style": hand|cap|help|inv, ...} ----
FONTS = {'sans': '/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf',
         'ital': '/usr/share/fonts/truetype/liberation/LiberationSansNarrow-BoldItalic.ttf',
         'bold': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'}
def _angle(rows, bg, skip=()):
    """principal-axis angle (degrees, counter-clockwise positive) of the non-background pixels"""
    import math
    pts = [(x, y) for y, r in enumerate(rows) for x, v in enumerate(r) if v != bg and v not in skip]
    if len(pts) < 8: return 0.0, None
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0]-mx)**2 for p in pts); syy = sum((p[1]-my)**2 for p in pts); sxy = sum((p[0]-mx)*(p[1]-my) for p in pts)
    a = 0.5 * math.atan2(2*sxy, sxx - syy)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return -math.degrees(a), (min(xs), min(ys), max(xs), max(ys))
def _coverage(s, w, h, angle, font, maxsize, minsize=6, align='c', box=None, lines=None, segs=None, stretch=None):
    """-> h x w coverage floats: s drawn as large as fits (<= maxsize px), rotated by angle, placed in box"""
    from PIL import ImageFont
    S = 4; lines = lines or s.split('|'); x0, y0, x1, y1 = box or (0, 0, w-1, h-1); bw, bh = x1-x0+1, y1-y0+1
    size = maxsize
    while True:
        f = ImageFont.truetype(FONTS[font], size*S)
        lw = max(int(f.getlength(l)) for l in lines); asc, desc = f.getmetrics(); lh = asc + desc; gap = -int(lh*0.12)
        if segs:   # [[text, units], ...]: each piece centred in a slot proportional to the original glyph count
            U = max(int(f.getlength(t)) / u for t, u in segs) * 1.08; lw = int(U * sum(u for _, u in segs))
        m = Image.new('L', (lw + 8*S, lh*len(lines) + gap*(len(lines)-1) + 4*S), 0); dr = ImageDraw.Draw(m)
        if segs:
            x = 4*S
            for t, u in segs:
                dr.text((x + (U*u - f.getlength(t))/2, 2*S), t, font=f, fill=255); x += U*u
        else:
          for k, l in enumerate(lines):
            lx = 4*S + ((lw - int(f.getlength(l)))//2 if align == 'c' else 0)
            dr.text((lx, 2*S + k*(lh+gap)), l, font=f, fill=255)
        if angle: m = m.rotate(angle, resample=Image.BICUBIC, expand=True)
        bb = m.getbbox(); m = m.crop(bb)
        if (m.width <= bw*S and m.height <= bh*S) or size <= minsize: break
        size -= 1
    m = m.resize((max(1, round(m.width/S)), max(1, round(m.height/S))), Image.LANCZOS)
    if stretch and m.width < stretch: m = m.resize((min(stretch, w), m.height), Image.LANCZOS)   # match the original's span
    if m.width > bw: m = m.resize((bw, m.height), Image.LANCZOS)      # last resort: squeeze
    if m.height > bh: m = m.resize((m.width, bh), Image.LANCZOS)
    out = Image.new('L', (w, h), 0)
    px = x0 if align == 'l' else x0 + (bw - m.width)//2
    py = y1 + 1 - m.height if align == 'l' else y0 + (bh - m.height)//2
    out.paste(m, (px, max(0, py)))
    return [[out.getpixel((x, y))/255 for x in range(w)] for y in range(h)], size
def styled_rows(d, im, spec):
    rows = indices(d, im); w, h = im['w'], im['h']; st = spec['style']; s = spec['t']
    def near(cov, x, y, t=0.45):
        return any(0 <= x+dx < w and 0 <= y+dy < h and cov[y+dy][x+dx] >= t for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    if st == 'hand':      # pencil on notebook paper: bg 15, ink = low/mid indices, text keeps the original slant
        bg = spec.get('bg', 15); kl = spec.get('keep_left', 0)
        ang, box = _angle([r[kl:] for r in rows], bg); box = box or (0, 0, w-1, h-1)
        segs = spec.get('segs'); span = (box[2] - box[0] + 1) if segs else None
        cov, _ = _coverage(s, w, h, ang, 'sans', spec.get('size', 16), align='l', box=(kl + box[0], 0, w-1, h-1),
                           segs=segs, stretch=span)
        # dark pencil: palette 0 = paper-white, 1..14 = near-black .. grey, 15 = transparent; the original ink is 1-6
        # notebook pencil is drawn with SUBTRACTIVE blending (seen in-game 2026-11-17): high index = darker pencil
        out = [[bg if c < 0.10 else (7 if c < 0.25 else (11 if c < 0.45 else 14)) for c in r] for r in cov]
        return [rows[y][:kl] + out[y][kl:] for y in range(h)]
    if st == 'save':      # save-screen / exorcism messages: bg 15, outline 2, fill 8 ('|' = new line)
        cov, _ = _coverage(s, w-2, h-2, 0, 'sans', spec.get('size', 13))
        cov = [[0.0]*w] + [[0.0] + r + [0.0] for r in cov] + [[0.0]*w]
        return [[(8 if cov[y][x] >= 0.5 else 2) if cov[y][x] >= 0.2 else (2 if near(cov, x, y) else 15) for x in range(w)] for y in range(h)]
    if st == 'btn':       # light button, dark text: bg 13
        cov, _ = _coverage(s, w, h, 0, 'sans', spec.get('size', 13))
        return [[13 if c < 0.15 else 10 if c < 0.4 else 6 if c < 0.7 else 3 for c in r] for r in cov]
    if st == 'inv':       # image 65: light pencil on black, 3 right-hand columns kept
        ang, box = _angle([r[:-3] for r in rows], 0); box = box or (0, 0, w-4, h-1)
        cov, _ = _coverage(s, w-3, h, ang, 'ital', spec.get('size', 11), align='l', box=(box[0], 0, w-4, h-1))
        return [[0 if c < 0.18 else (9 if c < 0.45 else 5) for c in r] + rows[y][-3:] for y, r in enumerate(cov)]
    if st == 'cap':       # white caption on the black strip: bg 15, 14 = full white
        cov, _ = _coverage(s, w, h, 0, 'sans', spec.get('size', 12))
        return [[15 if c < 0.07 else max(1, min(14, round(c*14))) for c in r] for r in cov]
    if st == 'help':      # light text with dark outline: bg 0, outline 14, text 5 (bright) .. 12
        cov, _ = _coverage(s, w-2, h-2, 0, 'sans', spec.get('size', 11))
        cov = [[0.0]*w] + [[0.0] + r + [0.0] for r in cov] + [[0.0]*w]
        out = []
        for y in range(h):
            out.append([])
            for x in range(w):
                c = cov[y][x]
                out[-1].append(5 if c >= 0.8 else 8 if c >= 0.6 else 10 if c >= 0.45 else (14 if near(cov, x, y) else 0))
        return out
    if st in ('msg', 'msgdark'):  # title-screen memory-card messages; '|' separates lines
        bg, ramp = (0, (8, 11, 14)) if st == 'msg' else (spec.get('bg', 12), (5, 3, 0))
        cov, _ = _coverage(s, w, h, 0, 'sans', spec.get('size', 12))
        return [[bg if c < 0.15 else ramp[0] if c < 0.35 else ramp[1] if c < 0.6 else ramp[2] for c in r] for r in cov]
    if st == 'ramp':      # generic: spec bg + 3-step ink ramp (faint, mid, solid)
        bg = spec['bg']; r0, r1, r2 = spec['ramp']
        cov, _ = _coverage(s, w, h, 0, spec.get('font', 'sans'), spec.get('size', 13))
        return [[bg if c < 0.2 else r0 if c < 0.4 else r1 if c < 0.65 else r2 for c in r] for r in cov]
    if st == 'auto':      # infer ink ramp + slant from the original pixels (map labels)
        from collections import Counter
        keep = spec.get('keep_left', 0)
        border = [v for v in rows[0][keep:] + rows[-1][keep:] + [r[keep] for r in rows] + [r[-1] for r in rows]]
        bg = spec.get('bg', Counter(border).most_common(1)[0][0])
        ink = Counter(); core = Counter()
        for y in range(h):
            for x in range(keep, w):
                v = rows[y][x]
                if v == bg: continue
                ink[v] += 1; core[v] += sum(1 for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)) if 0 <= x+dx < w and 0 <= y+dy < h and rows[y+dy][x+dx] != bg)
        if spec.get('ramp'): r0, r1, r2 = spec['ramp']
        else:   # map-label palettes are grey ramps (index ~ brightness): take ink percentiles
            vals = sorted(v for v, n in ink.items() for _ in range(n)) or [bg ^ 15]
            r0, r1, r2 = (vals[int(len(vals)*q)] for q in (0.25, 0.55, 0.92))
        ang, box = _angle([r[keep:] for r in rows], bg)
        if 'angle' in spec: ang = spec['angle']
        elif abs(ang) > 55: ang = -90 if ang < 0 or h > w else 90
        elif abs(ang) < 4: ang = 0
        cov, _ = _coverage(s, w - keep, h, ang, 'sans', spec.get('size', 14))
        out = [[bg if c < 0.2 else r0 if c < 0.4 else r1 if c < 0.65 else r2 for c in r] for r in cov]
        return [rows[y][:keep] + out[y] for y in range(h)]
    raise ValueError(st)
def disclaimer(d, lines):
    """d003/f000: full-screen 'this is fiction' notice, two 160x240 8bpp halves.  Erase the Japanese (its palette
    entries 7,15,25,36-50 occur nowhere else in the photo) plus its black shadow, refill from the same column above/below,
    then draw the English lines in the same white ramp with a 1px black shadow."""
    from PIL import ImageFont
    d = bytearray(d); ims = images(d); a, b = ims[0], ims[1]
    full = [ra + rb for ra, rb in zip(indices(bytes(d), a), indices(bytes(d), b))]; W, H = 320, 240
    T = {7, 15, 25} | set(range(36, 51))
    mask = [[full[y][x] in T for x in range(W)] for y in range(H)]
    R = 2   # erase the glyphs plus a 2px ring (shadow and the anti-aliasing that shares background palette entries)
    grow = [[any(0 <= y+dy < H and 0 <= x+dx < W and mask[y+dy][x+dx] for dx in range(-R, R+1) for dy in range(-R, R+1))
             for x in range(W)] for y in range(H)]
    src = [r[:] for r in full]
    for y in range(H):
        for x in range(W):
            if grow[y][x]:          # copy texture from a patch ~1.5 text lines away (same column), first clean one wins
                for k in (24, -24, 30, -30, 18, -18, 36, -36, 12, -12, 42, -42):
                    if 0 <= y+k < H and not grow[y+k][x]: full[y][x] = src[y+k][x]; break
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    ys = [76, 106, 136, 165]
    for t, y in zip(lines, ys): dr.text((W // 2, y), t, font=f, fill=255, anchor='mm')
    cov = [[m.getpixel((x, y)) / 255 for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            c = cov[y][x]
            if c >= 0.2: full[y][x] = 50 if c >= 0.7 else 46 if c >= 0.45 else 36
            elif (x > 0 and y > 0 and cov[y-1][x-1] >= 0.45): full[y][x] = 0
    d[a['off']:a['off'] + a['size']] = encode(a, [r[:160] for r in full])
    d[b['off']:b['off'] + b['size']] = encode(b, [r[160:] for r in full])
    return bytes(d)
def patch(d, texts):
    """texts: {image index (str/int): 'English'} -> new leaf bytes, same size"""
    if '_disclaimer' in texts: return disclaimer(d, texts['_disclaimer'])
    d = bytearray(d); ims = images(d)
    for k, s in texts.items():
        im = ims[int(k)]; d[im['off']:im['off'] + im['size']] = encode(im, styled_rows(bytes(d), im, s) if isinstance(s, dict) else text_rows(bytes(d), im, s))
    return bytes(d)
def leaf(path):
    f = open('extract/DATA/FILELINK.FLB', 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    for l in open('work/flb_tree.txt'):
        p = l.split()
        if p[0] == path: return m[int(p[2], 16):int(p[2], 16) + int(p[4])], int(p[2], 16)
if __name__ == '__main__':
    d, off = leaf(sys.argv[2])
    import json, os
    if len(sys.argv) > 4:  # montage <leaf> <out.png> preview : apply translation/ui/eas_text.json first
        d = patch(d, json.load(open('translation/ui/eas_text.json'))[sys.argv[2]])
    ims = images(d); W = 1400; x = y = 0; rowh = 0; cells = []
    for im in ims:
        if im['w'] == 0 or im['h'] == 0 or im['w'] > 640: continue
        g = decode(d, im); s = 2 if g.width <= 160 else 1; g = g.resize((g.width*s, g.height*s), Image.NEAREST)
        if x + g.width + 4 > W: x = 0; y += rowh + 14; rowh = 0
        cells.append((x, y, g, im['i'])); x += g.width + 4; rowh = max(rowh, g.height)
    out = Image.new('L', (W, y + rowh + 16), 90); dr = ImageDraw.Draw(out)
    for x, y, g, i in cells: out.paste(g, (x, y + 10)); dr.text((x, y), str(i), fill=255)
    out.save(sys.argv[3]); print(len(ims), 'images')
