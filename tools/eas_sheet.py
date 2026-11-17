import sys
sys.path.insert(0,'tools'); import eas
from PIL import Image, ImageDraw
def sheet(leafp, idxs, out, scale=3, W=1500, d=None):
    if d is None: d,_=eas.leaf(leafp)
    ims=eas.images(d); x=y=0; rowh=0; cells=[]
    for i in idxs:
        im=ims[i]
        if not im['w'] or not im['h']: continue
        rows=eas.indices(d,im); bg=rows[0][0]
        if im['bpp']==8: px=[v for r in rows for v in r]
        elif bg==15: px=[255 if v==15 else v*14 for r in rows for v in r]
        else: px=[v*17 for r in rows for v in r]
        g=Image.frombytes('L',(im['w'],im['h']),bytes(px)).resize((im['w']*scale,im['h']*scale),Image.NEAREST)
        if x+g.width+6>W: x=0; y+=rowh+16; rowh=0
        cells.append((x,y,g,i)); x+=g.width+6; rowh=max(rowh,g.height)
    o=Image.new('L',(W,y+rowh+18),90); dr=ImageDraw.Draw(o)
    for x,y,g,i in cells: o.paste(g,(x,y+12)); dr.text((x,y),str(i),fill=255)
    o.save(out)
if __name__=='__main__':
    a,b=map(int,sys.argv[3].split('-')); sheet(sys.argv[1],range(a,b+1),sys.argv[2],int(sys.argv[4]) if len(sys.argv)>4 else 3)
