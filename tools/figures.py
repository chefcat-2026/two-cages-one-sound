# Figuren für Camden Command, gebaut in Blender (bpy, headless). Export: models.json + models.bin
import bpy, bmesh, json, math, random, struct, sys
from mathutils import Vector, noise
OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '.'
random.seed(7)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def meta(name, elems, res=0.07, thresh=0.35):
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.threshold = thresh
    obj = bpy.data.objects.new(name, mb); bpy.context.collection.objects.link(obj)
    for e in elems:
        el = mb.elements.new(); el.type = e.get('type', 'BALL'); el.co = Vector(e['co']); el.radius = e['r']*1.55; el.stiffness = e.get('stiff', 2.0)
        if el.type == 'ELLIPSOID':
            el.size_x, el.size_y, el.size_z = e['size']
        if e.get('neg'): el.use_negative = True
    return obj

def to_mesh(obj, name):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
    me.name = name; new = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(new)
    bpy.data.objects.remove(obj, do_unlink=True); return new

def apply_all(obj):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
    old = obj.data; obj.modifiers.clear(); obj.data = me; bpy.data.meshes.remove(old)

def decimate(obj, tris):
    me = obj.data; me.calc_loop_triangles(); n = len(me.loop_triangles)
    if n > tris:
        m = obj.modifiers.new('dec', 'DECIMATE'); m.ratio = tris / n; apply_all(obj)

def displace(obj, strength, scale, noise_depth=2, mid=0.5):
    tex = bpy.data.textures.new('n', type='CLOUDS'); tex.noise_scale = scale; tex.noise_depth = noise_depth
    m = obj.modifiers.new('disp', 'DISPLACE'); m.texture = tex; m.strength = strength; m.mid_level = mid; apply_all(obj)

def subdiv(obj, levels=1):
    m = obj.modifiers.new('sub', 'SUBSURF'); m.levels = levels; apply_all(obj)

def smooth(obj):
    for p in obj.data.polygons: p.use_smooth = True

def primitive(kind, name, loc=(0,0,0), scale=(1,1,1), rot=(0,0,0), **kw):
    if kind == 'sphere': bpy.ops.mesh.primitive_uv_sphere_add(segments=kw.get('seg',14), ring_count=kw.get('ring',10), radius=1, location=loc)
    elif kind == 'cube': bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    elif kind == 'cone': bpy.ops.mesh.primitive_cone_add(vertices=kw.get('v',8), radius1=1, radius2=kw.get('r2',0), depth=1, location=loc)
    elif kind == 'cyl': bpy.ops.mesh.primitive_cylinder_add(vertices=kw.get('v',10), radius=1, depth=1, location=loc)
    elif kind == 'torus': bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=kw.get('minor',0.2), major_segments=kw.get('seg',20), minor_segments=8, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale; o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); return o

def colorize(obj, fn):
    me = obj.data
    attr = me.color_attributes.get('Col') or me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        c = fn(v.co, v.normal); attr.data[v.index].color = (c[0], c[1], c[2], 1.0)

def solid(col):
    return lambda co, n: col

def join(objs, name):
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); j = bpy.context.active_object; j.name = name
    for o in bpy.context.selected_objects: o.select_set(False)
    return j

def dark(c, k): return (c[0]*k, c[1]*k, c[2]*k)

# ---------- Export ----------
BIN = bytearray(); MANIFEST = {}
def export(obj, name, scale=1.0):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
    me.calc_loop_triangles(); attr = me.color_attributes.get('Col')
    # Blender Z-up, Front -Y  ->  Spiel Y-up, Front +Z : (x, z, -y)
    pos = []; nor = []; col = []
    vnormals = [Vector((0,0,0)) for _ in me.vertices]
    for p in me.polygons:
        for vi in p.vertices: vnormals[vi] += p.normal
    for v in me.vertices:
        n = vnormals[v.index]; n = n.normalized() if n.length > 0 else v.normal
        pos += [v.co.x*scale, v.co.z*scale, -v.co.y*scale]; nor += [n.x, n.z, -n.y]
        c = attr.data[v.index].color if attr else (0.8,0.8,0.8,1); col += [c[0], c[1], c[2]]
    idx = []
    for t in me.loop_triangles: idx += list(t.vertices)
    def put(arr, fmt, align):
        global BIN
        while len(BIN) % align: BIN += b'\0'
        off = len(BIN); BIN += struct.pack('<%d%s' % (len(arr), fmt), *arr); return [off, len(arr)]
    MANIFEST[name] = {'pos': put(pos, 'f', 4), 'nor': put(nor, 'f', 4), 'col': put(col, 'f', 4), 'idx': put(idx, 'H' if len(me.vertices) < 65535 else 'I', 2), 'tris': len(idx)//3, 'u32': len(me.vertices) >= 65535}
    print(name, 'verts', len(me.vertices), 'tris', len(idx)//3)
    bpy.data.meshes.remove(me)

# ---------- Meerschweinchen ----------
def guinea_pig(name, fur, patches=None, long_fur=False, curls=False, jacket=None, shades=False, scale=1.0, spikes=False):
    # Körper entlang -Y (vorne). Länge ~1.7, Höhe ~0.9
    elems = [
        {'type':'ELLIPSOID','co':(0,0.05,0.44),'r':0.58,'size':(0.66,0.95,0.56)},   # Rumpf
        {'type':'ELLIPSOID','co':(0,-0.62,0.46),'r':0.42,'size':(0.5,0.5,0.45)},   # Kopf
        {'co':(0,-0.98,0.40),'r':0.26},                                             # Schnauze
        {'co':(0.22,-0.72,0.40),'r':0.18},{'co':(-0.22,-0.72,0.40),'r':0.18},        # Backen
        {'type':'ELLIPSOID','co':(0.0,0.72,0.42),'r':0.35,'size':(0.5,0.4,0.4)},    # Hinterteil
        {'co':(0.3,-0.3,0.12),'r':0.14},{'co':(-0.3,-0.3,0.12),'r':0.14},{'co':(0.3,0.5,0.12),'r':0.14},{'co':(-0.3,0.5,0.12),'r':0.14}, # Pfoten
    ]
    body = to_mesh(meta(name+'_mb', elems, res=0.07), name+'_body')
    if long_fur:
        subdiv(body, 1); displace(body, 0.16, 0.22, 3)
    elif curls:
        subdiv(body, 1); displace(body, 0.07, 0.12, 2)
    decimate(body, 2200 if long_fur else 1700); smooth(body)
    base = fur
    def pigcol(co, n):
        c = base
        if patches:
            for (px,py,pz,r,pc) in patches:
                if (co - Vector((px,py,pz))).length < r: c = pc
        # Bauch heller
        if n.z < -0.4: c = tuple(min(1, x*1.12+0.03) for x in c)
        return c
    colorize(body, pigcol)
    parts = [body]
    # Ohren
    for sx in (1,-1):
        ear = primitive('sphere', name+'_ear', loc=(sx*0.3,-0.55,0.82), scale=(0.17,0.08,0.13), rot=(0.3,sx*0.5,0), seg=10, ring=6)
        colorize(ear, solid(dark(fur,0.6) if fur[0]<0.5 else (0.45,0.3,0.3))); parts.append(ear)
    # Augen
    for sx in (1,-1):
        eye = primitive('sphere', name+'_eye', loc=(sx*0.27,-0.88,0.56), scale=(0.075,0.06,0.075), seg=10, ring=6)
        colorize(eye, lambda co,n,sx=sx: (0.03,0.03,0.03) if (co - Vector((sx*0.27-0.02*sx,-0.93,0.59))).length > 0.025 else (1,1,1)); parts.append(eye)
    nose = primitive('sphere', name+'_nose', loc=(0,-1.22,0.42), scale=(0.07,0.05,0.05), seg=8, ring=6); colorize(nose, solid((0.85,0.5,0.52))); parts.append(nose)
    if shades:
        for sx in (1,-1):
            g = primitive('cube', name+'_sh', loc=(sx*0.25,-0.95,0.58), scale=(0.24,0.06,0.16)); colorize(g, solid((0.02,0.02,0.02))); parts.append(g)
        br = primitive('cube', name+'_br', loc=(0,-0.95,0.6), scale=(0.2,0.04,0.03)); colorize(br, solid((0.02,0.02,0.02))); parts.append(br)
    if jacket:
        # Lederjacke als Farbzone auf dem Rücken, Nieten auf der Körperoberfläche
        me = body.data; attr = me.color_attributes['Col']
        inzone = lambda co, n: (-0.42 < co.y < 0.42) and co.z > 0.30 and not (abs(co.x) < 0.12 and co.z < 0.6 and n.z < 0.2)
        for v in me.vertices:
            if inzone(v.co, v.normal): attr.data[v.index].color = (jacket[0], jacket[1], jacket[2], 1.0)
        cands = [v for v in me.vertices if inzone(v.co, v.normal) and v.normal.z > 0.15]
        random.shuffle(cands)
        for v in cands[:16]:
            st = primitive('sphere', name+'_st', loc=tuple(v.co + v.normal*0.02), scale=(0.035,0.035,0.035), seg=6, ring=4)
            colorize(st, solid((0.88,0.88,0.92))); parts.append(st)
        # Kragen
        kr = primitive('torus', name+'_kr', loc=(0,-0.42,0.52), scale=(0.44,0.44,0.36), rot=(math.pi/2,0,0), minor=0.09, seg=18)
        colorize(kr, solid(dark(jacket,1.3))); parts.append(kr)
    if spikes:
        me = body.data
        cands = [v for v in me.vertices if v.normal.z > 0.35 and -0.6 < v.co.y < 0.8]
        random.shuffle(cands)
        for v in cands[:22]:
            d = (v.normal + Vector((0, 0.9, -0.1))).normalized()
            rot = d.to_track_quat('Z', 'Y').to_euler()
            sp = primitive('cone', name+'_sp', loc=tuple(v.co + d*0.12), scale=(0.045,0.045,0.3), rot=tuple(rot), v=5)
            colorize(sp, solid(dark(fur,0.9))); parts.append(sp)
    obj = join(parts, name); smooth(obj); return obj

def mouse(name):
    elems = [{'type':'ELLIPSOID','co':(0,0,0.2),'r':0.26,'size':(0.5,0.9,0.5)},{'co':(0,-0.33,0.22),'r':0.17},{'co':(0,-0.5,0.2),'r':0.1}]
    body = to_mesh(meta(name+'_mb', elems, res=0.05), name+'_body'); decimate(body, 500); smooth(body)
    colorize(body, lambda co,n: (0.5,0.48,0.46) if n.z>-0.3 else (0.7,0.66,0.62)); parts=[body]
    for sx in (1,-1):
        ear = primitive('sphere', name+'_ear', loc=(sx*0.14,-0.3,0.42), scale=(0.11,0.04,0.11), seg=8, ring=6); colorize(ear, solid((0.72,0.58,0.56))); parts.append(ear)
        eye = primitive('sphere', name+'_eye', loc=(sx*0.08,-0.47,0.3), scale=(0.035,0.035,0.035), seg=6, ring=4); colorize(eye, solid((0.02,0.02,0.02))); parts.append(eye)
    tail = primitive('cyl', name+'_tail', loc=(0,0.55,0.12), scale=(0.025,0.6,0.025), rot=(math.pi/2.2,0,0), v=6); colorize(tail, solid((0.72,0.58,0.56))); parts.append(tail)
    return join(parts, name)

def cat(name, fur):
    elems = [
        {'type':'ELLIPSOID','co':(0,0.1,0.75),'r':0.7,'size':(0.72,1.25,0.62)}, {'type':'ELLIPSOID','co':(0,-0.95,1.02),'r':0.5,'size':(0.56,0.5,0.5)},
        {'co':(0,-1.3,0.95),'r':0.22},{'co':(0.22,-1.12,0.9),'r':0.2},{'co':(-0.22,-1.12,0.9),'r':0.2},
        {'co':(0.4,-0.6,0.28),'r':0.2},{'co':(-0.4,-0.6,0.28),'r':0.2},{'co':(0.4,0.75,0.28),'r':0.2},{'co':(-0.4,0.75,0.28),'r':0.2},
        {'type':'ELLIPSOID','co':(0,1.0,0.72),'r':0.45,'size':(0.6,0.5,0.5)},
    ]
    body = to_mesh(meta(name+'_mb', elems, res=0.08), name+'_body'); subdiv(body,1); displace(body, 0.05, 0.3, 2); decimate(body, 1500); smooth(body)
    colorize(body, lambda co,n: fur if n.z>-0.3 else tuple(min(1,x*1.15) for x in fur)); parts=[body]
    for sx in (1,-1):
        ear = primitive('cone', name+'_ear', loc=(sx*0.3,-0.95,1.48), scale=(0.17,0.1,0.3), rot=(0,sx*0.25,0), v=6); colorize(ear, solid(fur)); parts.append(ear)
        eye = primitive('sphere', name+'_eye', loc=(sx*0.2,-1.4,1.1), scale=(0.09,0.06,0.09), seg=8, ring=6); colorize(eye, lambda co,n,sx=sx: (0.85,0.65,0.12) if abs(co.x-sx*0.2)>0.03 else (0.02,0.02,0.02)); parts.append(eye)
    nose = primitive('sphere', name+'_nose', loc=(0,-1.5,0.96), scale=(0.06,0.04,0.045), seg=8, ring=6); colorize(nose, solid((0.3,0.2,0.22))); parts.append(nose)
    tail = primitive('cyl', name+'_tail', loc=(0,1.45,0.95), scale=(0.1,1.2,0.1), rot=(-0.9,0,0), v=8); colorize(tail, solid(fur)); parts.append(tail)
    return join(parts, name)

def man(name, suit, skin=(0.9,0.76,0.64), hair=(0.15,0.12,0.1), paper=False, case=False, robe=False, hat=False, shirt=None, amp=False, spikes=False):
    parts=[]
    torso = primitive('cube', name+'_t', loc=(0,0,1.05), scale=(0.56,0.32,0.76)); subdiv(torso,1); colorize(torso, solid(suit)); parts.append(torso)
    if shirt:
        sh = primitive('cube', name+'_sh', loc=(0,-0.17,1.1), scale=(0.3,0.03,0.24)); colorize(sh, solid(shirt)); parts.append(sh)
    for sx in (1,-1):
        leg = primitive('cube', name+'_l', loc=(sx*0.15,0,0.34), scale=(0.2,0.24,0.66)); colorize(leg, solid(dark(suit,0.6) if not robe else (0.3,0.2,0.25))); parts.append(leg)
        arm = primitive('cube', name+'_a', loc=(sx*0.37,0,1.05), scale=(0.15,0.16,0.62)); subdiv(arm,1); colorize(arm, solid(suit)); parts.append(arm)
        hand = primitive('sphere', name+'_h', loc=(sx*0.37,-0.02,0.7), scale=(0.08,0.08,0.08), seg=8, ring=6); colorize(hand, solid(skin)); parts.append(hand)
    head = primitive('sphere', name+'_hd', loc=(0,0,1.66), scale=(0.22,0.24,0.27), seg=14, ring=10)
    colorize(head, lambda co,n: hair if (co.z>1.72 and co.y>-0.12) or co.z>1.84 else skin); parts.append(head)
    for sx in (1,-1):
        eye = primitive('sphere', name+'_e', loc=(sx*0.08,-0.21,1.68), scale=(0.025,0.02,0.025), seg=6, ring=4); colorize(eye, solid((0.05,0.05,0.05))); parts.append(eye)
    if hat:
        h = primitive('cyl', name+'_hat', loc=(0,0,1.98), scale=(0.2,0.2,0.22), v=14); colorize(h, solid((0.05,0.05,0.06))); parts.append(h)
        br = primitive('cyl', name+'_brim', loc=(0,0,1.87), scale=(0.32,0.32,0.02), v=14); colorize(br, solid((0.05,0.05,0.06))); parts.append(br)
    if paper:
        p = primitive('cube', name+'_p', loc=(0.42,-0.22,0.98), scale=(0.3,0.01,0.4), rot=(0,0,0.3)); colorize(p, solid((0.97,0.96,0.92))); parts.append(p)
    if case:
        c = primitive('cube', name+'_c', loc=(0.46,0,0.62), scale=(0.34,0.1,0.26)); colorize(c, solid((0.12,0.09,0.07))); parts.append(c)
    if amp:
        a = primitive('cube', name+'_amp', loc=(0,0.38,1.25), scale=(0.7,0.4,0.55)); colorize(a, lambda co,n: (0.9,0.15,0.2) if (co.y>0.55 and abs(co.x-0.2)<0.05 and abs(co.z-1.4)<0.05) else (0.07,0.07,0.07)); parts.append(a)
    if spikes:
        for i in range(5):
            sp = primitive('cone', name+'_sp', loc=(-0.14+i*0.07,0,1.9), scale=(0.03,0.03,0.14), v=5); colorize(sp, solid((0.85,0.85,0.9))); parts.append(sp)
    return join(parts, name)

def build_all():
    reset()
    john = guinea_pig('john', (0.95,0.93,0.9), patches=[(0.25,0.0,0.5,0.42,(0.08,0.07,0.07)),(-0.2,0.75,0.45,0.35,(0.08,0.07,0.07)),(0.22,-0.6,0.6,0.26,(0.08,0.07,0.07))], curls=True, jacket=(0.08,0.07,0.08), shades=True)
    export(john, 'john', 1.0); bpy.data.objects.remove(john)
    theo = guinea_pig('theo', (0.06,0.055,0.055), long_fur=True, jacket=(0.1,0.08,0.09), spikes=True)
    export(theo, 'theo', 1.05); bpy.data.objects.remove(theo)
    adri = guinea_pig('adriana', (0.42,0.26,0.16), patches=[(0,-0.6,0.5,0.5,(0.95,0.93,0.9)),(0.2,0.6,0.5,0.3,(0.95,0.93,0.9))])
    export(adri, 'adriana', 0.9); bpy.data.objects.remove(adri)
    sus = guinea_pig('susanna', (0.22,0.14,0.1), patches=[(0,0.1,0.5,0.45,(0.9,0.82,0.7))])
    export(sus, 'susanna', 0.9); bpy.data.objects.remove(sus)
    m = mouse('maus'); export(m, 'maus', 1.0); bpy.data.objects.remove(m)
    sm = cat('smokey', (0.42,0.43,0.47)); export(sm, 'smokey', 1.0); bpy.data.objects.remove(sm)
    bo = cat('bounty', (0.55,0.56,0.6)); export(bo, 'bounty', 0.92); bpy.data.objects.remove(bo)
    b = man('bote', (0.8,0.76,0.68), paper=True); export(b, 'bote'); bpy.data.objects.remove(b)
    mk = man('makler', (0.16,0.22,0.3), case=True, hair=(0.3,0.25,0.2)); export(mk, 'makler'); bpy.data.objects.remove(mk)
    ins = man('inspektor', (0.33,0.4,0.28), paper=True, hair=(0.5,0.5,0.5)); export(ins, 'inspektor'); bpy.data.objects.remove(ins)
    nb = man('nachbar', (0.5,0.3,0.42), robe=True, paper=True, hair=(0.8,0.8,0.8)); export(nb, 'nachbar'); bpy.data.objects.remove(nb)
    dz = man('dezernent', (0.08,0.08,0.1), hat=True, case=True); export(dz, 'dezernent', 1.25); bpy.data.objects.remove(dz)
    fn = man('fan', (0.07,0.07,0.08), shirt=(0.75,0.12,0.16), hair=(0.05,0.05,0.05), spikes=True); export(fn, 'fan'); bpy.data.objects.remove(fn)
    rd = man('roadie', (0.14,0.14,0.15), amp=True, hair=(0.2,0.15,0.1)); export(rd, 'roadie'); bpy.data.objects.remove(rd)
    with open(OUT+'/models.bin','wb') as f: f.write(BIN)
    with open(OUT+'/models.json','w') as f: json.dump(MANIFEST, f)
    print('bytes', len(BIN))

build_all()
