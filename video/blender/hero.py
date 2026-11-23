"""Animazione Home in Blender/Cycles: il cantiere a Milano, il tramonto, il piano 5° e la pianta arredata.

Uso: python hero.py --res 1440 1440 --samples 24 --frames 1 432 [--still 200]"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Quaternion, Vector

from common import BD, BW, F, G0, H, LEVELS, PIT, SLAB, YF, Mats, V, build_city, emission_set, hexc, make_tree_protos, place_trees
from building import build_building, build_lot
from interior import ROOMS, build_interior, interior_mats

FPS = 24
N = 432
ap = argparse.ArgumentParser()
ap.add_argument('--res', nargs=2, type=int, default=[1440, 1440])
ap.add_argument('--samples', type=int, default=24)
ap.add_argument('--frames', nargs=2, type=int, default=[1, N])
ap.add_argument('--still', type=int, default=0)
ap.add_argument('--step', type=int, default=2)
ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'hero'))
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])

# ---------- utilità di tempo ----------
def clamp01(x):
    return max(0.0, min(1.0, x))


def io(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_c(x):
    return 1 - (1 - x) ** 3


def in_c(x):
    return x ** 3


def lin(f, a, b):
    return clamp01((f - a) / (b - a))


def ease(f, a, b, e=io):
    return e(lin(f, a, b))


T = dict(dig=(18, 48), pour=(48, 66), s0=66, sstep=11, core=(66, 190), f0=105, fstep=12, fdur=12, roof=(222, 250), land=(222, 272),
         sun=(140, 320), lights=(245, 320), floorlit=(285, 305), lift=(330, 366), facoff=(335, 356), interior=325, top=(350, 392))

# ---------- scena ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'
cy.samples = args.samples
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.04
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 5
cy.diffuse_bounces = 2
cy.glossy_bounces = 2
cy.transmission_bounces = 6
cy.transparent_max_bounces = 8
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.sample_clamp_indirect = 6
sc.render.use_persistent_data = True
sc.render.threads_mode = 'FIXED'
sc.render.threads = os.cpu_count() or 4
cy.use_fast_gi = True
cy.ao_bounces_render = 2
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.resolution_percentage = 100
sc.render.fps = FPS
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'
for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try:
        sc.view_settings.look = look
        break
    except Exception:
        pass
sc.render.film_transparent = False

coll = sc.collection
M = Mats()
city, trees, lamp_pts = build_city(M, coll)
protos = make_tree_protos(M, coll)
place_trees(trees, protos, coll)
L, core = build_building(M, coll)
lot = build_lot(M, coll)
lot_tree_obs = place_trees(lot['lot_trees'], protos, coll, 'lt')
lot_tree_base = [o.scale.copy() for o in lot_tree_obs]

# appartamento del piano F (e il gemello specchiato) + vano scala
IM = interior_mats()
apt = bpy.data.collections.new('apt')
coll.children.link(apt)
apt_root = bpy.data.objects.new('apt_root', None)
apt.objects.link(apt_root)
apt_root.location = V(0, G0 + YF, 0)
for o in build_interior(apt, IM):
    o.parent = apt_root
mir = bpy.data.objects.new('apt_mirror', None)
apt.objects.link(mir)
mir.parent = apt_root
mir.location = (BW, 0, 0)
mir.scale = (-1, 1, 1)
for o in build_interior(apt, IM):
    if o.parent is None:
        o.parent = mir

# ---------- luce: cielo fisico + sole ----------
world = bpy.data.worlds.new('world')
sc.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes['Background']
sky = wn.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_disc = False
sky.air_density = 1.0
sky.aerosol_density = 1.6
sky.ozone_density = 1.0
sky.altitude = 120
wn.links.new(sky.outputs['Color'], bg.inputs['Color'])
sun_data = bpy.data.lights.new('sun', 'SUN')
sun_data.angle = math.radians(0.8)
sun = bpy.data.objects.new('sun', sun_data)
coll.objects.link(sun)
bb = bpy.data.lights.new('apt_light', 'AREA')
bb.shape = 'RECTANGLE'
bb.size, bb.size_y = 16, 12
bb.color = (1.0, 0.9, 0.78)
apt_light = bpy.data.objects.new('apt_light', bb)
coll.objects.link(apt_light)
apt_light.location = V(7, G0 + YF + 7.5, 5.8)

cam_data = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_data)
coll.objects.link(cam)
sc.camera = cam
cam_data.sensor_fit = 'AUTO'
cam_data.sensor_width = 36
cam_data.clip_start = 0.3
cam_data.clip_end = 6000
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 6.0

# ---------- regia ----------
KEYS = [
    (0, (15, 4, 5), 40, 21, 190),
    (310, (15, 17, 5), 22, 12, 105),
    (350, (7, YF + 1.5, BD + 0.5), 8, 22, 26),
    (392, (7, YF, 5.8), 0, 90, 36),
    (N, (7, YF, 5.8), 0, 90, 34.5),
]


def cam_state(f):
    i = 0
    while i < len(KEYS) - 2 and f > KEYS[i + 1][0]:
        i += 1
    a, b = KEYS[i], KEYS[i + 1]
    u = lin(f, a[0], b[0])
    u = u if i == 3 else io(u)
    m = lambda p, q: p + (q - p) * u
    t = [m(a[1][k], b[1][k]) for k in range(3)]
    th = math.radians(m(a[2], b[2]))
    ph = math.radians(min(89.95, m(a[3], b[3])))
    d = math.exp(m(math.log(a[4]), math.log(b[4])))
    pos3 = (t[0] + math.sin(th) * math.cos(ph) * d, t[1] + math.sin(ph) * d, t[2] + math.cos(th) * math.cos(ph) * d)
    return V(*pos3), V(t[0], t[1] + G0, t[2]), math.degrees(ph), d


# indici dei piani illuminati la sera
LIT = [0.45, 0.0, 0.65, 0.3, 0.0, 1, 0.55, 0.0, 0.7, 0.35]


def place(ob, base, dz=0.0):
    ob.location = (base.x, base.y, base.z + dz)


def update(scene, *_):
    f = scene.frame_current
    # scavo e fondazione
    dig, pour = ease(f, *T['dig']), ease(f, *T['pour'], out_c)
    pd = PIT['depth'] * dig
    lot['pit_floor'].location.z = G0 - pd
    lot['pit_walls'].hide_render = pd < 0.01
    lot['pit_walls'].scale.z = max(0.001, pd)
    lot['found'].hide_render = pour <= 0
    lot['found'].scale.z = max(0.001, pd * pour)
    lot['found'].location.z = G0 - pd + pd * pour
    # piani
    lift = ease(f, *T['lift'], in_c)
    facoff = ease(f, *T['facoff'])
    for i, lv in L.items():
        s0 = T['s0'] + i * T['sstep']
        slabS = ease(f - s0, 0, 7, out_c)
        colS = ease(f - s0, 5, 12, out_c)
        dz = lift * (34 + (i - F) * 7) if i > F else 0.0
        gone = dz > 70
        lv['slab'].hide_render = slabS <= 0 or gone
        lv['slab'].scale.x = max(0.001, slabS)
        place(lv['slab'], lv['slab_base'], dz)
        if 'cols' in lv:
            lv['cols'].hide_render = colS <= 0 or gone or (i == F and f > T['interior'])
            lv['cols'].scale.z = max(0.001, colS * (H - SLAB))
            place(lv['cols'], lv['cols_base'], dz)
            fs = ease(f - (T['f0'] + i * T['fstep']), 0, T['fdur'], out_c)
            fsc = fs * (1 - facoff) if i == F else fs
            lv['fac'].hide_render = fsc <= 0.001 or gone
            lv['fac'].scale.z = max(0.001, fsc)
            place(lv['fac'], lv['fac_base'], dz)
            lv['band'].hide_render = fs <= 0.001 or gone or (i == F and facoff > 0.99)
            lv['band'].scale.z = max(0.001, fs)
            place(lv['band'], lv['band_base'], dz)
        if 'roof' in lv:
            r = ease(f, *T['roof'], out_c)
            lv['roof'].hide_render = r <= 0 or gone
            lv['roof'].scale.z = max(0.001, r)
            place(lv['roof'], lv['roof_base'], dz)
    ch = lin(f, *T['core']) * (LEVELS * H + 3)
    core.hide_render = ch < 0.05 or f > T['lift'][0] + 10
    core.scale.z = max(0.001, ch)
    # giardino
    for k, o in enumerate(lot['lawns']):
        s = ease(f, T['land'][0] + 5 * k, T['land'][0] + 30 + 5 * k, out_c)
        o.hide_render = s <= 0
        o.scale = (max(0.001, s), max(0.001, s), 1)
    ps = ease(f, T['land'][0] + 10, T['land'][0] + 40, out_c)
    lot['path'].hide_render = ps <= 0
    lot['path'].scale = (1, max(0.001, ps), 1)
    for k, o in enumerate(lot_tree_obs):
        s = ease(f, T['land'][0] + 3 * k, T['land'][0] + 40 + 3 * k, out_c)
        o.hide_render = s <= 0
        o.scale = lot_tree_base[k] * max(0.001, s)
    # appartamento
    show_apt = f >= T['interior']
    apt.hide_render = not show_apt
    # sole e cielo
    s = lin(f, *T['sun'])
    el = math.radians(30 - 28.5 * s ** 0.9)
    az = math.radians(-30 - 115 * s)
    d3 = (math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el))
    dB = V(*d3)
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = (-dB).to_track_quat('-Z', 'Y')
    top = ease(f, *T['top'])
    temp = 5600 - 3300 * s ** 1.4
    sun_data.color = blackbody(temp)
    sun_data.energy = (4.2 - 3.4 * s ** 1.5) * (1 - 0.85 * top)
    sky.sun_elevation = el
    sky.sun_rotation = math.atan2(dB.x, dB.y)
    bg.inputs['Strength'].default_value = (0.32 - 0.12 * s) * (1 - 0.6 * top)
    # luci della sera
    night = ease(f, *T['lights'])
    fl = ease(f, *T['floorlit'])
    for m in M.fac:
        emission_set(m, night * 2.2)
    emission_set(M.shop, night * 2.6)
    emission_set(M.lamp_head, ease(f, T['lights'][0] - 20, T['lights'][0] + 30) * 40)
    for i, g in enumerate(M.glass):
        base = LIT[i] * night * 3.0
        emission_set(g, max(base, fl * 14) if i == F else base)
    bb.energy = 1500 * ease(f, T['interior'] + 15, T['top'][1])
    # camera
    pos, tgt, ph, d = cam_state(f)
    cam.location = pos
    dirv = (tgt - pos).normalized()
    q = dirv.to_track_quat('-Z', 'Y')
    k = clamp01((ph - 55) / (89.95 - 55))
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = q.slerp(Quaternion(), k) if k > 0 else q
    cam_data.lens = 18 / math.tan(math.radians(20))
    cam_data.dof.focus_distance = (tgt - pos).length
    cam_data.dof.aperture_fstop = 8.0 if f < 300 else 4.0


def blackbody(t):
    # approssimazione RGB lineare del corpo nero
    t = t / 100
    r = 255 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    g = 99.47 * math.log(t) - 161.12 if t <= 66 else 288.1 * (t - 60) ** -0.0755
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5 * math.log(t - 10) - 305.04)
    c = [max(0, min(255, v)) / 255 for v in (r, g, b)]
    return tuple(x ** 2.2 for x in c)


bpy.app.handlers.frame_change_pre.append(update)
os.makedirs(args.out, exist_ok=True)

# posizioni delle etichette sulla pianta (vista zenitale finale)
from bpy_extras.object_utils import world_to_camera_view

sc.frame_set(400)
labels = []
for name, area, (lx, ly), *_ in ROOMS:
    p = world_to_camera_view(sc, cam, V(lx, G0 + YF, ly))
    labels.append(dict(name=name, area=area, x=p.x, y=1 - p.y))
dims = {k: list(world_to_camera_view(sc, cam, V(x, G0 + YF, y)))[:2] for k, (x, y) in dict(tl=(0, 0), tr=(14, 0), bl=(0, BD), title=(0, BD + 2.3)).items()}
with open(os.path.join(args.out, 'labels.json'), 'w') as fh:
    json.dump(dict(labels=labels, dims={k: [v[0], 1 - v[1]] for k, v in dims.items()}), fh, ensure_ascii=False)

if args.still:
    sc.frame_set(args.still)
    sc.render.filepath = os.path.join(args.out, f'still_{args.still:04d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = args.frames
    sc.frame_step = args.step
    sc.render.filepath = os.path.join(args.out, '')
    bpy.ops.render.render(animation=True)
