# Spielgebäude für Camden Command: Käfig, Proberaum, Bühne ... als glTF. Fußabdruck zentriert am Ursprung, Front nach -Y.
import bpy, math, random, sys, os, json, base64, struct
sys.argv_backup = sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'camden_set.py')).read().split('# ---------------- Reihenhaus-Module')[0])  # Helfer & Materialien
random.seed(11)
mat('hay', (0.8,0.65,0.3,1), 0.95); mat('concrete', (0.55,0.55,0.52,1), 0.85); mat('steel', (0.6,0.62,0.66,1), 0.35, 0.8); mat('corrugated', (0.35,0.38,0.42,1), 0.6, 0.5)
mat('black', (0.03,0.03,0.03,1), 0.6); mat('white', (0.9,0.9,0.88,1), 0.5); mat('neon', (1,0.2,0.25,1), 0.3, 0, (1,0.15,0.2,1)); mat('grille', (0.12,0.12,0.12,1), 0.8)

def amp(parts, x, y, z, w=1.2, h=0.9, d=0.6, tag='amp'):
    parts.append(box(tag, (w,d,h), (x,y,z+h/2), 'black')); parts.append(box(tag+'_gr', (w*0.85,0.04,h*0.7), (x,y-d/2-0.01,z+h*0.45), 'grille'))
    parts.append(box(tag+'_led', (0.06,0.03,0.06), (x+w*0.38,y-d/2-0.02,z+h*0.9), 'neon')); parts.append(box(tag+'_pl', (w*0.9,0.03,0.12), (x,y-d/2-0.01,z+h*0.9), 'metal'))

def b_kaefig():
    S=6.0; parts=[box('tray', (S*0.96,S*0.96,0.35), (0,0,0.175), 'paint'), box('hay', (S*0.9,S*0.9,0.3), (0,0,0.45), 'hay')]
    for i in range(14):
        parts.append(box('haylump', (0.5+random.random()*0.6,0.4+random.random()*0.6,0.2), (random.uniform(-2.3,2.3),random.uniform(-2.3,2.3),0.62), 'hay', rot=(0,0,random.random()*3)))
    W2=S*0.96; hh=2.8; n=12
    for i in range(n+1):
        o=-W2/2+i*(W2/n)
        for (x,y) in ((o,-W2/2),(o,W2/2),(-W2/2,o),(W2/2,o)): parts.append(cyl('bar', 0.03, hh, (x,y,0.35+hh/2), 'steel', v=6))
        parts.append(cyl('tbar', 0.025, W2, (o,0,0.35+hh), 'steel', v=6, rot=(math.pi/2,0,0))); parts.append(cyl('tbar2', 0.025, W2, (0,o,0.35+hh), 'steel', v=6, rot=(0,math.pi/2,0)))
    for z in (0.35, 1.3, 2.2, 3.15):
        for (loc,rot) in (((0,-W2/2,z),(0,math.pi/2,0)),((0,W2/2,z),(0,math.pi/2,0)),((-W2/2,0,z),(math.pi/2,0,0)),((W2/2,0,z),(math.pi/2,0,0))): parts.append(cyl('frame', 0.04, W2, loc, 'steel', v=6, rot=rot))
    parts.append(box('house', (1.8,1.4,1.1), (-1.6,-1.2,0.95), 'wood')); parts.append(prism('house_roof', 2.0, 1.6, 0.6, (-1.6,-1.2,1.5), 'wood')); parts.append(box('house_door', (0.6,0.05,0.7), (-1.6,-1.93,0.8), 'black'))
    parts.append(cyl('bottle', 0.14, 1.0, (2.3,2.2,1.3), 'glass', v=10)); parts.append(cyl('bottle_cap', 0.05, 0.3, (2.3,2.2,0.75), 'steel', v=6, rot=(0.5,0,0)))
    parts.append(cyl('bowl', 0.45, 0.18, (1.5,-1.5,0.7), 'white', v=14, r2=0.35))
    for i in range(7): parts.append(sph('kale', 0.35, (1.5+random.uniform(-0.3,0.3),-1.5+random.uniform(-0.3,0.3),0.9+random.random()*0.2), 'leaf', seg=8, ring=6, scale=(1,1,0.6)))
    return finish(parts, 'b_kaefig', 1.0)

def b_proberaum():
    S=6.0; parts=[box('wall', (S*0.95,S*0.95,3.6), (0,0,1.8), 'brick'), box('roofslab', (S*0.98,S*0.98,0.2), (0,0,3.7), 'corrugated')]
    for i in range(6): parts.append(box('ridge', (S*0.98,0.08,0.08), (0,-S*0.45+i*S*0.18,3.84), 'corrugated'))
    parts.append(box('door', (1.6,0.12,2.4), (0,-S*0.475-0.02,1.2), 'black')); parts.append(box('door_stripe', (0.2,0.02,2.4), (0,-S*0.475-0.1,1.2), 'red')); parts.append(box('door_frame', (1.9,0.2,0.2), (0,-S*0.475,2.5), 'stone'))
    parts.append(box('sign', (3.2,0.08,0.7), (0,-S*0.475-0.06,3.0), 'black')); parts.append(box('sign_neon', (2.8,0.04,0.35), (0,-S*0.475-0.12,3.0), 'neon'))
    amp(parts, -2.2, -S*0.3, 0, tag='amp1'); amp(parts, -2.2, -S*0.3, 0.9, 1.1, 0.7, tag='amp2'); amp(parts, 2.1, S*0.1, 0, tag='amp3')
    parts.append(cyl('pipe', 0.18, 1.6, (2.2,1.8,4.4), 'metal', v=8)); parts.append(box('vent', (0.8,0.8,0.5), (-1.8,1.6,4.0), 'metal'))
    parts.append(box('poster', (0.8,0.02,1.1), (1.9,-S*0.475-0.03,1.6), 'paint')); parts.append(box('poster2', (0.7,0.02,0.9), (-1.9,-S*0.475-0.03,1.5), 'white'))
    parts.append(cyl('drum', 0.5, 0.45, (1.2,1.0,4.05), 'red', v=14, rot=(math.pi/2,0,0))); parts.append(cyl('cymbal', 0.35, 0.03, (1.9,0.4,4.5), 'steel', v=12))
    return finish(parts, 'b_proberaum', 1.0)

def b_buehne():
    S=6.0; parts=[box('deck', (S*0.95,S*0.8,0.7), (0,0.3,0.35), 'wood'), box('deck_edge', (S*0.97,0.1,0.72), (0,-S*0.4+0.3,0.36), 'black')]
    for (x,y) in ((-S*0.42,-S*0.1),(S*0.42,-S*0.1),(-S*0.42,S*0.65-1.2),(S*0.42,S*0.65-1.2)): parts.append(cyl('truss_v', 0.08, 4.6, (x,y,2.3), 'steel', v=8))
    for y in (-S*0.1, S*0.65-1.2): parts.append(cyl('truss_h', 0.07, S*0.84, (0,y,4.6), 'steel', v=8, rot=(0,math.pi/2,0)))
    for x in (-S*0.42, S*0.42): parts.append(cyl('truss_d', 0.07, S*0.55, (x,S*0.2-0.4,4.6), 'steel', v=8, rot=(math.pi/2,0,0)))
    for i in range(5):
        x=-2.0+i*1.0; parts.append(cyl('can', 0.17, 0.45, (x,-S*0.1,4.3), 'black', v=10, rot=(0.9,0,0))); parts.append(cyl('can_light', 0.13, 0.05, (x,-S*0.1-0.22,4.1), random.choice(['neon','lamp']), v=10, rot=(0.9,0,0)))
    for x in (-S*0.36, S*0.36):
        amp(parts, x, S*0.3, 0.7, 1.4, 1.2, 0.8, tag='stack1'); amp(parts, x, S*0.3, 1.9, 1.4, 1.0, 0.8, tag='stack2'); amp(parts, x, S*0.3, 2.9, 1.3, 0.7, 0.7, tag='stack3')
    parts.append(box('backdrop', (S*0.8,0.08,3.6), (0,S*0.45,2.5), 'black')); parts.append(box('banner', (3.6,0.04,1.4), (0,S*0.45-0.06,2.8), 'red'))
    parts.append(cyl('micstand', 0.03, 1.6, (0,-S*0.25,1.5), 'steel', v=6)); parts.append(sph('mic', 0.12, (0,-S*0.25-0.1,2.35), 'metal', scale=(1,1,1.4)))
    parts.append(cyl('riser', 1.2, 0.3, (0.6,S*0.2,0.85), 'black', v=16)); parts.append(cyl('kick', 0.45, 0.5, (0.6,S*0.2,1.45), 'red', v=14, rot=(0,math.pi/2,0))); parts.append(cyl('snare', 0.25, 0.18, (0.0,S*0.2-0.5,1.5), 'steel', v=12)); parts.append(cyl('hihat', 0.26, 0.02, (-0.5,S*0.2-0.3,1.9), 'steel', v=12)); parts.append(cyl('crash', 0.34, 0.02, (1.6,S*0.2-0.2,2.2), 'steel', v=12))
    parts.append(box('cable', (3.0,0.08,0.03), (-0.5,-S*0.2,0.72), 'black', rot=(0,0,0.3)))
    return finish(parts, 'b_buehne', 1.0)

def b_heuturm():
    parts=[]
    for i,(z,rot,sc) in enumerate(((0.45,0.1,1.0),(1.35,-0.25,0.95),(2.25,0.35,0.9),(3.1,-0.1,0.8))):
        parts.append(box('bale', (1.7*sc,1.2*sc,0.9), (random.uniform(-0.1,0.1),random.uniform(-0.1,0.1),z), 'hay', rot=(0,0,rot)))
        parts.append(box('strap', (1.75*sc,0.06,0.06), (0,0.35*sc,z+0.2), 'black', rot=(0,0,rot))); parts.append(box('strap2', (1.75*sc,0.06,0.06), (0,-0.35*sc,z+0.2), 'black', rot=(0,0,rot)))
    parts.append(cyl('pole', 0.04, 1.4, (0.4,0.3,4.2), 'wood', v=6)); parts.append(box('flag', (0.6,0.02,0.4), (0.7,0.3,4.6), 'red'))
    parts.append(cyl('fork', 0.03, 1.6, (-0.6,-0.5,1.2), 'wood', v=6, rot=(0.3,0.4,0))); 
    return finish(parts, 'b_heuturm', 1.0)

def b_ampwall():
    parts=[box('base', (3.6,1.4,0.2), (0,0,0.1), 'black')]
    for col in range(3):
        for row in range(3):
            w = 1.1 if row<2 else 1.0; h = 0.9 if row<2 else 0.6
            amp(parts, -1.2+col*1.2, 0.0, 0.2+row*0.92, w, h, 0.7, tag=f'a{col}{row}')
    parts.append(box('head', (1.0,0.5,0.35), (0,0.0,3.0), 'black')); parts.append(box('head_pl', (0.9,0.03,0.1), (0,-0.26,3.1), 'steel'))
    parts.append(cyl('horn', 0.2, 0.5, (-1.3,-0.1,3.2), 'metal', v=10, r2=0.4, rot=(math.pi/2,0,0))); parts.append(cyl('horn2', 0.2, 0.5, (1.3,-0.1,3.2), 'metal', v=10, r2=0.4, rot=(math.pi/2,0,0)))
    return finish(parts, 'b_ampwall', 1.0)

def b_lager():
    parts=[box('floor', (3.6,3.6,0.15), (0,0,0.075), 'wood')]
    for i in range(9):
        x=-1.2+(i%3)*1.2; y=-1.0+(i//3)*1.0; z=0.15+(0.6 if i%2 else 0)
        parts.append(box('crate', (1.05,0.85,0.5), (x,y,z+0.25), 'wood')); parts.append(box('crate_slot', (0.9,0.87,0.06), (x,y,z+0.3), 'black'))
        for k in range(4): parts.append(sph('kaleb', 0.22, (x-0.3+k*0.2,y+random.uniform(-0.2,0.2),z+0.55), 'leaf', seg=7, ring=5, scale=(1,1,0.7)))
    for (x,y) in ((-1.7,-1.7),(1.7,-1.7),(-1.7,1.7),(1.7,1.7)): parts.append(cyl('post', 0.05, 2.6, (x,y,1.3), 'wood', v=6))
    parts.append(box('awning', (3.8,3.8,0.08), (0,0,2.6), 'canvas', rot=(0.05,0,0))); parts.append(box('awning_stripe', (3.8,0.4,0.1), (0,-1.7,2.62), 'red'))
    parts.append(box('board', (0.6,0.05,0.8), (1.9,-1.9,0.6), 'black', rot=(0,0.2,0))); parts.append(box('scale', (0.5,0.5,0.4), (-1.9,1.5,0.35), 'steel'))
    return finish(parts, 'b_lager', 1.0)

def b_buero():
    S=8.0; parts=[box('core', (S*0.92,S*0.92,14), (0,0,7), 'glass')]
    for f in range(5): parts.append(box('slab', (S*0.95,S*0.95,0.25), (0,0,2.8*f+2.7), 'concrete'))
    for i in range(7):
        parts.append(box('mullion', (0.12,0.12,14), (-S*0.46+i*S*0.92/6,-S*0.46,7), 'steel')); parts.append(box('mullion2', (0.12,0.12,14), (-S*0.46+i*S*0.92/6,S*0.46,7), 'steel'))
        parts.append(box('mullion3', (0.12,0.12,14), (-S*0.46,-S*0.46+i*S*0.92/6,7), 'steel')); parts.append(box('mullion4', (0.12,0.12,14), (S*0.46,-S*0.46+i*S*0.92/6,7), 'steel'))
    parts.append(box('roof', (S*0.9,S*0.9,0.6), (0,0,14.3), 'concrete')); parts.append(box('plant', (2.0,1.6,1.2), (1.5,1.2,15.2), 'metal'))
    parts.append(box('canopy', (4.0,2.0,0.2), (0,-S*0.5,3.2), 'steel')); parts.append(box('entrance', (3.0,0.1,2.8), (0,-S*0.46-0.02,1.4), 'glass'))
    parts.append(box('sign', (5.5,0.1,1.1), (0,-S*0.46-0.1,12.5), 'paint')); parts.append(box('sign_light', (5.2,0.04,0.5), (0,-S*0.46-0.18,12.5), 'lamp'))
    return finish(parts, 'b_buero', 1.0)

def b_condo():
    S=6.0; parts=[box('body', (S*0.9,S*0.9,9.5), (0,0,4.75), 'render')]
    for f in range(3):
        z=1.6+f*3.0; parts.append(box('win', (S*0.7,0.1,1.9), (0,-S*0.45-0.02,z), 'glass'))
        parts.append(box('balcony', (S*0.6,1.2,0.15), (0,-S*0.45-0.6,z-1.05), 'concrete'))
        for k in range(8): parts.append(box('bal_rail', (0.04,0.04,1.0), (-S*0.3+k*S*0.6/7,-S*0.45-1.18,z-0.5), 'metal'))
        parts.append(box('bal_top', (S*0.6,0.04,0.04), (0,-S*0.45-1.18,z), 'metal'))
        parts.append(box('win_b', (S*0.7,0.1,1.9), (0,S*0.45+0.02,z), 'glass')); parts.append(box('win_l', (0.1,S*0.5,1.5), (-S*0.45-0.02,0,z), 'glass')); parts.append(box('win_r', (0.1,S*0.5,1.5), (S*0.45+0.02,0,z), 'glass'))
    parts.append(box('roof', (S*0.92,S*0.92,0.3), (0,0,9.65), 'concrete')); parts.append(box('door', (1.2,0.1,2.3), (-S*0.3,-S*0.45-0.02,1.15), 'metal'))
    parts.append(box('board', (1.4,0.06,1.0), (S*0.3,-S*0.45-0.5,2.2), 'white')); parts.append(cyl('board_post', 0.05, 2.5, (S*0.3,-S*0.45-0.5,1.25), 'wood', v=6)); parts.append(box('board_txt', (1.2,0.02,0.4), (S*0.3,-S*0.45-0.54,2.2), 'red'))
    return finish(parts, 'b_condo', 1.0)

def b_kran():
    parts=[box('base', (3.6,3.6,0.5), (0,0,0.25), 'concrete')]
    for (x,y) in ((-0.5,-0.5),(0.5,-0.5),(-0.5,0.5),(0.5,0.5)): parts.append(cyl('mast', 0.08, 16, (x,y,8.5), 'paint', v=6))
    for z in range(1,16,2):
        parts.append(cyl('brace', 0.04, 1.0, (0,-0.5,z+0.5), 'paint', v=5, rot=(0,math.pi/2,0))); parts.append(cyl('brace2', 0.04, 1.0, (0,0.5,z+0.5), 'paint', v=5, rot=(0,math.pi/2,0)))
        parts.append(cyl('brace3', 0.04, 1.4, (-0.5,0,z+0.5), 'paint', v=5, rot=(math.pi/2,0,0.0))); parts.append(cyl('brace4', 0.04, 1.4, (0.5,0,z+0.5), 'paint', v=5, rot=(math.pi/2,0,0)))
    parts.append(box('cabin', (1.2,1.1,1.3), (0.9,0,16.8), 'paint')); parts.append(box('cabin_gl', (0.6,1.0,0.8), (1.5,0,16.9), 'glass'))
    parts.append(box('jib', (12,0.6,0.6), (5.0,0,17.6), 'paint')); parts.append(box('cjib', (4,0.7,0.7), (-3.0,0,17.6), 'paint')); parts.append(box('cweight', (1.4,1.0,1.4), (-4.6,0,16.8), 'concrete'))
    parts.append(cyl('tower_top', 0.06, 3.0, (0,0,19.0), 'paint', v=5)); parts.append(cyl('tie', 0.03, 10.5, (4.5,0,18.9), 'steel', v=4, rot=(0,1.45,0)))
    parts.append(cyl('cable', 0.03, 9.0, (8.5,0,12.8), 'steel', v=4)); parts.append(box('hook', (0.5,0.5,0.6), (8.5,0,8.0), 'metal')); parts.append(box('load', (2.0,1.2,1.0), (8.5,0,7.0), 'brick'))
    return finish(parts, 'b_kran', 1.0)

def b_amt():
    S=6.0; parts=[box('body', (S*0.92,S*0.92,8.0), (0,0,4.0), 'concrete'), box('roof', (S*0.96,S*0.96,0.3), (0,0,8.15), 'metal')]
    for f in range(3):
        for k in range(4): parts.append(box('win', (0.9,0.1,1.2), (-S*0.33+k*S*0.22,-S*0.46-0.02,1.7+f*2.5), 'glass')); parts.append(box('winb', (0.9,0.1,1.2), (-S*0.33+k*S*0.22,S*0.46+0.02,1.7+f*2.5), 'glass'))
        parts.append(box('band', (S*0.94,0.08,0.3), (0,-S*0.46-0.03,2.6+f*2.5), 'white'))
    parts.append(box('steps', (2.4,1.2,0.5), (0,-S*0.5,0.25), 'concrete')); parts.append(box('door', (1.6,0.1,2.2), (0,-S*0.46-0.02,1.3), 'glass')); parts.append(box('sign', (2.6,0.06,0.5), (0,-S*0.46-0.08,3.6), 'white'))
    parts.append(cyl('flagpole', 0.04, 5.0, (S*0.35,-S*0.6,2.5), 'steel', v=6)); parts.append(box('flag', (0.9,0.02,0.6), (S*0.35+0.45,-S*0.6,4.7), 'white'))
    return finish(parts, 'b_amt', 1.0)

def b_raum():
    S=6.0; parts=[box('wall', (S*0.95,S*0.95,4.2), (0,0,2.1), 'brick'), box('roof', (S*0.98,S*0.98,0.25), (0,0,4.3), 'corrugated')]
    parts.append(box('irondoor', (1.3,0.15,2.4), (0,-S*0.475-0.03,1.2), 'black')); parts.append(box('door_bar', (1.3,0.05,0.1), (0,-S*0.475-0.12,1.4), 'metal')); parts.append(box('door_bar2', (0.1,0.05,2.4), (0.3,-S*0.475-0.12,1.2), 'metal'))
    parts.append(cyl('bulb_arm', 0.03, 0.6, (0,-S*0.475-0.3,3.0), 'metal', v=5, rot=(math.pi/2,0,0))); parts.append(sph('bulb', 0.12, (0,-S*0.475-0.6,2.9), 'lamp', seg=8, ring=6))
    for i,(x,w,h) in enumerate(((-2.0,0.7,1.0),(-1.2,0.6,0.8),(1.4,0.8,1.1),(2.2,0.5,0.7))): parts.append(box('poster', (w,0.02,h), (x,-S*0.475-0.02,1.8+random.uniform(-0.3,0.3)), random.choice(['white','paint','red'])))
    parts.append(box('bins', (0.7,0.7,1.0), (2.3,-S*0.3,0.5), 'paint')); parts.append(box('bins2', (0.7,0.7,1.0), (2.3,-S*0.3+0.8,0.5), 'metal'))
    parts.append(cyl('vent', 0.3, 0.6, (-1.5,1.0,4.7), 'metal', v=10)); parts.append(box('crate', (0.9,0.6,0.5), (-2.2,-S*0.35,0.25), 'wood'))
    return finish(parts, 'b_raum', 1.0)

def b_z7():
    S=10.0; parts=[box('hall', (S*0.95,S*0.95,6.5), (0,0,3.25), 'corrugated'), prism('hall_roof', S*0.98, S*0.98, 1.8, (0,0,6.5), 'metal'), box('plinth', (S*0.96,S*0.96,1.0), (0,0,0.5), 'concrete')]
    parts.append(box('entrance', (3.0,0.3,3.2), (0,-S*0.475-0.1,1.6), 'black')); parts.append(box('entrance_light', (2.8,0.05,0.2), (0,-S*0.475-0.28,3.3), 'neon'))
    parts.append(box('sign_bg', (4.0,0.2,2.0), (0,-S*0.475-0.1,5.2), 'black')); parts.append(box('sign_z7', (3.0,0.06,1.4), (0,-S*0.475-0.22,5.2), 'neon'))
    for i in range(6): parts.append(box('led', (0.3,0.05,0.3), (-3.5+i*1.4,-S*0.475-0.05,1.0), 'neon'))
    parts.append(box('dock', (3.0,2.0,1.0), (3.0,S*0.5,0.5), 'concrete')); parts.append(box('dock_door', (2.4,0.2,2.6), (3.0,S*0.475,2.3), 'metal'))
    for i in range(4): parts.append(cyl('vent', 0.35, 0.8, (-3.0+i*2.0,1.5,8.3), 'metal', v=10))
    parts.append(box('poster_wall', (S*0.6,0.05,1.5), (-1.0,-S*0.475-0.03,2.2), 'paint'))
    return finish(parts, 'b_z7', 1.0)

def b_van():
    parts=[box('body', (4.6,2.0,1.9), (0,0,1.35), 'white'), box('cab', (1.3,1.95,1.5), (2.5,0,1.15), 'white'), box('windscreen', (0.1,1.8,0.9), (3.15,0,1.5), 'glass'), box('side_win', (1.1,0.05,0.6), (2.4,1.0,1.5), 'glass'), box('side_win2', (1.1,0.05,0.6), (2.4,-1.0,1.5), 'glass')]
    parts.append(box('rack', (3.5,1.6,0.08), (-0.3,0,2.4), 'metal')); parts.append(box('case', (1.4,0.8,0.5), (-0.5,0,2.7), 'black')); parts.append(box('bumper', (0.2,2.0,0.25), (3.2,0,0.5), 'rubber')); parts.append(box('bumper2', (0.2,2.0,0.25), (-2.4,0,0.5), 'rubber'))
    for x in (1.8,-1.6):
        for y in (0.95,-0.95): parts.append(cyl('wheel', 0.38, 0.25, (x,y,0.38), 'rubber', v=12, rot=(math.pi/2,0,0)))
    parts.append(box('stripe', (4.0,0.02,0.3), (-0.3,1.01,1.2), 'red')); parts.append(box('stripe2', (4.0,0.02,0.3), (-0.3,-1.01,1.2), 'red'))
    return finish(parts, 'b_van', 1.0)

def b_radio():
    parts=[box('table', (1.6,0.9,0.08), (0,0,0.75), 'wood'), box('leg', (0.08,0.08,0.75), (-0.7,-0.35,0.37), 'wood'), box('leg2', (0.08,0.08,0.75), (0.7,-0.35,0.37), 'wood'), box('leg3', (0.08,0.08,0.75), (-0.7,0.35,0.37), 'wood'), box('leg4', (0.08,0.08,0.75), (0.7,0.35,0.37), 'wood')]
    parts.append(box('radio', (1.1,0.5,0.6), (0,0,1.1), 'wood')); parts.append(box('dial', (0.5,0.03,0.2), (0.15,-0.26,1.2), 'lamp')); parts.append(cyl('knob', 0.06, 0.05, (-0.35,-0.27,1.1), 'black', v=8, rot=(math.pi/2,0,0))); parts.append(cyl('knob2', 0.06, 0.05, (-0.35,-0.27,1.28), 'black', v=8, rot=(math.pi/2,0,0)))
    parts.append(box('grille', (0.4,0.03,0.35), (0.15,-0.26,0.95), 'grille')); parts.append(cyl('antenna', 0.015, 1.4, (0.5,0.2,2.0), 'steel', v=5, rot=(0.3,0,0)))
    parts.append(box('cable', (0.03,0.8,0.03), (-0.2,0.4,0.78), 'black'))
    return finish(parts, 'b_radio', 1.0)

def b_wald():
    parts=[]
    for i in range(6):
        x=random.uniform(-2.0,2.0); y=random.uniform(-2.0,2.0); sc=0.8+random.random()*0.5
        parts.append(cyl('trunk', 0.18*sc, 2.0*sc, (x,y,1.0*sc), 'bark', v=7))
        for k,(zz,r) in enumerate(((1.8,1.3),(3.0,1.0),(4.0,0.65))): parts.append(cyl('fir', r*sc, 1.6*sc, (x,y,zz*sc), 'leaf', v=8, r2=0.05))
    parts.append(box('bench', (1.6,0.4,0.06), (0,-2.4,0.45), 'wood')); parts.append(box('bench_l', (0.08,0.4,0.45), (-0.6,-2.4,0.22), 'metal')); parts.append(box('bench_l2', (0.08,0.4,0.45), (0.6,-2.4,0.22), 'metal'))
    return finish(parts, 'b_wald', 1.0)

built=[b_kaefig(), b_proberaum(), b_buehne(), b_heuturm(), b_ampwall(), b_lager(), b_buero(), b_condo(), b_kran(), b_amt(), b_raum(), b_z7(), b_van(), b_radio(), b_wald()]
for o in built:
    o.location=(0,0,0)
    for p in o.data.polygons: p.use_smooth=False
tris=0
for o in built: o.data.calc_loop_triangles(); tris+=len(o.data.loop_triangles); print(o.name,'tris',len(o.data.loop_triangles))
print('total tris',tris)
glb=os.path.join(OUT,'buildings.glb'); bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_materials='EXPORT', export_image_format='NONE')
data=open(glb,'rb').read(); off=12; j=None; binchunk=None; length=len(data)
while off<length:
    clen,ctype=struct.unpack('<II',data[off:off+8]); body=data[off+8:off+8+clen]; off+=8+clen
    if ctype==0x4E4F534A: j=json.loads(body.decode('utf-8'))
    elif ctype==0x004E4942: binchunk=body
j['buffers'][0]['uri']='data:application/octet-stream;base64,'+base64.b64encode(binchunk).decode()
open(os.path.join(OUT,'buildings.json'),'w').write(json.dumps(j)); os.remove(glb); print('json bytes',os.path.getsize(os.path.join(OUT,'buildings.json')))
