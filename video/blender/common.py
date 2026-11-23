"""Scena Blender/Cycles condivisa: costruttore di mesh, materiali, quartiere, edificio, appartamento.

Convenzione: le geometrie sono descritte in coordinate "tre" (x destra, y alto, z verso la strada)
e convertite in Blender (X = x, Y = -z, Z = y)."""
import math
import os
import random

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'tex')

# ---------- dati edificio ----------
BW, BD, H, SLAB, LEVELS, F = 30.0, 10.0, 3.2, 0.3, 10, 5
YF = F * H + SLAB
BAL = dict(x0=0.8, x1=8.4, z1=BD + 1.75)
LOT = dict(x0=-12, x1=42, z0=-18, z1=26)
PIT = dict(x0=-1, x1=BW + 1, z0=-1, z1=BD + 1, depth=3.0)
G0 = 0.15  # quota del marciapiede/terreno


def V(x, y, z):
    return Vector((x, -z, y))


# ---------- costruttore di mesh multi-materiale ----------
class MB:
    def __init__(self):
        self.v, self.f, self.uv, self.mi = [], [], [], []

    def quad(self, o, du, dv, mod=1.0, modv=None, mat=0):
        modv = modv or mod
        o, du, dv = Vector(o), Vector(du), Vector(dv)
        n = len(self.v)
        pts = [o, o + du, o + du + dv, o + dv]
        self.v += [V(*p) for p in pts]
        self.f.append((n, n + 1, n + 2, n + 3))
        u0 = o.dot(du.normalized()) / mod
        v0 = o.dot(dv.normalized()) / modv
        ul, vl = du.length / mod, dv.length / modv
        self.uv.append([(u0, v0), (u0 + ul, v0), (u0 + ul, v0 + vl), (u0, v0 + vl)])
        self.mi.append(mat)
        return self

    def tri(self, a, b, c, mod=4.0, mat=0):
        n = len(self.v)
        self.v += [V(*a), V(*b), V(*c)]
        self.f.append((n, n + 1, n + 2))
        self.uv.append([((p[0] + p[2]) / mod, p[1] / mod) for p in (a, b, c)])
        self.mi.append(mat)
        return self

    def box(self, x0, y0, z0, x1, y1, z1, mod=1.0, faces='xXyYzZ', modv=None, mat=0):
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        q = lambda *a: self.quad(*a, mod=mod, modv=modv, mat=mat)
        if 'X' in faces:
            q((x1, y0, z1), (0, 0, -dz), (0, dy, 0))
        if 'x' in faces:
            q((x0, y0, z0), (0, 0, dz), (0, dy, 0))
        if 'Z' in faces:
            q((x0, y0, z1), (dx, 0, 0), (0, dy, 0))
        if 'z' in faces:
            q((x1, y0, z0), (-dx, 0, 0), (0, dy, 0))
        if 'Y' in faces:
            self.quad((x0, y1, z1), (dx, 0, 0), (0, 0, -dz), mod=mod, modv=mod, mat=mat)
        if 'y' in faces:
            self.quad((x0, y0, z0), (dx, 0, 0), (0, 0, dz), mod=mod, modv=mod, mat=mat)
        return self

    def floor(self, x0, z0, x1, z1, y, mod=1.0, mat=0):
        return self.quad((x0, y, z1), (x1 - x0, 0, 0), (0, 0, -(z1 - z0)), mod=mod, mat=mat)

    def gable(self, x0, x1, z0, z1, y, r, along_x, roof_mat, wall_mat, mod=4.0):
        dx, dz = x1 - x0, z1 - z0
        if along_x:
            zm = (z0 + z1) / 2
            self.quad((x0, y, z1), (dx, 0, 0), (0, r, -(z1 - zm)), mod=mod, mat=roof_mat)
            self.quad((x1, y, z0), (-dx, 0, 0), (0, r, zm - z0), mod=mod, mat=roof_mat)
            self.tri((x0, y, z0), (x0, y, z1), (x0, y + r, zm), mat=wall_mat)
            self.tri((x1, y, z1), (x1, y, z0), (x1, y + r, zm), mat=wall_mat)
        else:
            xm = (x0 + x1) / 2
            self.quad((x1, y, z1), (0, 0, -dz), (-(x1 - xm), r, 0), mod=mod, mat=roof_mat)
            self.quad((x0, y, z0), (0, 0, dz), (xm - x0, r, 0), mod=mod, mat=roof_mat)
            self.tri((x1, y, z0), (x0, y, z0), (xm, y + r, z0), mat=wall_mat)
            self.tri((x0, y, z1), (x1, y, z1), (xm, y + r, z1), mat=wall_mat)
        return self

    def build(self, name, mats, coll=None, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        uvl = me.uv_layers.new(name='UVMap')
        li = 0
        for pi, poly in enumerate(me.polygons):
            for k in range(poly.loop_total):
                uvl.data[poly.loop_start + k].uv = self.uv[pi][k]
            poly.material_index = self.mi[pi]
            poly.use_smooth = smooth
        for m in mats:
            me.materials.append(m)
        me.validate()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        return ob


# ---------- materiali ----------
_imgs = {}


def img(name, color=True):
    if name not in _imgs:
        im = bpy.data.images.load(os.path.join(TEX, name))
        if not color:
            im.colorspace_settings.name = 'Non-Color'
        _imgs[name] = im
    return _imgs[name]


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    return m, nt, b


def mat_basic(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, emit=None, emit_s=0.0, ior=1.45, spec=0.5):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['IOR'].default_value = ior
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_s
    return m


def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _bump(nt, b, height_out, strength, dist=0.02):
    bm = nt.nodes.new('ShaderNodeBump')
    bm.inputs['Strength'].default_value = strength
    bm.inputs['Distance'].default_value = dist
    nt.links.new(height_out, bm.inputs['Height'])
    nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])


def mat_image(name, tex, rough=0.6, bump=0.15, rough_tex=None, emit_tex=None, emit_col=(1, 0.8, 0.55), coat=0.0, mapping_scale=1.0):
    m, nt, b = new_mat(name)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img(tex)
    if mapping_scale != 1.0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (mapping_scale, mapping_scale, 1)
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if rough_tex:
        r = nt.nodes.new('ShaderNodeTexImage')
        r.image = img(rough_tex, color=False)
        mr = nt.nodes.new('ShaderNodeMath')
        mr.operation = 'MULTIPLY'
        mr.inputs[1].default_value = 1.0
        nt.links.new(r.outputs['Color'], mr.inputs[0])
        nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    if bump:
        _bump(nt, b, t.outputs['Color'], bump)
    if emit_tex:
        e = nt.nodes.new('ShaderNodeTexImage')
        e.image = img(emit_tex)
        nt.links.new(e.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = 0.0
    return m


def mat_noise(name, c1, c2, scale=8.0, rough=0.8, bump=0.3, detail=8.0, voronoi=False, coat=0.0):
    """Materiale procedurale: intonaco, cemento, terra, asfalto, prato."""
    m, nt, b = new_mat(name)
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = 0.6
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    h = n.outputs['Fac']
    if voronoi:
        vo = nt.nodes.new('ShaderNodeTexVoronoi')
        vo.inputs['Scale'].default_value = scale * 12
        mx = nt.nodes.new('ShaderNodeMath')
        mx.operation = 'ADD'
        nt.links.new(n.outputs['Fac'], mx.inputs[0])
        nt.links.new(vo.outputs['Distance'], mx.inputs[1])
        h = mx.outputs[0]
    if bump:
        _bump(nt, b, h, bump, 0.05)
    return m


def mat_glass(name, color, rough=0.02, transmission=1.0, alpha=1.0):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = 1.5
    b.inputs['Thin Wall'].default_value = True
    b.inputs['Alpha'].default_value = alpha
    return m


def mat_leaves(name, c1, c2):
    m, nt, b = new_mat(name)
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    b.inputs['Subsurface Weight'].default_value = 0.25
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 14.0
    _bump(nt, b, vo.outputs['Distance'], 0.9, 0.2)
    return m


class Mats:
    def __init__(self):
        c = hexc
        self.fac = [mat_image(f'fac{i}', f'fac{i}.jpg', rough=0.85, bump=0.25, rough_tex=f'fac{i}_r.png', emit_tex=f'fac{i}_e.jpg') for i in range(4)]
        self.shop = mat_image('shop', 'shop.jpg', rough=0.5, bump=0.1, emit_tex='shop_e.jpg')
        self.tiles_roof = mat_image('tiles_roof', 'tiles_roof.jpg', rough=0.75, bump=0.6)
        self.gravel = mat_noise('gravel', c('#7d7a75'), c('#a29e97'), scale=40, rough=0.95, bump=0.4, voronoi=True)
        self.trim = mat_noise('trim', c('#e3dbcd'), c('#efe9df'), scale=6, rough=0.7, bump=0.08)
        self.paving = mat_image('paving', 'paving.jpg', rough=0.8, bump=0.35)
        self.grass = mat_noise('grass', c('#4c6b33'), c('#6f8f45'), scale=1.2, rough=0.95, bump=0.6, voronoi=True)
        self.asphalt = mat_noise('asphalt', c('#34363a'), c('#4a4d52'), scale=30, rough=0.92, bump=0.25, voronoi=True)
        self.mark = mat_basic('mark', c('#e3e0d8'), rough=0.6)
        self.steel = mat_basic('steel', c('#a7abb1'), rough=0.25, metal=1.0)
        self.tower = mat_basic('tower', c('#6c7f8d'), rough=0.12, metal=0.6)
        self.dirt = mat_noise('dirt', c('#5c4330'), c('#8a6a4c'), scale=3, rough=1.0, bump=0.9, voronoi=True)
        self.dirt_wall = mat_noise('dirt_wall', c('#4a3626'), c('#7a5a40'), scale=4, rough=1.0, bump=1.2, voronoi=True)
        self.concrete = mat_noise('concrete', c('#a8a39b'), c('#c4bfb6'), scale=5, rough=0.9, bump=0.25, voronoi=True)
        self.white = mat_noise('white', c('#e6e2da'), c('#f1eee8'), scale=4, rough=0.55, bump=0.05)
        self.stone = mat_noise('stone', c('#ddd6ca'), c('#ece6dc'), scale=3, rough=0.5, bump=0.1)
        self.dark_stone = mat_noise('dark_stone', c('#4a4641'), c('#625d57'), scale=6, rough=0.55, bump=0.15)
        self.frame = mat_basic('frame', c('#25282c'), rough=0.35, metal=0.8)
        self.rail_glass = mat_glass('rail_glass', c('#cfe4ec'), rough=0.02)
        self.red = mat_basic('red', c('#b8261e'), rough=0.45)
        self.pv = mat_basic('pv', c('#152235'), rough=0.08, metal=0.4, coat=1.0)
        self.trunk = mat_noise('trunk', c('#3e3128'), c('#5e4b3c'), scale=20, rough=0.9, bump=0.8)
        self.leaves = [mat_leaves('leaves0', c('#2f4a1f'), c('#55743a')), mat_leaves('leaves1', c('#3a5322'), c('#6a8a3f')), mat_leaves('leaves2', c('#2a4321'), c('#4c6a35'))]
        self.lamp_head = mat_basic('lamp_head', c('#2c2f33'), rough=0.4, metal=0.6, emit=c('#ffd9a0'), emit_s=0.0)
        self.pole = mat_basic('pole', c('#2c2f33'), rough=0.45, metal=0.7)
        # vetro dell'edificio: uno per piano (luci accese di sera)
        self.glass = []
        for i in range(LEVELS):
            g = mat_basic(f'glass{i}', c('#3b4f5c'), rough=0.03, metal=0.0, ior=1.52, spec=1.0, emit=c('#ffcf8c'), emit_s=0.0)
            g.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 1.0
            self.glass.append(g)


def emission_set(mat, strength):
    mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = strength


# ---------- alberi ----------
def make_tree_protos(M, coll):
    protos = []
    for k in range(3):
        rnd = random.Random(100 + k)
        mb = MB()
        meshes = []
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.11, depth=0.85, location=(0, 0, 0.425))
        tr = bpy.context.active_object
        tr.data.materials.append(M.trunk)
        bpy.ops.transform.resize(value=(1, 1, 1))
        meshes.append(tr)
        for c in range(7):
            a = rnd.random() * 6.28
            rr = 0.35 + rnd.random() * 0.45
            z = 0.74 + rnd.random() * 0.16
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.36 + rnd.random() * 0.16, location=(math.cos(a) * rr * 0.75, math.sin(a) * rr * 0.75, z))
            s = bpy.context.active_object
            s.scale = (1, 1, 0.55)
            tex = bpy.data.textures.new(f'lt{k}{c}', 'CLOUDS')
            tex.noise_scale = 0.16
            d = s.modifiers.new('d', 'DISPLACE')
            d.texture = tex
            d.strength = 0.12
            s.data.materials.append(M.leaves[k])
            meshes.append(s)
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        t = bpy.context.active_object
        t.name = f'treeProto{k}'
        for p in t.data.polygons:
            p.use_smooth = True
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        # tronco: alto 1 → il tronco sarà scalato con l'albero intero
        for c2 in t.users_collection:
            c2.objects.unlink(t)
        protos.append(t.data)
    return protos


def place_trees(list_, protos, coll, prefix='t'):
    obs = []
    for i, (x, z, h, r, c) in enumerate(list_):
        me = protos[i % len(protos)]
        o = bpy.data.objects.new(f'{prefix}{i}', me)
        o.location = V(x, G0, z)
        o.scale = (r * 1.35, r * 1.35, h * 0.85)
        o.rotation_euler = (0, 0, c * 6.28)
        coll.objects.link(o)
        obs.append(o)
    return obs


# ---------- quartiere ----------
PX, PZ = 68.0, 58.0
CX, CZ = (LOT['x0'] + LOT['x1']) / 2, (LOT['z0'] + LOT['z1']) / 2
HB, HD, R = 27.0, 22.0, 3


def build_city(M, coll, radius=R):
    rnd = random.Random(101)
    mb = MB()  # materiali: 0-3 facciate, 4 negozi, 5 coppi, 6 ghiaia, 7 cornici, 8 marciapiede, 9 prato, 10 segnaletica, 11 binari, 12 torri
    mats = M.fac + [M.shop, M.tiles_roof, M.gravel, M.trim, M.paving, M.grass, M.mark, M.steel, M.tower]
    trees = []

    def seg(x0, z0, x1, z1, along_x):
        floors = 5 + int(rnd.random() * 4)
        h = 4 + floors * 3.2
        v = int(rnd.random() * 4)
        mb.box(x0, G0, z0, x1, 4, z1, 12.8, 'XxZz', 4, mat=4)
        mb.box(x0, 4, z0, x1, h, z1, 12.8, 'XxZz', mat=v)
        mb.box(x0 - 0.3, h, z0 - 0.3, x1 + 0.3, h + 0.5, z1 + 0.3, 2, 'XxZzYy', mat=7)
        if rnd.random() < 0.78:
            mb.gable(x0, x1, z0, z1, h + 0.5, 2.6, along_x, 5, 7)
        else:
            mb.floor(x0, z0, x1, z1, h + 0.51, 4, mat=6)
            bx = x0 + 2 + rnd.random() * max(1, x1 - x0 - 6)
            bz = z0 + 2 + rnd.random() * max(1, z1 - z0 - 6)
            mb.box(bx, h + 0.5, bz, bx + 3, h + 3.2, bz + 3, 2, mat=7)

    def side(a0, a1, b0, b1, along_x):
        a = a0
        while a < a1 - 0.1:
            l = 10 + rnd.random() * 10
            if a1 - (a + l) < 8:
                l = a1 - a
            if along_x:
                seg(a, b0, a + l, b1, True)
            else:
                seg(b0, a, b1, a + l, False)
            a += l

    for bx in range(-radius, radius + 1):
        for bz in range(-radius, radius + 1):
            if bx == 0 and bz == 0:
                continue
            cx, cz = CX + bx * PX, CZ + bz * PZ
            x0, x1, z0, z1 = cx - HB, cx + HB, cz - HD, cz + HD
            mb.box(x0, 0, z0, x1, G0, z1, 4, 'XxZzY', mat=8)
            park = (bx, bz) in [(0, 1), (1, 1), (-2, -1), (2, -2)]
            if park:
                mb.floor(x0 + 3, z0 + 3, x1 - 3, z1 - 3, G0 + 0.01, 4, mat=9)
                mb.floor(cx - 1.5, z0 + 3, cx + 1.5, z1 - 3, G0 + 0.02, 4, mat=8)
                mb.floor(x0 + 3, cz - 1.5, x1 - 3, cz + 1.5, G0 + 0.02, 4, mat=8)
                for _ in range(55):
                    x = x0 + 6 + rnd.random() * (2 * HB - 12)
                    z = z0 + 6 + rnd.random() * (2 * HD - 12)
                    if abs(x - cx) < 3 or abs(z - cz) < 3:
                        continue
                    trees.append((x, z, 8 + rnd.random() * 6, 2.8 + rnd.random() * 1.8, rnd.random()))
                continue
            e, dp = 3.5, 12
            side(x0 + e, x1 - e, z0 + e, z0 + e + dp, True)
            side(x0 + e, x1 - e, z1 - e - dp, z1 - e, True)
            side(z0 + e + dp, z1 - e - dp, x0 + e, x0 + e + dp, False)
            side(z0 + e + dp, z1 - e - dp, x1 - e - dp, x1 - e, False)
            mb.floor(x0 + e + dp, z0 + e + dp, x1 - e - dp, z1 - e - dp, G0 + 0.01, 4, mat=9)
            for _ in range(3):
                trees.append((cx + (rnd.random() - 0.5) * 18, cz + (rnd.random() - 0.5) * 8, 7 + rnd.random() * 4, 2.6 + rnd.random() * 1.4, rnd.random()))

    for _ in range(90):
        a = rnd.random() * math.pi * 2
        d = 250 + rnd.random() * 120
        x, z = CX + math.cos(a) * d, CZ + math.sin(a) * d
        w, dd, h = 14 + rnd.random() * 20, 12 + rnd.random() * 12, 16 + rnd.random() * 14
        mb.box(x, 0, z, x + w, h, z + dd, 12.8, 'XxZz', mat=int(rnd.random() * 4))
        mb.floor(x, z, x + w, z + dd, h, 4, mat=6)
    for _ in range(12):
        a = -2.6 + rnd.random() * 2.2
        d = 900 + rnd.random() * 500
        x, z = CX + math.cos(a) * d, CZ + math.sin(a) * d
        w, h = 18 + rnd.random() * 14, 40 + rnd.random() * 70
        mb.box(x, 0, z, x + w, h, z + w * (0.7 + rnd.random() * 0.5), 24, 'XxZzY', mat=12)

    tram_z = LOT['z1'] + 7
    for k in range(-radius - 1, radius + 1):
        sx = CX + k * PX + PX / 2
        z = CZ - (radius + 0.5) * PZ
        while z < CZ + (radius + 0.5) * PZ:
            mb.floor(sx - 0.08, z, sx + 0.08, z + 3, 0.02, 4, mat=10)
            z += 6
        sz = CZ + k * PZ + PZ / 2
        if abs(sz - tram_z) > 1:
            x = CX - (radius + 0.5) * PX
            while x < CX + (radius + 0.5) * PX:
                mb.floor(x, sz - 0.08, x + 3, sz + 0.08, 0.02, 4, mat=10)
                x += 6

    def zebra(x, z, along_x):
        for i in range(7):
            if along_x:
                mb.floor(x + i, z - 2, x + i + 0.5, z + 2, 0.021, 4, mat=10)
            else:
                mb.floor(x - 2, z + i, x + 2, z + i + 0.5, 0.021, 4, mat=10)

    for x in (LOT['x0'] - 7, LOT['x1'] + 7):
        zebra(x - 3.5, LOT['z0'] - 3, True)
        zebra(x - 3.5, LOT['z1'] + 3, True)
    for z in (LOT['z0'] - 7, LOT['z1'] + 7):
        zebra(LOT['x0'] - 3, z - 3.5, False)
        zebra(LOT['x1'] + 3, z - 3.5, False)
    for c0 in (tram_z - 1.6, tram_z + 1.6):
        for r_ in (c0 - 0.72, c0 + 0.72):
            mb.box(CX - (radius + 0.5) * PX, 0, r_ - 0.04, CX + (radius + 0.5) * PX, 0.05, r_ + 0.04, 4, mat=11)

    for k in range(-radius - 1, radius + 1):
        sx = CX + k * PX + PX / 2
        sz = CZ + k * PZ + PZ / 2
        for off in (-8.5, 8.5):
            z = CZ - radius * PZ
            while z < CZ + radius * PZ:
                dz = ((z - CZ - PZ / 2) % PZ + PZ) % PZ
                if 10 <= dz <= PZ - 10:
                    trees.append((sx + off, z + rnd.random() * 2, 8 + rnd.random() * 3, 2.6 + rnd.random() * 1.2, rnd.random()))
                z += 10
            x = CX - radius * PX
            while x < CX + radius * PX:
                dx = ((x - CX - PX / 2) % PX + PX) % PX
                skip = abs(sz - tram_z) < 1 and off < 0 and LOT['x0'] - 2 < x < LOT['x1'] + 2
                if 10 <= dx <= PX - 10 and not skip:
                    trees.append((x + rnd.random() * 2, sz + off, 8 + rnd.random() * 3, 2.6 + rnd.random() * 1.2, rnd.random()))
                x += 10

    city = mb.build('city', mats, coll)
    # asfalto
    bpy.ops.mesh.primitive_plane_add(size=2400, location=V(CX, 0, CZ))
    pl = bpy.context.active_object
    pl.data.materials.append(M.asphalt)
    for c2 in pl.users_collection:
        c2.objects.unlink(pl)
    coll.objects.link(pl)
    # lampioni lungo la strada del cantiere
    lamps = []
    x = LOT['x0'] - 60
    pts = []
    while x < LOT['x1'] + 70:
        pts += [(x, LOT['z1'] + 0.8), (x + 8, LOT['z1'] + 13.2)]
        x += 16
    z = LOT['z0'] - 40
    while z < LOT['z1'] + 40:
        pts += [(LOT['x1'] + 0.8, z), (LOT['x0'] - 0.8, z + 8)]
        z += 16
    lm = MB()
    for (px, pz) in pts:
        lm.box(px - 0.07, G0, pz - 0.07, px + 0.07, 7, pz + 0.07, 1, mat=0)
        lm.box(px - 0.25, 6.9, pz - 0.5, px + 0.25, 7.1, pz + 0.5, 1, mat=1)
    lm.build('lamps', [M.pole, M.lamp_head], coll)
    return city, trees, pts
