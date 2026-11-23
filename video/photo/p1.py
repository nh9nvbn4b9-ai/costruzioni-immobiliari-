"""Piastra P1 a 4x: struttura grezza in cemento armato (solette, pilastri, piani aperti)."""
import sys, numpy as np, cv2, torch
sys.path.insert(0, '/tmp/claude-0/work')
from geom import *
torch.set_num_threads(4)
SC4 = 4
im = cv2.imread('src4x.png').astype(np.float32)
p0 = cv2.imread('p0_4x.png').astype(np.float32)
H, W = im.shape[:2]
rng = np.random.default_rng(3)
Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
xo, yo = Xg / SC4, Yg / SC4
def F(poly): return fill(poly, sc=SC4) > 127
pl = cv2.imread('m_plants4x.png', 0) > 0
lama = torch.jit.load('/tmp/claude-0/models/big-lama.pt', map_location='cpu').eval()
def inpaint_region(img, mask, box, scale=0.5):
    """LaMa su un ritaglio (box in coordinate 4x), a risoluzione ridotta, poi riportato su."""
    x0, y0, x1, y1 = box
    crop = img[y0:y1, x0:x1]; m = mask[y0:y1, x0:x1]
    if m.sum() == 0: return img
    sw, sh = int((x1 - x0) * scale), int((y1 - y0) * scale)
    c = cv2.resize(crop.clip(0, 255).astype(np.uint8), (sw, sh), interpolation=cv2.INTER_AREA)
    ms = (cv2.resize(m.astype(np.uint8) * 255, (sw, sh), interpolation=cv2.INTER_AREA) > 10).astype(np.float32)
    ms = cv2.dilate(ms, np.ones((3, 3), np.uint8))
    ph, pw = (8 - sh % 8) % 8, (8 - sw % 8) % 8
    x = torch.from_numpy(cv2.cvtColor(np.pad(c, ((0, ph), (0, pw), (0, 0)), mode='reflect'), cv2.COLOR_BGR2RGB)).permute(2, 0, 1)[None].float() / 255
    mk = torch.from_numpy(np.pad(ms, ((0, ph), (0, pw)), mode='reflect'))[None, None]
    with torch.no_grad(): o = lama(x, mk)
    o = cv2.cvtColor((o[0].permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)[:sh, :sw], cv2.COLOR_RGB2BGR)
    o = cv2.resize(o, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    o += rng.normal(0, 2.0, o.shape)
    out = img.copy(); out[y0:y1, x0:x1][m] = o[m]
    return out

# ---------- solette: cemento senza piante e senza LED ----------
hsv = cv2.cvtColor(im.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
led = (hsv[..., 0] > 8) & (hsv[..., 0] < 25) & (hsv[..., 1] > 90) & (hsv[..., 2] > 120)
slab_m = {}
conc = im.copy()
for s in SLABS:
    m = F(slab_poly(s))
    slab_m[s] = m
    bad = m & (cv2.dilate((pl | led).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0)
    ys, xs = np.nonzero(m)
    box = (max(xs.min() - 80, 0), max(ys.min() - 80, 0), min(xs.max() + 80, W), min(ys.max() + 80, H))
    # contesto: fuori dalla soletta mettiamo cemento medio così LaMa non porta dentro il vetro
    ctx = conc.copy()
    mean = im[m & ~bad].mean(0)
    ctx[~m] = mean
    conc = np.where(m[..., None], inpaint_region(ctx, bad, box, 0.5), conc)
# cemento grezzo: un po' desaturato e più freddo, niente luci
gray = conc.mean(2, keepdims=True)
conc = conc * 0.45 + gray * 0.55
conc *= np.array([1.0, 0.99, 0.97], np.float32)

out = p0.copy()

# texture di dettaglio del cemento presa solo da una zona pulita della soletta D
_r = np.random.default_rng(9)
DTL = np.zeros((H, W), np.float32)
for sg, amp in ((1.0, 5.0), (3.0, 4.0), (9.0, 4.0), (30.0, 3.0)):
    n_ = cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), sg)
    DTL += n_ / (n_.std() + 1e-6) * amp
# ---------- piani aperti: ray-casting semplice dentro il volume dell'edificio ----------
KB = 0.72   # profondità del fondo dell'edificio (scala prospettica)
bands = band_masks(sc=SC4)
noise_c = cv2.GaussianBlur(cv2.resize(rng.random((H // 24, W // 24)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 18)
noise_c = (noise_c - noise_c.mean()) / (noise_c.std() + 1e-6) * 0.25 + 0.5
fine = rng.normal(0, 1, (H, W)).astype(np.float32); fine = cv2.GaussianBlur(fine, (0, 0), 1.2) * 0.04
for i, (upper, low) in enumerate(BANDS):
    bm = bands[i] > 127
    x0, x1 = (195, 536) if upper == 'ROOF' else CORE
    ftop = (lambda x: np.full_like(x, 198.0)) if upper == 'ROOF' else bottom_curve(upper)
    yf = ftop(xo)                       # bordo anteriore del soffitto sopra questo pixel
    # k a cui il raggio incontra il piano del soffitto
    kh = (yo - VP[1]) / np.minimum(yf - VP[1], -1)
    # x del pixel riportata sulla facciata alla profondità kh (per sapere se è dentro l'edificio)
    xf = VP[0] + (xo - VP[0]) / np.maximum(kh, 1e-3)
    ceil = bm & (kh > KB) & (kh <= 1.0)
    back = bm & ~ceil
    out[back] = p0[back] * 0.93
    t = np.clip((kh - KB) / (1 - KB), 0, 1)               # 1 = vicino alla facciata
    depth_m = 1 / np.maximum(kh, 0.05)
    planks = 1 + 0.015 * np.sign(np.sin(depth_m * 60))  # giunti dei casseri
    beams = 1 - 0.10 * np.clip(1 - np.abs(((depth_m - 1) * 4.5) % 1 - 0.5) / 0.05, 0, 1)
    dtl = DTL / 140
    val = (62 + 88 * t ** 1.6) * planks * beams * (0.97 + 0.06 * noise_c) * (1 + fine * 0.5 + dtl * np.clip(t * 1.5, 0.3, 1))
    cc = np.stack([val * 1.0, val * 1.01, val * 1.03], -1)
    out[ceil] = cc[ceil]
    # pilastri interni: tre file in profondità, quattro in larghezza
    xs_cols = [x0 + 4, x0 + (x1 - x0) * 0.36, x0 + (x1 - x0) * 0.68, x1 - 10]
    for kk in (0.80, 0.90):   # dal fondo verso il fronte
        for cx in xs_cols:
            wdt = 13
            px0 = VP[0] + (cx - wdt / 2 - VP[0]) * kk; px1 = VP[0] + (cx + wdt / 2 - VP[0]) * kk
            yt = VP[1] + (ftop(np.array([cx]))[0] - VP[1]) * kk
            yb = VP[1] + (low(np.array([cx]))[0] - VP[1]) * kk
            cm = bm & (xo >= px0) & (xo <= px1) & (yo >= yt) & (yo <= yb)
            sh = 0.55 + 0.45 * (kk - KB) / (1 - KB)
            side = np.clip((xo - px0) / max(px1 - px0, 1e-3), 0, 1)
            v = 150 * sh * (0.85 + 0.25 * side) * (0.95 + 0.1 * noise_c)
            out[cm] = np.stack([v, v * 1.01, v * 1.02], -1)[cm]
# pilastri d'angolo (fronte): cemento con la grana delle solette
detail = conc.mean(2) - cv2.GaussianBlur(conc.mean(2), (0, 0), 6)
for (cx0, cx1) in ((133, 168), (552, 580)):
    for i in range(4):
        cm = (bands[i] > 127) & (xo >= cx0) & (xo <= cx1)
        side = np.clip((xo - cx0) / (cx1 - cx0), 0, 1)
        v = 158 * (0.82 + 0.22 * np.sin(side * np.pi * 0.9)) * (0.96 + 0.08 * noise_c)
        # ombra portata dalla soletta sopra
        upper, low = BANDS[i]
        ft = (lambda x: np.full_like(x, 198.0)) if upper == 'ROOF' else bottom_curve(upper)
        v = v * (1 - 0.35 * np.clip(1 - (yo - ft(xo)) / 14, 0, 1))
        dt = DTL
        col = np.stack([v, v * 1.01, v * 1.025], -1) + dt[..., None] * 0.9
        out[cm] = col[cm]

# ---------- piano terra aperto: soffitto, pavimento grezzo, fondo del lotto ----------
g = F(GROUND)
for (a_, b_, c_, d_) in ((141, 822, 432, 962), (472, 858, 652, 962)):
    om = F([(a_, b_), (c_, b_), (c_, d_), (a_, d_)])
    yc, yfl = 822.0, 962.0
    up = yo < VP[1]
    kh = np.where(up, (yo - VP[1]) / (yc - VP[1]), (yo - VP[1]) / (yfl - VP[1]))
    inside = kh > KB
    t = np.clip((kh - KB) / (1 - KB), 0, 1)
    vc = (45 + 70 * t ** 1.5) * (0.92 + 0.16 * noise_c)
    vf = (70 + 60 * t) * (0.9 + 0.2 * noise_c) * (1 + fine * 2)
    v = np.where(up, vc, vf)
    col = np.stack([v, v * 1.01, v * 1.03], -1)
    sel = om & inside
    out[sel] = col[sel]
    sel = om & ~inside
    out[sel] = p0[sel] * 0.8
    globals()['open_' + str(a_)] = om

# ---------- solette sopra tutto ----------
for s in SLABS:
    m = slab_m[s]
    out[m] = conc[m]
# copertura e piano terra grezzi
roof = F(ROOF)
out[roof] = (im[roof] * 0.5 + im[roof].mean(1, keepdims=True) * 0.5)
g = F(GROUND)
gcon = im * 0.45 + im.mean(2, keepdims=True) * 0.55
gbad = g & (cv2.dilate((pl | F(LEFT_PLANTER)).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
gctx = gcon.copy(); gctx[~g] = gcon[g & ~gbad].mean(0)
gcon = inpaint_region(gctx, gbad, (int(40 * SC4), int(740 * SC4), int(700 * SC4), int(975 * SC4)), 0.5)
gm2 = g & ~(open_141 | open_472)
out[gm2] = gcon[gm2]
for om in (open_141, open_472):
    pass
out = out.clip(0, 255).astype(np.uint8)
cv2.imwrite('p1_4x.png', out)
np.savez_compressed('slab_masks.npz', **{k: v for k, v in slab_m.items()})
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/p1.jpg', cv2.resize(out, (700, 1061), interpolation=cv2.INTER_AREA))
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/p1_zoom.jpg', cv2.resize(out[1400:2600, 300:2560], (1130, 600), interpolation=cv2.INTER_AREA))
print('ok')
