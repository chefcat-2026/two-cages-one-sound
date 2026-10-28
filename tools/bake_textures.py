# Materialien für die Camden-Straße: prozedural in Blender, gebacken nach Farbe / Normal / Rauheit
import bpy, sys, math, os
OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '.'
SIZE = 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.render.bake.margin = 4
bpy.ops.mesh.primitive_plane_add(size=2); plane = bpy.context.active_object

def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n

def bake(name, build):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    build(nt, bsdf)
    plane.data.materials.clear(); plane.data.materials.append(m)
    img = bpy.data.images.new(name+'_bake', SIZE, SIZE); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
    bpy.ops.object.select_all(action='DESELECT'); plane.select_set(True); bpy.context.view_layer.objects.active = plane
    for pas, suffix, kw in (('DIFFUSE', 'col', {'pass_filter': {'COLOR'}}), ('NORMAL', 'nrm', {'normal_space': 'TANGENT'}), ('ROUGHNESS', 'rgh', {})):
        if suffix == 'nrm': img.colorspace_settings.name = 'Non-Color'
        else: img.colorspace_settings.name = 'sRGB'
        bpy.ops.object.bake(type=pas, margin=4, **kw)
        img.filepath_raw = os.path.join(OUT, f'{name}_{suffix}.jpg'); img.file_format = 'JPEG'; sc.render.image_settings.quality = 90; img.save()
        print('baked', name, suffix)
    bpy.data.images.remove(img)

def brick(nt, bsdf, c1, c2, mortar, scale=10, noise_dark=0.35, rough=0.75, bump=0.6):
    tc = node(nt, 'ShaderNodeTexCoord'); br = node(nt, 'ShaderNodeTexBrick', Scale=scale, Color1=c1, Color2=c2, Mortar=mortar); br.inputs['Mortar Size'].default_value = 0.025; br.inputs['Bias'].default_value = 0.0; br.offset = 0.5; br.squash = 1.8
    nt.links.new(tc.outputs['UV'], br.inputs['Vector'])
    nz = node(nt, 'ShaderNodeTexNoise', Scale=18, Detail=8, Roughness=0.7); nz2 = node(nt, 'ShaderNodeTexNoise', Scale=3, Detail=4)
    # Verwitterung: Rauschen dunkelt die Farbe
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix.inputs['Factor'].default_value = noise_dark
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(br.outputs['Color'], mix.inputs[6]); nt.links.new(ramp.outputs['Color'], mix.inputs[7])
    mix2 = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix2.inputs['Factor'].default_value = 0.25
    ramp2 = node(nt, 'ShaderNodeValToRGB'); ramp2.color_ramp.elements[0].position = 0.3
    nt.links.new(nz2.outputs['Fac'], ramp2.inputs['Fac']); nt.links.new(mix.outputs[2], mix2.inputs[6]); nt.links.new(ramp2.outputs['Color'], mix2.inputs[7])
    nt.links.new(mix2.outputs[2], bsdf.inputs['Base Color'])
    # Rauheit: Mörtel rauer, Ziegel glatter, plus Rauschen
    mr = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); mr.inputs[1].default_value = -0.25; mr.inputs[2].default_value = rough
    nt.links.new(br.outputs['Fac'], mr.inputs[0]); nt.links.new(mr.outputs[0], bsdf.inputs['Roughness'])
    # Relief: Fugen zurück, Rauschen für Oberfläche
    bmp = node(nt, 'ShaderNodeBump', Strength=bump, Distance=0.08); inv = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs['Fac'], inv.inputs[1])
    add = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); add.inputs[1].default_value = 0.15
    nt.links.new(nz.outputs['Fac'], add.inputs[0]); nt.links.new(inv.outputs[0], add.inputs[2])
    nt.links.new(add.outputs[0], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])

bake('brick_london', lambda nt, b: brick(nt, b, (0.56,0.44,0.28,1), (0.47,0.36,0.24,1), (0.62,0.6,0.56,1), scale=11, noise_dark=0.45))
bake('brick_red', lambda nt, b: brick(nt, b, (0.46,0.18,0.12,1), (0.36,0.14,0.1,1), (0.6,0.57,0.53,1), scale=11, noise_dark=0.35))
bake('brick_dark', lambda nt, b: brick(nt, b, (0.22,0.17,0.15,1), (0.17,0.13,0.12,1), (0.35,0.33,0.31,1), scale=11, noise_dark=0.5))

def slate(nt, bsdf):
    tc = node(nt, 'ShaderNodeTexCoord'); br = node(nt, 'ShaderNodeTexBrick', Scale=9, Color1=(0.16,0.17,0.2,1), Color2=(0.12,0.13,0.16,1), Mortar=(0.05,0.05,0.06,1)); br.inputs['Mortar Size'].default_value = 0.012; br.squash = 1.2; br.offset = 0.5
    nt.links.new(tc.outputs['UV'], br.inputs['Vector'])
    nz = node(nt, 'ShaderNodeTexNoise', Scale=25, Detail=6); mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='OVERLAY'); mix.inputs['Factor'].default_value = 0.35
    nt.links.new(br.outputs['Color'], mix.inputs[6]); nt.links.new(nz.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    bmp = node(nt, 'ShaderNodeBump', Strength=0.7, Distance=0.06); inv = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs['Fac'], inv.inputs[1]); nt.links.new(inv.outputs[0], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('slate', slate)

def asphalt(nt, bsdf):
    nz = node(nt, 'ShaderNodeTexNoise', Scale=60, Detail=10, Roughness=0.8); nz2 = node(nt, 'ShaderNodeTexNoise', Scale=4, Detail=5)
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.05,0.05,0.055,1); ramp.color_ramp.elements[1].color = (0.17,0.17,0.18,1); ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix.inputs['Factor'].default_value = 0.5
    ramp2 = node(nt, 'ShaderNodeValToRGB'); ramp2.color_ramp.elements[0].position = 0.3; ramp2.color_ramp.elements[0].color = (0.5,0.5,0.52,1)
    nt.links.new(nz2.outputs['Fac'], ramp2.inputs['Fac']); nt.links.new(ramp.outputs['Color'], mix.inputs[6]); nt.links.new(ramp2.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    # nass: Pfützen in Senken glatt
    rr = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); rr.inputs[1].default_value = 0.7; rr.inputs[2].default_value = 0.25
    nt.links.new(nz2.outputs['Fac'], rr.inputs[0]); nt.links.new(rr.outputs[0], bsdf.inputs['Roughness'])
    bmp = node(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.02); nt.links.new(nz.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('asphalt', asphalt)

def pavement(nt, bsdf):
    tc = node(nt, 'ShaderNodeTexCoord'); br = node(nt, 'ShaderNodeTexBrick', Scale=4, Color1=(0.5,0.49,0.46,1), Color2=(0.44,0.43,0.41,1), Mortar=(0.2,0.2,0.19,1)); br.inputs['Mortar Size'].default_value = 0.01; br.squash = 1.0; br.offset = 0.0
    nt.links.new(tc.outputs['UV'], br.inputs['Vector'])
    nz = node(nt, 'ShaderNodeTexNoise', Scale=30, Detail=8); nz2 = node(nt, 'ShaderNodeTexNoise', Scale=5, Detail=3)
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix.inputs['Factor'].default_value = 0.45
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[1].position = 0.8
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(br.outputs['Color'], mix.inputs[6]); nt.links.new(ramp.outputs['Color'], mix.inputs[7])
    mix2 = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix2.inputs['Factor'].default_value = 0.35
    ramp2 = node(nt, 'ShaderNodeValToRGB'); ramp2.color_ramp.elements[0].position = 0.35; ramp2.color_ramp.elements[0].color = (0.45,0.42,0.4,1)
    nt.links.new(nz2.outputs['Fac'], ramp2.inputs['Fac']); nt.links.new(mix.outputs[2], mix2.inputs[6]); nt.links.new(ramp2.outputs['Color'], mix2.inputs[7]); nt.links.new(mix2.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.8
    bmp = node(nt, 'ShaderNodeBump', Strength=0.5, Distance=0.05); inv = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs['Fac'], inv.inputs[1]); add = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); add.inputs[1].default_value = 0.2
    nt.links.new(nz.outputs['Fac'], add.inputs[0]); nt.links.new(inv.outputs[0], add.inputs[2]); nt.links.new(add.outputs[0], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('pavement', pavement)

def cobble(nt, bsdf):
    tc = node(nt, 'ShaderNodeTexCoord'); vo = node(nt, 'ShaderNodeTexVoronoi', Scale=14); vo.feature = 'F1'
    vo2 = node(nt, 'ShaderNodeTexVoronoi', Scale=14); vo2.feature = 'DISTANCE_TO_EDGE'
    nt.links.new(tc.outputs['UV'], vo.inputs['Vector']); nt.links.new(tc.outputs['UV'], vo2.inputs['Vector'])
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.22,0.2,0.18,1); ramp.color_ramp.elements[1].color = (0.42,0.4,0.37,1)
    nt.links.new(vo.outputs['Color'], ramp.inputs['Fac'])
    edge = node(nt, 'ShaderNodeMath', operation='SMOOTH_MIN'); edge.inputs[1].default_value = 0.05; edge.inputs[2].default_value = 0.02
    nt.links.new(vo2.outputs['Distance'], edge.inputs[0])
    er = node(nt, 'ShaderNodeValToRGB'); er.color_ramp.elements[0].color = (0.08,0.07,0.06,1); er.color_ramp.elements[1].color = (1,1,1,1); er.color_ramp.elements[1].position = 0.05
    nt.links.new(vo2.outputs['Distance'], er.inputs['Fac'])
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix.inputs['Factor'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], mix.inputs[6]); nt.links.new(er.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.5
    bmp = node(nt, 'ShaderNodeBump', Strength=0.8, Distance=0.1); nt.links.new(vo2.outputs['Distance'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('cobble', cobble)

def render_paint(nt, bsdf):
    nz = node(nt, 'ShaderNodeTexNoise', Scale=40, Detail=8); nz2 = node(nt, 'ShaderNodeTexNoise', Scale=3, Detail=4)
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.78,0.77,0.74,1); ramp.color_ramp.elements[1].color = (0.9,0.9,0.88,1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mix.inputs['Factor'].default_value = 0.3
    r2 = node(nt, 'ShaderNodeValToRGB'); r2.color_ramp.elements[0].position = 0.3; r2.color_ramp.elements[0].color = (0.55,0.53,0.5,1)
    nt.links.new(nz2.outputs['Fac'], r2.inputs['Fac']); nt.links.new(ramp.outputs['Color'], mix.inputs[6]); nt.links.new(r2.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.7
    bmp = node(nt, 'ShaderNodeBump', Strength=0.25, Distance=0.02); nt.links.new(nz.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('render', render_paint)

def wood_paint(nt, bsdf):
    tc = node(nt, 'ShaderNodeTexCoord'); wv = node(nt, 'ShaderNodeTexWave', Scale=14, Distortion=2.0, Detail=3); wv.bands_direction = 'Y'
    nt.links.new(tc.outputs['UV'], wv.inputs['Vector'])
    ramp = node(nt, 'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.07,0.12,0.09,1); ramp.color_ramp.elements[1].color = (0.11,0.18,0.13,1)
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.4
    bmp = node(nt, 'ShaderNodeBump', Strength=0.2, Distance=0.02); nt.links.new(wv.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])
bake('woodgreen', wood_paint)
print('done')
