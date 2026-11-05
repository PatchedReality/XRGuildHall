"""Original XR Guild Library. Run with Blender 5.2 --background --python.

Reference assets are inspected separately for proportion only; none are imported.
One Blender unit is one metre. Interior wall apothem = 4 m; apex = 6.2 m.
"""
import bpy
import math
import json
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
random.seed(23)
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.length_unit = 'METERS'
S.unit_settings.scale_length = 1
S.render.engine = 'CYCLES'
S.cycles.samples = 64
S.cycles.use_denoising = True
S.cycles.max_bounces = 8
S.cycles.diffuse_bounces = 4
S.cycles.glossy_bounces = 4
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'METAL'
    S.cycles.device = 'GPU'
except Exception:
    S.cycles.device = 'CPU'
S.render.resolution_x = 1800
S.render.resolution_y = 1400
S.render.resolution_percentage = 100
S.render.image_settings.file_format = 'PNG'
S.view_settings.view_transform = 'AgX'
S.view_settings.look = 'AgX - Medium High Contrast'
S.view_settings.exposure = 0.0
S.render.film_transparent = False
S.world = bpy.data.worlds.new('Blue hour exterior')
S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.30, .42, .53, 1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .18

collections = {}
for n in ['01 Architecture', '02 Labradorite columns', '03 Arched windows',
          '04 Empty walnut bookshelves', '05 Stone mandala', '06 Rotunda fresco',
          '07 Gilt inscriptions', '08 Library interface', '09 Meeting doors',
          '10 Lighting and cameras', '11 Optional meeting furniture', '12 Interaction anchors', '13 Exterior preview landscape']:
    c = bpy.data.collections.new(n)
    S.collection.children.link(c)
    collections[n[:2]] = c

def move(o, col):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collections[col].objects.link(o)
    return o

def mat(name, color, metal=0, rough=.4):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    return m

def noise_mat(name, colors, scale=5, rough=.4, metallic=0, stretch=(1,1,1), bump=.025):
    m = mat(name, colors[1], metallic, rough)
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n.get('Principled BSDF')
    tc = n.new('ShaderNodeTexCoord')
    mult = n.new('ShaderNodeVectorMath'); mult.operation='MULTIPLY'
    mult.inputs[1].default_value = stretch
    l.new(tc.outputs['Generated'], mult.inputs[0])
    noise = n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=5
    noise.inputs['Roughness'].default_value=.72
    noise.inputs['Distortion'].default_value=1.8
    l.new(mult.outputs['Vector'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,c in enumerate(colors):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(i/(len(colors)-1))
        e.position=i/(len(colors)-1); e.color=(*c,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0])
    l.new(ramp.outputs[0],b.inputs['Base Color'])
    if bump:
        bu=n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=.18
        bu.inputs['Distance'].default_value=bump
        l.new(noise.outputs['Fac'],bu.inputs['Height']); l.new(bu.outputs[0],b.inputs['Normal'])
    return m

gold = noise_mat('Gilt brass | gently aged',[(.16,.065,.014),(.48,.26,.065),(.76,.51,.18)],6,.29,.78,bump=.004)
gold_light = mat('Polished gold leaf edges',(.65,.40,.12),.8,.24)
bronze = mat('Patinated bronze recesses',(.08,.07,.036),.7,.4)
wall = noise_mat('Deep malachite green plaster',[(.012,.035,.028),(.024,.072,.053),(.065,.12,.083)],3,.83,bump=.015)
wall_dark = mat('Forest green damask backing',(.013,.034,.027),0,.74)
damask = mat('Silk fern damask',(.048,.083,.049),.12,.62)
wood = noise_mat('Handcrafted figured walnut',[(.012,.004,.002),(.055,.016,.005),(.15,.055,.016),(.29,.13,.044)],5,.34,stretch=(7,7,.12),bump=.008)
wood_dark = noise_mat('Walnut endgrain and recess',[(.019,.007,.004),(.065,.021,.009),(.14,.055,.019)],4,.43,stretch=(4,5,.2),bump=.008)
ivory = noise_mat('Warm ivory limestone',[(.23,.23,.18),(.55,.53,.43),(.76,.72,.58)],6,.3,bump=.012)
green_stone = noise_mat('Verde antique marble',[(.007,.022,.022),(.016,.075,.061),(.055,.17,.13),(.26,.31,.23)],4,.26,stretch=(1,1,2),bump=.008)
blue_stone = noise_mat('Blue petrol stone',[(.009,.025,.035),(.018,.07,.092),(.085,.19,.23)],6,.27,bump=.008)
black_stone = mat('Obsidian green stone grout',(.009,.018,.018),.08,.33)
lab = noise_mat('Labradorite | green stone with blue schiller',[(.012,.03,.026),(.027,.076,.065),(.09,.16,.11),(.24,.32,.22)],4,.21,.22,stretch=(1,1,2.5),bump=.018)
n,l=lab.node_tree.nodes,lab.node_tree.links
b=n.get('Principled BSDF'); b.inputs['Coat Weight'].default_value=.38; b.inputs['Coat Roughness'].default_value=.19
vor=n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value=9
tc=n.new('ShaderNodeTexCoord'); l.new(tc.outputs['Generated'],vor.inputs['Vector'])
r=n.new('ShaderNodeValToRGB')
r.color_ramp.elements[0].position=.57;r.color_ramp.elements[0].color=(0,0,0,1)
r.color_ramp.elements[1].position=.81;r.color_ramp.elements[1].color=(.4,.4,.4,1)
l.new(vor.outputs['Distance'],r.inputs[0])
mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MIX'
prev=b.inputs['Base Color'].links[0].from_socket
l.new(prev,mix.inputs[1]);mix.inputs[2].default_value=(.025,.23,.30,1)
l.new(r.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],b.inputs['Base Color'])
# Fine feldspar veins and irregular blue flashes, rather than a solid cyan shaft.
veinnoise=n.new('ShaderNodeTexNoise');veinnoise.inputs['Scale'].default_value=7;veinnoise.inputs['Detail'].default_value=7;veinnoise.inputs['Distortion'].default_value=4
l.new(tc.outputs['Generated'],veinnoise.inputs['Vector'])
veins=n.new('ShaderNodeValToRGB')
veins.color_ramp.elements[0].position=.46;veins.color_ramp.elements[0].color=(0,0,0,1)
veins.color_ramp.elements[1].position=.50;veins.color_ramp.elements[1].color=(0,0,0,1)
veins.color_ramp.elements.new(.48).color=(.7,.7,.7,1)
l.new(veinnoise.outputs['Fac'],veins.inputs[0])
vm=n.new('ShaderNodeMixRGB');l.new(mix.outputs[0],vm.inputs[1]);vm.inputs[2].default_value=(.29,.34,.24,1)
l.new(veins.outputs[0],vm.inputs[0]);l.new(vm.outputs[0],b.inputs['Base Color'])
glass = mat('Clear architectural glass | transparent, not frosted',(.96,.99,1.0),0,.018)
glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=1.0
glass.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45
glow = mat('Opal lamp glow',(.82,.62,.31),0,.26)
glow.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(1,.71,.35,1)
glow.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=3.5
screen = mat('Interface | deep teal glass',(.008,.034,.036),.25,.22)
screen.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.014,.075,.079,1)
screen.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.6
ink = mat('Interface | ivory luminous type',(.78,.83,.68),.05,.42)
ink.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.56,.71,.56,1)
ink.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.4
velvet = noise_mat('Bottle green velvet',[(.011,.035,.028),(.026,.09,.065),(.07,.16,.11)],75,.91,bump=.002)

def mesh(name, verts, faces, material, col, smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);collections[col].objects.link(o)
    if material:me.materials.append(material)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    return o

def cube(name, loc, dims, material, col, bevel=.01, rz=0):
    # Construct at final dimensions, retaining natural local texture coordinates.
    x,y,z=[v/2 for v in dims]
    verts=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o=mesh(name,verts,faces,material,col);o.location=loc;o.rotation_euler.z=rz
    if bevel:
        mod=o.modifiers.new('Soft handcrafted edges','BEVEL');mod.width=bevel;mod.segments=2
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def cyl(name, loc, radius, depth, material, col, vertices=64, r2=None):
    verts=[]
    for z,r in [(-depth/2,radius),(depth/2,r2 if r2 is not None else radius)]:
        verts += [(r*math.cos(2*math.pi*i/vertices),r*math.sin(2*math.pi*i/vertices),z) for i in range(vertices)]
    faces=[tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]
    faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    o=mesh(name,verts,faces,material,col);o.location=loc
    for p in o.data.polygons:
        p.use_smooth=len(p.vertices)==4
    return o

def curve(name, paths, radius, material, col, cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12
    cu.bevel_depth=radius;cu.bevel_resolution=3
    for pts in paths:
        sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
        for p,co in zip(sp.points,pts):p.co=(*co,1)
        sp.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,cu);collections[col].objects.link(o);cu.materials.append(material)
    return o

def ring(name,r,z,radius,material,col,steps=192):
    return curve(name,[[(r*math.cos(t*2*math.pi/steps),r*math.sin(t*2*math.pi/steps),z) for t in range(steps)]],radius,material,col,True)

def sphere(name,loc,scale,material,col):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;move(o,col);o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def bez(points,steps=28):
    return [tuple((1-t)**3*points[0][i]+3*(1-t)**2*t*points[1][i]+3*(1-t)*t*t*points[2][i]+t**3*points[3][i] for i in range(len(points[0]))) for t in [j/steps for j in range(steps+1)]]

# Local facade frame: x across the bay, y radially outward, z up.
def P(a,x,y,z):
    return (-math.sin(a)*x+math.cos(a)*y,math.cos(a)*x+math.sin(a)*y,z)
def C(name,a,x,y,z,w,d,h,m,col,bevel=.01):
    return cube(name,P(a,x,y,z),(w,d,h),m,col,bevel,a+math.pi/2)
def CV(name,a,paths,r,m,col,cyclic=False):
    return curve(name,[[P(a,*p) for p in pts] for pts in paths],r,m,col,cyclic)

def arch(w,bottom,spring,top,steps=32):
    # Two smooth, slightly pointed Art Nouveau shoulders, as in the supplied tracery views.
    right=bez([(w/2,spring),(w/2,top-.46*w),(.27*w,top-.12*w),(0,top)],steps)
    left=[(-x,z) for x,z in reversed(right)]
    return [(-w/2,bottom),(w/2,bottom)]+right+left

def panel(name,a,outline,y,depth,material,col):
    verts=[P(a,x,yy,z) for yy in [y-depth/2,y+depth/2] for x,z in outline]
    n=len(outline)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,material,col)

try:font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Baskerville.ttc')
except Exception:font=bpy.data.fonts.get('Bfont')

def txt(name,body,a,x,y,z,size,material=gold_light,col='07',max_width=None):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER'
    cu.size=size;cu.space_character=1.15;cu.space_line=1.18;cu.extrude=.0008;cu.bevel_depth=.0003;cu.resolution_u=8
    if font:cu.font=font
    o=bpy.data.objects.new(name,cu);collections[col].objects.link(o);cu.materials.append(material)
    o.location=P(a,x,y,z);o.rotation_euler=(math.pi/2,0,a-math.pi/2)
    bpy.context.view_layer.update()
    if max_width and o.dimensions.length>0:
        # Text local width is its bounding-box x span before rotation.
        w=max(v[0] for v in o.bound_box)-min(v[0] for v in o.bound_box)
        if w>max_width:o.scale=(max_width/w,)*3
    return o

def annulus(name,r1,r2,z,material,col='05',count=192):
    verts=[(r*math.cos(i*2*math.pi/count),r*math.sin(i*2*math.pi/count),z) for r in (r1,r2) for i in range(count)]
    faces=[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name,verts,faces,material,col)

def leaf3d(name,start,end,width,material,col):
    start,end=Vector(start),Vector(end);d=end-start
    side=d.cross(Vector((0,0,1)))
    if side.length<.001:side=Vector((1,0,0))
    side.normalize(); mid=start+d*.52
    normal=side.cross(d).normalized()
    pts=[]
    for j in range(13):
        t=j/12;w=width*.5*math.sin(math.pi*t)**.8
        center=start+d*t+normal*width*.20*math.sin(math.pi*t)
        pts.extend([tuple(center-side*w),tuple(center+normal*w*.24),tuple(center+side*w)])
    faces=[]
    for j in range(12):
        a=j*3;b=a+3
        faces.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2)])
    return mesh(name,pts,faces,material,col,True)

# Structural dodecagon and flush floor. The floor surface is at z=0.
apothem=4.0;half=apothem*math.tan(math.pi/12);outer=apothem/math.cos(math.pi/12)
floor=cyl('Twelve-sided foundation | 8 m across flats',(0,0,-.10),outer,.2,ivory,'01',12)
floor.rotation_euler.z=math.pi/12
floor['inside_width_m']=8.0

def wall_opening(i,opening):
    a=i*math.pi/6
    if opening[0][1]>0:
        C(f'Bay {i:02d} | lower wall',a,0,4.12,opening[0][1]/2,2*half,.24,opening[0][1],wall,'01',0)
    w=max(x for x,z in opening)*2;side=half-w/2
    for sign in [-1,1]:
        C(f'Bay {i:02d} | jamb masonry',a,sign*(w/2+side/2),4.12,2.38,side,.24,4.76,wall,'01',0)
    upper=opening[2:]
    for j in range(len(upper)-1):
        p,q=upper[j:j+2]
        if abs(p[0]-q[0])<1e-8:continue
        panel(f'Bay {i:02d} | arch spandrel {j:02d}',a,[p,q,(q[0],4.76),(p[0],4.76)],4.12,.24,wall,'01')

for i in range(12):
    a=i*math.pi/6
    if i%2==0:
        wall_opening(i,arch(.98,.55,3.52,4.25))
    elif i==9:
        wall_opening(i,arch(1.65,0,2.64,3.60))
    else:
        C(f'Bay {i:02d} | green wall',a,0,4.12,2.38,2*half,.24,4.76,wall,'01',0)
    # Layered walnut wainscot and continuous architectural cornice.
    if i!=9:
        C(f'Bay {i:02d} | walnut skirting',a,0,3.975,.10,2*half,.09,.20,wood,'01',.018)
        C(f'Bay {i:02d} | gilt skirting line',a,0,3.918,.195,2*half,.018,.018,gold,'01',.004)
    for z,depth,h,m in [(4.50,.12,.07,gold),(4.64,.16,.20,green_stone),(4.77,.21,.07,gold),(4.85,.25,.09,ivory)]:
        C(f'Bay {i:02d} | cornice {z}',a,0,4.02-depth/2,z,2*half+.02,depth,h,m,'01',.012)
    # Fine wall moldings and a leaf spray in each upper corner.
    for sign in (-1,1):
        CV(f'Bay {i:02d} | gilt wall tendril',a,[bez([(sign*.94,3.987,3.59),(sign*.84,3.987,4.13),(sign*.77,3.987,4.26),(sign*.59,3.987,4.40)])],.008,gold,'07')
        for k in range(3):
            leaf3d(f'Bay {i:02d} | foliage',P(a,sign*(.83-k*.06),3.985,4.04+k*.11),P(a,sign*(.97-k*.075),3.984,4.24+k*.06),.062,gold,'07')

# Twelve tall columns: taper, socle, collars, and sculpted leaf capitals.
for i in range(12):
    a=(i+.5)*math.pi/6
    x,y=3.95*math.cos(a),3.95*math.sin(a)
    for z,r,h,m,r2 in [(.11,.25,.22,green_stone,None),(.245,.23,.05,gold,None),(.31,.19,.10,lab,None),(.38,.19,.035,gold,None),
                       (2.20,.177,3.61,lab,.146),(4.03,.16,.06,gold,None),(4.11,.17,.10,gold,.215),(4.37,.255,.08,gold,None),
                       (4.43,.275,.05,green_stone,None),(4.475,.285,.04,gold,None)]:
        cyl(f'Column {i+1:02d} | {z:.2f}',(x,y,z),r,h,m,'02',48,r2)
    for k in range(12):
        t=k*math.pi/6
        p=(x+.16*math.cos(t),y+.16*math.sin(t),4.08)
        q=(x+.265*math.cos(t),y+.265*math.sin(t),4.37)
        leaf3d(f'Column {i+1:02d} | repoussé capital leaf {k+1:02d}',p,q,.13,gold,'02')
        curve(f'Column {i+1:02d} | leaf vein {k+1:02d}',[bez([p,(x+.175*math.cos(t),y+.175*math.sin(t),4.2),(x+.21*math.cos(t),y+.21*math.sin(t),4.33),q])],.009,gold_light,'02')
    # Attached globe sconces on every other pier.
    if i%2==0:
        nx,ny=math.cos(a),math.sin(a)
        curve(f'Sconce {i:02d} | curved brass arm',[bez([(x-nx*.15,y-ny*.15,1.2),(x-nx*.42,y-ny*.42,1.25),(x-nx*.38,y-ny*.38,1.57),(x-nx*.38,y-ny*.38,1.65)])],.022,gold,'02')
        loc=(x-nx*.38,y-ny*.38,1.70)
        sphere(f'Sconce {i:02d} | opal globe',loc,(.105,.105,.13),glow,'02')
        for z in (1.64,1.76):
            o=ring(f'Sconce {i:02d} | gilt globe band',.10,z,.012,gold,'02',48);o.location.x=loc[0];o.location.y=loc[1]
        data=bpy.data.lights.new(f'Sconce {i:02d} | warm pool','POINT');data.energy=22;data.color=(1,.70,.37);data.shadow_soft_size=.18
        o=bpy.data.objects.new(data.name,data);collections['10'].objects.link(o);o.location=loc

# The supplied multiview gilt pattern: slim central stem, paired shoulders,
# a large circular oculus, smaller top loop, and organic side leaves.
for i in range(0,12,2):
    a=i*math.pi/6;outline=arch(.98,.55,3.52,4.25)
    glass_o=panel(f'Window {i//2+1:02d} | clear glass glazing',a,outline,4.14,.008,glass,'03')
    glass_o['opening_width_m']=.98;glass_o['opening_height_m']=3.70
    for off,r,m,y in [(0,.071,green_stone,3.99),(-.075,.025,gold,3.924),(.13,.025,gold,4.0)]:
        line=arch(.98+off,.55,3.52,4.25+off*.65)
        CV(f'Window {i//2+1:02d} | arched surround {off}',a,[[(x,y,z) for x,z in line]],r,m,'03',True)
    C(f'Window {i//2+1:02d} | stone sill',a,0,3.93,.535,1.18,.36,.09,ivory,'03',.026)
    paths=[]
    # Uniform scale preserves the clean left reference's roundels and tall-light proportions.
    def T(x,z):return (x*.45,3.908,.55+z*.45)
    def stroke(p):paths.append(bez([T(x,z) for x,z in p]))
    stroke([(0,0),(0,1.7),(0,4.5),(0,5.5)])
    for sign in (-1,1):
        shoulder=[(0,5.5),(sign*.10,6.40),(sign*.91,6.68),(sign*.965,5.70)]
        stroke(shoulder)
        # Compute the shared junction directly on the lower arch: no loose ends.
        q=.32
        jx,jz=[sum(c*shoulder[k][axis] for k,c in enumerate([(1-q)**3,3*(1-q)**2*q,3*(1-q)*q*q,q**3])) for axis in (0,1)]
        stroke([(0,6.50),(sign*.17,6.45),(sign*.25,6.27),(jx,jz)])
        stroke([(jx,jz),(sign*.72,6.35),(sign*.96,6.78),(sign*.90,7.15)])
        stroke([(sign*.90,7.15),(sign*.88,7.273),(sign*.27,7.45),(0,7.42)])
        # End precisely on the inset perimeter curve, with no protruding or loose stem.
        rim=bez([(.905/2,3.52),(.905/2,4.20125-.46*.905),(.27*.905,4.20125-.12*.905),(0,4.20125)],32)[22]
        stroke([(jx,jz),(sign*.34,6.67),(sign*.60,7.25),(sign*rim[0]/.45,(rim[1]-.55)/.45)])
    # The fine crossing curves are clear in the LEFT source window but washed out in the center one.
    fine=[]
    for sign in (-1,1):
        fine.append(bez([T(sign*.97,6.07),T(sign*.78,6.59),T(sign*.56,6.63),T(sign*.34,6.65)]))
    CV(f'Window {i//2+1:02d} | fine reference cross-curves',a,fine,.0075,gold,'03')
    # Oculus and smaller crown loop are true circular/oval gilt geometry.
    for rr,zc in [(.46,6.96),(.27,7.69)]:
        paths.append([T(rr*math.cos(t*2*math.pi/96),zc+rr*math.sin(t*2*math.pi/96)) for t in range(97)])
    CV(f'Window {i//2+1:02d} | botanical gilt tracery',a,paths,.014,gold,'03')
    # Filled tapering foot and corner spandrels match the reference's rooted mullion.
    foot=bez([(-.095,.568),(-.045,.576),(-.016,.63),(0,.69)],20)+bez([(0,.69),(.016,.63),(.045,.576),(.095,.568)],20)
    panel(f'Window {i//2+1:02d} | central gilt foot',a,foot,3.904,.018,gold,'03')
    for sign in (-1,1):
        corner=bez([(sign*.36,.568),(sign*.41,.590),(sign*.45,.630),(sign*.46,.718)],20)+[(sign*.46,.568)]
        panel(f'Window {i//2+1:02d} | gilt sill corner',a,corner,3.904,.018,gold,'03')
    zjoin=.55+7.42*.45
    panel(f'Window {i//2+1:02d} | roundel joining jewel',a,[(-.024,zjoin),(0,zjoin+.031),(.024,zjoin),(0,zjoin-.031)],3.899,.018,gold,'03')
    sphere(f'Window {i//2+1:02d} | gilt apex jewel',P(a,0,3.965,4.37),(.055,.039,.096),gold_light,'03')
    # Daylight supplements the exterior world without appearing as white panels in glass.
    data=bpy.data.lights.new(f'Window {i//2+1:02d} | daylight','AREA');data.energy=310;data.shape='RECTANGLE';data.size=1.24;data.size_y=2.7;data.color=(.68,.85,1)
    o=bpy.data.objects.new(data.name,data);collections['10'].objects.link(o);o.location=P(a,0,3.96,2.35)
    o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
    data.specular_factor=0

def ornament(a,xc,zc,scale,y,col='04'):
    paths=[]
    for sign in (-1,1):
        paths.append(bez([(xc,y,zc),(xc+sign*.03*scale,y,zc+.19*scale),(xc+sign*.29*scale,y,zc+.12*scale),(xc+sign*.28*scale,y,zc+.35*scale)]))
        paths.append(bez([(xc,y,zc+.03*scale),(xc+sign*.33*scale,y,zc+.02*scale),(xc+sign*.48*scale,y,zc+.22*scale),(xc+sign*.43*scale,y,zc+.29*scale)]))
    CV('Hand carved gilt honeysuckle',a,paths,.011*scale,gold,col)
    for sign in (-1,1):
        leaf3d('Gilt honeysuckle petal',P(a,xc,y,zc+.08*scale),P(a,xc+sign*.16*scale,y,zc+.37*scale),.08*scale,gold,col)
    leaf3d('Gilt honeysuckle central petal',P(a,xc,y,zc+.07*scale),P(a,xc,y,zc+.43*scale),.09*scale,gold,col)

# Five bookcases. The north bookcase reserves a central, reachable interface.
for i in [1,3,5,7,11]:
    a=i*math.pi/6
    C(f'Bookcase {i:02d} | wallpaper backing',a,0,3.944,1.95,1.70,.035,3.34,wall_dark,'04')
    paths=[]
    for xx in [-.6,-.3,0,.3,.6]:
        for zz in [.8,1.3,1.8,2.3,2.8,3.3]:
            for sign in (-1,1):
                paths.append(bez([(xx,3.921,zz-.13),(xx+sign*.13,3.921,zz),(xx+sign*.1,3.921,zz+.05),(xx,3.921,zz+.16)]))
    CV(f'Bookcase {i:02d} | woven fern wallpaper',a,paths,.004,damask,'04')
    for x in [-.84,.84]:
        C(f'Bookcase {i:02d} | walnut side',a,x,3.75,1.99,.10,.40,3.48,wood,'04',.018)
        C(f'Bookcase {i:02d} | carved stile',a,x,3.514,1.99,.072,.055,3.50,wood,'04',.012)
        C(f'Bookcase {i:02d} | gilt stile inlay',a,x,3.48,2.0,.011,.01,3.44,gold,'04',.003)
    for z,w,d,h,m in [(.25,1.87,.51,.18,wood_dark),(.37,1.82,.48,.075,wood),(.435,1.75,.40,.055,gold),
                       (3.69,1.86,.50,.09,wood),(3.76,1.92,.54,.055,gold),(3.805,1.82,.43,.05,wood)]:
        C(f'Bookcase {i:02d} | molding {z}',a,0,3.72,z,w,d,h,m,'04',.014)
    for j,z in enumerate([.47,.87,1.27,1.67,2.07,2.47,2.87,3.27,3.63]):
        if i==3 and .87<=z<=1.67:
            for sign in (-1,1):
                C(f'Bookcase {i:02d} | empty side shelf {j}',a,sign*.688,3.73,z,.20,.40,.046,wood,'04',.008)
        else:
            sh=C(f'Bookcase {i:02d} | empty shelf {j}',a,0,3.73,z,1.61,.40,.046,wood,'04',.008)
            sh['purpose']='Empty shelf reserved for authors and resources'
            C(f'Bookcase {i:02d} | shelf brass pencil edge {j}',a,0,3.521,z,1.61,.014,.012,gold,'04',.003)
    for x in [-.39,.39]:
        C(f'Bookcase {i:02d} | lower cabinet panel',a,x,3.49,.315,.67,.045,.16,wood,'04',.007)
    if i==3:
        for x in [-.565,.565]:
            C('Interface bay | walnut partition',a,x,3.71,1.34,.055,.44,1.7,wood,'04',.01)
    # Delicate arched pediment remains below the continuous frieze.
    ped=arch(1.56,3.82,3.85,4.23,20)
    panel(f'Bookcase {i:02d} | arched crown',a,ped,3.83,.11,wood_dark,'04')
    CV(f'Bookcase {i:02d} | pediment gilt edge',a,[[(x,3.765,z) for x,z in ped]],.017,gold,'04',True)
    ornament(a,0,3.83,.78,3.742)

# Exact current content-category names; line breaks are purely typographic.
topics=[
    ('AI Ethics','AI ETHICS','https://library.xrguild.org/ai-ethics'),
    ('Current Peer-Reviewed Immersive Technologies','CURRENT PEER-REVIEWED\nIMMERSIVE TECHNOLOGIES','https://library.xrguild.org/current-peer-reviewed-immersive-technologies'),
    ('Ethical Responsibility','ETHICAL RESPONSIBILITY','https://library.xrguild.org/ethical-responsibility'),
    ('XR Industry news/events/Sources','XR INDUSTRY\nNEWS / EVENTS / SOURCES','https://library.xrguild.org/xr-industry-news-events-sources'),
    ('Neurotechnology, Brain Tech, and Ethical Challenges','NEUROTECHNOLOGY, BRAIN TECH,\nAND ETHICAL CHALLENGES','https://library.xrguild.org/neurotechnology-brain-tech-and-ethical-challenges'),
    ('Mind Control and Privacy at Work','MIND CONTROL\nAND PRIVACY AT WORK','https://library.xrguild.org/mind-control-and-privacy-at-work'),
    ('Physiological and Psychological effects of XR','PHYSIOLOGICAL AND\nPSYCHOLOGICAL EFFECTS OF XR','https://library.xrguild.org/physiological-and-psychological-effects-of-xr'),
    ('Privacy & Policy','PRIVACY & POLICY','https://library.xrguild.org/privacy-and-policy'),
    ('Security & Safety','SECURITY & SAFETY','https://library.xrguild.org/security-and-safety')]
for i,(name,label,url) in enumerate(topics):
    bay=[0,1,2,4,5,6,7,8,10][i]
    o=txt('Topic | '+name,label,bay*math.pi/6,0,3.852,4.65,.065,max_width=1.79)
    o['topic']=name;o['url']=url
txt('Frieze | library title','XR GUILD LIBRARY',3*math.pi/6,0,3.852,4.65,.094,max_width=1.7)
txt('Frieze | gathering','A PLACE TO THINK TOGETHER',9*math.pi/6,0,3.852,4.65,.070,max_width=1.79)
txt('Frieze | collection','KNOWLEDGE · IMAGINATION · CARE',11*math.pi/6,0,3.852,4.65,.068,max_width=1.79)

# Inlaid circular stone mandala: layered, bilateral and rotational symmetry.
cyl('Mandala | dark stone substrate',(0,0,.001),3.20,.010,black_stone,'05',192)
annulus('Mandala | ivory perimeter',2.82,3.18,.008,ivory)
annulus('Mandala | petrol outer inlay',2.64,2.79,.009,blue_stone)
annulus('Mandala | main verde field',.36,2.61,.009,green_stone)
for rr in [.39,.44,.78,1.00,2.60,2.64,2.79,2.83,3.14,3.18]:
    ring('Mandala | flush brass circular joint',rr,.012,.007,gold,'05')

def polar_leaf(name,t,r0,r1,width,m):
    # Pointed, subtly curved stone petal made of a fan of quads.
    verts=[]
    for j in range(33):
        q=j/32;r=r0+(r1-r0)*q;w=width*math.sin(math.pi*q)**.82
        for s in (-1,1):
            ang=t+s*w
            z=.018 if m==blue_stone else .016
            verts.append((r*math.cos(ang),r*math.sin(ang),z))
    faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(32)]
    o=mesh(name,verts,faces,m,'05')
    edge=verts[::2]+list(reversed(verts[1::2]))
    curve(name+' | gilt seam',[edge],.006,gold,'05',True)
    return o

for k in range(12):
    t=k*math.pi/6
    polar_leaf(f'Mandala | ivory lotus petal {k+1:02d}',t,.43,2.56,.117,ivory)
    polar_leaf(f'Mandala | blue inner petal {k+1:02d}',t,.50,1.58,.072,blue_stone)
    polar_leaf(f'Mandala | ivory outer ray {k+1:02d}',t+math.pi/12,1.53,2.53,.050,ivory)
    # Scrollwork winds around each radial blossom, kept entirely flush.
    for sign in (-1,1):
        pts=[]
        for j in range(100):
            q=j/99;ang=t+sign*(.025+.155*math.sin(q*math.pi));r=.88+q*1.61
            pts.append((r*math.cos(ang),r*math.sin(ang),.020))
        curve('Mandala | organic gilt stems',[pts],.006,gold,'05')
    # Twelve directional tesserae in the outer ring.
    for j in range(7):
        ang=t+(j-3)*.040
        r=3.00
        x,y=r*math.cos(ang),r*math.sin(ang)
        o=cube('Mandala | border tessera',(x,y,.014),(.08,.12,.006),green_stone,'05',0,ang+math.pi/4)
cyl('Mandala | ivory center',(0,0,.016),.36,.010,ivory,'05',96)
for k in range(12):
    polar_leaf('Mandala | central sun',k*math.pi/6,.06,.31,.16,gold)
# Radial limestone floor joints outside the mandala.
for i in range(48):
    t=i*math.pi/24
    # Hit the containing dodecagon precisely.
    rel=(t+math.pi/12)%(math.pi/6)-math.pi/12
    rr=4/math.cos(rel)
    curve('Floor | fine limestone radial joint',[[(3.20*math.cos(t),3.20*math.sin(t),.001),(rr*math.cos(t),rr*math.sin(t),.001)]],.002,bronze,'05')

# Replace the simple blockout inlays with the reference-matched intarsia texture.
# The mesh UVs mirror a single 15-degree wedge around all twelve sectors, so the
# final installed mandala is exactly symmetric even if the painted asset is not.
for old in list(collections['05'].objects):
    if not old.name.startswith('Floor |'):
        bpy.data.objects.remove(old,do_unlink=True)
intarsia=mat('Mandala | veined marble intarsia',(.3,.27,.2),.10,.25)
n,l=intarsia.node_tree.nodes,intarsia.node_tree.links
im=n.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(ROOT/'textures/stone_mandala.png'));im.image.pack()
l.new(im.outputs['Color'],n['Principled BSDF'].inputs['Base Color'])
bumpnode=n.new('ShaderNodeBump');bumpnode.inputs['Strength'].default_value=.12;bumpnode.inputs['Distance'].default_value=.001
l.new(im.outputs['Color'],bumpnode.inputs['Height']);l.new(bumpnode.outputs[0],n['Principled BSDF'].inputs['Normal'])
nn=720
vv=[(0,0,.013)]+[(3.20*math.cos(t*2*math.pi/nn),3.20*math.sin(t*2*math.pi/nn),.013) for t in range(nn)]
ff=[(0,1+t,1+(t+1)%nn) for t in range(nn)]
disk=mesh('Mandala | twelvefold mirrored marble tessellation',vv,ff,intarsia,'05')
uv=disk.data.uv_layers.new(name='Twelvefold mirrored intarsia')
for p in disk.data.polygons:
    for li in p.loop_indices:
        v=disk.data.vertices[disk.data.loops[li].vertex_index].co
        rr=math.hypot(v.x,v.y)
        theta=math.atan2(v.y,v.x)
        folded=abs((theta+math.pi/12)%(math.pi/6)-math.pi/12)
        uv.data[li].uv=(.5+rr*math.sin(folded)/6.55,.5+rr*math.cos(folded)/6.55)
disk['symmetry']='12-fold radial symmetry and mirror symmetry, imposed by mesh UV mapping'
ring('Mandala | outer brass joint',3.2,.018,.006,gold,'05')

# Rotunda. Painterly panoramic narrative mapped around the lower vault.
R=4.025;Z0=4.88;H=1.32;segs=192;rings=40
verts=[(0,0,Z0+H)];uvs=[(.5,.5)]
for j in range(1,rings+1):
    rr=R*j/rings;z=Z0+H*math.sqrt(max(0,1-(rr/R)**2))
    for k in range(segs):
        t=2*math.pi*k/segs;x=rr*math.cos(t);y=rr*math.sin(t)
        verts.append((x,y,z));uvs.append((.5+x/(2*R),.5+y/(2*R)))
faces=[]
for k in range(segs):faces.append((0,1+(k+1)%segs,1+k))
for j in range(rings-1):
    a=1+j*segs;b=a+segs
    for k in range(segs):faces.append((a+k,a+(k+1)%segs,b+(k+1)%segs,b+k))
fresco=mat('Fresco | Past / Present / Future | packed original artwork',(.3,.23,.14),0,.87)
n,l=fresco.node_tree.nodes,fresco.node_tree.links
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures/immersive_eras_fresco_v2.png'));tex.image.pack()
l.new(tex.outputs['Color'],n['Principled BSDF'].inputs['Base Color'])
l.new(tex.outputs['Color'],n['Principled BSDF'].inputs['Emission Color']);n['Principled BSDF'].inputs['Emission Strength'].default_value=.09
# A quiet mineral-blue zenith avoids pinching the panoramic image at the pole.
coord=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Generated'],sep.inputs[0])
sx=n.new('ShaderNodeMath');sx.operation='SUBTRACT';sx.inputs[1].default_value=.5;l.new(sep.outputs['X'],sx.inputs[0])
sy=n.new('ShaderNodeMath');sy.operation='SUBTRACT';sy.inputs[1].default_value=.5;l.new(sep.outputs['Y'],sy.inputs[0])
comb=n.new('ShaderNodeCombineXYZ');l.new(sx.outputs[0],comb.inputs[0]);l.new(sy.outputs[0],comb.inputs[1])
length=n.new('ShaderNodeVectorMath');length.operation='LENGTH';l.new(comb.outputs[0],length.inputs[0])
fade=n.new('ShaderNodeMapRange');fade.interpolation_type='SMOOTHSTEP';fade.inputs['From Min'].default_value=.17;fade.inputs['From Max'].default_value=.27
l.new(length.outputs['Value'],fade.inputs['Value'])
mixf=n.new('ShaderNodeMixRGB');mixf.inputs[1].default_value=(.008,.026,.031,1)
l.new(fade.outputs[0],mixf.inputs[0]);l.new(tex.outputs[0],mixf.inputs[2])
l.new(mixf.outputs[0],n['Principled BSDF'].inputs['Base Color']);l.new(mixf.outputs[0],n['Principled BSDF'].inputs['Emission Color'])
o=mesh('Rotunda | painted interior vault',verts,faces,fresco,'06',True)
layer=o.data.uv_layers.new(name='Panoramic fresco | lower dome band')
for p in o.data.polygons:
    # Repeat the panorama on the two semicircles. This presents all three eras
    # together from each entrance-facing view, as in the reference images.
    angles=[]
    for li in p.loop_indices:
        v=o.data.vertices[o.data.loops[li].vertex_index].co
        angles.append((math.atan2(v.y,v.x)/math.pi)%1.0)
    seam=max(angles)-min(angles)>.5
    for j,li in enumerate(p.loop_indices):
        v=o.data.vertices[o.data.loops[li].vertex_index].co
        u=angles[j]+(1 if seam and angles[j]<.5 else 0)
        radial=math.hypot(v.x,v.y)/R
        # Keep the important figures on the broad lower two-thirds of the vault.
        vv=max(0,min(1,(1-radial)/.66))
        layer.data[li].uv=(1-u,vv)
o['apex_height_m']=6.2;o['narrative']='Amber: optical history. Emerald: present embodied XR. Lapis: shared future worlds.'
# Circular springing masks the twelve-sided structure above the cornice.
for rr,z,rad,m in [(3.91,4.89,.041,gold),(3.965,4.98,.022,gold_light),(3.80,5.29,.020,gold),(3.85,5.24,.015,gold_light)]:
    ring('Rotunda | concentric gilt molding',rr,z,rad,m,'06')
# Dark drum between the first concentric rims, with modest era lettering.
for side in (0,180):
    for degrees,label in [(150,'PAST · OPTICAL WORLDS'),(90,'PRESENT · SHARED PRESENCE'),(30,'FUTURE · POSSIBLE WORLDS')]:
        a=(degrees+side)*math.pi/180
        txt('Rotunda | '+label+(' | opposite' if side else ''),label,a,0,3.785,5.13,.083,col='06',max_width=1.62)

# Embedded bookshelf screen: a designed spatial interface, not a loose monitor.
a=math.pi/2
C('Library interface | carved walnut surround',a,0,3.475,1.405,1.12,.125,1.27,wood,'08',.045)
C('Library interface | gilt bezel',a,0,3.402,1.405,1.034,.037,1.183,gold,'08',.030)
display=C('Library interface | interactive display',a,0,3.374,1.405,.97,.026,1.115,screen,'08',.022)
display['interaction']='open_url';display['url']='https://library.xrguild.org/';display['screen_center_height_m']=1.405
txt('Display | guild','XR GUILD',a,0,3.354,1.82,.068,ink,'08',.76)
txt('Display | title','THE LIBRARY',a,0,3.353,1.705,.046,gold_light,'08',.74)
C('Display | search outline',a,0,3.35,1.55,.79,.008,.13,gold,'08',.022)
C('Display | search field',a,0,3.343,1.55,.773,.008,.112,screen,'08',.018)
txt('Display | search text','Search resources & topics',a,.025,3.334,1.55,.033,ink,'08',.62)
CV('Display | magnifying glass',a,[[( -.333+.018*math.cos(t*2*math.pi/32),3.331,1.553+.018*math.sin(t*2*math.pi/32)) for t in range(33)],[(-.32,3.331,1.54),(-.305,3.331,1.525)]],.003,ink,'08')
for j,label in enumerate(['AI ETHICS','PRIVACY & POLICY','SECURITY & SAFETY']):
    z=1.398-j*.101
    txt('Display | '+label,label,a,0,3.338,z,.029,ink,'08',.65)
    C('Display | divider',a,0,3.337,z-.045,.69,.005,.003,gold,'08',0)
C('Display | browse button',a,0,3.333,1.045,.75,.016,.12,gold,'08',.02)
txt('Display | browse','EXPLORE THE COLLECTION',a,0,3.318,1.046,.031,screen,'08',.69)
txt('Display | domain','library.xrguild.org',a,0,3.334,.922,.027,ink,'08',.67)
ornament(a,0,2.065,.45,3.48,'08')
txt('Library interface | carved lintel','RESOURCES & RESEARCH',a,0,3.476,2.31,.065,gold_light,'08',1.46)

# Double meeting doors in south bay, with true hinge pivots and one animated control.
S['door_open']=0.0
S.id_properties_ui('door_open').update(min=0.0,max=1.0,description='0 = closed for meetings; 1 = fully open outward')
a=3*math.pi/2
door_outline=arch(1.65,0,2.64,3.60)
for width,yy,r,ma in [(1.78,3.95,.055,green_stone),(1.68,3.89,.018,gold)]:
    CV('Meeting entrance | arched jamb',a,[[(x,yy,z) for x,z in arch(width,0,2.64,3.65)]],r,ma,'09',True)
panel('Meeting entrance | fixed fanlight',a,arch(1.57,2.48,2.62,3.54),4.055,.065,glass,'09')
for sign in (-1,1):
    paths=[bez([(0,3.984,2.50),(sign*.10,3.984,2.94),(sign*.40,3.984,3.18),(sign*.04,3.984,3.50)]),
           bez([(sign*.70,3.984,2.52),(sign*.70,3.984,2.88),(sign*.40,3.984,3.10),(0,3.984,3.14)])]
    CV('Meeting entrance | fanlight tracery',a,paths,.018,gold,'09')
    hinge=bpy.data.objects.new('Door hinge | '+('left' if sign<0 else 'right'),None);collections['09'].objects.link(hinge);hinge.location=P(a,sign*.813,4.055,0);hinge.empty_display_size=.12
    children=[]
    children.append(C('Door leaf | '+str(sign),a,sign*.408,4.055,1.24,.802,.10,2.48,wood,'09',.017))
    for zz,hh in [(.47,.67),(1.61,1.37)]:
        children.append(C('Door | recessed forest panel',a,sign*.408,3.998,zz,.606,.020,hh,green_stone,'09',.013))
        for xx in [sign*.408-.312,sign*.408+.312]:
            children.append(C('Door | gilt panel upright',a,xx,3.979,zz,.016,.017,hh+.035,gold,'09',.004))
        for z in [zz-hh/2-.012,zz+hh/2+.012]:
            children.append(C('Door | gilt panel rail',a,sign*.408,3.979,z,.64,.017,.016,gold,'09',.004))
    children.append(C('Door | bronze pull',a,sign*.13,3.91,1.13,.029,.042,.26,gold_light,'09',.014))
    # Elegant botanical inlay in each upper door panel.
    children.append(CV('Door | iris inlay',a,[bez([(sign*.41,3.965,.96),(sign*.23,3.965,1.30),(sign*.59,3.965,1.75),(sign*.41,3.965,2.20)])],.011,gold,'09'))
    bpy.context.view_layer.update()
    for child in children:
        mw=child.matrix_world.copy();child.parent=hinge;child.matrix_world=mw
    drv=hinge.driver_add('rotation_euler',2).driver
    drv.expression=f'{sign} * opening * 1.745329252'
    v=drv.variables.new();v.name='opening';v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=S;v.targets[0].data_path='["door_open"]'
    hinge['pivot_type']='hinge';hinge['open_angle_degrees']=sign*100
txt('Door | meeting room sign','THE LIBRARY',a,0,3.94,3.96,.107,gold_light,'09',1.60)
txt('Door | purpose','A ROOM FOR SHARED DISCOVERY',a,0,3.94,3.80,.047,gold_light,'09',1.62)
for frame,val in [(1,0),(24,0),(72,1),(120,1),(168,0)]:
    S['door_open']=val;S.keyframe_insert(data_path='["door_open"]',frame=frame)
S.frame_start=1;S.frame_end=168;S.frame_set(1)
for name,f in [('CLOSED · meeting',1),('OPEN · entrance',72),('CLOSED · return',168)]:S.timeline_markers.new(name,frame=f)

# Optional meeting layout: eight chairs and a walnut table. Hidden by default.
table=cyl('Meeting table | walnut top',(0,0,.76),1.13,.085,wood,'11',96)
ring('Meeting table | gilt rim',1.126,.76,.012,gold,'11')
cyl('Meeting table | green pedestal',(0,0,.37),.26,.67,green_stone,'11',48,.19)
cyl('Meeting table | brass foot',(0,0,.06),.47,.075,gold,'11',64)
for k in range(8):
    a=k*math.pi/4;r=1.65
    # Local x=tangent, y=radial. Chairs face the central table.
    C(f'Chair {k+1:02d} | walnut seat',a,0,r,.445,.55,.56,.085,wood,'11',.045)
    C(f'Chair {k+1:02d} | velvet seat',a,0,r-.018,.507,.50,.49,.095,velvet,'11',.05)
    C(f'Chair {k+1:02d} | carved back',a,0,r+.245,.86,.53,.075,.64,wood,'11',.06)
    C(f'Chair {k+1:02d} | velvet back',a,0,r+.197,.873,.44,.052,.49,velvet,'11',.05)
    for xx in [-.215,.215]:
        for yy in [-.21,.21]:
            C(f'Chair {k+1:02d} | tapered leg',a,xx,r+yy,.22,.043,.043,.41,wood,'11',.01)
            C(f'Chair {k+1:02d} | brass shoe',a,xx,r+yy,.045,.046,.046,.075,gold,'11',.008)
collections['11'].hide_render=True
collections['11'].hide_viewport=True

# Export-friendly intent anchors. They do not imply a particular runtime.
for name,loc,props in [
    ('INTERACT_Library_URL',P(math.pi/2,0,3.30,1.405),{'action':'open_url','url':'https://library.xrguild.org/','target_object':display.name}),
    ('INTERACT_Door',P(3*math.pi/2,0,3.83,1.1),{'action':'toggle_door','property':'scene.door_open'}),
    ('Meeting_center',(0,0,0),{'clear_radius_m':2.9,'furniture_collection':collections['11'].name})]:
    o=bpy.data.objects.new(name,None);collections['12'].objects.link(o);o.location=loc;o.empty_display_type='CUBE';o.empty_display_size=.09
    for key,value in props.items():o[key]=value

# Broad soft fill and upward ceiling wash, matching the warm/cool reference lighting.
def area(name,loc,target,energy,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);collections['10'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Warm rotunda bounce',(0,0,4.8),(0,0,0),105,(1,.79,.52),4.8)
area('Fresco soft uplight',(0,0,3.5),(0,0,6.2),65,(1,.86,.65),4.0)
area('Entry reflected light',(0,-3.5,3.4),(0,1,2.0),24,(.80,.9,1),2.4)
for ob in S.objects:
    if ob.type=='LIGHT' and ob.name.startswith('Window '):
        ob.data.energy=100;ob.data.color=(.84,.93,1)
    if ob.type=='LIGHT' and ob.data.type=='POINT':ob.data.energy=4
    if ob.type=='LIGHT':
        ob.visible_glossy=False
        ob.visible_transmission=False

# A separate preview landscape makes the clear windows legible in renders.
# It is not part of the room asset and can be disabled for installation elsewhere.
skyground=mat('Exterior | distant meadow',(.16,.24,.17),0,.95)
nearhill=mat('Exterior | forest green hills',(.15,.26,.22),0,1)
midhill=mat('Exterior | hazy blue green ridge',(.22,.34,.34),0,1)
farhill=mat('Exterior | pale mountain atmosphere',(.40,.54,.59),0,1)
lake=mat('Exterior | distant lake',(.24,.43,.47),.15,.18)
for m in [skyground,nearhill,midhill,farhill]:
    mb=m.node_tree.nodes['Principled BSDF']
    mb.inputs['Emission Color'].default_value=m.diffuse_color
    mb.inputs['Emission Strength'].default_value=.30
cyl('PREVIEW ONLY | landscape ground',(0,0,-.31),220,.1,skyground,'13',128)
cyl('PREVIEW ONLY | tranquil distant water',(0,0,-.246),95,.006,lake,'13',128)
# Concentric real-geometry ridges, with softened distant colors.
for layer,(rr,high,ma,seed) in enumerate([(46,9,nearhill,11),(85,18,midhill,28),(135,36,farhill,41)]):
    count=360;vertices=[]
    for radial in [rr,rr+20]:
        for j in range(count):
            t=j*2*math.pi/count
            h=high*(.35+.27*math.sin(3*t+seed)+.15*math.cos(7*t+seed)+.10*math.sin(13*t)+.06*math.cos(23*t))
            h=max(1.0,h)+(0 if radial==rr else 1.7)
            vertices.extend([(radial*math.cos(t),radial*math.sin(t),-.29),(radial*math.cos(t),radial*math.sin(t),h)])
    faces=[]
    for j in range(count):
        k=(j+1)%count
        faces.extend([(j*2,k*2,k*2+1,j*2+1),(j*2+1,k*2+1,count*2+k*2+1,count*2+j*2+1)])
    mesh(f'PREVIEW ONLY | atmospheric ridge {layer+1}',vertices,faces,ma,'13',True)
# A sparse distant treeline, built as grouped crown silhouettes rather than a flat image.
for k in range(100):
    t=k*2*math.pi/100;rr=32+random.uniform(-3,5);height=random.uniform(2.8,5.4)
    x,y=rr*math.cos(t),rr*math.sin(t)
    cyl('PREVIEW ONLY | tree trunk',(x,y,height*.30),.095,height*.60,wood_dark,'13',8)
    for j in range(3):
        cyl('PREVIEW ONLY | evergreen canopy',(x,y,height*(.46+j*.17)),height*(.25-j*.052),height*.47,nearhill,'13',9,0)
# Camera rays see a soft sky; architectural illumination remains controlled.
wn,wl=S.world.node_tree.nodes,S.world.node_tree.links
sky=wn.new('ShaderNodeBackground');sky.inputs['Color'].default_value=(.53,.70,.83,1);sky.inputs['Strength'].default_value=.85
lp=wn.new('ShaderNodeLightPath');wm=wn.new('ShaderNodeMixShader')
visible=wn.new('ShaderNodeMath');visible.operation='MAXIMUM';wl.new(lp.outputs['Is Camera Ray'],visible.inputs[0]);wl.new(lp.outputs['Is Transmission Ray'],visible.inputs[1])
wl.new(visible.outputs[0],wm.inputs[0]);wl.new(wn['Background'].outputs[0],wm.inputs[1]);wl.new(sky.outputs[0],wm.inputs[2]);wl.new(wm.outputs[0],wn['World Output'].inputs[0])
collections['13']['purpose']='Optional render context only. Exclude from room export or replace with the destination world.'

def camera(name,loc,target,lens=21):
    d=bpy.data.cameras.new(name);d.lens=lens;d.clip_start=.03;d.clip_end=100
    o=bpy.data.objects.new(name,d);collections['10'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
hero=camera('01 | Entrance interior',(0,-3.60,1.70),(0,1.5,2.42),18.5)
camera('02 | Window and bookcase',(1.0,-2.0,1.70),(3.9,.5,2.45),24)
camera('03 | Library interface',(.15,1.40,1.58),(0,3.6,1.60),44)
camera('04 | Fresco',(0,0,.95),(0,0,6.2),18)
camera('05 | Meeting entrance',(.55,2.55,1.70),(0,-3.8,2.28),23)
plan=camera('06 | Plan',(0,0,13),(0,0,0),35);plan.data.type='ORTHO';plan.data.ortho_scale=9.6
camera('07 | Elevated interior',(-1.7,-2.35,3.0),(.7,1.0,2.7),17)
tracecam=camera('08 | Tracery straight on',(1.45,0,3.70),(4.0,0,3.70),50)
tracecam.data.type='ORTHO';tracecam.data.ortho_scale=1.60
S.camera=hero
S['project']='XR Guild Library | Art Nouveau rotunda'
S['specification']='12 sides · 8.0 m across inner flats · 6.2 m apex · 6 windows · 5 empty bookcases · closable double doors'
S['library_url']='https://library.xrguild.org/'
S['topics_verified']='2026-09-23; https://library.xrguild.org/'
S['reference_policy']='All architecture is newly modeled. Supplied BLEND/GLB files used only to inspect scale and proportions.'
S['furniture_note']='Optional eight-chair meeting layout is in collection 11; hidden in the default open-floor scene.'

# Pack font and artwork so the blend is self-contained.
for f in bpy.data.fonts:
    if f.filepath and f.name!='Bfont':
        try:f.pack()
        except Exception:pass
for filename in ['library_controls.py']:
    p=ROOT/'scripts'/filename
    if p.exists():bpy.data.texts.load(str(p))
readme=bpy.data.texts.new('START HERE · XR Guild Library')
readme.write('XR GUILD LIBRARY\n\n8.0 m across inner flats; 6.2 m dome apex. One unit = one metre.\n'
             'Frame 1: closed doors. Frame 72: fully open doors.\n'
             'Collection 11 contains optional meeting furniture; disabled by default.\n'
             'The library interface stores its destination in the url custom property.\n'
             'Run library_controls.py from the Text Editor to add an XR Guild sidebar with door, furniture and URL controls.\n'
             'No script auto-runs. Browser search itself belongs to library.xrguild.org.\n'
             'All supplied reference models remain unchanged.\n')
for screen_data in bpy.data.screens:
    for ar in screen_data.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.shading.type='MATERIAL'
            ar.spaces.active.overlay.show_overlays=False

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=display
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'XR_Guild_Library.blend'),compress=True)
report={'interior_across_flats_m':8.0,'interior_corner_diameter_m':outer*2,'apex_m':6.2,'wall_sides':12,'arched_windows':6,'bookcases':5,
        'books':0,'meeting_chairs_optional':8,'floor_center_clear_radius_m':2.9,'door_clear_width_m':1.626,'door_height_m':2.48,
        'screen_center_m':1.405,'object_count':len(S.objects),'materials':len(bpy.data.materials),
        'mesh_triangles_base':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in S.objects if o.type=='MESH'),
        'fresco_texture':str(ROOT/'textures/immersive_eras_fresco_v2.png'),'topics':[{'name':n,'url':u} for n,t,u in topics]}
(ROOT/'evidence/model_manifest.json').write_text(json.dumps(report,indent=2))
print('LIBRARY_BUILD_COMPLETE',json.dumps(report))
