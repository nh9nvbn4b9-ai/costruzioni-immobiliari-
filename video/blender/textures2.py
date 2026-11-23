"""Texture realistiche per gli interni: parquet di rovere, marmo, pietre reali dalle foto."""
import os, numpy as np, cv2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex2')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(4)
W = 4096


def blur_noise(h, w, sx, sy, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h, w)).astype(np.float32)
    p = int(3 * max(sx, sy)) + 1
    n = np.pad(n, ((p, p), (p, p)), mode='wrap')
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=sx, sigmaY=sy)[p:-p, p:-p]
    return (n - n.mean()) / (n.std() + 1e-6)


# ---------- parquet: 4 m x 4 m, doghe 1,8 m x 0,19 m, posa a correre ----------
PX = W / 4.0                      # pixel per metro
ph = int(0.19 * PX)               # altezza doga
rows = W // ph + 1
col = np.zeros((W, W, 3), np.float32); rough = np.zeros((W, W), np.float32); bump = np.zeros((W, W), np.float32)
yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
grain_fine = blur_noise(W, W, 18, 0.6, 1)       # fibre lunghe lungo x
grain_mid = blur_noise(W, W, 40, 1.5, 2)
pores = np.clip(blur_noise(W, W, 5, 0.5, 5) - 1.6, 0, 2)
warp = blur_noise(W, W, 260, 60, 3)
base_cols = np.array([[118, 152, 188], [108, 142, 178], [124, 160, 196], [100, 134, 170], [114, 148, 184], [96, 126, 160]], np.float32)  # BGR rovere naturale
for r in range(rows):
    y0, y1 = r * ph, min((r + 1) * ph, W)
    if y0 >= W: break
    off = rng.uniform(0, 1.8 * PX)
    x = -off
    while x < W:
        L = 1.8 * PX * rng.uniform(0.7, 1.0)
        a, b = int(max(x, 0)), int(min(x + L, W))
        if b > a:
            sl = (slice(y0, y1), slice(a, b))
            c = base_cols[rng.integers(len(base_cols))] * rng.uniform(0.9, 1.08)
            # anelli di crescita: seno di una coordinata deformata
            ph_ = rng.uniform(0, 100); fr = rng.uniform(0.05, 0.11)
            ring = np.sin((yy[sl] - y0 + warp[sl] * 14 + (xx[sl] - a) * rng.uniform(-0.01, 0.01)) * fr * 2 * np.pi / 3 + ph_)
            ring = np.clip(ring, -1, 1) ** 3
            g = 0.05 * grain_fine[sl] + 0.04 * grain_mid[sl] + 0.10 * ring - 0.12 * pores[sl]
            col[sl] = c * (1 + g)[..., None]
            rough[sl] = 0.42 + 0.08 * rng.uniform(-1, 1) + 0.05 * grain_fine[sl]
            bump[sl] = 0.5 + 0.15 * ring + 0.1 * grain_fine[sl]
            # nodi rari
            if rng.random() < 0.25:
                kx, ky = rng.uniform(a, b), rng.uniform(y0, y1)
                d = np.sqrt(((xx[sl] - kx) / 1.6) ** 2 + (yy[sl] - ky) ** 2)
                k = np.exp(-d ** 2 / (2 * 9 ** 2))
                col[sl] *= (1 - 0.45 * k)[..., None]
            # fuga tra le doghe (testa)
            for e in (a, b - 1):
                if 0 <= e < W:
                    col[y0:y1, max(e - 2, 0):e + 2] *= 0.55; bump[y0:y1, max(e - 2, 0):e + 2] = 0.2
        x += L
    col[y0:min(y0 + 3, W)] *= 0.55; bump[y0:min(y0 + 3, W)] = 0.2
col = col * (1 + 0.04 * blur_noise(W, W, 300, 300, 9))[..., None]
cv2.imwrite(f'{OUT}/oak.jpg', col.clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite(f'{OUT}/oak_r.jpg', (rough.clip(0, 1) * 255).astype(np.uint8))
cv2.imwrite(f'{OUT}/oak_b.jpg', (bump.clip(0, 1) * 255).astype(np.uint8))

# ---------- marmo: poche venature grigie morbide su fondo caldo ----------
M = 2048
n1 = blur_noise(M, M, 140, 140, 21) + 0.35 * blur_noise(M, M, 40, 40, 22)
lines = np.zeros((M, M), np.float32)
for lev, wdt, amp in ((0.0, 0.07, 0.9), (0.9, 0.04, 0.5), (-1.1, 0.03, 0.4), (1.7, 0.02, 0.3)):
    lines += amp * np.exp(-((n1 - lev) / wdt) ** 2)
halo = cv2.GaussianBlur(lines, (0, 0), 8) * 0.5
cloud = blur_noise(M, M, 60, 60, 24) * 0.015
base = np.array([244, 245, 247], np.float32)
vein_c = np.array([150, 152, 158], np.float32)
mar = base[None, None] * (1 + cloud)[..., None]
a_ = np.clip(lines * 0.8 + halo * 0.3, 0, 1)[..., None]
mar = mar * (1 - a_) + vein_c[None, None] * a_
cv2.imwrite(f'{OUT}/marble.jpg', mar.clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])

# ---------- pietre reali dalle foto ----------
liv = cv2.imread('/tmp/claude-0/work/living4x.png')
stone = liv[int(430 * 4):int(860 * 4), 0:int(740 * 4)]                 # parete in pietra (tutta la larghezza)
cv2.imwrite(f'{OUT}/stone.jpg', stone, [cv2.IMWRITE_JPEG_QUALITY, 92])
bag = cv2.imread('/tmp/claude-0/work/bagno4x.png')
blue = bag[int(128 * 4):int(410 * 4), int(450 * 4):int(720 * 4)]
cv2.imwrite(f'{OUT}/bluestone.jpg', blue, [cv2.IMWRITE_JPEG_QUALITY, 92])
# ---------- tessuto: trama fine ----------
F = 1024
yf, xf = np.mgrid[0:F, 0:F].astype(np.float32)
weave = (np.sin(xf / F * 2 * np.pi * 220) * np.sin(yf / F * 2 * np.pi * 220)) * 0.5 + 0.5
fab = (weave * 0.35 + 0.5 + 0.15 * blur_noise(F, F, 2, 2, 31)).clip(0, 1)
cv2.imwrite(f'{OUT}/weave.jpg', (fab * 255).astype(np.uint8))
print('ok')
