import sys
from PIL import Image, ImageDraw
src, step, sc, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
im = Image.open(src).convert('RGB'); im = im.resize((int(im.width * sc), int(im.height * sc)))
d = ImageDraw.Draw(im)
for x in range(0, int(im.width / sc), step):
    d.line([(x * sc, 0), (x * sc, im.height)], fill=(255, 0, 0) if x % (step * 5) == 0 else (255, 255, 0), width=1)
    if x % (step * 5) == 0: d.text((x * sc + 2, 2), str(x), fill=(255, 0, 0))
for y in range(0, int(im.height / sc), step):
    d.line([(0, y * sc), (im.width, y * sc)], fill=(255, 0, 0) if y % (step * 5) == 0 else (255, 255, 0), width=1)
    if y % (step * 5) == 0: d.text((2, y * sc + 2), str(y), fill=(255, 0, 0))
im.save(out)
