"""Edificio in costruzione: scavo, fondazioni, solai, pilastri, facciate, copertura, giardino."""
import bpy
from mathutils import Vector

from common import BAL, BD, BW, G0, H, LEVELS, LOT, MB, PIT, SLAB, V

COLS_X = [0.3, 5, 10, 13.8, 16.2, 20, 25, 29.7]
COLS_Z = [0.3, 5, 9.7]


def ob_link(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def build_building(M, coll):
    """Restituisce un dizionario di oggetti per piano da animare."""
    L = {}
    hF = H - SLAB

    def mk(mb, name, mats):
        return mb.build(name, mats, coll)

    for i in range(LEVELS + 1):
        lv = {}
        # solaio: origine al bordo sinistro (getto che avanza)
        mb = MB().box(0, 0, -0.25, BW + 0.5, SLAB, BD + 0.25, 3)
        if 1 <= i < LEVELS:
            mb.box(BAL['x0'] + 0.25, 0.08, BD + 0.25, BAL['x1'] + 0.25, SLAB, BAL['z1'], 3)
            mb.box(BW - BAL['x1'] + 0.25, 0.08, BD + 0.25, BW - BAL['x0'] + 0.25, SLAB, BAL['z1'], 3)
        lv['slab'] = mk(mb, f'slab{i}', [M.concrete])
        lv['slab_base'] = V(-0.25, G0 + i * H, 0)
        if i < LEVELS:
            mb = MB()
            for x in COLS_X:
                for z in COLS_Z:
                    mb.box(x - 0.2, 0, z - 0.2, x + 0.2, 1, z + 0.2, 3)
            lv['cols'] = mk(mb, f'cols{i}', [M.concrete])
            lv['cols_base'] = V(0, G0 + i * H + SLAB, 0)
            # facciata (0 vetro, 1 telai, 2 muro, 3 ringhiera vetro, 4 corrimano, 5 pietra scura, 6 rosso)
            mb = MB()
            if i == 0:
                mb.quad((0.25, 0, BD + 0.02), (BW - 0.5, 0, 0), (0, hF, 0), mat=0)
                x = 0.25
                while x <= BW - 0.2:
                    mb.box(x - 0.05, 0, BD, x + 0.05, hF, BD + 0.1, mat=1)
                    x += 2.4
                mb.box(0.25, 2.6, BD, BW - 0.25, 2.68, BD + 0.1, mat=1)
                mb.box(-0.08, 0, -0.08, BW + 0.08, hF, 0.06, 1.6, 'z', mat=5)
                mb.box(-0.08, 0, -0.08, 0.06, hF, BD + 0.08, 1.6, 'x', mat=5)
                mb.box(BW - 0.06, 0, -0.08, BW + 0.08, hF, BD + 0.08, 1.6, 'X', mat=5)
                mb.box(-0.08, 0, BD - 0.1, 0.25, hF, BD + 0.1, 1.6, mat=5)
                mb.box(BW - 0.25, 0, BD - 0.1, BW + 0.08, hF, BD + 0.1, 1.6, mat=5)
                mb.box(12.4, 2.6, BD, 17.6, 2.82, BD + 2.6, 2, mat=6)
            else:
                def front(x0, x1):
                    mb.quad((x0, 0, BD + 0.02), (x1 - x0, 0, 0), (0, hF, 0), mat=0)
                    n = round((x1 - x0) / 1.45)
                    for k in range(n + 1):
                        x = x0 + (x1 - x0) * k / n
                        mb.box(x - 0.035, 0, BD, x + 0.035, hF, BD + 0.09, mat=1)
                    mb.box(x0, 2.35, BD, x1, 2.41, BD + 0.08, mat=1)
                front(0.25, 13.6)
                front(16.4, BW - 0.25)
                mb.box(13.6, 0, BD - 0.05, 16.4, hF, BD + 0.06, 2, mat=2)
                mb.box(-0.06, 0, -0.06, BW + 0.06, hF, 0.05, 2, 'z', mat=2)
                mb.box(-0.06, 0, -0.06, 0.05, hF, BD + 0.06, 2, 'x', mat=2)
                mb.box(BW - 0.05, 0, -0.06, BW + 0.06, hF, BD + 0.06, 2, 'X', mat=2)
                x = 1.0
                while x < BW - 1:
                    if not (13 < x < 16.5):
                        mb.quad((x + 1.7, 0.85, -0.08), (-1.7, 0, 0), (0, 1.6, 0), mat=0)
                        mb.box(x - 0.04, 0.8, -0.12, x + 1.74, 0.85, -0.04, mat=1)
                    x += 3.2
                for a, b in ((1.2, 3.4), (6, 8.5)):
                    mb.quad((-0.08, 0.85, a), (0, 0, b - a), (0, 1.6, 0), mat=0)
                    mb.quad((BW + 0.08, 0.85, b), (0, 0, a - b), (0, 1.6, 0), mat=0)
                for a, b in ((BAL['x0'], BAL['x1']), (BW - BAL['x1'], BW - BAL['x0'])):
                    mb.box(a, 0, BAL['z1'] - 0.05, b, 1.05, BAL['z1'] - 0.02, mat=3)
                    mb.box(a, 0, BD + 0.3, a + 0.03, 1.05, BAL['z1'] - 0.02, mat=3)
                    mb.box(b - 0.03, 0, BD + 0.3, b, 1.05, BAL['z1'] - 0.02, mat=3)
                    mb.box(a, 1.05, BAL['z1'] - 0.07, b, 1.1, BAL['z1'], mat=4)
            lv['fac'] = mk(mb, f'fac{i}', [M.glass[i], M.frame, M.white, M.rail_glass, M.frame, M.dark_stone, M.red])
            lv['fac_base'] = V(0, G0 + i * H + SLAB, 0)
            # fascia marcapiano
            mb = MB().box(-0.32, -0.04, -0.32, BW + 0.32, SLAB + 0.04, BD + 0.32, 2, 'XxZz')
            if i >= 1:
                for a, b in ((BAL['x0'], BAL['x1']), (BW - BAL['x1'], BW - BAL['x0'])):
                    mb.box(a - 0.02, -0.26, BAL['z1'] - 0.02, b + 0.02, 0.04, BAL['z1'] + 0.04, 2, 'XxZ')
            lv['band'] = mk(mb, f'band{i}', [M.stone])
            lv['band_base'] = V(0, G0 + i * H, 0)
        else:
            # copertura
            mb = MB()
            mb.box(-0.3, 0, -0.3, BW + 0.3, 1.1, 0, 2, mat=0)
            mb.box(-0.3, 0, BD, BW + 0.3, 1.1, BD + 0.3, 2, mat=0)
            mb.box(-0.3, 0, 0, 0, 1.1, BD, 2, mat=0)
            mb.box(BW, 0, 0, BW + 0.3, 1.1, BD, 2, mat=0)
            mb.box(13.4, 0, 2.2, 16.6, 3.0, 7.8, 2, mat=0)
            mb.box(13.38, 2.45, 2.18, 16.62, 3.0, 7.82, 2, 'XxZz', mat=1)
            mb.floor(0.4, 0.4, 13.2, 9.6, 0.12, 3, mat=2)
            mb.floor(16.8, 0.4, BW - 0.4, 9.6, 0.12, 3, mat=2)
            for x0, x1 in ((1.2, 12.4), (17.6, 28.8)):
                z = 1.0
                while z < 8.6:
                    mb.quad((x0, 0.25, z + 1.1), (x1 - x0, 0, 0), (0, 0.5, -1.0), mat=3)
                    mb.quad((x1, 0.25, z + 1.1), (-(x1 - x0), 0, 0), (0, 0.5, -1.0), mat=3)
                    z += 1.55
            lv['roof'] = mk(mb, 'roof', [M.white, M.red, M.grass, M.pv])
            lv['roof_base'] = V(0, G0 + i * H + SLAB, 0)
        L[i] = lv
    # vano scala che anticipa la struttura
    core = MB().box(13.6, 0, 2.4, 16.4, 1, 7.6, 3).build('core', [M.concrete], coll)
    core.location = V(0, G0, 0)
    return L, core


def build_lot(M, coll):
    """Marciapiede, terra, scavo (pareti e fondo) e fondazione."""
    e, y = 4, G0
    mb = MB()
    for (x0, z0, x1, z1) in ((LOT['x0'], LOT['z0'], LOT['x1'], LOT['z0'] + e), (LOT['x0'], LOT['z1'] - e, LOT['x1'], LOT['z1']),
                             (LOT['x0'], LOT['z0'] + e, LOT['x0'] + e, LOT['z1'] - e), (LOT['x1'] - e, LOT['z0'] + e, LOT['x1'], LOT['z1'] - e)):
        mb.box(x0, 0, z0, x1, y, z1, 4, 'XxZzY', mat=0)
    ix0, ix1, iz0, iz1 = LOT['x0'] + e, LOT['x1'] - e, LOT['z0'] + e, LOT['z1'] - e
    for (x0, z0, x1, z1) in ((ix0, iz0, ix1, PIT['z0']), (ix0, PIT['z1'], ix1, iz1), (ix0, PIT['z0'], PIT['x0'], PIT['z1']), (PIT['x1'], PIT['z0'], ix1, PIT['z1'])):
        mb.floor(x0, z0, x1, z1, y, 6, mat=1)
    sidewalk = mb.build('lot', [M.paving, M.dirt], coll)
    # fondo dello scavo (si abbassa) e pareti (scalate in altezza)
    pw, pd_ = PIT['x1'] - PIT['x0'], PIT['z1'] - PIT['z0']
    pit_floor = MB().floor(0, 0, pw, pd_, 0, 6).build('pit_floor', [M.dirt], coll)
    pit_floor.location = V(PIT['x0'], y, PIT['z0'])
    mb = MB()
    mb.quad((PIT['x0'], -1, PIT['z0']), (pw, 0, 0), (0, 1, 0), 3, mat=0)
    mb.quad((PIT['x1'], -1, PIT['z1']), (-pw, 0, 0), (0, 1, 0), 3, mat=0)
    mb.quad((PIT['x0'], -1, PIT['z1']), (0, 0, -pd_), (0, 1, 0), 3, mat=0)
    mb.quad((PIT['x1'], -1, PIT['z0']), (0, 0, pd_), (0, 1, 0), 3, mat=0)
    walls = mb.build('pit_walls', [M.dirt_wall], coll)
    walls.location = V(0, y, 0)
    found = MB().box(PIT['x0'] + 0.01, -1, PIT['z0'] + 0.01, PIT['x1'] - 0.01, 0, PIT['z1'] - 0.01, 3, 'XxZzY').build('foundation', [M.concrete], coll)
    found.location = V(0, y, 0)
    # prati e camminamenti finali (scalati da 0 a 1)
    lawns = []
    rects = [(ix0, iz0, ix1, PIT['z0'] - 0.6), (ix0, PIT['z0'] - 0.6, PIT['x0'] - 0.6, iz1), (PIT['x1'] + 0.6, PIT['z0'] - 0.6, ix1, iz1),
             (PIT['x0'] - 0.6, PIT['z1'] + 0.6, 12, iz1), (18, PIT['z1'] + 0.6, PIT['x1'] + 0.6, iz1)]
    for k, (x0, z0, x1, z1) in enumerate(rects):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        o = MB().floor(x0 - cx, z0 - cz, x1 - cx, z1 - cz, 0, 4).build(f'lawn{k}', [M.grass], coll)
        o.location = V(cx, y + 0.02, cz)
        lawns.append(o)
    path = MB().floor(-3, PIT['z1'] - 0.6, 3, iz1, 0, 4).floor(PIT['x0'] - 15 - 0.6, PIT['z0'] - 0.6, PIT['x1'] - 15 + 0.6, PIT['z1'] + 0.6, -0.005, 4).build('paths', [M.paving], coll)
    path.location = V(15, y + 0.025, 0)
    lot_trees = [(x, z, 6 + (i % 3), 2.2 + (i % 4) * 0.25, (i * 0.37) % 1) for i, (x, z) in enumerate(
        [(-5, -10), (3, -11), (12, -10.5), (21, -11), (30, -10), (37, -9), (-5, 2), (36, 3), (-4, 16), (3.5, 18), (26.5, 18), (35, 16)])]
    return dict(pit_floor=pit_floor, pit_walls=walls, found=found, lawns=lawns, path=path, lot_trees=lot_trees)
