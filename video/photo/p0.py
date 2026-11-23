"""Piastra P0 a 4x: il lotto vuoto (edificio rimosso)."""
import sys, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/work')
from geom import *
SC4 = 4
im = cv2.imread('src4x.png')
H, W = im.shape[:2]
rng = np.random.default_rng(7)
Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
xo, yo = Xg / SC4, Yg / SC4   # coordinate originali


def F(poly): return fill(poly, sc=SC4) > 127


# ---------- maschere ----------
slabs = np.zeros((H, W), bool)
for s in SLABS:
    m = F(slab_poly(s))
    sh = np.zeros_like(m); sh[22 * SC4:] = m[:-22 * SC4]   # il sottobalcone curvo alle estremità
    slabs |= m | sh
bld = slabs.copy()
for p in (ROOF, GROUND, LEFT_PLANTER, [(84, 742), (135, 742), (135, 792), (84, 792)]): bld |= F(p)
for m in band_masks(sc=SC4): bld |= m > 127
p1 = cv2.resize(cv2.imread('m_plant_raw.png', 0), (W0, H0), interpolation=cv2.INTER_AREA) > 100
b1 = cv2.resize(bld.astype(np.uint8), (W0, H0), interpolation=cv2.INTER_AREA) > 0
z1 = cv2.dilate(b1.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (121, 121))) > 0
y1, x1_ = np.mgrid[0:H0, 0:W0]
z1 &= ~((x1_ > 648) & (y1 > 640)) & ~((x1_ < 86) & (y1 > 700))
n, lab = cv2.connectedComponents(p1.astype(np.uint8), connectivity=8)
keep = np.unique(lab[z1 & p1]); keep = keep[keep > 0]
pl1 = np.isin(lab, keep) & ~((x1_ > 648) & (y1 > 640)) & ~((x1_ < 86) & (y1 > 700))
pl = cv2.resize(pl1.astype(np.uint8) * 255, (W, H), interpolation=cv2.INTER_LINEAR) > 100
plant = cv2.resize(cv2.imread('m_plant_raw.png', 0), (W, H)) > 127
pl = (pl & plant) | (cv2.erode(pl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
pl = cv2.morphologyEx(pl.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8)) > 0
R = cv2.dilate((bld | pl).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 0
# vicino all'edificio: via tutto ciò che non è cielo e non appartiene ai vicini
sky_raw = cv2.resize(cv2.imread('m_sky_raw.png', 0), (W, H)) > 127
near = cv2.dilate(cv2.resize(R.astype(np.uint8), (W0, H0), interpolation=cv2.INTER_AREA), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
near = cv2.resize(near, (W, H)) > 0
neigh = ((xo < 92) & (yo > 425)) | ((xo > 612) & (yo > np.array([line_y(RW_TOP, x) for x in [0]])[0] * 0 + (RW_TOP[1] + (VP[1] - RW_TOP[1]) * (xo - RW_TOP[0]) / (VP[0] - RW_TOP[0])) - 6) & ~R) | ((xo > 648) & (yo > 640)) | (yo > 966)
R |= near & ~sky_raw & ~neigh
R = cv2.morphologyEx(R.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
cv2.imwrite('m_building4x.png', R.astype(np.uint8) * 255)
cv2.imwrite('m_plants4x.png', pl.astype(np.uint8) * 255)


def fbm(sx, sy, octaves=6, base=8, seed=0):
    """rumore frattale continuo campionato su coordinate (sx, sy) arbitrarie."""
    r = np.random.default_rng(seed)
    acc = np.zeros(sx.shape, np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        g = r.random((256, 256)).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 1.0)
        f = base * 2 ** o
        acc += amp * cv2.remap(g, ((sx * f) % 256).astype(np.float32), ((sy * f) % 256).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
        tot += amp; amp *= 0.5
    return acc / tot


# ---------- cielo ----------
sky = (cv2.resize(cv2.imread('m_sky_raw.png', 0), (W, H)) > 127) & ~R
sk = cv2.erode(sky.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
ys, xs = np.nonzero(sk)
sel = rng.choice(len(ys), 80000, replace=False)
ysn, xsn = ys[sel] / H, xs[sel] / W
def basis(x, y): return np.stack([np.ones_like(x), x, y, x * y, x * x, y * y, y ** 3, x * x * y], -1)
Yc = np.minimum(Yg / H, 640 / 1061)
Af = basis(Xg / W, Yc)
skyimg = np.zeros((H, W, 3), np.float32)
for c in range(3):
    coef, *_ = np.linalg.lstsq(basis(xsn, ysn), im[..., c][ys[sel], xs[sel]].astype(np.float32), rcond=None)
    skyimg[..., c] = Af @ coef
haze = np.clip((yo - 640) / 260, 0, 1)[..., None]
skyimg = skyimg * (1 - 0.18 * haze) + np.array([235, 226, 214], np.float32) * 0.18 * haze
skyimg += rng.normal(0, 1.0, skyimg.shape)
out = im.astype(np.float32)
skyall = cv2.GaussianBlur(((sky_raw & ~R) | R).astype(np.float32), (0, 0), 2)
skyall = np.where(R, 1.0, skyall * (sky_raw | R))[..., None]
out = out * (1 - skyall) + skyimg * skyall

# ---------- pareti cieche dei vicini, in prospettiva ----------
def wall(poly, front_x, color, light, seed):
    m = F(poly)
    k = np.abs((xo - VP[0]) / (front_x - VP[0])).clip(0.05, 2)   # scala prospettica
    d = 1 / k                                                     # profondità
    hgt = (yo - VP[1]) / k                                        # altezza sul piano verticale
    n = fbm(d * 6, hgt / 90, 6, 4, seed)
    streak = fbm(d * 40, hgt / 900, 4, 4, seed + 1)
    tex = 0.93 + 0.10 * (n - 0.5) - 0.06 * np.clip(streak - 0.55, 0, 1)
    ao = 1 - 0.18 * np.clip((hgt - (966 - VP[1]) + 60) / 60, 0, 1)   # ombra alla base
    sh = light * (1 - 0.06 * (d - 1))
    col = np.array(color, np.float32)[None, None] * (tex * ao * sh)[..., None]
    out[m] = col[m]
    return m
lw = wall(LWALL, 0, [214, 224, 232], 1.0, 11)
rw = wall(RWALL, 700, [170, 172, 172], 1.0, 21)
RW2 = [(700, RW_TOP[1]), (636, line_y(RW_TOP, 636)), (636, line_y(RW_BOT, 636)), (700, RW_BOT[1])]
m2 = F(RW2) & R
o_save = out.copy(); rw2 = wall(RW2, 700, [170, 172, 172], 1.0, 21)
out[~m2 & rw2] = o_save[~m2 & rw2]; rw |= m2
# copertine sui muri
for (p, fx) in ((LW_TOP, 0), (RW_TOP, 700)):
    xs_ = np.linspace(80 if fx == 0 else RX, LX if fx == 0 else 640, 200)
    pts = np.stack([xs_, [line_y(p, x) for x in xs_]], 1)
    cv2.polylines(out, [np.round(pts * SC4).astype(np.int32)], False, (120, 122, 125), 3, cv2.LINE_AA)

# ---------- terreno ----------
gpoly = [(0, line_y(LW_BOT, 0)), (LX, BACK_Y), (RX, BACK_Y), (700, 966), (700, 975), (0, 975)]
gm = F(gpoly) & R
dy = np.maximum(yo - VP[1], 0.5)
Z = 1600 / dy                       # profondità in metri (camera a 1,6 m, focale ~1000 px)
X = (xo - VP[0]) * 1.6 / dy
foot = 1600 / dy ** 2 / SC4         # metri per pixel in profondità
def gfbm(fx, oct_, seed, amp0=1.0):
    r = np.random.default_rng(seed); acc = np.zeros(X.shape, np.float32); amp = amp0
    for o in range(oct_):
        f = fx * 2 ** o
        w = np.clip(1.2 - f * foot * 2.5, 0, 1)       # niente aliasing in lontananza
        g = cv2.GaussianBlur(r.random((256, 256)).astype(np.float32), (0, 0), 1.0)
        acc += amp * w * (cv2.remap(g, ((X * f) % 256).astype(np.float32), ((Z * f) % 256).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP) - 0.5)
        amp *= 0.55
    return acc
# texture reale: l'asfalto della strada (y 1006-1061), ripiegato in profondità e ricolorato
src_s = im[1006 * SC4:1061 * SC4].astype(np.float32)
lum = src_s.mean(2)
lum = lum / cv2.GaussianBlur(lum, (0, 0), 60)          # solo il dettaglio
levels = [lum] + [cv2.GaussianBlur(lum, (0, 0), sg) for sg in (1.5, 3, 6, 12)]
Zs0, Zs1 = 1600 / (1061 - VP[1]), 1600 / (1006 - VP[1])   # 8,8 m .. 12,8 m
span = Zs1 - Zs0
t = (Z - Zs0) / span
t = np.abs(((t % 2) + 2) % 2 - 1)                       # ripetizione a specchio
Zq = Zs0 + t * span
dys = 1600 / Zq
ysrc = (VP[1] + dys - 1006) * SC4
hw = 350 * 1.6 / dys                                     # semi-larghezza visibile in metri
Xq = X + 3.1 * np.floor(Z / span)                        # sposta ogni ripetizione
Xq = np.abs(((Xq / hw + 1) % 4 + 4) % 4 - 2) - 1
xsrc = (VP[0] + Xq * hw * dys / 1.6) * SC4
detail = np.zeros_like(X)
lev = np.clip(np.log2(np.maximum(foot / 0.004, 1)), 0, 4)
for i, L in enumerate(levels):
    wgt = np.clip(1 - np.abs(lev - i), 0, 1)
    if wgt.max() == 0: continue
    detail += wgt * cv2.remap(L, xsrc.astype(np.float32), np.clip(ysrc, 0, L.shape[0] - 1).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
big = gfbm(0.3, 3, 31) * 0.5 + 0.5
gcol = np.array([92, 116, 146], np.float32)[None, None] * (0.75 + 0.5 * big)[..., None]
gcol *= np.clip(1 + (detail - 1) * 1.6, 0.4, 1.8)[..., None]
fog = np.clip((Z - 15) / 60, 0, 0.3)[..., None]
gcol = gcol * (1 - fog) + np.array([200, 196, 190], np.float32) * fog
out[gm] = gcol[gm]

# ---------- siepe sul fondo: piante vere ritagliate dalla foto ----------
srcs = [(455, 590, 645, 705), (92, 585, 270, 672), (440, 300, 625, 400), (95, 445, 245, 520), (440, 450, 625, 545)]
alpha_full = cv2.GaussianBlur(pl.astype(np.float32), (0, 0), 1.2)
bx = LX
k = (BACK_Y - VP[1]) / (966 - VP[1])   # scala del fondo
rear_bottom = BACK_Y
i = 0
backwall = F([(LX, BACK_Y - 26), (RX, BACK_Y - 26), (RX, BACK_Y), (LX, BACK_Y)]) & R
out[backwall] = (np.array([176, 184, 190], np.float32) * (0.92 + 0.1 * fbm(xo / 30, yo / 30, 4, 4, 41))[..., None])[backwall]
while bx < RX - 10:
    x0, y0, x1, y1 = srcs[i % len(srcs)]; i += 1
    crop = im[y0 * SC4:y1 * SC4, x0 * SC4:x1 * SC4].astype(np.float32)
    a = alpha_full[y0 * SC4:y1 * SC4, x0 * SC4:x1 * SC4]
    if i % 2: crop, a = crop[:, ::-1], a[:, ::-1]
    s = k * rng.uniform(0.75, 0.95)
    nw, nh = int(crop.shape[1] * s), int(crop.shape[0] * s)
    crop = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA); a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)
    crop = crop * 0.85 + np.array([150, 150, 140], np.float32) * 0.15
    px, py = int(bx * SC4) - nw // 6, int((BACK_Y - 16) * SC4) - nh
    xa, ya = max(px, 0), max(py, 0); xb, yb_ = min(px + nw, W), min(py + nh, H)
    sub = (slice(ya, yb_), slice(xa, xb))
    aa = a[ya - py:yb_ - py, xa - px:xb - px][..., None] * R[sub][..., None]
    out[sub] = out[sub] * (1 - aa) + crop[ya - py:yb_ - py, xa - px:xb - px] * aa
    bx += (x1 - x0) * s * 0.62
# il terreno davanti alla siepe va sopra
out[gm] = gcol[gm]
import torch
torch.set_num_threads(4)
lama = torch.jit.load('/tmp/claude-0/models/big-lama.pt', map_location='cpu').eval()
covered = lw | rw | gm | backwall
resid = R & ~covered & (yo > 700) & ((xo < LX) | (xo > RX))
small = cv2.resize(out.clip(0, 255).astype(np.uint8), (W0 * 2, H0 * 2), interpolation=cv2.INTER_AREA)
ms = cv2.resize(resid.astype(np.uint8) * 255, (W0 * 2, H0 * 2), interpolation=cv2.INTER_AREA) > 20
ms = cv2.dilate(ms.astype(np.uint8), np.ones((5, 5), np.uint8))
hh, ww = small.shape[:2]; ph, pw = (8 - hh % 8) % 8, (8 - ww % 8) % 8
x = torch.from_numpy(cv2.cvtColor(np.pad(small, ((0, ph), (0, pw), (0, 0)), mode='reflect'), cv2.COLOR_BGR2RGB)).permute(2, 0, 1)[None].float() / 255
mk = torch.from_numpy(np.pad(ms, ((0, ph), (0, pw)), mode='reflect').astype(np.float32))[None, None]
with torch.no_grad(): o = lama(x, mk)
o = cv2.cvtColor((o[0].permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)[:hh, :ww], cv2.COLOR_RGB2BGR)
o4 = cv2.resize(o, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) + rng.normal(0, 2.5, (H, W, 3))
out[resid] = o4[resid]
out = out.clip(0, 255).astype(np.uint8)
cv2.imwrite('p0_4x.png', out)
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/p0.jpg', cv2.resize(out, (700, 1061), interpolation=cv2.INTER_AREA))
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/p0_zoom.jpg', cv2.resize(out[3300:4000, 0:2800], (1400, 350), interpolation=cv2.INTER_AREA))
print('ok')
