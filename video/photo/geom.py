"""Geometria della facciata (coordinate della foto originale 700x1061)."""
import numpy as np, cv2

SC = 4  # lavoriamo sul 4x (2800x4244)
W0, H0 = 700, 1061

SLABS = {  # dal basso verso l'alto: D (1° piano), C, B, A
    'D': dict(top=[(92,666),(110,660),(150,658),(200,659),(250,664),(300,676),(350,685),(400,684),(450,675),(500,667),(550,667),(600,675),(622,687)],
              right=[(626,705),(624,728),(615,734)],
              bottom=[(500,735),(400,737),(300,737),(200,732),(100,732),(92,725),(89,700)]),
    'C': dict(top=[(96,524),(110,515),(150,510),(200,511),(250,519),(300,535),(330,542),(360,545),(400,540),(450,531),(500,526),(550,526),(600,529),(613,540)],
              right=[(616,560),(614,580),(605,588)],
              bottom=[(550,586),(500,586),(450,590),(400,594),(350,594),(300,590),(250,583),(150,581),(115,588),(100,578),(95,550)]),
    'B': dict(top=[(100,386),(108,375),(120,372),(150,369),(200,368),(230,371),(260,380),(290,391),(320,399),(350,402),(380,400),(410,395),(450,386),(500,379),(550,380),(580,384),(600,391),(612,402)],
              right=[(614,420),(612,432),(605,442)],
              bottom=[(580,446),(500,448),(400,450),(300,452),(200,448),(150,450),(125,457),(108,452),(101,440),(99,415)]),
    'A': dict(top=[(103,262),(110,252),(130,240),(151,234),(200,230),(250,236),(300,249),(350,261),(400,256),(450,245),(500,241),(550,242),(600,254),(612,265)],
              right=[(614,290),(612,305),(600,313)],
              bottom=[(550,316),(500,316),(400,312),(300,314),(200,316),(150,319),(128,323),(110,319),(104,308),(102,290)]),
}
ROOF = [(165,150),(550,150),(550,162),(536,198),(195,198),(165,162)]
GROUND = [(61,782),(150,785),(200,791),(230,800),(260,810),(290,818),(300,822),(420,822),(430,812),(460,806),(500,800),(600,798),(645,800),(651,812),(652,858),(680,858),(680,962),(61,962)]
LEFT_PLANTER = [(5,893),(178,893),(178,968),(5,968)]
CORE = (133, 578)  # facce esterne dei pilastri


def catmull(pts, n=8):
    pts = [np.array(p, float) for p in pts]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(len(pts) - 1, i + 2)]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return np.array(out)


def slab_poly(s):
    d = SLABS[s]
    return catmull(d['top'] + d['right'] + d['bottom'] + [d['top'][0]])


def top_curve(s):
    """y del bordo superiore della soletta in funzione di x (orig)."""
    c = catmull(SLABS[s]['top'], 12)
    return lambda x: np.interp(x, c[:, 0], c[:, 1])


def bottom_curve(s):
    c = catmull(SLABS[s]['bottom'][::-1], 12)
    c = c[np.argsort(c[:, 0])]
    return lambda x: np.interp(x, c[:, 0], c[:, 1])


def fill(poly, shape=None, sc=SC):
    shape = shape or (H0 * sc, W0 * sc)
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(poly) * sc).astype(np.int32)], 255, lineType=cv2.LINE_AA)
    return m


def band_poly(upper, lower_top_fn, x0, x1, upper_is_roof=False):
    """fascia del piano: dal bordo inferiore di 'upper' al bordo superiore della soletta sotto."""
    xs = np.linspace(x0, x1, 60)
    if upper == 'ROOF':
        yt = np.full_like(xs, 198.0)
    else:
        yt = bottom_curve(upper)(xs)
    yb = lower_top_fn(xs)
    return np.concatenate([np.stack([xs, yt], 1), np.stack([xs[::-1], yb[::-1]], 1)])


def ground_top(xs):
    g = np.array(GROUND[:14], float)
    return np.interp(xs, g[:, 0], g[:, 1])


# fasce vetrate dal 1° al 5° piano (sopra: elemento che le chiude)
BANDS = [
    ('D', ground_top),            # 1° piano: tra soletta D e muro del piano terra
    ('C', top_curve('D')),        # 2°
    ('B', top_curve('C')),        # 3°
    ('A', top_curve('B')),        # 4°
    ('ROOF', top_curve('A')),     # 5°
]


def band_masks(sc=SC):
    out = []
    for upper, low in BANDS:
        x0, x1 = (195, 536) if upper == 'ROOF' else CORE
        out.append(fill(band_poly(upper, low, x0, x1), sc=sc))
    return out


VP = (350, 880)


def toward_vp(p, k):
    """punto p spostato verso il punto di fuga (k=1: invariato, k=0: nel punto di fuga)."""
    return (VP[0] + (p[0] - VP[0]) * k, VP[1] + (p[1] - VP[1]) * k)


def line_y(p, x):
    """y sulla retta da p al punto di fuga, in x."""
    return p[1] + (VP[1] - p[1]) * (x - p[0]) / (VP[0] - p[0])


LX, RX = 205, 495   # profondità del fondo del lotto (x dei bordi posteriori delle pareti)
LW_TOP, LW_BOT = (0, 436), (0, 966)        # spigoli della parete laterale del vicino di sinistra
RW_TOP, RW_BOT = (700, 485), (700, 966)    # vicino di destra
LWALL = [(92, line_y(LW_TOP, 92)), (LX, line_y(LW_TOP, LX)), (LX, line_y(LW_BOT, LX)), (92, line_y(LW_BOT, 92))]
RWALL = [(636, line_y(RW_TOP, 636)), (RX, line_y(RW_TOP, RX)), (RX, line_y(RW_BOT, RX)), (636, line_y(RW_BOT, 636))]
BACK_Y = line_y(LW_BOT, LX)
