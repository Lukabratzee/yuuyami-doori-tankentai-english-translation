#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint8_t F[256],B[256]; static uint32_t EDC[256];
static void init(){for(int i=0;i<256;i++){int j=((i<<1)^((i&0x80)?0x11D:0))&0xFF;F[i]=j;B[i^j]=i;uint32_t e=i;for(int k=0;k<8;k++)e=(e>>1)^((e&1)?0xD8018001u:0);EDC[i]=e;}}
static uint32_t edc(const uint8_t*d,int n){uint32_t e=0;while(n--)e=(e>>8)^EDC[(e^*d++)&0xFF];return e;}
static void ecc(const uint8_t*src,int mc,int nc,int mm,int mi,uint8_t*out){int size=mc*nc;for(int m=0;m<mc;m++){int idx=(m>>1)*mm+(m&1);uint8_t a=0,b=0;for(int k=0;k<nc;k++){uint8_t t=src[idx];idx+=mi;if(idx>=size)idx-=size;a=F[a^t];b^=t;}a=B[F[a]^b];out[m]=a;out[m+mc]=a^b;}}
static int bcd(int x){return (x/10)*16+x%10;}
int main(int c,char**v){init();FILE*f=fopen(v[1],"rb");uint8_t s[2352];long lba=0,bad_sync=0,bad_hdr=0,bad_edc=0,bad_ecc=0,f1=0,f2=0,other=0;
 while(fread(s,1,2352,f)==2352){
  static const uint8_t sy[12]={0,255,255,255,255,255,255,255,255,255,255,0};
  if(memcmp(s,sy,12)){bad_sync++;}
  long l=lba+150;int m=l/4500,sec=(l/75)%60,fr=l%75;
  if(s[12]!=bcd(m)||s[13]!=bcd(sec)||s[14]!=bcd(fr)||s[15]!=2){bad_hdr++; if(bad_hdr<5)printf("hdr lba %ld\n",lba);}
  int sub=s[18];
  if(s[16]!=s[20]||s[17]!=s[21]||s[18]!=s[22]||s[19]!=s[23])bad_hdr++;
  if(!(sub&0x20)){f1++;
    uint32_t e=edc(s+16,2056);uint32_t g=s[2072]|s[2073]<<8|s[2074]<<16|(uint32_t)s[2075]<<24;
    if(e!=g){bad_edc++;if(bad_edc<5)printf("edc lba %ld\n",lba);}
    uint8_t src[4+2060+172];memset(src,0,4);memcpy(src+4,s+16,2060);uint8_t p[172],q[104];
    ecc(src,86,24,2,86,p);memcpy(src+4+2060,p,172);ecc(src,52,43,86,88,q);
    if(memcmp(p,s+2076,172)||memcmp(q,s+2248,104)){bad_ecc++;if(bad_ecc<5)printf("ecc lba %ld\n",lba);}
  } else {f2++; uint32_t e=edc(s+16,2332);uint32_t g=s[2348]|s[2349]<<8|s[2350]<<16|(uint32_t)s[2351]<<24; if(g&&e!=g){bad_edc++;if(bad_edc<5)printf("f2edc lba %ld\n",lba);}}
  lba++;}
 printf("sectors %ld form1 %ld form2 %ld bad_sync %ld bad_hdr %ld bad_edc %ld bad_ecc %ld\n",lba,f1,f2,bad_sync,bad_hdr,bad_edc,bad_ecc);}
