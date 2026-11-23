"""Appartamento tipo arredato (piano 5°). Coordinate di pianta: x → x, y → z (metri)."""
import math

import bpy

from common import BAL, BD, MB, V, hexc, mat_basic, mat_glass, mat_image, mat_noise

WALL_H = 2.7

ROOMS = [
    ('Soggiorno · Cucina', '46,6 m²', (5.3, 8.9), 'wood', [(0, 4, 4.4, 10), (4.4, 5.4, 8.8, 10)]),
    ('Camera', '17,6 m²', (2.9, 3.4), 'wood', [(0, 0, 4.4, 4)]),
    ('Bagno', '6,8 m²', (5.7, 1.55), 'tiles', [(4.4, 0, 7, 2.6)]),
    ('Rip.', '3,6 m²', (5.0, 3.0), 'tiles', [(4.4, 2.6, 7, 4)]),
    ('Studio', '13,6 m²', (8.7, 1.9), 'wood', [(7, 0, 10.4, 4)]),
    ('Matrimoniale', '19,4 m²', (12.4, 4.0), 'wood', [(10.4, 0, 14, 5.4)]),
    ('Disimpegno', '8,4 m²', (7.6, 4.75), 'wood', [(4.4, 4, 10.4, 5.4)]),
    ('Bagno', '6,6 m²', (9.9, 6.6), 'tiles', [(8.8, 5.4, 11, 8.4)]),
    ('Lav.', '3,5 m²', (9.9, 8.9), 'tiles', [(8.8, 8.4, 11, 10)]),
    ('Camera', '13,8 m²', (12.3, 9.2), 'wood', [(11, 5.4, 14, 10)]),
]
INNER = [((0, 4), (3.2, 4)), ((4.4, 0), (4.4, 4)), ((7, 0), (7, 4)), ((4.4, 2.6), (5.2, 2.6)), ((6.1, 2.6), (7, 2.6)),
         ((4.1, 4), (5.0, 4)), ((5.8, 4), (7.6, 4)), ((8.5, 4), (10.4, 4)), ((10.4, 0), (10.4, 4.2)), ((10.4, 5.1), (10.4, 5.4)),
         ((8.8, 5.4), (9.2, 5.4)), ((10.0, 5.4), (14, 5.4)), ((8.8, 5.4), (8.8, 8.6)), ((8.8, 9.6), (8.8, 10)), ((8.8, 8.4), (11, 8.4)),
         ((11, 5.4), (11, 8.6)), ((11, 9.5), (11, 10))]
DOORS = [((4.1, 4), 0.9, 1.5 * math.pi), ((5.0, 4), 0.8, -0.5 * math.pi), ((6.1, 2.6), 0.9, 1.5 * math.pi), ((8.5, 4), 0.9, 1.5 * math.pi),
         ((10.4, 4.2), 0.9, -0.5 * math.pi), ((9.2, 5.4), 0.8, 0.5 * math.pi), ((11, 8.6), 0.9, 0)]
WINDOWS = [('S', 1, 3.5), ('S', 4.5, 7.5), ('S', 11.8, 13.2), ('N', 1.2, 3.2), ('N', 7.8, 9.6), ('N', 11.4, 13), ('W', 6, 8.5), ('W', 1, 3)]

# [x0, y0, x1, y1, base, h, mat, bevel]
ITEMS = [
    (0.15, 4.2, 0.78, 4.85, 0, 2.3, 'white', 0.01), (0.15, 4.85, 0.75, 7.6, 0, 0.88, 'white', 0.01), (0.12, 4.85, 0.78, 7.63, 0.88, 0.04, 'darkStone', 0.005),
    (0.3, 5.55, 0.62, 6.2, 0.905, 0.025, 'steel', 0.02), (0.24, 6.55, 0.7, 7.2, 0.92, 0.012, 'hob', 0), (0.15, 4.85, 0.5, 7.6, 1.55, 0.8, 'white', 0.01),
    (1.9, 4.9, 3.6, 5.6, 0, 0.9, 'white', 0.02), (1.85, 4.85, 3.65, 5.65, 0.9, 0.04, 'marble', 0.01),
    (5.15, 6.6, 7.45, 7.6, 0.72, 0.05, 'walnut', 0.02),
    (0.1, 8.1, 0.5, 9.7, 0, 0.45, 'walnut', 0.01), (0.22, 8.35, 0.27, 9.45, 0.55, 0.68, 'black', 0.005),
    (1.0, 7.7, 3.05, 9.75, 0.0, 0.012, 'rug1', 0),
    (2.85, 7.45, 3.75, 9.88, 0, 0.42, 'fabricGrey', 0.07), (3.48, 7.45, 3.88, 9.88, 0, 0.82, 'fabricGrey', 0.07),
    (1.95, 9.0, 2.86, 9.88, 0, 0.42, 'fabricGrey', 0.07), (1.95, 9.52, 2.86, 9.9, 0, 0.82, 'fabricGrey', 0.07),
    (2.92, 7.55, 3.46, 8.4, 0.42, 0.14, 'fabricLight', 0.06), (2.92, 8.45, 3.46, 9.3, 0.42, 0.14, 'fabricLight', 0.06),
    (2.05, 9.05, 2.8, 9.5, 0.42, 0.14, 'fabricLight', 0.06), (3.22, 7.6, 3.46, 8.05, 0.5, 0.36, 'ochre', 0.07),
    (2.2, 9.28, 2.65, 9.5, 0.5, 0.36, 'teal', 0.07), (1.7, 8.42, 2.1, 8.7, 0.38, 0.04, 'book', 0.005),
    (0.05, 0.95, 0.16, 2.85, 0, 1.0, 'fabricBeige', 0.03), (0.12, 1.05, 2.2, 2.75, 0, 0.3, 'oak', 0.02),
    (0.17, 1.1, 2.15, 2.7, 0.3, 0.22, 'linen', 0.06), (0.8, 1.07, 2.18, 2.73, 0.45, 0.11, 'sage', 0.05),
    (1.72, 1.05, 2.02, 2.75, 0.54, 0.04, 'rust', 0.02), (0.25, 1.2, 0.68, 1.86, 0.52, 0.15, 'pillow', 0.07),
    (0.25, 1.94, 0.68, 2.6, 0.52, 0.15, 'pillow', 0.07), (0.1, 0.48, 0.52, 0.95, 0, 0.5, 'oak', 0.01),
    (0.1, 2.85, 0.52, 3.32, 0, 0.5, 'oak', 0.01), (3.75, 0.2, 4.28, 2.8, 0, 2.3, 'white', 0.01), (2.35, 1.2, 3.5, 2.6, 0.0, 0.012, 'rug2', 0),
    (4.55, 0.15, 6.85, 0.92, 0, 0.58, 'ceramic', 0.12), (4.7, 0.28, 6.7, 0.79, 0.5, 0.06, 'water', 0.1),
    (4.48, 1.72, 4.66, 2.22, 0, 0.8, 'ceramic', 0.03), (6.4, 1.15, 6.92, 2.25, 0, 0.85, 'walnut', 0.01), (6.5, 1.42, 6.86, 1.98, 0.85, 0.12, 'ceramic', 0.04),
    (5.9, 3.25, 6.55, 3.9, 0, 0.85, 'white', 0.03), (4.5, 3.4, 5.4, 3.92, 0, 1.8, 'oak', 0.01),
    (7.3, 0.2, 9.1, 0.85, 0.72, 0.04, 'oak', 0.01), (7.9, 0.33, 8.35, 0.66, 0.76, 0.02, 'steel', 0.005),
    (9.98, 0.4, 10.33, 3.4, 0, 2.0, 'walnut', 0.01), (7.15, 2.1, 7.95, 3.8, 0, 0.45, 'fabricBeige', 0.07),
    (7.08, 2.1, 7.34, 3.8, 0, 0.82, 'fabricBeige', 0.07), (7.4, 2.25, 7.85, 2.75, 0.45, 0.3, 'teal', 0.07),
    (10.45, 1.2, 10.6, 3.2, 0, 1.1, 'fabricGrey', 0.03), (10.55, 1.3, 12.6, 3.1, 0, 0.3, 'walnut', 0.02),
    (10.6, 1.35, 12.55, 3.05, 0.3, 0.22, 'linen', 0.06), (11.15, 1.33, 12.58, 3.07, 0.45, 0.11, 'cream', 0.05),
    (12.12, 1.31, 12.45, 3.09, 0.54, 0.04, 'navy', 0.02), (10.7, 1.45, 11.12, 2.15, 0.52, 0.15, 'pillow', 0.07),
    (10.7, 2.25, 11.12, 2.95, 0.52, 0.15, 'pillow', 0.07), (10.5, 0.7, 10.95, 1.15, 0, 0.5, 'walnut', 0.01),
    (10.5, 3.25, 10.95, 3.7, 0, 0.5, 'walnut', 0.01), (11.6, 4.7, 13.85, 5.25, 0, 2.3, 'oak', 0.01),
    (12.9, 0.3, 13.75, 1.15, 0, 0.42, 'leather', 0.08), (13.45, 0.3, 13.8, 1.15, 0, 0.8, 'leather', 0.07), (12.85, 1.5, 13.8, 3.1, 0.0, 0.012, 'rug1', 0),
    (6.0, 4.08, 7.4, 4.42, 0, 0.8, 'walnut', 0.01),
    (10.05, 7.45, 10.92, 8.32, 0, 0.05, 'ceramic', 0.01), (9.98, 7.4, 10.04, 8.32, 0, 2.0, 'glass', 0),
    (8.85, 7.6, 9.03, 8.05, 0, 0.8, 'ceramic', 0.03), (8.85, 5.95, 9.35, 6.95, 0, 0.85, 'walnut', 0.01), (8.9, 6.2, 9.3, 6.7, 0.85, 0.12, 'ceramic', 0.04),
    (9.0, 9.2, 9.65, 9.85, 0, 0.85, 'white', 0.03), (9.7, 9.2, 10.35, 9.85, 0, 0.85, 'white', 0.03), (10.5, 8.55, 10.9, 9.85, 0, 1.8, 'oak', 0.01),
    (12.9, 6.0, 13.88, 8.05, 0, 0.3, 'oak', 0.02), (12.95, 6.05, 13.83, 8.0, 0.3, 0.2, 'linen', 0.05),
    (12.93, 6.6, 13.85, 8.03, 0.42, 0.1, 'mustard', 0.05), (13.05, 6.12, 13.75, 6.5, 0.48, 0.13, 'pillow', 0.06),
    (11.2, 5.55, 12.4, 6.05, 0.72, 0.04, 'white', 0.01), (11.1, 6.6, 11.65, 8.4, 0, 2.2, 'white', 0.01), (11.9, 7.0, 12.8, 8.6, 0.0, 0.012, 'rug2', 0),
    (1.2, 10.95, 3.1, 11.6, 0, 0.4, 'fabricLight', 0.07), (1.2, 11.35, 3.1, 11.62, 0, 0.75, 'fabricLight', 0.05), (5.0, 11.2, 8.2, 11.62, 0, 0.5, 'darkStone', 0.01),
    # decorazioni: listelli TV, quadri, libri
    (1.35, 4.06, 2.95, 4.1, 1.15, 1.15, 'black', 0), (1.4, 4.1, 2.9, 4.11, 1.2, 1.05, 'art', 0),
    (10.41, 1.55, 10.45, 2.85, 1.35, 0.75, 'black', 0), (10.45, 1.6, 10.46, 2.8, 1.4, 0.65, 'navy', 0),
]
for x in (5.6, 6.3, 7.0):
    ITEMS += [(x - 0.22, 6.18, x + 0.22, 6.58, 0.43, 0.06, 'fabricBeige', 0.025), (x - 0.22, 6.12, x + 0.22, 6.2, 0.43, 0.45, 'fabricBeige', 0.02),
              (x - 0.22, 7.62, x + 0.22, 8.02, 0.43, 0.06, 'fabricBeige', 0.025), (x - 0.22, 8.0, x + 0.22, 8.08, 0.43, 0.45, 'fabricBeige', 0.02)]
z = 7.9
while z < 9.95:
    ITEMS.append((0.15, z, 0.2, z + 0.05, 0, 2.7, 'walnut', 0))
    z += 0.09
for r in range(4):
    for k in range(9):
        zz = 0.5 + k * 0.32 + ((r * 7 + k * 3) % 5) * 0.01
        ITEMS.append((10.02, zz, 10.3, zz + 0.24, 0.35 + r * 0.45, 0.28 + ((k + r) % 3) * 0.04, ['book', 'navy', 'mustard', 'linen', 'teal', 'rust'][(k + r * 2) % 6], 0))

# cilindri [cx, cy, r, base, h, mat, scala_x]
CYLS = [(2.2, 5.95, 0.2, 0, 0.75, 'black', 1), (2.75, 5.95, 0.2, 0, 0.75, 'black', 1), (3.3, 5.95, 0.2, 0, 0.75, 'black', 1),
        (1.9, 8.6, 0.45, 0, 0.38, 'oak', 1), (5.8, 7.1, 0.22, 1.75, 0.08, 'lamp', 1), (6.8, 7.1, 0.22, 1.75, 0.08, 'lamp', 1),
        (0.31, 0.72, 0.13, 0.5, 0.32, 'lamp', 1), (0.31, 3.08, 0.13, 0.5, 0.32, 'lamp', 1), (10.72, 0.92, 0.13, 0.5, 0.32, 'lamp', 1),
        (10.72, 3.47, 0.13, 0.5, 0.32, 'lamp', 1), (4.95, 1.97, 0.22, 0, 0.42, 'ceramic', 1.35), (9.28, 7.82, 0.2, 0, 0.42, 'ceramic', 1.35),
        (8.2, 1.25, 0.28, 0, 0.5, 'black', 1), (11.8, 6.4, 0.24, 0, 0.45, 'navy', 1), (3.7, 10.95, 0.38, 0, 0.72, 'teak', 1), (4.3, 11.25, 0.22, 0, 0.45, 'teak', 1),
        (5.8, 7.1, 0.006, 1.83, 0.87, 'black', 1), (6.8, 7.1, 0.006, 1.83, 0.87, 'black', 1)]
PLANTS = [(4.1, 9.55, 0.5), (8.4, 5.85, 0.42), (9.65, 3.6, 0.38), (13.6, 4.4, 0.35), (5.6, 11.4, 0.32), (6.6, 11.4, 0.36), (7.6, 11.4, 0.32), (0.5, 9.75, 0.35)]
SPOTS = [(1.5, 5.5), (3.5, 5.5), (1.5, 8.5), (3.5, 8.5), (6, 6.2), (7.5, 9), (5.5, 9), (7.5, 4.7), (5.5, 4.7), (2, 1.5), (12, 2), (12, 7.5), (8.7, 2), (5.7, 1.3), (9.9, 7.0)]


def interior_mats():
    c = hexc
    leaves = mat_noise('plant', c('#2f5a24'), c('#5c8a3c'), scale=6, rough=0.6, bump=0.6, voronoi=True)
    return {
        'white': mat_basic('i_white', c('#f1eee8'), 0.45), 'wall': mat_noise('i_wall', c('#efece6'), c('#f6f4ef'), scale=3, rough=0.85, bump=0.03),
        'oak': mat_basic('i_oak', c('#c39a6b'), 0.5), 'walnut': mat_basic('i_walnut', c('#6a452c'), 0.45, coat=0.2), 'teak': mat_basic('i_teak', c('#8a6446'), 0.6),
        'fabricGrey': mat_basic('i_fg', c('#8d8f92'), 0.95, sheen=0.6), 'fabricLight': mat_basic('i_fl', c('#dcd6cc'), 0.95, sheen=0.6),
        'fabricBeige': mat_basic('i_fb', c('#c8b49a'), 0.95, sheen=0.5), 'leather': mat_basic('i_le', c('#8b5a36'), 0.5, coat=0.3),
        'linen': mat_basic('i_li', c('#f4f1ea'), 0.9, sheen=0.4), 'pillow': mat_basic('i_pi', c('#fbfaf6'), 0.9, sheen=0.5),
        'ochre': mat_basic('i_oc', c('#c99a3e'), 0.9, sheen=0.5), 'teal': mat_basic('i_te', c('#3e6f6c'), 0.9, sheen=0.5),
        'sage': mat_basic('i_sa', c('#a9b59a'), 0.92, sheen=0.5), 'cream': mat_basic('i_cr', c('#ebe2d2'), 0.92, sheen=0.5),
        'mustard': mat_basic('i_mu', c('#d2a43f'), 0.92, sheen=0.5), 'rust': mat_basic('i_ru', c('#a8573a'), 0.95, sheen=0.5),
        'navy': mat_basic('i_na', c('#2f3c57'), 0.9, sheen=0.4), 'black': mat_basic('i_bl', c('#1d1e20'), 0.4),
        'steel': mat_basic('i_st', c('#c0c4ca'), 0.22, metal=1.0), 'ceramic': mat_basic('i_ce', c('#fbfbf8'), 0.08, coat=0.6),
        'water': mat_glass('i_wa', c('#bfe0e8'), 0.0), 'marble': mat_image('i_ma', 'marble.jpg', rough=0.15, bump=0.02, coat=0.5),
        'darkStone': mat_basic('i_ds', c('#2e2d2b'), 0.3, coat=0.3), 'hob': mat_image('i_hob', 'hob.jpg', rough=0.1, bump=0, coat=1.0),
        'glass': mat_glass('i_gl', c('#e2eef2'), 0.0), 'win': mat_glass('i_win', c('#eef6f8'), 0.0),
        'lamp': mat_basic('i_lamp', c('#fff3d6'), 0.6, emit=c('#ffd79a'), emit_s=6.0), 'book': mat_basic('i_bo', c('#a23a2c'), 0.8),
        'rug1': mat_image('i_r1', 'rug1.jpg', rough=1.0, bump=0.3), 'rug2': mat_image('i_r2', 'rug2.jpg', rough=1.0, bump=0.3),
        'art': mat_image('i_art', 'art.jpg', rough=0.8, bump=0.05),
        'wood': mat_image('i_wood', 'wood.jpg', rough=0.32, bump=0.15, coat=0.25), 'tiles': mat_image('i_tiles', 'tiles.jpg', rough=0.18, bump=0.2, coat=0.3),
        'deck': mat_image('i_deck', 'deck.jpg', rough=0.7, bump=0.4), 'pot': mat_basic('i_pot', c('#d6cfc4'), 0.8),
        'leaves': leaves, 'spot': mat_basic('i_spot', c('#ffffff'), 0.5, emit=c('#fff1d6'), emit_s=25.0),
        'ceiling': mat_basic('i_ceil', c('#f4f2ee'), 0.9), 'slab': mat_noise('i_slab', c('#d8d3cb'), c('#e8e4dd'), scale=4, rough=0.9, bump=0.1),
        'rail': mat_basic('i_rail', c('#8a8d92'), 0.35, metal=0.8),
    }


def build_interior(coll, M, with_ceiling=False, mirror=False, hide_doors=()):
    """Costruisce l'appartamento con origine nel pavimento. Restituisce la lista di oggetti."""
    obs = []

    mb = MB()  # 0 legno, 1 piastrelle, 2 deck, 3 muri, 4 vetro finestre, 5 soletta
    for _, _, _, fl, rects in ROOMS:
        for (x0, y0, x1, y1) in rects:
            mb.floor(x0, y0, x1, y1, 0.004, 2, mat=0 if fl == 'wood' else 1)
    mb.floor(BAL['x0'], BD + 0.15, BAL['x1'], BAL['z1'] - 0.05, 0.004, 2, mat=2)
    for (a, b) in INNER:
        t = 0.06
        mb.box(min(a[0], b[0]) - t, 0, min(a[1], b[1]) - t, max(a[0], b[0]) + t, WALL_H, max(a[1], b[1]) + t, 2, mat=3)
    t = 0.15
    for s, frm, to in (('N', -t, 14 + t), ('S', -t, 14 + t), ('W', 0, BD), ('E', 0, BD)):
        ws = sorted([(w[1], w[2]) for w in WINDOWS if w[0] == s])
        cpos = frm

        def seg(a, b):
            if b - a < 0.01:
                return
            if s == 'N':
                mb.box(a, 0, -t, b, WALL_H, t, 2, mat=3)
            if s == 'S':
                mb.box(a, 0, BD - t, b, WALL_H, BD + t, 2, mat=3)
            if s == 'W':
                mb.box(-t, 0, a, t, WALL_H, b, 2, mat=3)
            if s == 'E':
                mb.box(14 - t, 0, a, 14 + t, WALL_H, b, 2, mat=3)
        for (a, b) in ws:
            seg(cpos, a)
            if s in 'NS':
                zz = 0 if s == 'N' else BD
                mb.box(a, 0, zz - 0.02, b, WALL_H - 0.05, zz + 0.02, 2, 'zZ', mat=4)
                mb.box(a, WALL_H - 0.05, zz - t, b, WALL_H, zz + t, 2, mat=3)
            else:
                mb.box(-0.02, 0, a, 0.02, WALL_H - 0.05, b, 2, 'xX', mat=4)
                mb.box(-t, WALL_H - 0.05, a, t, WALL_H, b, 2, mat=3)
            cpos = b
        seg(cpos, to)
    mb.box(-0.3, -0.32, -0.3, 14.3, 0, BD + 0.3, 3, 'XxZzy', mat=5)
    mb.box(BAL['x0'], -0.3, BD + 0.3, BAL['x1'], 0, BAL['z1'], 3, 'XxZzy', mat=5)
    # parapetto del terrazzo
    mb.box(BAL['x0'], 0, BAL['z1'] - 0.05, BAL['x1'], 1.05, BAL['z1'] - 0.02, 1, mat=4)
    mb.box(BAL['x1'] - 0.03, 0, BD + 0.2, BAL['x1'], 1.05, BAL['z1'], 1, mat=4)
    mb.box(BAL['x0'], 1.05, BAL['z1'] - 0.05, BAL['x1'], 1.08, BAL['z1'] - 0.01, 1, mat=6)
    base = mb.build('apt_shell', [M['wood'], M['tiles'], M['deck'], M['wall'], M['win'], M['slab'], M['rail']], coll)
    obs.append(base)
    if with_ceiling:
        obs.append(MB().box(-0.3, WALL_H, -0.3, 14.3, WALL_H + 0.3, BD + 0.3, 3).build('apt_ceiling', [M['ceiling']], coll))

    # arredi
    for i, (x0, y0, x1, y1, b0, h, m, bev) in enumerate(ITEMS):
        o = MB().box(x0, b0, y0, x1, b0 + h, y1, 1).build(f'it{i}', [M[m]], coll)
        if bev and bev > 0.004:
            md = o.modifiers.new('b', 'BEVEL')
            md.width = min(bev, (x1 - x0) / 2.2, (y1 - y0) / 2.2, h / 2.2)
            md.segments = 3
            o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
        obs.append(o)
    for i, (cx, cy, r, b0, h, m, sx) in enumerate(CYLS):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=1)
        o = bpy.context.active_object
        o.name = f'cy{i}'
        o.location = V(cx, b0 + h / 2, cy)
        o.scale = (r * sx, r, h)
        o.data.materials.append(M[m])
        for p in o.data.polygons:
            p.use_smooth = True
        for c2 in list(o.users_collection):
            c2.objects.unlink(o)
        coll.objects.link(o)
        obs.append(o)
    for i, (x, y, r) in enumerate(PLANTS):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r * 0.55, depth=0.44, location=V(x, 0.22, y))
        pot = bpy.context.active_object
        pot.data.materials.append(M['pot'])
        parts = [pot]
        for (dx, dy, dz, s) in ((0, 0, 0.75, 1.0), (0.3, -0.2, 0.95, 0.6), (-0.3, 0.25, 0.9, 0.55), (0.1, 0.3, 1.1, 0.45)):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r * s, location=V(x + dx * r, dz, y + dy * r))
            lf = bpy.context.active_object
            lf.scale = (1, 1, 0.85)
            tx = bpy.data.textures.new(f'pl{i}', 'CLOUDS')
            tx.noise_scale = 0.1
            d = lf.modifiers.new('d', 'DISPLACE')
            d.texture = tx
            d.strength = r * 0.25
            lf.data.materials.append(M['leaves'])
            parts.append(lf)
        for p in parts:
            for c2 in list(p.users_collection):
                c2.objects.unlink(p)
            coll.objects.link(p)
            obs.append(p)
    for i, ((hx, hy), r, a1) in enumerate(DOORS):
        if i in hide_doors:
            continue
        o = MB().box(0, 0, -0.02, r, 2.1, 0.02, 1).build(f'door{i}', [M['oak']], coll)
        o.location = V(hx, 0, hy)
        o.rotation_euler = (0, 0, -a1)
        obs.append(o)
    if with_ceiling:
        for i, (x, y) in enumerate(SPOTS):
            bpy.ops.mesh.primitive_circle_add(vertices=20, radius=0.07, fill_type='NGON', location=V(x, WALL_H - 0.002, y))
            s = bpy.context.active_object
            s.rotation_euler = (math.pi, 0, 0)
            s.data.materials.append(M['spot'])
            for c2 in list(s.users_collection):
                c2.objects.unlink(s)
            coll.objects.link(s)
            obs.append(s)
    return obs
