"""Strati per il montaggio: P2 (finito), P3 (sera, luci spente), GLOW (3° piano acceso), mappe dei tempi."""
import sys, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/work')
from geom import *
SC4 = 4
im = cv2.imread('src4x.png').astype(np.float32)
p0 = cv2.imread('p0_4x.png').astype(np.float32)
p1 = cv2.imread('p1_4x.png').astype(np.float32)
H, W = im.shape[:2]
Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
xo, yo = Xg / SC4, Yg / SC4
def F(poly): return fill(poly, sc=SC4) > 127
R = cv2.imread('m_building4x.png', 0) > 0
pl = cv2.imread('m_plants4x.png', 0) > 0
sky_raw = cv2.resize(cv2.imread('m_sky_raw.png', 0), (W, H)) > 127

# ---------- P2: foto originale con lo stesso cielo di P0 ----------
sa = cv2.GaussianBlur((sky_raw & ~R).astype(np.float32), (0, 0), 2)[..., None]
p2 = im * (1 - sa) + p0 * sa
cv2.imwrite('p2_4x.png', p2.clip(0, 255).astype(np.uint8))

# ---------- maschere degli elementi ----------
slabs = {s: F(slab_poly(s)) for s in SLABS}
bands = [m > 127 for m in band_masks(sc=SC4)]
roof = F(ROOF); ground = F(GROUND)
cols = np.zeros((H, W), bool)
for (a, b) in ((131, 169), (551, 581)): cols |= (xo >= a) & (xo <= b)
hsv = cv2.cvtColor(im.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
led = (hsv[..., 0] > 8) & (hsv[..., 0] < 25) & (hsv[..., 1] > 90) & (hsv[..., 2] > 120)

INF = np.float32(1e9)
# ---------- tempi di costruzione dello scheletro (secondi) ----------
Ts = np.full((H, W), INF, np.float32)
t = 1.2
gt = 962 - 782
Ts[ground] = (t + 0.6 * (962 - yo) / gt)[ground]
t += 0.6
upper_of = ['D', 'C', 'B', 'A', 'ROOF']
FLOOR_T = []
for i in range(5):
    bm = bands[i]
    up = upper_of[i]
    ys = np.where(bm.any(1))[0]
    yt, yb = ys.min() / SC4, ys.max() / SC4
    Ts[bm] = (t + 0.4 * (yb - yo) / (yb - yt))[bm]
    sm = roof if up == 'ROOF' else slabs[up]
    sm = sm & ~bm
    cx = 355
    Ts[sm] = np.minimum(Ts[sm], (t + 0.38 + 0.3 * np.abs(xo - cx) / 270)[sm])
    FLOOR_T.append(t)
    t += 0.7
# zone di P1 fuori dagli elementi ma diverse da P0 (sottobalconi): con la soletta più vicina
diff = (np.abs(p1 - p0).sum(2) > 6) & (Ts == INF)
TOPS = [(1.2, 966), (1.8, 782), (2.5, 660), (3.2, 512), (3.9, 370), (4.6, 232), (5.3, 150)]
tt_ = np.array([a for a, _ in TOPS]); yy_ = np.array([b for _, b in TOPS], float)
ty = np.interp(-yo, -yy_, tt_)
Ts[diff] = ty[diff]
print('fine scheletro', t)

# ---------- tempi delle finiture (vetri, solette finite, verde, cancelli) ----------
Tf = np.full((H, W), INF, np.float32)
t0 = 5.9
Tf[ground] = (t0 + 0.5 * (xo - 60) / 620)[ground]
for i in range(5):
    tt = t0 + 0.45 + i * 0.55
    bm = bands[i] & ~pl
    x0, x1 = (195, 536) if i == 4 else CORE
    Tf[bm] = (tt + 0.45 * np.clip((xo - x0) / (x1 - x0), 0, 1))[bm]
    up = upper_of[i]
    sm = (roof if up == 'ROOF' else slabs[up]) & ~pl
    Tf[sm] = np.minimum(Tf[sm], tt + 0.25)
# verde: cresce dal basso verso l'alto, piano per piano
lows = [lambda x: np.full_like(x, 800.0), top_curve('D'), top_curve('C'), top_curve('B'), top_curve('A')]
plt = np.full((H, W), INF, np.float32)
for i, low in enumerate(lows):
    base = low(xo)
    sel = pl & (yo <= base + 15) & (yo > base - 120)
    tt = t0 + 0.75 + i * 0.55
    plt[sel] = np.minimum(plt[sel], (tt + 0.5 * np.clip((base - yo) / 90, 0, 1))[sel])
rest = pl & (plt == INF)
plt[rest] = t0 + 3.5
Tf[pl] = plt[pl]
Tf[R & (Tf == INF)] = t0 + 3.4
np.save('Ts.npy', Ts.astype(np.float16)); np.save('Tf.npy', Tf.astype(np.float16))

# ---------- P3: sera, luci spente ----------
yn = Yg / H
c_top = np.array([62, 30, 18], np.float32); c_mid = np.array([120, 70, 52], np.float32); c_hor = np.array([120, 140, 215], np.float32)
a = np.clip((yo - 0) / 560, 0, 1)[..., None]; b = np.clip((yo - 560) / 330, 0, 1)[..., None]
dusk_sky = (c_top * (1 - a) + c_mid * a) * (1 - b) + c_hor * b
off = p2.copy()
off[led] = p1[led]                                          # LED spenti
glass = np.zeros((H, W), bool)
for bm in bands: glass |= bm
glass &= ~cols & ~pl
lum = off.mean(2, keepdims=True)
dark = off * 0.30 * np.array([1.25, 1.0, 0.85], np.float32) + lum * 0.04
dark[glass] = (off[glass] * 0.16 * np.array([1.4, 1.05, 0.8], np.float32))   # vetri scuri con riflesso del cielo
p3 = dark * (1 - sa) + dusk_sky * sa
# finestre accese qua e là sui vicini: nessuna (restano scuri e credibili)
cv2.imwrite('p3_4x.png', p3.clip(0, 255).astype(np.uint8))

# ---------- GLOW: si accende il 3° piano (fascia indice 2) ----------
f3 = bands[2] & ~cols
g = np.zeros((H, W, 3), np.float32)
warm = off * np.array([0.72, 1.0, 1.42], np.float32) * 1.0 + np.array([8, 24, 52], np.float32)
g[f3 & ~pl] = warm[f3 & ~pl]
g[f3 & pl] = (dark[f3 & pl] * 1.6 + np.array([10, 30, 60], np.float32))   # piante in controluce
ledB = led & cv2.dilate(slabs['B'].astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
g[ledB] = p2[ledB] * np.array([0.9, 1.2, 1.5], np.float32)
gm = (f3 | ledB).astype(np.float32)
bloom = cv2.GaussianBlur(g, (0, 0), 60) * 0.55
np.save('glow_mask.npy', cv2.GaussianBlur(gm, (0, 0), 1.5).astype(np.float16))
cv2.imwrite('glow_4x.png', g.clip(0, 255).astype(np.uint8))
cv2.imwrite('bloom_4x.png', bloom.clip(0, 255).astype(np.uint8))
# ordine di accensione delle vetrate (da sinistra a destra)
on = np.full((H, W), INF, np.float32)
on[f3] = (np.floor((xo - 133) / 50) * 0.08)[f3]
on[ledB] = 0.5
np.save('Ton.npy', on.astype(np.float16))
prev = cv2.resize((p3 * 0.7 + 0), (700, 1061))
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/p3.jpg', cv2.resize(np.clip(p3 + g * gm[..., None] + bloom, 0, 255).astype(np.uint8), (700, 1061), interpolation=cv2.INTER_AREA))
print('ok', FLOOR_T)
