"""Texture fotografiche-procedurali generate con PIL (nessuna immagine esterna)."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), 'tex')


def noise_img(w, h, base, amp, n, size, seed):
    rnd = random.Random(seed)
    im = Image.new('RGB', (w, h), base)
    d = ImageDraw.Draw(im, 'RGBA')
    for _ in range(n):
        v = (rnd.random() - 0.5) * amp
        c = (255, 255, 255, int(v * 255)) if v > 0 else (0, 0, 0, int(-v * 255))
        x, y = rnd.random() * w, rnd.random() * h
        s = size * (0.4 + rnd.random())
        d.rectangle([x, y, x + s, y + s], fill=c)
    return im


def facade(name, wall, shutter, seed):
    """Facciata milanese 4x4 moduli (12.8 m): colore, rugosità, emissione notturna."""
    rnd = random.Random(seed)
    S = 1024
    m = S // 4
    col = noise_img(S, S, wall, 0.10, 30000, 4, seed).filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(col, 'RGBA')
    rough = Image.new('L', (S, S), 225)
    dr = ImageDraw.Draw(rough)
    em = Image.new('RGB', (S, S), (0, 0, 0))
    de = ImageDraw.Draw(em)
    for r in range(4):
        for k in range(4):
            x, y = k * m, r * m
            # marcapiano e zoccolatura
            d.rectangle([x, y + m - 14, x + m, y + m - 6], fill=(255, 255, 255, 50))
            d.rectangle([x, y + m - 6, x + m, y + m - 4], fill=(0, 0, 0, 40))
            wx, wy, ww, wh = x + 84, y + 46, 88, 160
            # cornice in pietra
            d.rectangle([wx - 10, wy - 12, wx + ww + 10, wy + wh + 14], fill=(236, 230, 219, 255))
            d.rectangle([wx - 14, wy + wh + 6, wx + ww + 14, wy + wh + 16], fill=(214, 207, 196, 255))
            # vetro con riflesso del cielo
            for yy in range(wh):
                t = yy / wh
                c = (int(118 - 70 * t), int(138 - 72 * t), int(156 - 70 * t), 255)
                d.line([wx, wy + yy, wx + ww, wy + yy], fill=c)
            d.rectangle([wx + ww // 2 - 2, wy, wx + ww // 2 + 2, wy + wh], fill=(225, 220, 210, 255))
            d.rectangle([wx, wy + 52, wx + ww, wy + 55], fill=(225, 220, 210, 255))
            dr.rectangle([wx, wy, wx + ww, wy + wh], fill=20)
            # tende interne
            if rnd.random() < 0.5:
                d.rectangle([wx + 4, wy + 4, wx + 22, wy + wh - 4], fill=(240, 236, 228, 140))
            closed = rnd.random() < 0.22
            sc = shutter
            if closed:
                d.rectangle([wx, wy, wx + ww, wy + wh], fill=sc + (255,))
                for yy in range(wy + 6, wy + wh, 7):
                    d.line([wx, yy, wx + ww, yy], fill=(0, 0, 0, 70), width=2)
                dr.rectangle([wx, wy, wx + ww, wy + wh], fill=200)
            else:
                for sx in (wx - 50, wx + ww + 8):
                    d.rectangle([sx, wy, sx + 42, wy + wh], fill=sc + (255,))
                    for yy in range(wy + 6, wy + wh, 7):
                        d.line([sx, yy, sx + 42, yy], fill=(0, 0, 0, 70), width=2)
                    d.line([sx + 42, wy, sx + 42, wy + wh], fill=(0, 0, 0, 90), width=3)
                if rnd.random() < 0.42:
                    v = rnd.random()
                    de.rectangle([wx + 2, wy + 2, wx + ww - 2, wy + wh - 2], fill=(255, int(196 + 30 * v), int(130 + 40 * v)))
            # balconcino con ringhiera
            if r % 2 == 0 and k % 2 == 1:
                d.rectangle([wx - 26, wy + wh - 4, wx + ww + 26, wy + wh + 6], fill=(205, 198, 188, 255))
                d.rectangle([wx - 26, wy + wh - 56, wx + ww + 26, wy + wh - 52], fill=(30, 30, 30, 230))
                for xx in range(wx - 26, wx + ww + 26, 8):
                    d.line([xx, wy + wh - 56, xx, wy + wh - 4], fill=(30, 30, 30, 220), width=2)
    # sporcizia verticale
    for _ in range(60):
        x = rnd.random() * S
        d.line([x, 0, x + rnd.random() * 6, S], fill=(60, 50, 40, 10), width=int(2 + rnd.random() * 10))
    col.save(os.path.join(OUT, f'{name}.jpg'), quality=92)
    rough.filter(ImageFilter.GaussianBlur(1)).save(os.path.join(OUT, f'{name}_r.png'))
    em.filter(ImageFilter.GaussianBlur(1.5)).save(os.path.join(OUT, f'{name}_e.jpg'), quality=92)


def shop():
    rnd = random.Random(5)
    W, H = 1024, 320  # 12.8 x 4 m
    im = noise_img(W, H, (118, 110, 100), 0.12, 8000, 3, 5)
    d = ImageDraw.Draw(im, 'RGBA')
    em = Image.new('RGB', (W, H), (0, 0, 0))
    de = ImageDraw.Draw(em)
    cols = [(110, 40, 34), (40, 74, 58), (44, 60, 92), (92, 74, 40), (60, 60, 60)]
    for x in range(0, W, 256):
        d.rectangle([x + 22, 64, x + 234, 300], fill=(28, 36, 44, 255))
        d.rectangle([x + 26, 68, x + 80, 296], fill=(255, 255, 255, 28))
        c = rnd.choice(cols)
        d.rectangle([x + 14, 28, x + 242, 62], fill=c + (255,))
        for s in range(x + 14, x + 242, 26):
            d.rectangle([s, 28, s + 13, 62], fill=(255, 255, 255, 60))
        if rnd.random() < 0.75:
            de.rectangle([x + 22, 64, x + 234, 300], fill=(255, 214, 160))
    im.save(os.path.join(OUT, 'shop.jpg'), quality=92)
    em.save(os.path.join(OUT, 'shop_e.jpg'), quality=92)


def roof_tiles():
    rnd = random.Random(9)
    S = 1024
    im = Image.new('RGB', (S, S), (150, 74, 50))
    d = ImageDraw.Draw(im, 'RGBA')
    rh = 32
    for y in range(0, S, rh):
        off = 20 if (y // rh) % 2 else 0
        for x in range(-40, S, 40):
            v = rnd.random() * 34 - 17
            d.rounded_rectangle([x + off, y, x + off + 38, y + rh - 5], radius=8, fill=(int(158 + v), int(80 + v * 0.6), int(54 + v * 0.4)))
            if rnd.random() < 0.08:
                d.rectangle([x + off, y, x + off + 38, y + rh - 5], fill=(60, 60, 50, 60))
        d.rectangle([0, y + rh - 5, S, y + rh], fill=(50, 15, 5, 120))
    im = Image.blend(im, noise_img(S, S, (128, 128, 128), 0.25, 20000, 3, 9), 0.12)
    im.save(os.path.join(OUT, 'tiles_roof.jpg'), quality=92)


def paving():
    rnd = random.Random(3)
    S = 1024
    n = 8
    s = S // n
    im = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(im, 'RGBA')
    for i in range(n):
        for j in range(n):
            v = 182 + rnd.random() * 22
            d.rectangle([i * s, j * s, i * s + s, j * s + s], fill=(int(v), int(v - 5), int(v - 13)))
    im = Image.blend(im, noise_img(S, S, (128, 128, 128), 0.3, 30000, 2, 3), 0.2)
    d = ImageDraw.Draw(im, 'RGBA')
    for i in range(n + 1):
        d.line([i * s, 0, i * s, S], fill=(70, 64, 58, 150), width=4)
        d.line([0, i * s, S, i * s], fill=(70, 64, 58, 150), width=4)
    im.save(os.path.join(OUT, 'paving.jpg'), quality=92)


def wood():
    rnd = random.Random(21)
    S = 2048  # 2 x 2 m
    im = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(im, 'RGBA')
    pw = 184
    for y in range(0, S, pw):
        x = -rnd.random() * 800
        while x < S:
            ln = 520 + rnd.random() * 840
            v = rnd.random() * 26 - 13
            d.rectangle([x, y, x + ln, y + pw], fill=(int(176 + v), int(134 + v * 0.8), int(90 + v * 0.6)))
            for _ in range(14):
                gy = y + 8 + rnd.random() * (pw - 16)
                pts = [(x + t * ln / 10, gy + math.sin(t * 0.9 + rnd.random()) * 4) for t in range(11)]
                d.line(pts, fill=(95, 58, 28, int(30 + rnd.random() * 40)), width=2)
            if rnd.random() < 0.3:
                kx, ky = x + rnd.random() * ln, y + pw / 2
                d.ellipse([kx - 10, ky - 6, kx + 10, ky + 6], fill=(90, 55, 28, 120))
            d.line([x, y, x, y + pw], fill=(60, 35, 15, 140), width=3)
            x += ln
        d.line([0, y, S, y], fill=(60, 35, 15, 120), width=3)
    im.save(os.path.join(OUT, 'wood.jpg'), quality=92)


def tiles():
    rnd = random.Random(31)
    S = 1024
    n = 3
    s = S // n
    im = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(im, 'RGBA')
    for i in range(n):
        for j in range(n):
            v = 212 + rnd.random() * 12
            d.rectangle([i * s, j * s, i * s + s, j * s + s], fill=(int(v), int(v - 2), int(v - 7)))
            for _ in range(3):
                pts = [(i * s + rnd.random() * s, j * s)]
                for t in range(1, 8):
                    pts.append((pts[-1][0] + (rnd.random() - 0.5) * 60, j * s + t * s / 7))
                d.line(pts, fill=(150, 145, 140, 60), width=2)
    for i in range(n + 1):
        d.line([i * s, 0, i * s, S], fill=(170, 164, 156), width=6)
        d.line([0, i * s, S, i * s], fill=(170, 164, 156), width=6)
    im.save(os.path.join(OUT, 'tiles.jpg'), quality=92)


def marble():
    rnd = random.Random(41)
    S = 1024
    im = Image.new('RGB', (S, S), (242, 240, 235))
    d = ImageDraw.Draw(im, 'RGBA')
    for _ in range(18):
        x, y = rnd.random() * S, 0
        pts = [(x, y)]
        while y < S:
            x += (rnd.random() - 0.5) * 80
            y += 30 + rnd.random() * 50
            pts.append((x, y))
        d.line(pts, fill=(120, 120, 128, int(40 + rnd.random() * 60)), width=int(1 + rnd.random() * 3))
    im.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(OUT, 'marble.jpg'), quality=92)


def rug(name, a, b, kind):
    S = 1024
    im = noise_img(S, S, a, 0.12, 60000, 2, 7)
    d = ImageDraw.Draw(im)
    if kind == 0:
        d.rectangle([48, 48, S - 48, S - 48], outline=b, width=12)
        for i in range(6):
            y0 = 160 + i * 140
            pts = [(120 + k * 40, y0 + (36 if k % 2 else -36)) for k in range(20)]
            d.line(pts, fill=b, width=6)
    else:
        for x in range(80, S, 112):
            d.line([x, 0, x, S], fill=b, width=20)
    im.save(os.path.join(OUT, f'{name}.jpg'), quality=92)


def deck():
    rnd = random.Random(51)
    S = 1024
    im = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(im)
    bw = 72
    for x in range(0, S, bw):
        v = rnd.random() * 20 - 10
        d.rectangle([x, 0, x + bw - 6, S], fill=(int(126 + v), int(98 + v), int(74 + v)))
        d.rectangle([x + bw - 6, 0, x + bw, S], fill=(30, 20, 10))
    im.save(os.path.join(OUT, 'deck.jpg'), quality=92)


def hob():
    S = 512
    im = Image.new('RGB', (S, S), (18, 19, 20))
    d = ImageDraw.Draw(im)
    for x, y, r in [(140, 140, 88), (372, 140, 68), (140, 372, 68), (372, 372, 88)]:
        d.ellipse([x - r, y - r, x + r, y + r], outline=(92, 95, 99), width=6)
    im.save(os.path.join(OUT, 'hob.jpg'), quality=92)


def art():
    S = 512
    im = Image.new('RGB', (S, S), (200, 70, 42))
    d = ImageDraw.Draw(im)
    d.rectangle([150, 120, 360, 400], fill=(233, 162, 59))
    d.ellipse([200, 180, 310, 290], fill=(150, 40, 30))
    noise_img(S, S, (128, 128, 128), 0.2, 9000, 3, 2)
    im.save(os.path.join(OUT, 'art.jpg'), quality=92)


def main():
    os.makedirs(OUT, exist_ok=True)
    facade('fac0', (215, 178, 124), (74, 90, 60), 11)
    facade('fac1', (201, 128, 95), (91, 59, 43), 23)
    facade('fac2', (231, 220, 198), (63, 81, 65), 37)
    facade('fac3', (184, 179, 171), (67, 70, 74), 53)
    shop()
    roof_tiles()
    paving()
    wood()
    tiles()
    marble()
    rug('rug1', (217, 205, 184), (59, 58, 55), 0)
    rug('rug2', (185, 194, 196), (125, 106, 85), 1)
    deck()
    hob()
    art()


if __name__ == '__main__':
    main()
