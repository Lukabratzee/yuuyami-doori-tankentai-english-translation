#!/usr/bin/env python3
"""Find runs of Shift-JIS double-byte text. Usage: sjis_scan.py <file> [minchars] [base_hex]"""
import sys
d=open(sys.argv[1],'rb').read(); mn=int(sys.argv[2]) if len(sys.argv)>2 else 5; base=int(sys.argv[3],16) if len(sys.argv)>3 else 0
def ok(a,b):
    # kana, punctuation rows and level-1 kanji only (keeps false positives down)
    return ((a==0x81 and 0x40<=b<=0xac) or (a==0x82 and 0x4f<=b<=0xf1) or (a==0x83 and 0x40<=b<=0x96) or (0x88<=a<=0x97 and 0x40<=b<=0xfc)) and b!=0x7f
i=0;n=len(d);hits=0
while i<n-1:
    j=i;kana=0
    while j<n-1 and ok(d[j],d[j+1]):
        if d[j] in(0x82,0x83): kana+=1
        j+=2
    c=(j-i)//2
    if c>=mn and kana>=2:
        try: print('%08x %s'%(base+i,d[i:j].decode('cp932'))); hits+=1
        except: pass
        i=j
    else: i+=1
print('hits',hits,file=sys.stderr)
