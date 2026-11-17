"""Contact sheets of glyph tiles (dark ink on white, as a reader would expect).  Tile palette: 15 transparent, 14 white ink, low = dark fringe."""
from PIL import Image, ImageDraw
def timg(t):
    px = bytes(255 if v == 15 else max(0, 235 - v * 17) if v >= 6 else 225 for b in t for v in (b & 15, b >> 4))
    return Image.frombytes('L', (16, 16), px)
def sheet(tiles, path, cols=20, scale=4, start=0):
    cw = 16*scale + 6; ch = 16*scale + 14; rows = (len(tiles) + cols - 1) // cols
    img = Image.new('L', (cols*cw + 34, rows*ch + 4), 190); dr = ImageDraw.Draw(img)
    for i, t in enumerate(tiles):
        x = 34 + (i % cols)*cw; y = 2 + (i // cols)*ch
        img.paste(timg(t).resize((16*scale, 16*scale), Image.LANCZOS), (x + 3, y + 12))
        if i % cols == 0: dr.text((1, y + 30), str(start + i), fill=0)
        dr.text((x + 3, y), str(i % cols), fill=70)
    img.save(path)
