# Camden-Straßenset für Camden Command. Blender headless. Export: GLB + eingebettete JSON-Variante.
# Konventionen: 1 Einheit = 1 m. Hausmodul: x in [-2,2], y in [0,4] (Tiefe in den Block), Front bei y=0 zeigt nach -Y.
import bpy, bmesh, math, random, sys, os, json, base64, struct
from mathutils import Vector
OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '.'
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)

MATS = {}
def mat(name, color=(0.8,0.8,0.8,1), rough=0.8, metal=0.0, emit=None):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color; b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = emit; b.inputs['Emission Strength'].default_value = 2.0
    MATS[name] = m; return m
# Materialnamen sind die Schnittstelle zum Spiel (dort bekommen sie die gebackenen Texturen)
mat('brick', (0.5,0.4,0.3,1)); mat('slate', (0.15,0.16,0.2,1), 0.6); mat('stone', (0.78,0.75,0.68,1), 0.7); mat('render', (0.85,0.84,0.8,1), 0.7)
mat('frame', (0.92,0.92,0.9,1), 0.5); mat('glass', (0.08,0.1,0.13,1), 0.1, 0.3); mat('door', (0.6,0.6,0.6,1), 0.45); mat('metal', (0.06,0.06,0.07,1), 0.45, 0.6)
mat('wood', (0.1,0.17,0.12,1), 0.4); mat('paint', (0.7,0.7,0.7,1), 0.35, 0.1); mat('rubber', (0.05,0.05,0.05,1), 0.9); mat('lamp', (1,0.9,0.7,1), 0.3, 0, (1,0.85,0.6,1))
mat('red', (0.62,0.05,0.07,1), 0.4); mat('clay', (0.55,0.3,0.2,1), 0.8); mat('leaf', (0.2,0.33,0.14,1), 0.8); mat('bark', (0.3,0.27,0.22,1), 0.9); mat('canvas', (0.7,0.68,0.6,1), 0.9); mat('pavement', (0.5,0.49,0.46,1), 0.8); mat('asphalt', (0.1,0.1,0.11,1), 0.7)

def box(name, size, loc, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True, scale=True); o.data.materials.append(mat(m)); return o
def cyl(name, r, h, loc, m, v=12, r2=None, rot=(0,0,0)):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=loc)
    else: bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r, radius2=r2, depth=h, location=loc)
    o = bpy.context.active_object; o.name = name; o.rotation_euler = rot; bpy.ops.object.transform_apply(rotation=True); o.data.materials.append(mat(m)); return o
def sph(name, r, loc, m, seg=12, ring=8, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc); o = bpy.context.active_object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(mat(m)); return o
def prism(name, w, d, h, loc, m):  # Satteldach: Dreiecksprisma, First entlang X
    me = bpy.data.meshes.new(name); verts = [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w/2,0,h),(w/2,0,h)]
    faces = [(0,1,5,4),(2,3,4,5),(0,4,3),(1,2,5),(0,3,2,1)]
    me.from_pydata(verts, [], faces); me.update(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.location = loc; o.data.materials.append(mat(m)); return o

def cube_uv(obj, scale=2.0):
    """Würfelprojektion in Weltmaßen: 1 UV-Kachel = scale Meter (passt zur Backfläche von 2 m)."""
    me = obj.data; bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.verify(); M = obj.matrix_world
    for f in bm.faces:
        n = (M.to_3x3() @ f.normal); ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = M @ l.vert.co
            if ax == 0: u, v = p.y, p.z
            elif ax == 1: u, v = p.x, p.z
            else: u, v = p.x, p.y
            l[uv].uv = (u/scale, v/scale)
    bm.to_mesh(me); bm.free()

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); j = bpy.context.active_object; j.name = name; return j

def finish(parts, name, uvscale=2.0):
    for p in parts: cube_uv(p, uvscale)
    o = join(parts, name); o.location = (0,0,0); return o

# ---------------- Reihenhaus-Module ----------------
FLOOR = 3.1
def sash_window(parts, x, z, w=1.0, h=1.5, y=0.0, depth_sign=-1, tag='w'):
    # Fensterlaibung (Glas leicht zurückgesetzt), Rahmen, Sturz und Sims aus Stein
    yy = y + depth_sign*(-0.02)
    parts.append(box(tag+'_gl', (w, 0.06, h), (x, y+depth_sign*0.08, z), 'glass'))
    parts.append(box(tag+'_fr', (w+0.12, 0.08, 0.08), (x, y+depth_sign*0.1, z+h/2), 'frame')); parts.append(box(tag+'_fr2', (w+0.12, 0.08, 0.08), (x, y+depth_sign*0.1, z-h/2), 'frame'))
    parts.append(box(tag+'_fr3', (0.08, 0.08, h), (x-w/2, y+depth_sign*0.1, z), 'frame')); parts.append(box(tag+'_fr4', (0.08, 0.08, h), (x+w/2, y+depth_sign*0.1, z), 'frame'))
    parts.append(box(tag+'_fr5', (w, 0.06, 0.05), (x, y+depth_sign*0.1, z), 'frame'))  # Querholz
    parts.append(box(tag+'_li', (w+0.4, 0.18, 0.22), (x, y+depth_sign*0.06, z+h/2+0.15), 'stone'))  # Sturz
    parts.append(box(tag+'_si', (w+0.3, 0.22, 0.1), (x, y+depth_sign*0.1, z-h/2-0.07), 'stone'))   # Sims

def door(parts, x, y=0.0, color_tag='door'):
    parts.append(box('door', (0.95, 0.1, 2.15), (x, y-0.12, 1.1), color_tag))
    parts.append(box('door_fan', (0.95, 0.06, 0.5), (x, y-0.1, 2.5), 'glass')); parts.append(box('door_fr', (1.2, 0.12, 0.1), (x, y-0.12, 2.8), 'frame'))
    parts.append(box('door_fr2', (0.12, 0.12, 2.9), (x-0.55, y-0.12, 1.45), 'frame')); parts.append(box('door_fr3', (0.12, 0.12, 2.9), (x+0.55, y-0.12, 1.45), 'frame'))
    parts.append(box('door_step', (1.3, 0.5, 0.15), (x, y-0.3, 0.075), 'stone')); parts.append(box('door_knob', (0.06,0.06,0.06), (x+0.3, y-0.2, 1.05), 'metal'))
    parts.append(box('door_arch', (1.4, 0.2, 0.3), (x, y-0.08, 3.0), 'stone'))

def bay_window(parts, x, z, y=0.0, h=1.6):
    # Erker: drei Fensterflächen, Steinsockel, kleines Dach
    parts.append(box('bay_base', (2.0, 0.9, 0.9), (x, y-0.45, 0.45), 'brick'))
    parts.append(box('bay_body', (1.6, 0.75, h+0.3), (x, y-0.42, z), 'brick'))
    parts.append(box('bay_gl', (1.3, 0.06, h), (x, y-0.82, z), 'glass')); parts.append(box('bay_glL', (0.06, 0.6, h), (x-0.82, y-0.5, z), 'glass')); parts.append(box('bay_glR', (0.06, 0.6, h), (x+0.82, y-0.5, z), 'glass'))
    for dx in (-0.65, 0.65): parts.append(box('bay_fr', (0.1, 0.9, h+0.2), (x+dx, y-0.42, z), 'frame'))
    parts.append(box('bay_frT', (1.7, 0.9, 0.1), (x, y-0.42, z+h/2+0.05), 'frame')); parts.append(box('bay_frB', (1.7, 0.9, 0.1), (x, y-0.42, z-h/2-0.05), 'frame'))
    parts.append(box('bay_sill', (1.9, 1.0, 0.12), (x, y-0.45, z-h/2-0.15), 'stone')); parts.append(box('bay_roof', (2.1, 1.1, 0.12), (x, y-0.5, z+h/2+0.3), 'metal'))

def terrace(name, variant='plain', floors=3, corner=False, shop=False, roofkind='pitched'):
    parts = []; W, D = 4.0, 4.0; H = floors*FLOOR
    parts.append(box('wall', (W, D, H), (0, D/2, H/2), 'brick'))
    # Vorderfront: Tür links, Fenster rechts; obere Stockwerke zwei Fenster
    if shop:
        parts.append(box('shop_gl', (3.2, 0.1, 2.1), (-0.2, -0.1, 1.45), 'glass')); parts.append(box('shop_fr', (3.4, 0.14, 0.1), (-0.2, -0.12, 2.55), 'wood'))
        parts.append(box('shop_frL', (0.14, 0.14, 2.3), (-1.85, -0.12, 1.45), 'wood')); parts.append(box('shop_frR', (0.14, 0.14, 2.3), (1.45, -0.12, 1.45), 'wood'))
        parts.append(box('shop_stall', (3.4, 0.2, 0.5), (-0.2, -0.1, 0.25), 'wood')); parts.append(box('shop_fascia', (W, 0.25, 0.7), (0, -0.14, 3.0), 'wood'))
        parts.append(box('shop_sign', (3.4, 0.03, 0.45), (0, -0.28, 3.0), 'paint'))
        parts.append(box('shop_door', (0.9, 0.1, 2.1), (1.5, -0.1, 1.05), 'door')); parts.append(box('shop_doorgl', (0.6, 0.04, 1.0), (1.5, -0.16, 1.4), 'glass'))
        # Markise
        aw = box('awning', (3.6, 1.1, 0.08), (-0.2, -0.65, 2.75), 'canvas', rot=(0.35,0,0)); parts.append(aw)
    else:
        door(parts, -1.2)
        if variant == 'bay': bay_window(parts, 0.9, 1.7)
        else: sash_window(parts, 0.9, 1.75, 1.1, 1.7)
    for f in range(1, floors):
        z = f*FLOOR + 1.6
        hw = 1.5 if f < floors-1 else 1.3
        sash_window(parts, -1.1, z, 1.0, hw); sash_window(parts, 1.0, z, 1.0, hw)
        if variant == 'bay' and f == 1: bay_window(parts, 0.9, z-0.05, h=1.5)  # Erker über zwei Geschosse
    if corner:
        for f in range(0 if not shop else 1, floors):
            z = f*FLOOR + 1.65
            sash_window(parts, 2.0, z, 1.0, 1.4, y=1.2, depth_sign=1, tag='cw'); sash_window(parts, 2.0, z, 1.0, 1.4, y=2.9, depth_sign=1, tag='cw')
    # Rückseite
    for f in range(floors):
        sash_window(parts, 0.9, f*FLOOR+1.7, 0.9, 1.3, y=D, depth_sign=1, tag='rw')
    if floors > 1: parts.append(box('backdoor', (0.9, 0.1, 2.0), (-1.1, D+0.03, 1.0), 'door'))
    # Gesims, Sockel, Fallrohr
    parts.append(box('cornice', (W+0.1, 0.3, 0.3), (0, -0.1, H-0.15), 'stone')); parts.append(box('plinth', (W, 0.12, 0.6), (0, -0.06, 0.3), 'stone'))
    parts.append(cyl('pipe', 0.06, H-0.4, (-1.95, -0.15, H/2-0.2), 'metal', v=8))
    # Dach
    if roofkind == 'pitched':
        roof = prism('roof', W+0.1, D+0.3, 2.2, (0, D/2, H), 'slate'); parts.append(roof)
        parts.append(box('ridge', (W+0.1, 0.18, 0.12), (0, D/2, H+2.2), 'metal'))
        parts.append(box('gutter', (W+0.1, 0.16, 0.12), (0, -0.1, H-0.02), 'metal'))
        # Schornstein mit Töpfen
        parts.append(box('chimney', (0.9, 0.7, 1.6), (-1.5, D/2, H+2.0), 'brick'))
        for i, dx in enumerate((-1.75, -1.5, -1.25)): parts.append(cyl('pot', 0.1, 0.45, (dx, D/2, H+2.95), 'clay', v=8))
        if random.random() < 0.6: parts.append(cyl('aerial', 0.02, 1.2, (1.2, D/2+0.6, H+2.6), 'metal', v=6)); parts.append(box('aerial2', (0.6, 0.02, 0.02), (1.2, D/2+0.6, H+3.1), 'metal'))
    else:
        parts.append(box('parapet', (W+0.1, 0.25, 0.6), (0, -0.05, H+0.3), 'stone')); parts.append(box('flat', (W, D, 0.1), (0, D/2, H+0.05), 'asphalt'))
        parts.append(box('chimney', (0.9, 0.7, 1.2), (-1.5, D/2, H+0.6), 'brick'))
    return finish(parts, name)

# ---------------- Straßenmöbel ----------------
def lamp_post():
    parts = [cyl('base', 0.18, 0.5, (0,0,0.25), 'metal', v=10), cyl('base2', 0.12, 0.6, (0,0,0.75), 'metal', v=10), cyl('col', 0.07, 3.4, (0,0,2.7), 'metal', v=10),
             cyl('neck', 0.09, 0.3, (0,0,4.45), 'metal', v=10), box('lantern', (0.42,0.42,0.55), (0,0,4.85), 'glass'), box('lamp_core', (0.2,0.2,0.3), (0,0,4.85), 'lamp'),
             cyl('cap', 0.32, 0.25, (0,0,5.2), 'metal', v=8, r2=0.05), box('ladderbar', (0.5,0.04,0.04), (0,0,4.2), 'metal')]
    return finish(parts, 'lamp_post')
def phone_box():
    parts = [box('k6_base', (1.0,1.0,0.15), (0,0,0.075), 'metal'), box('k6_body', (0.96,0.96,2.3), (0,0,1.3), 'red')]
    for (x,y,sx,sy) in ((0,-0.49,0.7,0.04),(0,0.49,0.7,0.04),(-0.49,0,0.04,0.7),(0.49,0,0.04,0.7)):
        parts.append(box('k6_gl', (sx,sy,1.5), (x,y,1.55), 'glass'))
    parts.append(box('k6_roof', (1.06,1.06,0.12), (0,0,2.5), 'red')); parts.append(sph('k6_dome', 0.55, (0,0,2.45), 'red', scale=(1,1,0.45)))
    parts.append(box('k6_sign', (0.8,1.08,0.22), (0,0,2.3), 'glass'))
    return finish(parts, 'phone_box')
def pillar_box():
    parts = [cyl('pb_base', 0.34, 0.2, (0,0,0.1), 'metal', v=14), cyl('pb_body', 0.3, 1.3, (0,0,0.85), 'red', v=14), cyl('pb_cap', 0.34, 0.12, (0,0,1.56), 'metal', v=14), sph('pb_top', 0.3, (0,0,1.6), 'red', scale=(1,1,0.5)), box('pb_slot', (0.3,0.05,0.04), (0,-0.29,1.2), 'metal')]
    return finish(parts, 'pillar_box')
def bollard():
    return finish([cyl('bo', 0.12, 0.9, (0,0,0.45), 'metal', v=10), sph('bo_top', 0.14, (0,0,0.95), 'metal')], 'bollard')
def wheelie_bin():
    return finish([box('bin', (0.6,0.7,1.0), (0,0,0.55), 'paint'), box('bin_lid', (0.64,0.74,0.08), (0,0,1.08), 'paint'), cyl('bin_w', 0.1, 0.08, (-0.25,0.3,0.1), 'rubber', v=8, rot=(0,math.pi/2,0)), cyl('bin_w2', 0.1, 0.08, (0.25,0.3,0.1), 'rubber', v=8, rot=(0,math.pi/2,0))], 'wheelie_bin')
def railing():
    parts = [box('rail_top', (2.0,0.04,0.04), (0,0,1.0), 'metal'), box('rail_mid', (2.0,0.03,0.03), (0,0,0.15), 'metal')]
    for i in range(9):
        x = -0.95 + i*0.2375; parts.append(box('rail_v', (0.03,0.03,1.05), (x,0,0.55), 'metal')); parts.append(cyl('rail_tip', 0.04, 0.12, (x,0,1.1), 'metal', v=5, r2=0.0))
    return finish(parts, 'railing')
def car(name='car', cab=False):
    L, Wd = (4.4, 1.85) if not cab else (4.5, 1.9); h1 = 0.65 if not cab else 0.8; h2 = 0.5 if not cab else 0.75
    parts = [box('body', (L, Wd, h1), (0,0,0.35+h1/2), 'paint'), box('cabin', (L*0.52, Wd*0.92, h2), (-0.2 if not cab else -0.1, 0, 0.35+h1+h2/2), 'paint'),
             box('win_f', (0.05, Wd*0.86, h2*0.8), (L*0.26-0.2, 0, 0.35+h1+h2/2), 'glass'), box('win_b', (0.05, Wd*0.86, h2*0.8), (-L*0.26-0.2, 0, 0.35+h1+h2/2), 'glass'),
             box('win_l', (L*0.48, 0.05, h2*0.75), (-0.2, Wd*0.46, 0.35+h1+h2/2), 'glass'), box('win_r', (L*0.48, 0.05, h2*0.75), (-0.2, -Wd*0.46, 0.35+h1+h2/2), 'glass'),
             box('bumper_f', (0.2, Wd, 0.25), (L/2, 0, 0.45), 'rubber'), box('bumper_b', (0.2, Wd, 0.25), (-L/2, 0, 0.45), 'rubber'),
             box('light_l', (0.08, 0.3, 0.15), (L/2+0.05, Wd*0.35, 0.75), 'lamp'), box('light_r', (0.08, 0.3, 0.15), (L/2+0.05, -Wd*0.35, 0.75), 'lamp')]
    for x in (L*0.32, -L*0.32):
        for y in (Wd/2-0.05, -Wd/2+0.05): parts.append(cyl('wheel', 0.33, 0.22, (x, y, 0.33), 'rubber', v=12, rot=(math.pi/2,0,0)))
    return finish(parts, name)
def bus():
    L, Wd, H = 10.4, 2.5, 4.4
    parts = [box('bus_body', (L, Wd, H-0.5), (0,0,0.5+(H-0.5)/2), 'red'), box('bus_roof', (L-0.3, Wd-0.3, 0.15), (0,0,H+0.05), 'red')]
    for z in (1.5, 3.3):
        parts.append(box('bus_win', (L-1.2, Wd+0.02, 0.9), (0, 0, z), 'glass'))
    parts.append(box('bus_front', (0.06, Wd-0.3, 1.1), (L/2+0.01, 0, 1.7), 'glass')); parts.append(box('bus_front2', (0.06, Wd-0.3, 1.0), (L/2+0.01, 0, 3.4), 'glass'))
    parts.append(box('bus_dest', (0.06, Wd-0.6, 0.35), (L/2+0.02, 0, 4.0), 'lamp'))
    for x in (L*0.33, -L*0.3):
        for y in (Wd/2-0.1, -Wd/2+0.1): parts.append(cyl('bwheel', 0.5, 0.3, (x, y, 0.5), 'rubber', v=14, rot=(math.pi/2,0,0)))
    return finish(parts, 'bus')
def market_stall():
    parts = [box('table', (2.4,1.2,0.08), (0,0,0.85), 'wood'), box('cloth', (2.5,1.3,0.6), (0,0,0.5), 'canvas')]
    for x in (-1.1, 1.1):
        for y in (-0.5, 0.5): parts.append(cyl('post', 0.03, 2.4, (x,y,1.2), 'metal', v=6))
    parts.append(box('canopy', (2.8,1.6,0.06), (0,0,2.45), 'red', rot=(0.12,0,0)))
    for i in range(6): parts.append(box('goods', (0.3,0.3,0.25), (-1.0+i*0.4, random.uniform(-0.3,0.3), 1.0), random.choice(['paint','red','canvas','leaf'])))
    return finish(parts, 'market_stall')
def plane_tree():
    parts = [cyl('trunk', 0.28, 3.2, (0,0,1.6), 'bark', v=9, r2=0.2), cyl('branch', 0.1, 1.6, (0.4,0.2,3.6), 'bark', v=6, rot=(0.6,0.5,0)), cyl('branch2', 0.1, 1.5, (-0.4,-0.2,3.6), 'bark', v=6, rot=(-0.6,-0.4,0))]
    for (x,y,z,r) in ((0,0,4.6,1.9),(1.2,0.6,4.2,1.4),(-1.2,-0.5,4.3,1.4),(0.3,-1.2,4.8,1.3),(-0.4,1.1,5.0,1.3),(0,0,5.9,1.3)):
        parts.append(sph('crown', r, (x,y,z), 'leaf', seg=10, ring=7))
    return finish(parts, 'plane_tree', uvscale=1.0)
def bench():
    parts = [box('seat', (1.8,0.45,0.06), (0,0,0.45), 'wood'), box('back', (1.8,0.06,0.45), (0,0.22,0.75), 'wood')]
    for x in (-0.8, 0.8): parts.append(box('leg', (0.08,0.45,0.45), (x,0,0.22), 'metal')); parts.append(box('legb', (0.08,0.08,0.5), (x,0.22,0.72), 'metal'))
    return finish(parts, 'bench')

built = []
built.append(terrace('house_plain', 'plain')); built.append(terrace('house_bay', 'bay')); built.append(terrace('house_shop', 'plain', shop=True))
built.append(terrace('house_plain2', 'plain', floors=2)); built.append(terrace('house_corner', 'plain', corner=True)); built.append(terrace('house_cornershop', 'plain', corner=True, shop=True))
built.append(terrace('house_flat', 'plain', floors=3, roofkind='flat'))
built += [lamp_post(), phone_box(), pillar_box(), bollard(), wheelie_bin(), railing(), car('car'), car('cab', cab=True), bus(), market_stall(), plane_tree(), bench()]
# Objekte nebeneinander legen (nur fürs Debuggen; die Positionen werden im Spiel ignoriert, da pro Node die Geometrie genutzt wird)
for i, o in enumerate(built): o.location = (0,0,0)
for o in built:
    for p in o.data.polygons: p.use_smooth = False
tris = 0
for o in built: o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles); print(o.name, 'tris', len(o.data.loop_triangles))
print('total tris', tris)
glb = os.path.join(OUT, 'camden.glb')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_materials='EXPORT', export_image_format='NONE', export_texcoords=True, export_normals=True)
# GLB -> JSON mit eingebettetem Puffer (Artefakt-tauglich)
data = open(glb,'rb').read(); magic, ver, length = struct.unpack('<III', data[:12]); off = 12; j = None; binchunk = None
while off < length:
    clen, ctype = struct.unpack('<II', data[off:off+8]); body = data[off+8:off+8+clen]; off += 8+clen
    if ctype == 0x4E4F534A: j = json.loads(body.decode('utf-8'))
    elif ctype == 0x004E4942: binchunk = body
j['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binchunk).decode()
open(os.path.join(OUT, 'camden.json'), 'w').write(json.dumps(j)); print('json bytes', os.path.getsize(os.path.join(OUT,'camden.json')))
