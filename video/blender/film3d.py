"""Pianta animata + tour 3D dentro l'appartamento (Blender/Cycles), un unico piano sequenza.

Uso: python film3d.py --res 1280 1280 --samples 20 --frames 0 600 --step 2 [--still 400] --out out/film3d"""
import argparse, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
from common import V, hexc, MB
from interior import ROOMS, INNER, DOORS, WALL_H, ITEMS, CYLS, PLANTS

HERE = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.join(HERE, 'tex2')
T1 = os.path.join(HERE, 'tex')
ap = argparse.ArgumentParser()
ap.add_argument('--res', nargs=2, type=int, default=[1280, 1280])
ap.add_argument('--samples', type=int, default=20)
ap.add_argument('--frames', nargs=2, type=int, default=[0, 600])
ap.add_argument('--step', type=int, default=2)
ap.add_argument('--still', type=int, default=-1)
ap.add_argument('--out', default=os.path.join(HERE, 'out', 'film3d'))
ap.add_argument('--labels', action='store_true')
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
N = 520
BD = 10.0
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'; cy.samples = args.samples
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 8
cy.caustics_reflective = False; cy.caustics_refractive = False
cy.sample_clamp_indirect = 3.0
cy.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.render.threads_mode = 'FIXED'; sc.render.threads = os.cpu_count() or 4
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.fps = 24
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
sc.view_settings.exposure = 0.0
ROOT = sc.collection

# ====================== materiali ======================
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    return m, nt, b

def pbr(name, col, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, spec=0.5, emit=None, emit_s=0.0, sss=0.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = emit_s
    return m

def tex_node(nt, path, color=True, scale=1.0, proj='FLAT'):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True)
    if not color: t.image.colorspace_settings.name = 'Non-Color'
    t.projection = proj
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    return t

def img_mat(name, path, rough=0.5, rough_path=None, bump_path=None, bump=0.2, scale=1.0, coat=0.0, rough_mul=1.0):
    m, nt, b = node_mat(name)
    t = tex_node(nt, path, True, scale)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if rough_path:
        r = tex_node(nt, rough_path, False, scale)
        mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = rough_mul
        nt.links.new(r.outputs['Color'], mt.inputs[0]); nt.links.new(mt.outputs[0], b.inputs['Roughness'])
    if bump_path:
        bb = tex_node(nt, bump_path, False, scale)
        bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = bump; bn.inputs['Distance'].default_value = 0.002
        nt.links.new(bb.outputs['Color'], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    return m

def fabric(name, col, rough=0.92, sheen=0.7, scale=40.0, bump=0.25):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Roughness'].default_value = 0.4
    b.inputs['Specular IOR Level'].default_value = 0.3
    t = tex_node(nt, os.path.join(T2, 'weave.jpg'), False, scale)
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3.0
    mix = nt.nodes.new('ShaderNodeMath'); mix.operation = 'ADD'
    nt.links.new(t.outputs['Color'], mix.inputs[0]); nt.links.new(n.outputs['Fac'], mix.inputs[1])
    bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = bump; bn.inputs['Distance'].default_value = 0.001
    nt.links.new(mix.outputs[0], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    # leggera variazione di colore (usura)
    cr = nt.nodes.new('ShaderNodeMixRGB'); cr.blend_type = 'MULTIPLY'; cr.inputs['Fac'].default_value = 0.12
    cr.inputs['Color1'].default_value = (*col, 1)
    nt.links.new(n.outputs['Color'], cr.inputs['Color2']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    return m

def plaster(name, col, scale=2.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.88
    b.inputs['Specular IOR Level'].default_value = 0.35
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 60; n.inputs['Detail'].default_value = 8
    bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = 0.04; bn.inputs['Distance'].default_value = 0.002
    nt.links.new(n.outputs['Fac'], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    return m

def glass(name, col=(0.96, 0.98, 0.98), rough=0.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.45
    try:
        b.inputs['Thin Walled'].default_value = True
    except Exception:
        pass
    return m

def sheer(name):
    m, nt, b = node_mat(name)
    out = nt.nodes['Material Output']
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (0.95, 0.93, 0.9, 1)
    tp = nt.nodes.new('ShaderNodeBsdfTransparent')
    b.inputs['Base Color'].default_value = (0.95, 0.94, 0.92, 1); b.inputs['Roughness'].default_value = 0.9; b.inputs['Sheen Weight'].default_value = 0.6
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = 0.55
    nt.links.new(b.outputs['BSDF'], m1.inputs[1]); nt.links.new(tr.outputs['BSDF'], m1.inputs[2])
    m2 = nt.nodes.new('ShaderNodeMixShader'); m2.inputs['Fac'].default_value = 0.45
    nt.links.new(m1.outputs['Shader'], m2.inputs[1]); nt.links.new(tp.outputs['BSDF'], m2.inputs[2])
    nt.links.new(m2.outputs['Shader'], out.inputs['Surface'])
    return m

def leaves(name, c1, c2):
    m, nt, b = node_mat(name)
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 4.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Subsurface Weight'].default_value = 0.15
    b.inputs['Coat Weight'].default_value = 0.2
    return m

def fade_mat(m):
    """aggiunge un fattore di dissolvenza (alpha) controllabile: nodo Value 'fade'."""
    nt = m.node_tree; out = nt.nodes['Material Output']
    src = out.inputs['Surface'].links[0].from_socket
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    val = nt.nodes.new('ShaderNodeValue'); val.name = 'fade'; val.outputs[0].default_value = 1.0
    nt.links.new(val.outputs[0], mx.inputs['Fac']); nt.links.new(tp.outputs['BSDF'], mx.inputs[1]); nt.links.new(src, mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return val

c = hexc
MAT = dict(
    oak=img_mat('oak', os.path.join(T2, 'oak.jpg'), 0.4, os.path.join(T2, 'oak_r.jpg'), os.path.join(T2, 'oak_b.jpg'), 0.25, 1.0, coat=0.15, rough_mul=1.0),
    tiles=img_mat('tiles', os.path.join(T1, 'tiles.jpg'), 0.2, None, None, 0.0, 1.0, coat=0.3),
    deck=img_mat('deck', os.path.join(T1, 'deck.jpg'), 0.7, None, os.path.join(T1, 'deck.jpg'), 0.3, 1.0),
    wall=plaster('wall', c('#ece8e1')), ceiling=plaster('ceiling', c('#f3f1ec')),
    stone=img_mat('stone', os.path.join(T2, 'stone.jpg'), 0.85, None, os.path.join(T2, 'stone.jpg'), 0.6, 1.0),
    marble=img_mat('marble', os.path.join(T2, 'marble.jpg'), 0.12, None, None, 0.0, 1.0, coat=0.6),
    slab=plaster('slab', c('#b8b3ab')), frame=pbr('frame', c('#2b2d30'), 0.35, metal=0.6),
    win=glass('win'), lacquer=pbr('lacquer', c('#efede8'), 0.3, coat=0.2), lacquer_g=pbr('lacquer_g', c('#c9c6bf'), 0.35, coat=0.2),
    darkStone=pbr('darkStone', c('#2a2927'), 0.25, coat=0.4), steel=pbr('steel', c('#c4c7cc'), 0.25, metal=1.0),
    black=pbr('black', c('#1b1c1e'), 0.45), blackGloss=pbr('blackGloss', c('#0c0d0e'), 0.05, coat=1.0),
    walnut=None,
    sofa=fabric('sofa', c('#cfc8bc')), sofa2=fabric('sofa2', c('#ddd7cc')), boucle=fabric('boucle', c('#ece7de'), bump=0.6, scale=25),
    ochre=fabric('ochre', c('#b9852f')), teal=fabric('teal', c('#2f5c5a')), rust=fabric('rust', c('#9a4a2e')),
    linen=fabric('linen', c('#f1eee7'), sheen=0.5), duvet=fabric('duvet', c('#e9e5dd'), sheen=0.5), sage=fabric('sage', c('#9aa98a')),
    wool=fabric('wool', c('#cfc6b6'), bump=0.8, scale=18), wool2=fabric('wool2', c('#7d756a'), bump=0.8, scale=18),
    leather=pbr('leather', c('#7a4b2c'), 0.45, coat=0.3), ceramic=pbr('ceramic', c('#f6f5f1'), 0.08, coat=0.6),
    pot=pbr('pot', c('#d2cabd'), 0.75), potDark=pbr('potDark', c('#3a3834'), 0.6),
    lampShade=pbr('lampShade', c('#f3e9d6'), 0.8, emit=c('#ffcf8a'), emit_s=3.0, sss=0.3), bulb=pbr('bulb', c('#ffffff'), 0.5, emit=c('#ffd39a'), emit_s=12.0),
    led=pbr('led', c('#ffffff'), 0.5, emit=c('#ffd8a0'), emit_s=8.0),
    spot=pbr('spot', c('#ffffff'), 0.5, emit=c('#fff0d8'), emit_s=20.0), rail=pbr('rail', c('#8a8d92'), 0.35, metal=0.8),
    art=img_mat('art', os.path.join(T1, 'art.jpg'), 0.8), book1=pbr('book1', c('#8e3b2c'), 0.7), book2=pbr('book2', c('#2e3d57'), 0.7),
    book3=pbr('book3', c('#c9b48a'), 0.7), book4=pbr('book4', c('#4f6b4a'), 0.7), curtain=sheer('curtain'),
    leaf1=leaves('leaf1', c('#2c5122'), c('#5e8c36')), leaf2=leaves('leaf2', c('#365f27'), c('#8fb24a')),
    soil=pbr('soil', c('#3b2c20'), 1.0), parapet=plaster('parapet', c('#aaa69f')), tv=pbr('tv', c('#050506'), 0.08, coat=1.0),
)
def wood_proc(name, c1, c2, scale=3.0):
    m, nt, b = node_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale * 0.12, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 2.0; n.inputs['Detail'].default_value = 6
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 2.2
    wv.inputs['Distortion'].default_value = 6.0; wv.inputs['Detail'].default_value = 3
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector']); nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.6
    nt.links.new(wv.outputs['Fac'], mx.inputs[0]); nt.links.new(n.outputs['Fac'], mx.inputs[2])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(mx.outputs[0], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.4; b.inputs['Coat Weight'].default_value = 0.3; b.inputs['Coat Roughness'].default_value = 0.15
    bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = 0.05
    nt.links.new(mx.outputs[0], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    return m
MAT['walnut'] = wood_proc('walnut', c('#3e2717'), c('#7a5233'))
ceil_fade = fade_mat(MAT['ceiling'])

# ====================== geometria ======================
ANIM = []   # (oggetto, tipo, frame inizio, durata)

def link(ob, coll=ROOT):
    for c2 in list(ob.users_collection): c2.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def weld(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob

def recenter(ob, bottom=True):
    me = ob.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    cen = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs) if bottom else (min(zs) + max(zs)) / 2))
    me.transform(Matrix.Translation(-cen)); ob.location = ob.location + cen
    return ob

def rbox(x0, y0, z0, x1, y1, z1, mat, bev=0.01, seg=3, name='box', anim=None):
    o = weld(MB().box(x0, y0, z0, x1, y1, z1, 1).build(name, [mat], ROOT))
    if bev > 0.002:
        md = o.modifiers.new('b', 'BEVEL'); md.width = min(bev, (x1 - x0) / 2.1, (y1 - y0) / 2.1, (z1 - z0) / 2.1); md.segments = seg
        md.harden_normals = False
        o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
        try:
            o.modifiers.new('wn', 'WEIGHTED_NORMAL')
        except Exception:
            pass
    recenter(o)
    if anim: ANIM.append((o, *anim))
    return o

def cushion(x0, y0, z0, x1, y1, z1, mat, r=0.06, puff=0.012, name='cush', anim=None):
    """cuscino morbido: smusso ampio, suddivisione e rigonfiamento casuale."""
    o = weld(MB().box(x0, y0, z0, x1, y1, z1, 1).build(name, [mat], ROOT))
    md = o.modifiers.new('b', 'BEVEL'); md.width = min(r, (x1 - x0) / 3.5, (y1 - y0) / 3.5, (z1 - z0) / 3.5); md.segments = 3
    sd = o.modifiers.new('s', 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
    tx = bpy.data.textures.new(name + 't', 'CLOUDS'); tx.noise_scale = 0.35
    dp = o.modifiers.new('d', 'DISPLACE'); dp.texture = tx; dp.strength = puff * 0.6; dp.mid_level = 0.5
    o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    recenter(o)
    if anim: ANIM.append((o, *anim))
    return o

def cyl(cx, cz, r, y0, h, mat, verts=48, name='cyl', anim=None, bev=0.004, sx=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=1, depth=1)
    o = link(bpy.context.active_object); o.name = name
    o.location = V(cx, y0 + h / 2, cz); o.scale = (r * sx, r, h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev > 0:
        md = o.modifiers.new('b', 'BEVEL'); md.width = min(bev, h / 2.1, r / 2); md.segments = 2
    o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    o.data.materials.append(mat)
    me = o.data; me.transform(Matrix.Translation(Vector((0, 0, 0.5 * h)))); o.location.z -= 0.5 * h
    if anim: ANIM.append((o, *anim))
    return o

def sphere(cx, y, cz, r, mat, sy=1.0, name='sph', anim=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=V(cx, y, cz))
    o = link(bpy.context.active_object); o.name = name; o.scale = (1, 1, sy)
    o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons)); o.data.materials.append(mat)
    if anim: ANIM.append((o, *anim))
    return o

def plant(x, z, r, h, mats=('leaf1', 'leaf2'), pot=True, base=0.0, anim=None, seed=0):
    rnd = random.Random(seed)
    parts = []
    if pot:
        parts.append(cyl(x, z, r * 0.42, base, h * 0.32, MAT['pot' if rnd.random() < 0.6 else 'potDark'], name='pot'))
        parts.append(cyl(x, z, r * 0.4, base + h * 0.3, 0.02, MAT['soil'], name='soil', bev=0))
    bm = bmesh.new()
    nl = rnd.randint(14, 22); y0 = base + (h * 0.32 if pot else 0)
    for k in range(nl):
        ang = k / nl * 2 * math.pi * 2.3 + rnd.uniform(-0.3, 0.3)
        L = r * rnd.uniform(0.9, 1.5) * (0.7 + 0.6 * (k / nl)); wdt = L * rnd.uniform(0.12, 0.2)
        lift = rnd.uniform(0.5, 1.2)
        segs = 10; prev = None
        for i in range(segs + 1):
            t = i / segs
            w = wdt * math.sin(math.pi * min(t * 1.05, 1)) * (1 - 0.3 * t)
            d = L * t
            up = d * math.sin(lift) - (d ** 2) * 0.55 / max(L, 0.1)
            cx, cz = x + math.cos(ang) * d * math.cos(lift), z + math.sin(ang) * d * math.cos(lift)
            px, pz = -math.sin(ang) * w, math.cos(ang) * w
            a_ = bm.verts.new(V(cx + px, y0 + up, cz + pz)); m_ = bm.verts.new(V(cx, y0 + up + w * 0.2, cz)); b_ = bm.verts.new(V(cx - px, y0 + up, cz - pz))
            if prev:
                bm.faces.new((prev[0], prev[1], m_, a_)); bm.faces.new((prev[1], prev[2], b_, m_))
            prev = (a_, m_, b_)
    me = bpy.data.meshes.new('leaf'); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    o = bpy.data.objects.new('plant', me); ROOT.objects.link(o); me.materials.append(MAT[mats[seed % 2]])
    sd = o.modifiers.new('s', 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
    so = o.modifiers.new('sol', 'SOLIDIFY'); so.thickness = 0.003
    recenter(o)
    parts.append(o)
    if anim:
        for p in parts: ANIM.append((p, anim[0], anim[1], anim[2]))
    return parts

def curtain(x0, x1, z, h=2.62, depth=0.06, waves=None, name='curt', anim=None):
    bm = bmesh.new()
    n = int((x1 - x0) / 0.02); waves = waves or (x1 - x0) / 0.14
    rows = []
    for j in range(2):
        y = 0.02 + j * h
        row = []
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            dz = depth * math.sin(i / n * waves * 2 * math.pi)
            row.append(bm.verts.new(V(x, y, z + dz)))
        rows.append(row)
    for i in range(n):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me); ROOT.objects.link(o); me.materials.append(MAT['curtain'])
    recenter(o)
    if anim: ANIM.append((o, *anim))
    return o

# ---------- tempi: ordine delle stanze ----------
def room_of(x, z):
    for i, (_, _, _, _, rects) in enumerate(ROOMS):
        for (a, b, c_, d) in rects:
            if a - 0.05 <= x <= c_ + 0.05 and b - 0.05 <= z <= d + 0.05:
                return i
    return 0
ROOM_ORDER = [0, 6, 5, 9, 1, 4, 2, 3, 7, 8]
def t_room(x, z):
    return 80 + ROOM_ORDER.index(room_of(x, z)) * 8

# ---------- guscio ----------
F_FLOOR, F_WALL = (14, 22), (36, 40)
for i, (_, _, _, fl, rects) in enumerate(ROOMS):
    for (x0, z0, x1, z1) in rects:
        o = MB().floor(x0, z0, x1, z1, 0.004, 4.0 if fl == 'wood' else 1.2, 0).build('floor', [MAT['oak'] if fl == 'wood' else MAT['tiles']], ROOT)
        recenter(o, bottom=False)
        ANIM.append((o, 'grow', F_FLOOR[0] + ROOM_ORDER.index(i) * 2, F_FLOOR[1]))
slab = MB().box(-0.3, -0.32, -0.3, 14.3, 0, BD + 0.3, 3, 'XxZzy').build('slab', [MAT['slab']], ROOT)
ANIM.append((slab, 'fadein', 0, 14))
T = 0.15
WINDOWS = [('S', 1.0, 3.5), ('S', 4.5, 7.5), ('S', 11.8, 13.2), ('N', 1.2, 3.2), ('N', 7.8, 9.6), ('N', 11.4, 13), ('W', 1, 3)]
walls = []
def wbox(x0, y0, z0, x1, y1, z1, mat='wall'):
    o = rbox(x0, y0, z0, x1, y1, z1, MAT[mat], bev=0.004, seg=1, name='wall')
    walls.append(o)
    return o
for (a, b) in INNER:
    wbox(min(a[0], b[0]) - 0.06, 0, min(a[1], b[1]) - 0.06, max(a[0], b[0]) + 0.06, WALL_H, max(a[1], b[1]) + 0.06)
win_objs, portals = [], []
for s, frm, to in (('N', -T, 14 + T), ('S', -T, 14 + T), ('W', 0, BD), ('E', 0, BD)):
    ws = sorted([(w[1], w[2]) for w in WINDOWS if w[0] == s]); cpos = frm
    def seg(a, b):
        if b - a < 0.01: return
        if s == 'N': wbox(a, 0, -T, b, WALL_H, T)
        if s == 'S': wbox(a, 0, BD - T, b, WALL_H, BD + T)
        if s == 'W': wbox(-T, 0, a, T, WALL_H, b)
        if s == 'E': wbox(14 - T, 0, a, 14 + T, WALL_H, b)
    for (a, b) in ws:
        seg(cpos, a)
        if s in 'NS':
            zz = 0 if s == 'N' else BD
            wbox(a, WALL_H - 0.08, zz - T, b, WALL_H, zz + T)
            g = rbox(a, 0.02, zz - 0.01, b, WALL_H - 0.1, zz + 0.01, MAT['win'], bev=0, name='glass'); win_objs.append(g)
            for xx in [a, b - 0.05] + [a + (b - a) * k / 3 for k in (1, 2)]:
                win_objs.append(rbox(xx, 0, zz - 0.04, xx + 0.05, WALL_H - 0.08, zz + 0.04, MAT['frame'], bev=0.004, name='mull'))
            win_objs.append(rbox(a, 0, zz - 0.04, b, 0.05, zz + 0.04, MAT['frame'], bev=0.004, name='sill'))
            portals.append((s, a, b, zz))
        else:
            wbox(-T, WALL_H - 0.08, a, T, WALL_H, b)
            win_objs.append(rbox(-0.01, 0.02, a, 0.01, WALL_H - 0.1, b, MAT['win'], bev=0, name='glass'))
            for zz_ in (a, b - 0.05):
                win_objs.append(rbox(-0.04, 0, zz_, 0.04, WALL_H - 0.08, zz_ + 0.05, MAT['frame'], bev=0.004, name='mull'))
            portals.append((s, a, b, 0))
        cpos = b
    seg(cpos, to)
# battiscopa nelle zone del tour
for (x0, z0, x1, z1) in ((0.16, 4.07, 4.33, 4.09), (4.47, 4.07, 10.33, 4.09), (4.47, 5.31, 8.73, 5.33)):
    rbox(x0, 0, z0, x1, 0.08, z1, MAT['lacquer'], bev=0.002, seg=1, name='skirting')
for w in walls:
    ANIM.append((w, 'rise', F_WALL[0] + int((w.location.x + w.location.y * 0.3) * 1.2), F_WALL[1]))
for o in win_objs:
    ANIM.append((o, 'rise', 70, 18))
# parete in pietra dietro la TV (parete ovest, z 7.85-10)
stone = MB()
stone.quad((T + 0.003, 0, 10 - T), (0, 0, -(10 - T - 7.85)), (0, WALL_H, 0), mod=1.0, mat=0)
so = stone.build('stonewall', [MAT['stone']], ROOT)
uvl = so.data.uv_layers[0].data
for li, l in enumerate(uvl):
    u, v = l.uv
    l.uv = ((u - so.data.vertices[so.data.loops[li].vertex_index].co.x * 0) , v)
# rimappa UV sull'intera immagine
for poly in so.data.polygons:
    for k, li in enumerate(range(poly.loop_start, poly.loop_start + poly.loop_total)):
        so.data.uv_layers[0].data[li].uv = [(0, 0), (0.62, 0), (0.62, 1), (0, 1)][k]
recenter(so); ANIM.append((so, 'rise', 60, 20))
# soffitto (compare solo in discesa)
ceiling = MB().box(-0.3, WALL_H, -0.3, 14.3, WALL_H + 0.25, BD + 0.3, 3).build('ceiling', [MAT['ceiling']], ROOT)
spots = []
for (x, z) in ((1.5, 5.5), (3.5, 5.5), (1.5, 8.5), (3.5, 8.5), (5.6, 9.0), (7.6, 9.0), (7.5, 4.7), (5.5, 4.7), (9.3, 4.7), (12, 2), (11.8, 4.2)):
    o = cyl(x, z, 0.06, WALL_H - 0.006, 0.006, MAT['spot'], verts=24, name='spot', bev=0)
    spots.append(o)

# ---------- balcone ondulato con fioriere (come in facciata) ----------
def wave(x): return 1.55 + 0.55 * math.sin((x - 1.0) / 14.0 * 2 * math.pi) + 0.15 * math.sin(x * 1.3)
outer = [(-0.7 + 15.4 * i / 120, 10 + wave(min(max(-0.7 + 15.4 * i / 120, 0.3), 13.7))) for i in range(121)]
def ribbon(pin, pout, y0, y1, mat, name):
    bm = bmesh.new(); vs = []
    for (a, b) in zip(pin, pout):
        vs.append([bm.verts.new(V(a[0], y0, a[1])), bm.verts.new(V(b[0], y0, b[1])), bm.verts.new(V(b[0], y1, b[1])), bm.verts.new(V(a[0], y1, a[1]))])
    for i in range(len(vs) - 1):
        for k in range(4): bm.faces.new((vs[i][k], vs[i + 1][k], vs[i + 1][(k + 1) % 4], vs[i][(k + 1) % 4]))
    bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me); ROOT.objects.link(o); me.materials.append(mat); return o
for o in (ribbon([(x, 10.0) for x, _ in outer], outer, -0.32, -0.02, MAT['slab'], 'balslab'),
          ribbon([(x, z - 0.14) for x, z in outer], outer, -0.02, 1.0, MAT['parapet'], 'balpar'),
          ribbon([(x, z - 0.75) for x, z in outer], [(x, z - 0.14) for x, z in outer], -0.02, 0.55, MAT['parapet'], 'planter'),
          ribbon([(x, z - 0.72) for x, z in outer], [(x, z - 0.17) for x, z in outer], 0.55, 0.6, MAT['soil'], 'psoil')):
    ANIM.append((o, 'fadein', 6, 16))
deck = MB().floor(0.8, BD + 0.15, 8.4, BD + 1.0, 0.004, 1.0, 0).build('deck', [MAT['deck']], ROOT); ANIM.append((deck, 'fadein', 10, 16))
k = 0
for (xa, xb, dens) in ((-0.5, 3.6, 12), (9.8, 14.5, 13), (5.2, 6.6, 4)):
    for i in range(dens):
        x = random.uniform(xa, xb); zz = 10 + wave(min(max(x, 0.3), 13.7)) - 0.45
        plant(x, zz + random.uniform(-0.12, 0.12), random.uniform(0.45, 0.8), random.uniform(0.7, 1.2), pot=False, base=0.6, anim=('grow', 140 + random.randint(0, 22), 18), seed=k); k += 1

# ====================== arredi ======================
def A(x, z, extra=0): return ('drop', t_room(x, z) + extra + random.randint(0, 5), 16)
# --- cucina lungo la parete ovest ---
rbox(0.15, 0, 4.2, 0.78, 2.3, 4.85, MAT['lacquer'], 0.008, name='colonna', anim=A(0.4, 4.5))
rbox(0.78, 0.9, 4.3, 0.8, 1.5, 4.8, MAT['blackGloss'], 0.004, name='forno', anim=A(0.4, 4.5))
rbox(0.15, 0.1, 4.85, 0.74, 0.88, 7.6, MAT['lacquer'], 0.006, name='basi', anim=A(0.4, 6))
rbox(0.15, 0, 4.87, 0.70, 0.1, 7.58, MAT['black'], 0.002, name='zoccolo', anim=A(0.4, 6))
for zz in (5.45, 6.05, 6.65, 7.0):
    rbox(0.74, 0.12, zz - 0.003, 0.745, 0.86, zz + 0.003, MAT['black'], 0, name='fuga', anim=A(0.4, 6))
rbox(0.12, 0.88, 4.85, 0.78, 0.92, 7.62, MAT['darkStone'], 0.004, name='top', anim=A(0.4, 6, 3))
rbox(0.32, 0.905, 5.55, 0.6, 0.922, 6.15, MAT['steel'], 0.01, name='lavello', anim=A(0.4, 6, 3))
cyl(0.25, 5.85, 0.02, 0.92, 0.32, MAT['steel'], name='rubinetto', anim=A(0.4, 6, 4))
rbox(0.24, 0.92, 6.55, 0.7, 0.93, 7.2, MAT['blackGloss'], 0.004, name='piano', anim=A(0.4, 6, 4))
rbox(0.15, 1.5, 4.85, 0.5, 2.3, 7.6, MAT['lacquer'], 0.006, name='pensili', anim=A(0.4, 6, 2))
rbox(0.45, 1.49, 4.9, 0.47, 1.5, 7.55, MAT['led'], 0, name='ledcucina', anim=A(0.4, 6, 2))
# isola con top in marmo e sgabelli
rbox(1.9, 0, 4.9, 3.6, 0.88, 5.6, MAT['lacquer_g'], 0.01, name='isola', anim=A(2.7, 5.2))
rbox(1.82, 0.88, 4.86, 3.68, 0.93, 5.72, MAT['marble'], 0.01, name='isolatop', anim=A(2.7, 5.2, 3))
for x in (2.2, 2.75, 3.3):
    cyl(x, 5.98, 0.19, 0.64, 0.06, MAT['leather'], name='sgabello', anim=A(x, 6, 6), bev=0.02)
    cyl(x, 5.98, 0.022, 0, 0.64, MAT['black'], name='gamba', anim=A(x, 6, 6))
    cyl(x, 5.98, 0.16, 0, 0.012, MAT['black'], name='base', anim=A(x, 6, 6))
for x in (2.3, 3.2):
    cyl(x, 5.25, 0.004, 1.75, 0.95, MAT['black'], name='cavo', anim=A(x, 5.2, 8), bev=0)
    sphere(x, 1.68, 5.25, 0.13, MAT['bulb'], sy=0.9, name='pendente', anim=A(x, 5.2, 8))
# --- zona pranzo ---
rbox(5.15, 0.70, 6.6, 7.45, 0.75, 7.6, MAT['walnut'], 0.012, name='tavolo', anim=A(6.3, 7.1))
for x in (5.45, 7.15):
    rbox(x - 0.04, 0, 6.75, x + 0.04, 0.7, 7.45, MAT['black'], 0.006, name='gambetavolo', anim=A(6.3, 7.1))
for x in (5.6, 6.3, 7.0):
    for (zs, zb) in ((6.38, 6.12), (7.82, 8.08)):
        rbox(x - 0.22, 0.43, zs - 0.2, x + 0.22, 0.49, zs + 0.2, MAT['boucle'], 0.025, seg=4, name='sedia', anim=A(x, zs, 10))
        rbox(x - 0.21, 0.5, min(zb, zb + (0.06 if zb < 7 else -0.06)), x + 0.21, 0.92, max(zb, zb + (0.06 if zb < 7 else -0.06)), MAT['walnut'], 0.02, name='schienale', anim=A(x, zs, 10))
        for dx in (-0.19, 0.19):
            for dz in (-0.17, 0.17):
                cyl(x + dx, zs + dz, 0.012, 0, 0.43, MAT['black'], verts=16, name='gambasedia', anim=A(x, zs, 10), bev=0)
for x in (5.8, 6.8):
    cyl(x, 7.1, 0.004, 1.85, 0.85, MAT['black'], name='cavo', anim=A(x, 7.1, 12), bev=0)
    cyl(x, 7.1, 0.2, 1.7, 0.16, MAT['lampShade'], name='paralume', anim=A(x, 7.1, 12), bev=0.01)
cyl(6.3, 7.1, 0.09, 0.75, 0.22, MAT['ceramic'], name='vaso', anim=A(6.3, 7.1, 14))
# --- soggiorno ---
rbox(1.0, 0, 7.7, 3.05, 0.012, 9.75, MAT['wool'], 0.004, name='tappeto', anim=A(2, 8.7))
rbox(2.85, 0, 7.45, 3.9, 0.36, 9.9, MAT['sofa'], 0.03, name='divano_base', anim=A(3.2, 8.7, 2))
rbox(1.95, 0, 9.0, 2.85, 0.36, 9.9, MAT['sofa'], 0.03, name='divano_base2', anim=A(3.2, 8.7, 2))
for (za, zb) in ((7.55, 8.45), (8.5, 9.45)):
    cushion(2.9, 0.34, za, 3.55, 0.5, zb, MAT['sofa2'], r=0.07, puff=0.012, name='seduta', anim=A(3.2, 8.7, 4))
cushion(1.98, 0.34, 9.05, 2.84, 0.5, 9.5, MAT['sofa2'], r=0.07, puff=0.012, name='seduta', anim=A(3.2, 8.7, 4))
cushion(3.5, 0.34, 7.5, 3.88, 0.85, 9.85, MAT['sofa2'], r=0.09, puff=0.015, name='schienale', anim=A(3.2, 8.7, 5))
cushion(1.98, 0.34, 9.5, 3.5, 0.85, 9.88, MAT['sofa2'], r=0.09, puff=0.015, name='schienale', anim=A(3.2, 8.7, 5))
cushion(2.86, 0.34, 7.45, 3.9, 0.66, 7.6, MAT['sofa'], r=0.06, puff=0.006, name='bracciolo', anim=A(3.2, 8.7, 5))
for (x, z, m_) in ((3.3, 7.8, 'ochre'), (3.32, 8.25, 'boucle'), (2.25, 9.33, 'teal'), (2.6, 9.35, 'rust')):
    o = cushion(x - 0.2, 0.48, z - 0.06, x + 0.2, 0.86, z + 0.06, MAT[m_], r=0.07, puff=0.012, name='cuscino', anim=A(3.2, 8.7, 7))
    o.rotation_euler = (0, 0, random.uniform(-0.25, 0.25)); o.rotation_mode = 'XYZ'
    o.rotation_euler = (math.radians(random.uniform(-12, -4) if z < 9 else 0), math.radians(random.uniform(-10, 10)), o.rotation_euler[2])
cyl(1.9, 8.6, 0.48, 0.3, 0.05, MAT['marble'], name='tavolino', anim=A(1.9, 8.6, 6), bev=0.012)
cyl(1.9, 8.6, 0.38, 0.0, 0.3, MAT['walnut'], name='tavolinobase', anim=A(1.9, 8.6, 6), bev=0.01)
for i, m_ in enumerate(('book1', 'book3', 'book2')):
    rbox(1.65, 0.35 + i * 0.03, 8.45, 1.95, 0.38 + i * 0.03, 8.66, MAT[m_], 0.003, name='libro', anim=A(1.9, 8.6, 8))
cyl(2.12, 8.55, 0.07, 0.35, 0.2, MAT['ceramic'], name='vasetto', anim=A(1.9, 8.6, 8))
rbox(0.1, 0, 8.0, 0.52, 0.42, 9.8, MAT['walnut'], 0.008, name='mobiletv', anim=A(0.3, 8.9))
rbox(0.16, 0.95, 8.15, 0.2, 1.62, 9.55, MAT['tv'], 0.004, name='tv', anim=A(0.3, 8.9, 3))
# lampada ad arco
cyl(0.9, 9.55, 0.16, 0, 0.04, MAT['darkStone'], name='baselampada', anim=A(0.9, 9.5, 6))
for i in range(24):
    t = i / 23; x = 0.9 + 0.9 * t; yv = 0.04 + 1.9 * math.sin(t * math.pi * 0.85) + 0.1 * t
    sphere(x, yv, 9.55 - 0.6 * t, 0.018, MAT['steel'], name='arco', anim=A(0.9, 9.5, 6))
sphere(1.8, 1.72, 8.95, 0.18, MAT['lampShade'], sy=0.6, name='lampada', anim=A(0.9, 9.5, 7))
# piante e quadro
for (x, z, r_) in ((4.1, 9.55, 0.55), (0.55, 9.6, 0.4), (8.4, 5.85, 0.45), (13.6, 4.4, 0.38), (9.65, 3.6, 0.38)):
    plant(x, z, r_, 1.1, anim=('grow', 140 + random.randint(0, 20), 18), seed=int(x * 10))
rbox(1.35, 1.15, 4.08, 2.95, 2.3, 4.12, MAT['black'], 0.004, name='cornice', anim=A(2, 4.5, 4))
rbox(1.4, 1.2, 4.12, 2.9, 2.25, 4.125, MAT['art'], 0, name='quadro', anim=A(2, 4.5, 4))
# tende leggere sulle finestre sud del soggiorno
for (x0, x1) in ((1.0, 1.6), (2.9, 3.5), (4.5, 5.1), (6.9, 7.5)):
    curtain(x0, x1, BD - 0.22, anim=('rise', 84, 16))
# --- camera matrimoniale ---
rbox(10.45, 0, 1.1, 10.62, 1.25, 3.3, MAT['boucle'], 0.03, name='testata', anim=A(11.5, 2.2))
rbox(10.62, 0, 1.3, 12.6, 0.28, 3.1, MAT['walnut'], 0.015, name='letto', anim=A(11.5, 2.2, 2))
cushion(10.64, 0.26, 1.33, 12.55, 0.5, 3.07, MAT['linen'], r=0.06, puff=0.008, name='materasso', anim=A(11.5, 2.2, 3))
cushion(11.1, 0.46, 1.25, 12.65, 0.58, 3.15, MAT['duvet'], r=0.08, puff=0.03, name='piumone', anim=A(11.5, 2.2, 5))
cushion(12.05, 0.56, 1.27, 12.45, 0.62, 3.13, MAT['sage'], r=0.04, puff=0.012, name='plaid', anim=A(11.5, 2.2, 6))
for z in (1.45, 2.3):
    cushion(10.68, 0.5, z, 11.1, 0.66, z + 0.7, MAT['linen'], r=0.07, puff=0.018, name='guanciale', anim=A(11.5, 2.2, 7))
for z in (0.7, 3.25):
    rbox(10.5, 0, z, 10.98, 0.5, z + 0.45, MAT['walnut'], 0.01, name='comodino', anim=A(11.5, 2.2, 4))
    cyl(10.74, z + 0.22, 0.05, 0.5, 0.3, MAT['steel'], name='lampbase', anim=A(11.5, 2.2, 8))
    cyl(10.74, z + 0.22, 0.12, 0.78, 0.18, MAT['lampShade'], name='abat', anim=A(11.5, 2.2, 8))
rbox(11.6, 0, 4.7, 13.85, 2.35, 5.25, MAT['walnut'], 0.008, name='armadio', anim=A(12.7, 5))
for x in (12.15, 12.7, 13.25):
    rbox(x - 0.002, 0.05, 4.69, x + 0.002, 2.3, 4.7, MAT['black'], 0, name='fugaarm', anim=A(12.7, 5))
cushion(12.85, 0, 0.3, 13.8, 0.42, 1.15, MAT['leather'], r=0.08, puff=0.01, name='poltrona', anim=A(13.3, 0.7))
cushion(13.4, 0.3, 0.3, 13.8, 0.85, 1.15, MAT['leather'], r=0.08, puff=0.01, name='poltronasch', anim=A(13.3, 0.7))
rbox(12.85, 0, 1.5, 13.8, 0.012, 3.1, MAT['wool2'], 0.004, name='tappeto2', anim=A(13.3, 2.3))
for (x0, x1) in ((11.4, 11.8), (12.6, 13.0)):
    curtain(x0, x1, 0.22, anim=('rise', 84, 16))
# --- altre stanze (viste solo dall'alto): arredi semplici con smussi ---
TOUR_ROOMS = {0, 5}
SKIP_MAT = {'art', 'black'}
for (x0, z0, x1, z1, b0, h, m_, bev) in ITEMS:
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    if room_of(cx, cz) in TOUR_ROOMS or cz > 10.0:
        continue
    mm = {'white': 'lacquer', 'fabricGrey': 'sofa', 'fabricLight': 'sofa2', 'fabricBeige': 'boucle', 'pillow': 'linen', 'cream': 'duvet',
          'mustard': 'ochre', 'navy': 'book2', 'book': 'book1', 'hob': 'blackGloss', 'rug1': 'wool', 'rug2': 'wool2', 'water': 'win',
          'glass': 'win', 'oak': 'walnut'}.get(m_, m_)
    if mm not in MAT: mm = 'lacquer'
    if mm in ('linen', 'duvet', 'sofa', 'sofa2', 'boucle', 'ochre', 'teal', 'rust', 'sage') and h > 0.05:
        cushion(x0, b0, z0, x1, b0 + h, z1, MAT[mm], r=min(0.06, h / 2.2), puff=0.008, name='it', anim=A(cx, cz))
    else:
        rbox(x0, b0, z0, x1, b0 + h, z1, MAT[mm], max(bev, 0.004), name='it', anim=A(cx, cz))
for (cx, cz, r, b0, h, m_, sx) in CYLS:
    if room_of(cx, cz) in TOUR_ROOMS: continue
    mm = {'oak': 'walnut', 'lamp': 'lampShade', 'navy': 'book2', 'teak': 'walnut'}.get(m_, m_)
    cyl(cx, cz, r, b0, h, MAT.get(mm, MAT['lacquer']), sx=sx, name='cy', anim=A(cx, cz))
# porte
door_objs = []
for i, ((hx, hy), r, a1) in enumerate(DOORS):
    o = rbox(0, 0, -0.02, r, 2.1, 0.02, MAT['walnut'], 0.004, name='porta')
    o.location = V(hx, 0, hy) + o.location; o.rotation_euler = (0, 0, -a1)
    if i == 4:
        o.hide_render = True; door_objs.append(o); continue
    ANIM.append((o, 'rise', 70, 16)); door_objs.append(o)

# ====================== luci, mondo, camera ======================
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
wn = world.node_tree; bg = wn.nodes['Background']
sky = wn.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False
sky.sun_elevation = math.radians(22); sky.sun_rotation = math.radians(200)
lp = wn.nodes.new('ShaderNodeLightPath')
dark = wn.nodes.new('ShaderNodeRGB'); dark.outputs[0].default_value = (0.0055, 0.0068, 0.0095, 1)
skyc = wn.nodes.new('ShaderNodeMixRGB'); skyc.name = 'camsky'
skyc.inputs['Fac'].default_value = 0.0
nt_mul = wn.nodes.new('ShaderNodeMath'); nt_mul.operation = 'MULTIPLY'
wn.links.new(lp.outputs['Is Camera Ray'], nt_mul.inputs[0])
camdark = wn.nodes.new('ShaderNodeValue'); camdark.name = 'camdark'; camdark.outputs[0].default_value = 1.0
wn.links.new(camdark.outputs[0], nt_mul.inputs[1])
mixw = wn.nodes.new('ShaderNodeMixRGB')
wn.links.new(nt_mul.outputs[0], mixw.inputs['Fac']); wn.links.new(sky.outputs['Color'], mixw.inputs['Color1']); wn.links.new(dark.outputs[0], mixw.inputs['Color2'])
wn.links.new(mixw.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(1.5); sd.color = (1.0, 0.86, 0.68)
sun = bpy.data.objects.new('sun', sd); ROOT.objects.link(sun)
sun_dir = V(math.sin(math.radians(200)) * 0.3, -1, 0) ; 
el, az = math.radians(24), math.radians(160)
d_ = V(math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el))   # verso il sole (z+ = sud)
sun.rotation_mode = 'QUATERNION'; sun.rotation_quaternion = (-d_).to_track_quat('-Z', 'Y')
# portali alle finestre
portal_objs = []
for (s, a, b, zz) in portals:
    l = bpy.data.lights.new('portal', 'AREA'); l.shape = 'RECTANGLE'
    try:
        l.cycles.is_portal = True
    except Exception:
        pass
    l.size = b - a; l.size_y = WALL_H - 0.15
    o = bpy.data.objects.new('portal', l); ROOT.objects.link(o)
    if s in 'NS':
        o.location = V((a + b) / 2, (WALL_H - 0.1) / 2, zz + (0.2 if s == 'S' else -0.2))
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (V(0, 0, -1 if s == 'S' else 1)).to_track_quat('-Z', 'Y')
    else:
        o.location = V(-0.2, (WALL_H - 0.1) / 2, (a + b) / 2)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (V(1, 0, 0)).to_track_quat('-Z', 'Y')
    portal_objs.append(o)
# luci interne calde
ilights = []
for (x, z, e) in ((2.3, 5.25, 25), (3.2, 5.25, 25), (5.8, 7.1, 30), (6.8, 7.1, 30), (1.8, 8.95, 25), (10.74, 0.92, 10), (10.74, 3.47, 10), (7.5, 4.7, 20), (9.3, 4.7, 20), (12.2, 2.2, 45), (12.4, 4.0, 35)):
    l = bpy.data.lights.new('il', 'POINT'); l.energy = e; l.color = (1.0, 0.8, 0.58); l.shadow_soft_size = 0.12
    o = bpy.data.objects.new('il', l); ROOT.objects.link(o); o.location = V(x, 2.4 if x > 12 else (1.55 if (x, z) not in ((10.74, 0.92), (10.74, 3.47)) else 0.85), z)
    ilights.append((o, e))
# luce di studio per il plastico (dall'alto)
st = bpy.data.lights.new('studio', 'AREA'); st.size = 16; st.energy = 2500; st.color = (1, 0.97, 0.93)
studio = bpy.data.objects.new('studio', st); ROOT.objects.link(studio)
studio.location = V(7, 14, 5); studio.rotation_mode = 'QUATERNION'; studio.rotation_quaternion = (V(0, -1, 0)).to_track_quat('-Z', 'Y')

cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); ROOT.objects.link(cam); sc.camera = cam
cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 400; cd.dof.use_dof = True

# ====================== regia ======================
def clamp01(x): return max(0.0, min(1.0, x))
def eio(x):
    x = clamp01(x); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def eout(x):
    x = clamp01(x); return 1 - (1 - x) ** 3
def lerpv(a, b, u): return a + (b - a) * u

CEN = Vector(V(7, 0.4, 5.6))
ORB = 200
def orbit(f):
    yaw = math.radians(-34 + 26 * eio(f / ORB))
    pitch = math.radians(60 - 6 * eio(f / ORB))
    dist = 22.5 - 2.5 * eio(f / ORB)
    off = V(math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)) * dist
    return CEN + off, CEN
def P(x, z, y=1.55): return Vector(V(x, y, z))
T0 = 262
TOUR = [(T0, P(6.9, 9.3, 1.6), P(2.6, 6.4, 1.0)), (310, P(6.2, 8.9), P(1.2, 8.6, 0.95)), (356, P(5.0, 8.1), P(1.6, 5.3, 1.0)),
        (398, P(4.9, 6.3), P(7.2, 7.1, 0.85)), (440, P(6.6, 4.9), P(10.6, 4.7, 1.2)), (482, P(9.8, 4.7), P(12.8, 4.2, 1.0)),
        (N, P(11.2, 4.4, 1.5), P(11.7, 2.0, 0.7))]
def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
def tour(f, idx):
    i = 0
    while i < len(TOUR) - 2 and f > TOUR[i + 1][0]: i += 1
    a, b = TOUR[i], TOUR[i + 1]
    u = clamp01((f - a[0]) / (b[0] - a[0])); u = u * u * (3 - 2 * u) * 0.4 + u * 0.6
    pts = [k[idx] for k in TOUR]
    return cr(pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)], u)

DIVE = [(ORB, None, None), (236, P(6.6, 9.0, 5.2), P(3.2, 6.6, 0.3)), (T0, TOUR[0][1], TOUR[0][2])]
def cam_state(f):
    if f <= ORB:
        pos, tgt = orbit(f); lens = 50
    elif f < T0:
        p0, t0 = orbit(ORB)
        p1, t1 = DIVE[1][1], DIVE[1][2]
        p2, t2 = DIVE[2][1], DIVE[2][2]
        if f < 236:
            u = eio((f - ORB) / (236 - ORB)); pos = lerpv(p0, p1, u); tgt = lerpv(t0, t1, u)
            lens = 50 + (26 - 50) * u
        else:
            u = (f - 236) / (T0 - 236); e = 1 - (1 - u) ** 2
            pos = lerpv(p1, p2, e); tgt = lerpv(t1, t2, e); lens = 26 + (20 - 26) * e
    else:
        pos, tgt = tour(f, 1), tour(f, 2); lens = 20
        pos = pos + Vector((0.006 * math.sin(f * 0.21), 0.006 * math.sin(f * 0.17 + 1), 0.004 * math.sin(f * 0.13 + 2)))
    return pos, tgt, lens

BASE = {}
for (o, kind, f0, du) in ANIM:
    BASE[o.name] = (o.location.copy(), o.scale.copy())

def update(scene, *_):
    f = scene.frame_current
    for (o, kind, f0, du) in ANIM:
        loc, scl = BASE[o.name]
        u = clamp01((f - f0) / du)
        o.hide_render = u <= 0
        if kind == 'rise':
            o.scale = (scl[0], scl[1], scl[2] * max(eout(u), 1e-3)); o.location = loc
        elif kind == 'grow':
            s = max(eout(u), 1e-3); o.scale = scl * s; o.location = loc
        elif kind == 'drop':
            e = eout(u)
            o.location = loc + Vector((0, 0, 0.9 * (1 - e))); o.scale = scl * (0.85 + 0.15 * e)
        elif kind == 'fadein':
            o.scale = scl * (0.96 + 0.04 * eout(u)) if u < 1 else scl; o.location = loc
    pos, tgt, lens = cam_state(f)
    cam.location = pos; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (tgt - pos).to_track_quat('-Z', 'Y')
    cd.lens = lens; cd.dof.focus_distance = max(0.4, (tgt - pos).length)
    cd.dof.aperture_fstop = 16 if f < ORB else (5.6 if f >= T0 else 11)
    h = pos.z
    inside = clamp01((2.45 - h) / 0.6)            # il soffitto compare solo quando la camera è sotto i muri
    ceiling.hide_render = inside <= 0
    ceil_fade.outputs[0].default_value = inside
    for s_ in spots: s_.hide_render = inside < 0.5
    camdark.outputs[0].default_value = 1 - clamp01((f - 228) / 26)
    st.energy = 2500 * (1 - inside)
    for o, e in ilights: o.data.energy = e * clamp01((f - 230) / 30)
    for o in portal_objs: o.hide_render = inside <= 0
    scene.view_settings.exposure = 0.35 * inside

bpy.app.handlers.frame_change_pre.append(update)
os.makedirs(args.out, exist_ok=True)

if args.labels:
    from bpy_extras.object_utils import world_to_camera_view
    data = []
    for f in range(0, 271):
        sc.frame_set(f)
        data.append([[round(p.x, 4), round(1 - p.y, 4)] for p in (world_to_camera_view(sc, cam, V(lx, 0.6, lz)) for (_, _, (lx, lz), *_r) in ROOMS)])
    json.dump(dict(rooms=[dict(name=r[0], area=r[1]) for r in ROOMS], pos=data, res=args.res), open(os.path.join(args.out, 'labels.json'), 'w'), ensure_ascii=False)
    print('labels ok'); sys.exit(0)
if args.still >= 0:
    sc.frame_set(args.still)
    sc.render.filepath = os.path.join(args.out, f'still_{args.still:04d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = args.frames; sc.frame_step = args.step
    sc.render.filepath = os.path.join(args.out, '')
    bpy.ops.render.render(animation=True)
