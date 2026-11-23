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
DUR = 15.4
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
PAD = 736 if PORT else 0
if PAD:
    def padsky(img):
        top = img[:200].astype(np.float32)
        g = (top[0] - top[199]) / 199.0                       # gradiente verticale per colonna
        rows = np.arange(PAD, 0, -1, dtype=np.float32)[:, None, None]
        ext = np.clip(top[0][None] + g[None] * rows * 0.8, 0, 255)
        ext = cv2.GaussianBlur(ext, (0, 0), 3)
        return np.concatenate([ext.astype(np.uint8), img], 0)
    for n in ('p0', 'p1', 'p2', 'p3'):
        L4[n] = padsky(L4[n])
    for n in ('glow', 'bloom'):
        L4[n] = np.concatenate([np.zeros((PAD,) + L4[n].shape[1:], np.uint8), L4[n]], 0)
    for n in ('Ts', 'Tf', 'Ton'):
        T4[n] = np.concatenate([np.full((PAD, T4[n].shape[1]), np.inf, np.float32), T4[n]], 0)
    T4['gm'] = np.concatenate([np.zeros((PAD, T4['gm'].shape[1]), np.float32), T4['gm']], 0)
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

def render_crop(t, cx, cy, h, w, OW_, OH_):
    cx = min(max(cx, w / 2), PW - w / 2); cy = min(max(cy, h / 2), PH - h / 2)
    lv = 2 if h / OH_ >= 2.0 else 1
    L, T = (L2, T2) if lv == 2 else (L4, T4)
    s4 = 1 / lv
    x0, y0 = (cx - w / 2) * s4, (cy - h / 2) * s4
    ix0, iy0 = max(int(x0) - 2, 0), max(int(y0) - 2, 0)
    ix1, iy1 = min(int(x0 + w * s4) + 3, L['p0'].shape[1]), min(int(y0 + h * s4) + 3, L['p0'].shape[0])
    sl = (slice(iy0, iy1), slice(ix0, ix1))
    img = compose(t, L, T, sl)
    sc = OW_ / (w * s4)
    if sc < 1:
        img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        M = np.array([[1, 0, -(x0 - ix0) * sc], [0, 1, -(y0 - iy0) * sc]], np.float32); interp = cv2.INTER_LINEAR
    else:
        M = np.array([[sc, 0, -(x0 - ix0) * sc], [0, sc, -(y0 - iy0) * sc]], np.float32); interp = cv2.INTER_CUBIC
    return cv2.warpAffine(img, M, (OW_, OH_), flags=interp, borderMode=cv2.BORDER_REPLICATE)

def facade_frame(t, cx, cy, h):
    w = h * OW / OH
    if w <= PW:
        return render_crop(t, cx, cy, h, w, OW, OH)
    # orizzontale con edificio intero: pannello nitido + sfondo sfocato
    pw_px = int(round(PW / h * OH)) // 2 * 2
    panel = render_crop(t, PW / 2, cy, h, PW, pw_px, OH)
    bgw = OW; bgh = int(OH * 1.0)
    small = cv2.resize(panel, (max(pw_px // 6, 8), OH // 6), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(small, (OW, int(OW * OH / pw_px)), interpolation=cv2.INTER_LINEAR)
    oy = (bg.shape[0] - OH) // 2
    bg = cv2.GaussianBlur(bg[oy:oy + OH], (0, 0), 60) * 0.32 + BG * 0.25
    k = np.clip((PW / h * OH - OW * 0.0) / OW, 0, 1)
    X = int(OW * 0.62 + (OW * 0.5 - OW * 0.62) * np.clip((pw_px / OW - 0.42) / 0.58, 0, 1) - pw_px / 2)
    X = min(max(X, 0), OW - pw_px)
    out = bg.copy()
    feather = np.clip(np.minimum(np.arange(pw_px), np.arange(pw_px)[::-1]) / 50.0, 0, 1)[None, :, None]
    out[:, X:X + pw_px] = out[:, X:X + pw_px] * (1 - feather) + panel * feather
    return out

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
        return lerpk([(0, 1400, 2489, 4978), (10.0, 1400, 2560, 4700), (12.2, 1405, 2600, 4500), (15.4, 1420, 1990 + PAD, 2700)], t)
    return lerpk([(0, 1400, 2330, 3820), (10.0, 1400, 2300, 3550), (12.2, 1405, 2200, 3300), (15.4, 1420, 1990, 1750)], t)

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
    img = facade_frame(t, *facade_cam(t))
    fade = ss(0, 0.6, t)
    img = img * VIG
    img += GR[fi % 6][..., None] * 3.0
    img = BG + (img - BG) * fade
    return img.clip(0, 255).astype(np.uint8), {}

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
