"""Latin glyph tiles in the game's format: 16x16, 4bpp, low nibble = left pixel.
Palette (file's own CLUT): 15 = transparent, 14 = white ... 1 = near black, 0 = black.  So ink is HIGH, and the
original glyphs carry a dark fringe.  (Confirmed in DuckStation 2026-11-15: ink=0 gave hollow, dotted letters.)
glyph(ch) -> (128-byte tile, advance_px)"""
from PIL import Image, ImageDraw, ImageFont
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf', 11)   # condensed: only ~265 of the 320 px are visible
BASELINE = 12
_cache = {}
def glyph(ch):
    if ch in _cache: return _cache[ch]
    img = Image.new('L', (16, 16), 255)
    if ch != ' ':
        ImageDraw.Draw(img).text((0, BASELINE), ch, font=FONT, fill=0, anchor='ls')
    adv = 4 if ch == ' ' else min(16, max(2, round(FONT.getlength(ch))))
    cov = [255 - v for v in img.tobytes()]                       # 0..255 ink coverage
    px = [15 if c < 40 else min(14, 2 + c * 12 // 255) for c in cov]
    for y in range(16):                                          # 1px dark fringe so text survives bright backgrounds
        for x in range(16):
            if px[y*16+x] == 15 and any(0 <= x+dx < 16 and 0 <= y+dy < 16 and cov[(y+dy)*16+x+dx] >= 128 for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))): px[y*16+x] = 1
    tile = bytes(px[i] | (px[i+1] << 4) for i in range(0, 256, 2))
    _cache[ch] = (tile, adv); return _cache[ch]
if __name__ == '__main__':
    import sys
    s = 'The quick brown fox jumps over 0123456789 lazy dogs! "Yes?" - it\'s, OK...'
    img = Image.new('L', (420, 20), 255); x = 2
    for ch in s:
        t, adv = glyph(ch)
        g = Image.frombytes('L', (16, 16), bytes(v for b in t for v in ((b & 15) * 17, (b >> 4) * 17)))
        img.paste(Image.composite(g, img.crop((x, 2, x+16, 18)), Image.eval(g, lambda v: 255 if v < 255 else 0)), (x, 2)); x += adv
    img.resize((1260, 60), Image.NEAREST).save(sys.argv[1])
