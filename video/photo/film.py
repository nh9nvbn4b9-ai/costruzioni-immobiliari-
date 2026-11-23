"""Montaggio del film della Home: costruzione da foto reale -> sera -> pianta -> tour.

Uso: python film.py --orient portrait|landscape --out base.mp4 [--preview 3.0,7.5]"""
import argparse, json, math, subprocess, sys, os
import numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/work')

ap = argparse.ArgumentParser()
ap.add_argument('--orient', default='portrait')
ap.add_argument('--out', default='base.mp4')
ap.add_argument('--preview', default='')
ap.add_argument('--fps', type=int, default=24)
args = ap.parse_args()
PORT = args.orient == 'portrait'
OW, OH = (1080, 1920) if PORT else (1920, 1080)
FPS = args.fps
DUR = 33.5
BG = np.array([20, 15, 12], np.float32)
os.chdir('/tmp/claude-0/work')

def ss(a, b, t):
    x = min(max((t - a) / (b - a), 0.0), 1.0)
    return x * x * (3 - 2 * x)
def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

# ---------- strati della facciata (4x) + piramide 2x ----------
names = ['p0', 'p1', 'p2', 'p3', 'glow', 'bloom']
L4 = {n: cv2.imread(f'{n}_4x.png') for n in names}
T4 = {'Ts': np.load('Ts.npy').astype(np.float32), 'Tf': np.load('Tf.npy').astype(np.float32),
      'Ton': np.load('Ton.npy').astype(np.float32), 'gm': np.load('glow_mask.npy').astype(np.float32)}
PH, PW = L4['p0'].shape[:2]
L2 = {n: cv2.resize(v, (PW // 2, PH // 2), interpolation=cv2.INTER_AREA) for n, v in L4.items()}
T2 = {n: cv2.resize(v, (PW // 2, PH // 2), interpolation=cv2.INTER_NEAREST if n != 'gm' else cv2.INTER_AREA) for n, v in T4.items()}

def compose(t, L, T, sl):
    f = lambda n: L[n][sl].astype(np.float32)
    img = f('p0')
    a = np.clip((t - T['Ts'][sl]) / 0.08, 0, 1)[..., None]
    if a.max() > 0: img += (f('p1') - img) * a
    b = np.clip((t - T['Tf'][sl]) / 0.15, 0, 1)[..., None]
    if b.max() > 0: img += (f('p2') - img) * b
    g = ss(9.0, 9.6, t)
    if g > 0: img += (f('p2') - img) * g
    d = ss(10.0, 11.4, t)
    if d > 0: img += (f('p3') - img) * d
    if t > 11.5:
        lit = (np.clip((t - 11.6 - T['Ton'][sl]) / 0.3, 0, 1) * T['gm'][sl])[..., None]
        img += (f('glow') - img) * lit
        img += f('bloom') * ss(11.6, 12.5, t)
    return img

def facade_frame(t, cx, cy, h):
    """camera virtuale: centro (cx, cy) e altezza h in pixel della piastra 4x."""
    w = h * OW / OH
    if w > PW: w = PW; h = w * OH / OW
    cx = min(max(cx, w / 2), PW - w / 2); cy = min(max(cy, h / 2), PH - h / 2)
    lv = 2 if h / OH >= 2.0 else 1
    L, T = (L2, T2) if lv == 2 else (L4, T4)
    s4 = 1 / lv
    x0, y0 = (cx - w / 2) * s4, (cy - h / 2) * s4
    ix0, iy0 = max(int(x0) - 2, 0), max(int(y0) - 2, 0)
    ix1, iy1 = min(int(x0 + w * s4) + 3, L['p0'].shape[1]), min(int(y0 + h * s4) + 3, L['p0'].shape[0])
    sl = (slice(iy0, iy1), slice(ix0, ix1))
    img = compose(t, L, T, sl)
    sc = OW / (w * s4)
    M = np.array([[sc, 0, -(x0 - ix0) * sc], [0, sc, -(y0 - iy0) * sc]], np.float32)
    interp = cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC
    if sc < 1:
        img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        M = np.array([[1, 0, -(x0 - ix0) * sc], [0, 1, -(y0 - iy0) * sc]], np.float32)
        interp = cv2.INTER_LINEAR
    return cv2.warpAffine(img, M, (OW, OH), flags=interp, borderMode=cv2.BORDER_REPLICATE)

# ---------- regia della facciata ----------
def lerpk(keys, t):
    if t <= keys[0][0]: return keys[0][1:]
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if t <= tb:
            u = eio((t - ta) / (tb - ta))
            return [x + (y - x) * u for x, y in zip(a, b)]
    return keys[-1][1:]

TOPS = [(1.2, 966), (1.8, 782), (2.5, 660), (3.2, 512), (3.9, 370), (4.6, 232), (5.3, 150), (6.0, 150)]
def build_top(t):
    if t <= TOPS[0][0]: return TOPS[0][1]
    for (ta, ya), (tb, yb) in zip(TOPS, TOPS[1:]):
        if t <= tb: return ya + (yb - ya) * ss(ta, tb, t)
    return TOPS[-1][1]

def facade_cam(t):
    if PORT:
        return lerpk([(0, 1400, 2150, 4120), (10.0, 1400, 2070, 3720), (12.2, 1405, 2040, 3450), (14.6, 1420, 1990, 2300), (15.6, 1425, 1985, 1250)], t)
    H0 = PW * OH / OW
    if t < 9.3:
        top_edge = build_top(min(t, 6.0)) * 4 - 0.16 * H0
        cy_build = min(top_edge + H0 / 2, PH - H0 / 2 - 230)
        if t <= 6.0:
            return [1400, cy_build, H0]
        u = eio((t - 6.0) / 3.3)
        return [1400, cy_build + (2000 - cy_build) * u, H0]
    return lerpk([(9.3, 1400, 2000, H0), (12.2, 1405, 1995, H0), (14.6, 1420, 1990, H0 * 0.62), (15.6, 1425, 1985, H0 * 0.34)], t)

# ---------- pianta ----------
_pp = '/home/user/costruzioni-immobiliari-/video/blender/out/plan.png'
if not os.path.exists(_pp): _pp = _pp.replace('plan.png', 'plan_test.png')
plan = cv2.imread(_pp, cv2.IMREAD_UNCHANGED).astype(np.float32)
pa = plan[..., 3:4] / 255; prgb = plan[..., :3]
PLH, PLW = plan.shape[:2]
if PORT:
    base_w, base_c = OW * 0.94, (OW / 2, OH * 0.40)
else:
    base_w, base_c = OH * 0.86 * PLW / PLH, (OW * 0.62, OH / 2)
LIV = (0.25, 0.66)   # zona divano nella pianta (coordinate normalizzate)
def plan_xf(t):
    """restituisce scala (larghezza in px), punto della pianta (u,v) e dove sta sullo schermo (X,Y)."""
    s = 1.8 + (1.0 - 1.8) * eio((t - 14.8) / 1.4)
    s *= 1 + 0.04 * ss(16.2, 18.6, t)
    z = eio((t - 18.4) / 2.0)
    u, v = 0.5 + (LIV[0] - 0.5) * z, 0.5 + (LIV[1] - 0.5) * z
    X, Y = base_c[0] + (OW / 2 - base_c[0]) * z, base_c[1] + (OH / 2 - base_c[1]) * z
    s *= 1 + 1.5 * z ** 1.6
    return base_w * s, u, v, X, Y
def plan_frame(t):
    wpx, u, v, X, Y = plan_xf(t)
    sc = wpx / PLW
    M = np.array([[sc, 0, X - u * PLW * sc], [0, sc, Y - v * PLH * sc]], np.float32)
    interp = cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC
    rgb = cv2.warpAffine(prgb, M, (OW, OH), flags=cv2.INTER_LINEAR, borderValue=0)
    a = cv2.warpAffine(pa, M, (OW, OH), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    vg = 1 - 0.35 * (((xx - OW / 2) / OW) ** 2 + ((yy - OH / 2) / OH) ** 2) * 2
    bg = BG[None, None] * vg[..., None]
    # ombra morbida sotto il plastico
    sh = cv2.GaussianBlur(a, (0, 0), 18)[..., None] if a.ndim == 2 else cv2.GaussianBlur(a[..., 0], (0, 0), 18)[..., None]
    bg = bg * (1 - 0.6 * sh)
    return bg * (1 - a) + rgb * a, (X - u * PLW * sc, Y - v * PLH * sc, PLW * sc, PLH * sc)

# ---------- tour: foto reali con carrello in prospettiva (profondità a scatola) ----------
ROOMS = {
    'living': dict(img='living4x.png', vp=(600, 650), back=(-1e9, 205, 1e9, 1080)),
    'bagno': dict(img='bagno4x.png', vp=(600, 335), back=(370, 118, 862, 505)),
}
def depth(r, x, y):
    vx, vy = r['vp']; xl, yt, xr, yb = r['back']
    Z = np.ones_like(x)
    with np.errstate(divide='ignore', invalid='ignore'):
        if xl > -1e8: Z = np.where(x < xl, np.minimum(Z, (vx - xl) / np.maximum(vx - x, 1e-3)), Z)
        if xr < 1e8: Z = np.where(x > xr, np.minimum(Z, (xr - vx) / np.maximum(x - vx, 1e-3)), Z)
        Z = np.where(y < yt, np.minimum(Z, (vy - yt) / np.maximum(vy - y, 1e-3)), Z)
        Z = np.where(y > yb, np.minimum(Z, (yb - vy) / np.maximum(y - vy, 1e-3)), Z)
    return np.clip(Z, 0.12, 1)
def tour_frame(name, dz, cx, cy, ch):
    """cx, cy, ch: inquadratura nella foto (pixel originali); dz: avanzamento (frazione della profondità della parete)."""
    r = ROOMS[name]
    if 'im' not in r: r['im'] = cv2.imread(r['img'])
    im = r['im']; S = im.shape[1] / 1179
    cw = ch * OW / OH
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    qx = cx - cw / 2 + xx / OW * cw; qy = cy - ch / 2 + yy / OH * ch
    vx, vy = r['vp']
    px, py = qx.copy(), qy.copy()
    for _ in range(4):
        Z = depth(r, px, py)
        k = (Z - dz) / Z
        px = vx + (qx - vx) * k; py = vy + (qy - vy) * k
    return cv2.remap(im, (px * S).astype(np.float32), (py * S).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32)

def tour(t):
    out = None
    # soggiorno 20.2 -> 26.8
    if t < 26.9:
        u = (t - 19.5) / 7.3
        dz = -0.06 + 0.30 * eio(u)
        if PORT:
            ch = 1542 * 0.98; cx = 470 + 240 * eio(u); cy = 771
        else:
            ch = 1179 * OH / OW; cx = 589; cy = 420 + 650 * eio(u)
        out = tour_frame('living', dz, cx, cy, ch)
    if t > 26.0:
        u = (t - 26.0) / 7.5
        dz = 0.0 + 0.34 * eio(u)
        if PORT:
            ch = 727 * 0.98; cx = 380 + 420 * eio(u); cy = 360
        else:
            ch = 1179 * OH / OW * 0.98; cx = 589; cy = 360
        b = tour_frame('bagno', dz, cx, cy, ch)
        x = ss(26.0, 26.9, t)
        out = b if out is None else out * (1 - x) + b * x
    return out

# ---------- grana e vignetta ----------
rng = np.random.default_rng(1)
GR = [cv2.GaussianBlur(rng.normal(0, 1, (OH, OW)).astype(np.float32), (0, 0), 0.7) for _ in range(6)]
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.16 * (((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2) ** 1.4).clip(0.55, 1)[..., None]

def frame(t, fi):
    meta = {}
    if t < 15.6:
        img = facade_frame(t, *facade_cam(t))
    if 14.8 <= t < 20.6:
        pf, rect = plan_frame(t)
        meta['plan'] = rect
        x = ss(14.8, 15.6, t)
        img = pf if t >= 15.6 else img * (1 - x) + pf * x
        if t < 15.6:
            img += np.array([40, 70, 110], np.float32) * 0.35 * math.sin(math.pi * x)
    if t >= 19.5:
        tf = tour(t)
        x = ss(19.5, 20.6, t)
        img = tf if t >= 20.6 else img * (1 - x) + tf * x
    fade = ss(0, 0.6, t) * (1 - ss(DUR - 0.8, DUR, t))
    img = img * VIG
    img += GR[fi % 6][..., None] * 3.0
    img = BG + (img - BG) * fade
    return img.clip(0, 255).astype(np.uint8), meta

if args.preview:
    for tt in [float(x) for x in args.preview.split(',')]:
        im, _ = frame(tt, 0)
        cv2.imwrite(f'/tmp/claude-0/work/prev_{args.orient}_{tt:05.2f}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    sys.exit()

N = int(DUR * FPS)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
metas = []
for i in range(N):
    im, meta = frame(i / FPS, i)
    ff.stdin.write(im.tobytes()); metas.append(meta.get('plan'))
    if i % 48 == 0: print(i, N, flush=True)
ff.stdin.close(); ff.wait()
json.dump(dict(fps=FPS, frames=N, plan=metas), open(args.out.replace('.mp4', '.json'), 'w'))
print('done')
