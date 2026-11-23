import numpy as np, cv2
im = cv2.imread('src2x.png')
conc = cv2.imread('m_conc_raw.png', 0) > 0
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
c = cv2.morphologyEx(conc.astype(np.uint8), cv2.MORPH_CLOSE, k)
c = cv2.morphologyEx(c, cv2.MORPH_OPEN, np.ones((1, 81), np.uint8))
c = cv2.morphologyEx(c, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
n, lab, st, cen = cv2.connectedComponentsWithStats(c)
viz = (im * 0.4).astype(np.uint8)
rng = np.random.default_rng(1)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 4000: continue
    col = rng.integers(80, 255, 3)
    viz[lab == i] = col
    cv2.putText(viz, str(i), (int(cen[i][0]), int(cen[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
    print(i, x // 2, y // 2, (x + w) // 2, (y + h) // 2, a)
np.save('conc_lab.npy', lab)
cv2.imwrite('/tmp/claude-0/-home-user-costruzioni-immobiliari-/8eaa9ce9-18f0-5907-a68f-43ed218ba4f5/scratchpad/viz2.jpg', cv2.resize(viz, (700, 1061)))
