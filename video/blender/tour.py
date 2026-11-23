"""Tour dell'appartamento in Blender/Cycles: plastico che ruota, poi visita a altezza d'occhi al tramonto.

Uso: python tour.py --res 1280 720 --samples 8 --frames 1 432 --step 2 [--still 200]"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

from common import G0, YF, Mats, V, build_city, emission_set, hexc, make_tree_protos, place_trees
from interior import build_interior, interior_mats

N = 432
SWITCH = 140
ap = argparse.ArgumentParser()
ap.add_argument('--res', nargs=2, type=int, default=[1280, 720])
ap.add_argument('--samples', type=int, default=8)
ap.add_argument('--frames', nargs=2, type=int, default=[1, N])
ap.add_argument('--step', type=int, default=2)
ap.add_argument('--still', type=int, default=0)
ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'tour'))
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])


def clamp01(x):
    return max(0.0, min(1.0, x))


def io(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def lin(f, a, b):
    return clamp01((f - a) / (b - a))


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
cy.diffuse_bounces = 3
cy.glossy_bounces = 2
cy.transmission_bounces = 6
cy.transparent_max_bounces = 8
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.sample_clamp_indirect = 5
cy.use_fast_gi = True
cy.ao_bounces_render = 2
sc.render.use_persistent_data = True
sc.render.threads_mode = 'FIXED'
sc.render.threads = os.cpu_count() or 4
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.resolution_percentage = 100
sc.render.fps = 24
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'
for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try:
        sc.view_settings.look = look
        break
    except Exception:
        pass

root = sc.collection
M = Mats()
city_coll = bpy.data.collections.new('city')
root.children.link(city_coll)
city, trees, _ = build_city(M, city_coll)
protos = make_tree_protos(M, city_coll)
place_trees(trees, protos, city_coll)
# la notte non è ancora arrivata: qualche finestra accesa
for m in M.fac:
    emission_set(m, 0.5)
emission_set(M.shop, 1.2)
emission_set(M.lamp_head, 10)

IM = interior_mats()
apt = bpy.data.collections.new('apt')
root.children.link(apt)
apt_root = bpy.data.objects.new('apt_root', None)
apt.objects.link(apt_root)
apt_root.location = V(0, G0 + YF, 0)
for o in build_interior(apt, IM, with_ceiling=True, hide_doors=()):
    o.parent = apt_root
# piano bianco del plastico
model_coll = bpy.data.collections.new('model')
root.children.link(model_coll)
bpy.ops.mesh.primitive_plane_add(size=400, location=V(7, G0 + YF - 0.33, 5.8))
ground = bpy.context.active_object
for c in list(ground.users_collection):
    c.objects.unlink(ground)
model_coll.objects.link(ground)
from common import mat_basic
ground.data.materials.append(mat_basic('studio', hexc('#efece6'), 0.9))

ceil = bpy.data.objects['apt_ceiling']
spots = [o for o in apt.objects if o.data is not None and len(getattr(o.data, 'materials', [])) and o.data.materials[0] == IM['spot']]

# ---------- mondo: cielo al tramonto / studio bianco ----------
world = bpy.data.worlds.new('world')
sc.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes['Background']
sky = wn.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_disc = True
sky.sun_size = math.radians(1.2)
sky.aerosol_density = 2.2
sky.altitude = 120
mix = wn.nodes.new('ShaderNodeMixRGB')
mix.inputs['Color2'].default_value = (0.92, 0.91, 0.89, 1)
wn.links.new(sky.outputs['Color'], mix.inputs['Color1'])
wn.links.new(mix.outputs['Color'], bg.inputs['Color'])
el, az = math.radians(4.0), math.radians(28)
dB = V(math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el))
sky.sun_elevation = el
sky.sun_rotation = math.atan2(dB.x, dB.y)
sun_d = bpy.data.lights.new('sun', 'SUN')
sun_d.angle = math.radians(1.0)
sun = bpy.data.objects.new('sun', sun_d)
root.objects.link(sun)
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = (-dB).to_track_quat('-Z', 'Y')
# luci di riempimento: pannello del plastico e plafoniere interne
ad = bpy.data.lights.new('studio', 'AREA')
ad.size = 30
studio = bpy.data.objects.new('studio', ad)
root.objects.link(studio)
studio.location = V(4, G0 + YF + 22, 14)
studio.rotation_mode = 'QUATERNION'
studio.rotation_quaternion = (V(7, G0 + YF, 5.8) - studio.location).to_track_quat('-Z', 'Y')
fills = []
for (x, y, e) in ((2.5, 7.0, 200), (6.5, 6.5, 150), (12.2, 2.6, 130), (8.5, 2.0, 80), (12.4, 7.6, 80), (5.7, 1.3, 50)):
    l = bpy.data.lights.new('fill', 'AREA')
    l.size = 1.2
    l.energy = e
    l.color = (1.0, 0.92, 0.82)
    o = bpy.data.objects.new('fill', l)
    root.objects.link(o)
    o.location = V(x, G0 + YF + 2.6, y)
    fills.append((o, e))

cam_d = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_d)
root.objects.link(cam)
sc.camera = cam
cam_d.sensor_fit = 'AUTO'
cam_d.sensor_width = 36
cam_d.clip_start = 0.05
cam_d.clip_end = 6000
cam_d.dof.use_dof = True

FY = G0 + YF


def P(x, z, y=1.55):
    return V(x, FY + y, z)


KEYS = [(SWITCH, P(8.4, 4.75, 1.7), P(2.0, 9.8, 1.1)), (195, P(6.8, 5.9), P(1.5, 10.6, 1.2)), (247, P(5.0, 7.3), P(0.4, 5.3, 1.1)),
        (290, P(4.1, 8.6), P(7.4, 7.0, 0.9)), (328, P(5.4, 9.3), P(6.2, 13.5, 1.3)), (374, P(8.0, 4.7), P(11.8, 4.55, 1.4)),
        (412, P(11.75, 4.5), P(11.6, 2.0, 0.8)), (N, P(12.6, 4.15), P(10.9, 1.7, 0.9))]


def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def path(f, idx):
    i = 0
    while i < len(KEYS) - 2 and f > KEYS[i + 1][0]:
        i += 1
    a, b = KEYS[i], KEYS[i + 1]
    u = lin(f, a[0], b[0])
    u = u * u * (3 - 2 * u) * 0.35 + u * 0.65
    pts = [k[idx] for k in KEYS]
    p0 = pts[max(0, i - 1)]
    p3 = pts[min(len(pts) - 1, i + 2)]
    return cr(p0, pts[i], pts[i + 1], p3, u)


def update(scene, *_):
    f = scene.frame_current
    inside = f >= SWITCH
    city_coll.hide_render = not inside
    model_coll.hide_render = inside
    ceil.hide_render = not inside
    for s in spots:
        s.hide_render = not inside
    mix.inputs['Fac'].default_value = 0.0 if inside else 1.0
    bg.inputs['Strength'].default_value = 0.55 if inside else 1.0
    sun_d.energy = 3.2 if inside else 1.2
    sun_d.color = (1.0, 0.62, 0.36) if inside else (1, 0.97, 0.92)
    ad.energy = 0 if inside else 9000
    for o, e in fills:
        o.data.energy = e if inside else 0
    if not inside:
        c = Vector(V(7, FY + 0.4, 5.8))
        th = math.radians(-38 + 66 * io(lin(f, 0, 125)))
        dive = io(lin(f, 115, SWITCH))
        ph = math.radians(40 - 30 * dive)
        d = (27 - 4 * lin(f, 0, 115)) * (1 - dive) + 2.2 * dive
        t = c.lerp(Vector(V(4.2, FY + 1.2, 8.0)), dive)
        off = V(math.sin(th) * math.cos(ph) * d, math.sin(ph) * d, math.cos(th) * math.cos(ph) * d)
        pos = t + off
        cam_d.lens = 18 / math.tan(math.radians((32 + 20 * dive) / 2)) * 0.5625
        cam_d.dof.aperture_fstop = 11
    else:
        pos, t = path(f, 1), path(f, 2)
        cam_d.lens = 18 / math.tan(math.radians(29)) * 0.5625 / 0.5625 * 0.62
        cam_d.dof.aperture_fstop = 5.6
    cam.location = pos
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (t - pos).to_track_quat('-Z', 'Y')
    cam_d.dof.focus_distance = max(0.5, (t - pos).length)


bpy.app.handlers.frame_change_pre.append(update)
os.makedirs(args.out, exist_ok=True)
if args.still:
    sc.frame_set(args.still)
    sc.render.filepath = os.path.join(args.out, f'still_{args.still:04d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = args.frames
    sc.frame_step = args.step
    sc.render.filepath = os.path.join(args.out, '')
    bpy.ops.render.render(animation=True)
