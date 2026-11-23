import numpy as np, cv2
im = cv2.imread('src4x.png'); im = cv2.resize(im, (1400, 2122), interpolation=cv2.INTER_AREA)
cv2.imwrite('src2x.png', im)
f = im.astype(np.float32) / 255
b, g, r = f[..., 0], f[..., 1], f[..., 2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
Hh, S, V = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
sky = (b > r + 0.12) & (b > g + 0.02) & (V > 0.55) & (Hh > 200) & (Hh < 235)
plant = (((Hh > 45) & (Hh < 160) & (S > 0.22)) | ((Hh > 20) & (Hh < 45) & (S > 0.55) & (V > 0.5))) & (V > 0.12)
conc = (S < 0.16) & (V > 0.42) & (V < 0.88)
def save(n, m): cv2.imwrite(n, (m.astype(np.uint8) * 255))
save('m_sky_raw.png', sky); save('m_plant_raw.png', plant); save('m_conc_raw.png', conc)
viz = im.copy()
viz[sky] = (viz[sky] * 0.3 + np.array([255, 0, 0]) * 0.7).astype(np.uint8)
viz[plant] = (viz[plant] * 0.3 + np.array([0, 255, 0]) * 0.7).astype(np.uint8)
viz[conc] = (viz[conc] * 0.3 + np.array([0, 0, 255]) * 0.7).astype(np.uint8)
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/viz1.jpg', cv2.resize(viz, (700, 1061)))
