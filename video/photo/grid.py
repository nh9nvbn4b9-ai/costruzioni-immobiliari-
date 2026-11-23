import sys
from PIL import Image, ImageDraw
x0,y0,x1,y1,sc,out=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
im=Image.open('src4x.png').crop((x0*4,y0*4,x1*4,y1*4)).resize((int((x1-x0)*sc),int((y1-y0)*sc)),Image.LANCZOS)
d=ImageDraw.Draw(im)
for x in range((x0//10)*10,x1+1,10):
    if x<x0: continue
    c=(255,0,0) if x%50==0 else (255,255,0,)
    d.line([((x-x0)*sc,0),((x-x0)*sc,im.height)],fill=c,width=1)
    if x%50==0: d.text(((x-x0)*sc+2,2),str(x),fill=(255,0,0))
for y in range((y0//10)*10,y1+1,10):
    if y<y0: continue
    c=(255,0,0) if y%50==0 else (255,255,0)
    d.line([(0,(y-y0)*sc),(im.width,(y-y0)*sc)],fill=c,width=1)
    if y%50==0: d.text((2,(y-y0)*sc+2),str(y),fill=(255,0,0))
im.save(out)
