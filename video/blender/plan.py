"""Pianta arredata vista dall'alto (still ad alta qualità) con il balcone ondulato dell'edificio.

Uso: python plan.py --res 2400 1920 --samples 48 --out out/plan.png"""
import argparse, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
from common import V, hexc, mat_basic, mat_noise, mat_leaves
from interior import build_interior, interior_mats

ap = argparse.ArgumentParser()
ap.add_argument('--res', nargs=2, type=int, default=[2400, 1920])
ap.add_argument('--samples', type=int, default=48)
ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'plan.png'))
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'; cy.samples = args.samples; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 4; cy.glossy_bounces = 2; cy.caustics_reflective = False; cy.caustics_refractive = False
cy.sample_clamp_indirect = 4
sc.render.threads_mode = 'FIXED'; sc.render.threads = os.cpu_count() or 4
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

coll = sc.collection
IM = interior_mats()
build_interior(coll, IM, with_ceiling=False)

# ---------- balcone ondulato come nella facciata ----------
def wave(x):
    return 1.55 + 0.55 * math.sin((x - 1.0) / 14.0 * 2 * math.pi * 1.0) + 0.15 * math.sin(x * 1.3)
X0, X1 = -0.7, 14.7
N = 120
outer = []
for i in range(N + 1):
    x = X0 + (X1 - X0) * i / N
    outer.append((x, 10 + wave(min(max(x, 0.3), 13.7))))
# estremità arrotondate
def rounded(pts):
    L = []
    (xa, za), (xb, zb) = pts[0], pts[-1]
    for j in range(10):
        a = math.pi / 2 + j / 9 * math.pi / 2
        L.append((xa + 0.0 * math.cos(a), 10 + (za - 10) * (0.5 + 0.5 * math.sin(a))))
    return L
slab_mat = mat_noise('bal_slab', hexc('#b9b5ae'), hexc('#cbc7c0'), scale=5, rough=0.85, bump=0.15)
parapet_mat = mat_noise('bal_par', hexc('#a9a59f'), hexc('#bdb9b2'), scale=7, rough=0.9, bump=0.25)
soil = mat_noise('soil', hexc('#3b2c20'), hexc('#5a4332'), scale=30, rough=1.0, bump=0.6, voronoi=True)

def ribbon(pts_in, pts_out, y0, y1, mat, name):
    bm = bmesh.new()
    vs = []
    for (a, b) in zip(pts_in, pts_out):
        vs.append([bm.verts.new(V(a[0], y0, a[1])), bm.verts.new(V(b[0], y0, b[1])), bm.verts.new(V(b[0], y1, b[1])), bm.verts.new(V(a[0], y1, a[1]))])
    for i in range(len(vs) - 1):
        for k in range(4):
            bm.faces.new((vs[i][k], vs[i + 1][k], vs[i + 1][(k + 1) % 4], vs[i][(k + 1) % 4]))
    bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); me.materials.append(mat)
    return ob

inner = [(x, 10.0) for x, _ in outer]
ribbon(inner, outer, -0.32, -0.02, slab_mat, 'bal_slab')
par_in = [(x, z - 0.14) for x, z in outer]
ribbon(par_in, outer, -0.02, 1.0, parapet_mat, 'bal_parapet')
pl_in = [(x, z - 0.75) for x, z in outer]
ribbon(pl_in, par_in, -0.02, 0.55, parapet_mat, 'planter')
ribbon([(x, z - 0.72) for x, z in outer], [(x, z - 0.17) for x, z in outer], 0.55, 0.62, soil, 'soil')
# fianchi del balcone
for xs in ((X0, 0.0), (14.0, X1)):
    pass

# piante nelle fioriere: cespugli folti alle estremità, come nella foto
import random
random.seed(5)
leaf = mat_leaves('bal_leaves', hexc('#2f5524'), hexc('#6d9a3e'))
leaf2 = mat_leaves('bal_leaves2', hexc('#3d6a2a'), hexc('#9bb84a'))
def bush(x, z, r, h, mat):
    """pianta a rosetta: foglie allungate disposte a raggiera, leggermente sollevate."""
    bm = bmesh.new()
    nl = random.randint(9, 15)
    for k in range(nl):
        ang = k / nl * 2 * math.pi + random.uniform(-0.2, 0.2)
        L = r * random.uniform(0.75, 1.25); wdt = L * random.uniform(0.16, 0.26)
        lift = random.uniform(0.25, 0.7)
        segs = 8; prev = None
        for i in range(segs + 1):
            t = i / segs
            w = wdt * math.sin(math.pi * min(t * 1.05, 1)) * (1 - 0.3 * t)
            d = L * t
            up = h * 0.25 + d * math.sin(lift) - (d ** 2) * 0.35 / max(L, 0.1)
            cx, cz = x + math.cos(ang) * d * math.cos(lift), z + math.sin(ang) * d * math.cos(lift)
            px, pz = -math.sin(ang) * w, math.cos(ang) * w
            a_ = bm.verts.new(V(cx + px, 0.62 + up, cz + pz)); m_ = bm.verts.new(V(cx, 0.62 + up + w * 0.25, cz)); b_ = bm.verts.new(V(cx - px, 0.62 + up, cz - pz))
            if prev:
                bm.faces.new((prev[0], prev[1], m_, a_)); bm.faces.new((prev[1], prev[2], b_, m_))
            prev = (a_, m_, b_)
    me = bpy.data.meshes.new('leafs'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('plant', me); coll.objects.link(ob); me.materials.append(mat)
for (xa, xb, dens) in ((-0.5, 3.6, 14), (9.8, 14.5, 15), (5.2, 6.6, 4)):
    for i in range(dens):
        x = random.uniform(xa, xb)
        zz = 10 + wave(min(max(x, 0.3), 13.7)) - 0.45
        bush(x, zz + random.uniform(-0.12, 0.12), random.uniform(0.45, 0.85), random.uniform(0.6, 1.1), leaf if i % 2 else leaf2)

# ---------- luci e camera ----------
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.9, 0.93, 1.0, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.6; sd.angle = math.radians(4); sd.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new('sun', sd); coll.objects.link(sun)
sun.rotation_euler = (math.radians(32), math.radians(-18), math.radians(25))
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 17.6
cam = bpy.data.objects.new('cam', cd); coll.objects.link(cam); sc.camera = cam
cam.location = V(7.0, 30, 6.35)
cam.rotation_euler = (0, 0, 0)
cd.clip_end = 100
os.makedirs(os.path.dirname(args.out), exist_ok=True)
sc.render.filepath = args.out
bpy.ops.render.render(write_still=True)
# posizioni delle etichette (coordinate normalizzate dell'immagine)
import json
from bpy_extras.object_utils import world_to_camera_view
from interior import ROOMS
lab = []
for name, area, (lx, lz), *_ in ROOMS:
    p = world_to_camera_view(sc, cam, V(lx, 0, lz))
    lab.append(dict(name=name, area=area, x=p.x, y=1 - p.y))
corners = {k: list(world_to_camera_view(sc, cam, V(x, 0, z)))[:2] for k, (x, z) in dict(tl=(0, 0), tr=(14, 0), bl=(0, 10), br=(14, 10)).items()}
json.dump(dict(labels=lab, corners={k: [v[0], 1 - v[1]] for k, v in corners.items()}), open(args.out.replace('.png', '.json'), 'w'), ensure_ascii=False)
print('done')
