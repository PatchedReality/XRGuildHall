"""Add reference-led, editable Art Nouveau craftsmanship to the approved v1.
Run: Blender -b --python v2/scripts/build_v2.py. Never overwrites v1.
"""
import ast
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'XR_Guild_Library.blend'))
S=bpy.context.scene
S.frame_set(1)
collections={c.name[:2]:c for c in S.collection.children}
materials={'gold':'Gilt brass | gently aged','gold_light':'Polished gold leaf edges','bronze':'Patinated bronze recesses',
'wall':'Deep malachite green plaster','wall_dark':'Forest green damask backing','damask':'Silk fern damask',
'wood':'Handcrafted figured walnut','wood_dark':'Walnut endgrain and recess','ivory':'Warm ivory limestone',
'green_stone':'Verde antique marble','blue_stone':'Blue petrol stone','lab':'Labradorite | green stone with blue schiller',
'glass':'Clear architectural glass | transparent, not frosted','glow':'Opal lamp glow','velvet':'Bottle green velvet'}
for key,name in materials.items():globals()[key]=bpy.data.materials.get(name)
font=next((f for f in bpy.data.fonts if 'Baskerville' in f.name),bpy.data.fonts.get('Bfont'))
# Reuse the existing construction vocabulary, without rerunning its scene generator.
module=ast.parse((SOURCE/'scripts/build_library.py').read_text())
names={'move','mat','noise_mat','mesh','cube','cyl','curve','ring','sphere','bez','P','C','CV','arch','panel','txt','annulus','leaf3d','ornament','camera'}
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'v1_geometry_helpers','exec'))
if blue_stone is None:blue_stone=mat('Blue petrol stone',(.018,.07,.092),.20,.22)
for code,name in [('14','14 V2 carved joinery'),('15','15 V2 botanical plasterwork'),('16','16 V2 sculpted capitals'),('17','17 V2 lanterns and perimeter seating'),('18','18 V2 celestial ceiling ornament')]:
    col=bpy.data.collections.new(name);S.collection.children.link(col);collections[code]=col

# Slightly warmer, brighter leaf edges and darker green plaster match the reference palette.
gold_light.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.22
wall.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72
for n in wall.node_tree.nodes:
    if n.type=='VALTORGB':
        for e,c in zip(n.color_ramp.elements,[(.007,.020,.014,1),(.014,.043,.028,1),(.038,.075,.045,1)]):e.color=c
# Rich feldspar plates and warm hairline veins replace the first pass's vertical noise.
n,l=lab.node_tree.nodes,lab.node_tree.links
b=n['Principled BSDF']
for link in list(b.inputs['Base Color'].links):l.remove(link)
tc=n.new('ShaderNodeTexCoord')
warp=n.new('ShaderNodeTexNoise');warp.inputs['Scale'].default_value=5;warp.inputs['Detail'].default_value=4
l.new(tc.outputs['Generated'],warp.inputs['Vector'])
add=n.new('ShaderNodeVectorMath');add.operation='SCALE';add.inputs[3].default_value=.10;l.new(warp.outputs['Color'],add.inputs[0])
vsum=n.new('ShaderNodeVectorMath');vsum.operation='ADD';l.new(tc.outputs['Generated'],vsum.inputs[0]);l.new(add.outputs[0],vsum.inputs[1])
voro=n.new('ShaderNodeTexVoronoi');voro.distance='EUCLIDEAN';voro.inputs['Scale'].default_value=14;l.new(vsum.outputs[0],voro.inputs['Vector'])
sep=n.new('ShaderNodeSeparateColor');l.new(voro.outputs['Color'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(p,c) in enumerate([(0,(.009,.028,.022,1)),(.33,(.028,.068,.049,1)),(.58,(.078,.13,.096,1)),(.76,(.018,.14,.20,1)),(.92,(.065,.24,.34,1)),(1,(.23,.30,.23,1))]):
    e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(p);e.position=p;e.color=c
l.new(sep.outputs[0],ramp.inputs[0])
edge=n.new('ShaderNodeTexVoronoi');edge.feature='DISTANCE_TO_EDGE';edge.inputs['Scale'].default_value=14;l.new(vsum.outputs[0],edge.inputs['Vector'])
er=n.new('ShaderNodeValToRGB');er.color_ramp.elements[0].position=.004;er.color_ramp.elements[0].color=(.65,.65,.65,1);er.color_ramp.elements[1].position=.016;er.color_ramp.elements[1].color=(0,0,0,1);l.new(edge.outputs['Distance'],er.inputs[0])
stone_noise=n.new('ShaderNodeTexNoise');stone_noise.inputs['Scale'].default_value=11;stone_noise.inputs['Detail'].default_value=7;stone_noise.inputs['Roughness'].default_value=.78;stone_noise.inputs['Distortion'].default_value=3
l.new(vsum.outputs[0],stone_noise.inputs['Vector'])
stone_ramp=n.new('ShaderNodeValToRGB');stone_ramp.color_ramp.elements[0].position=.25;stone_ramp.color_ramp.elements[0].color=(.005,.019,.015,1);stone_ramp.color_ramp.elements[1].position=.73;stone_ramp.color_ramp.elements[1].color=(.13,.20,.15,1)
stone_ramp.color_ramp.elements.new(.49).color=(.019,.052,.039,1)
stone_ramp.color_ramp.elements.new(.62).color=(.026,.10,.112,1)
l.new(stone_noise.outputs['Fac'],stone_ramp.inputs[0])
feldspar=n.new('ShaderNodeMixRGB');feldspar.inputs[0].default_value=.20;l.new(stone_ramp.outputs[0],feldspar.inputs[1]);l.new(ramp.outputs[0],feldspar.inputs[2])
mix=n.new('ShaderNodeMixRGB');l.new(er.outputs[0],mix.inputs[0]);l.new(feldspar.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(.12,.15,.09,1);l.new(mix.outputs[0],b.inputs['Base Color'])
b.inputs['Roughness'].default_value=.24;b.inputs['Metallic'].default_value=.20

# Turned profiles have real ogees, torus beads and undercuts, not stacked plain cylinders.
def lathe(name,xy,profile,ma,col='16',segments=64):
    vs=[(xy[0]+r*math.cos(k*math.tau/segments),xy[1]+r*math.sin(k*math.tau/segments),z) for r,z in profile for k in range(segments)]
    fs=[]
    for j in range(len(profile)-1):
        for k in range(segments):
            q=j*segments+k;nk=j*segments+(k+1)%segments
            fs.append((q,nk,nk+segments,q+segments))
    return mesh(name,vs,fs,ma,col,True)

def fern(a,x,z,h,w,y,col='15',ma=None):
    ma=ma or gold
    paths=[bez([(x,y,z),(x+w*.08,y,z+h*.35),(x-w*.06,y,z+h*.7),(x,y,z+h)])]
    for j in range(5):
        t=.15+j*.145
        for sign in [-1,1]:
            xx=x+sign*w*.5*math.sin(math.pi*t)
            zz=z+h*(t+.15)
            paths.append(bez([(x,y,z+h*t),(x+sign*w*.24,y,z+h*(t+.05)),(xx,y,zz-.035),(xx,y,zz)]))
            leaf3d('V2 | engraved fern leaflet',P(a,xx-sign*.015,y,zz-.02),P(a,xx+sign*w*.09,y,zz+h*.085),w*.10,ma,col)
    CV('V2 | branching fern stems',a,paths,.0045,ma,col)

def rosette(a,x,y,z,r,col='15'):
    paths=[]
    for k in range(8):
        t=k*math.tau/8
        pts=[]
        for j in range(25):
            q=j*math.tau/24
            radial=r*(.42+.55*(.5-.5*math.cos(q)))
            ang=t+.17*math.sin(q)
            pts.append((x+radial*math.cos(ang),y,z+radial*math.sin(ang)))
        paths.append(pts)
    CV('V2 | eight-petal chased rosette',a,paths,.005,gold_light,col)
    o=sphere('V2 | cabochon rosette heart',P(a,x,y,z),(.022,.013,.022),blue_stone,col)

# Replace simple first-pass capital leaves and sconces while preserving the shaft dimensions.
for o in list(S.objects):
    if ('repoussé capital leaf' in o.name or '| leaf vein ' in o.name or o.name.startswith('Sconce ')):
        bpy.data.objects.remove(o,do_unlink=True)
# Each capital has two overlapping rows of lobed, concave leaves with curling tips.
for i in range(12):
    a=(i+.5)*math.pi/6;x,y=3.95*math.cos(a),3.95*math.sin(a)
    lathe(f'V2 | Column {i+1:02d} turned socle',(x,y),[(.25,.015),(.258,.035),(.258,.06),(.24,.075),(.225,.10),(.223,.14),(.232,.16),(.235,.18),(.22,.20),(.211,.225),(.23,.238),(.231,.255),(.20,.27)],gold)
    lathe(f'V2 | Column {i+1:02d} neck astragal',(x,y),[(.17,3.97),(.18,3.99),(.185,4.005),(.18,4.025),(.17,4.04)],gold_light)
    for row in range(2):
        for k in range(12):
            t=k*math.tau/12+row*math.pi/12
            start=4.045+row*.07;h=.26+row*.04;width=.115+row*.018
            vs=[];fs=[];mid=[]
            for j in range(25):
                u=j/24
                rr=.163+.052*math.sin(u*math.pi*.65)+.060*u**5
                zz=start+h*u-.045*u**9
                scallop=.78+.22*math.cos(u*math.pi*10)
                ww=width*.5*math.sin(math.pi*u)**.65*scallop
                mid.append((x+(rr+.012)*math.cos(t),y+(rr+.012)*math.sin(t),zz))
                for f in [-1,-.5,0,.5,1]:
                    rad=rr+.022*(1-f*f)*math.sin(math.pi*u)
                    vs.append((x+rad*math.cos(t)-f*ww*math.sin(t),y+rad*math.sin(t)+f*ww*math.cos(t),zz))
            for j in range(24):
                for q in range(4):v=j*5+q;fs.append((v,v+1,v+6,v+5))
            mesh(f'V2 | capital {i+1:02d} acanthus row {row+1} leaf {k+1:02d}',vs,fs,gold,'16',True)
            curve('V2 | capital chased midrib',[mid],.0035,gold_light,'16')
            veins=[]
            for j in [5,9,13,17]:
                for sign in [-1,1]:
                    endpoint=vs[(j+3)*5+(0 if sign<0 else 4)]
                    veins.append([mid[j],endpoint])
            curve('V2 | capital acanthus side veins',veins,.0024,bronze,'16')
    # Four inward-facing volutes curl under the abacus.
    for k in range(8):
        t=k*math.tau/8;pts=[]
        for j in range(45):
            u=j/44;ang=u*math.pi*2.3;r=.064*(1-u*.75)
            radial=.229+r*math.sin(ang)
            pts.append((x+radial*math.cos(t),y+radial*math.sin(t),4.335+r*math.cos(ang)))
        curve('V2 | capital rolled volute',[pts],.008,gold_light,'16')
    lathe('V2 | capital scalloped abacus edge',(x,y),[(.252,4.36),(.268,4.375),(.269,4.39),(.255,4.405),(.279,4.421)],gold)
    # Fine shaft filigree is restricted to the top and foot, leaving the stone visible.
    fern(a,0,.43,.43,.20,3.758,'16')

# Enrich the cornice without changing the fresco profile or lettering positions.
for i in range(12):
    a=i*math.pi/6
    old=bpy.data.objects.get(f'Bay {i:02d} | cornice 4.85')
    if old:old.data.materials[0]=green_stone
    for z,yy,w,h in [(4.79,3.77,2.16,.019),(4.82,3.755,2.16,.018),(4.90,3.76,2.16,.021),(4.53,3.89,2.15,.012)]:
        C('V2 | cornice reed and bead',a,0,yy,z,w,.025,h,gold_light,'15',.006)
    # Small alternating buds and curling leaves on the upper frieze.
    for j in range(11):
        xx=(j-5)*.181
        for sign in [-1,1]:
            CV('V2 | cornice running honeysuckle',a,[bez([(xx,3.755,4.825),(xx+sign*.025,3.755,4.90),(xx+sign*.075,3.755,4.883),(xx+sign*.074,3.755,4.84)])],.0045,gold,'15')
        if j%2==0:
            leaf3d('V2 | cornice seed',P(a,xx,3.75,4.825),P(a,xx,3.75,4.885),.029,gold_light,'15')
    for sign in [-1,1]:
        fern(a,sign*.79,3.85,.52,.31,3.98)
        CV('V2 | bay upper swept molding',a,[bez([(sign*.93,3.975,3.62),(sign*.89,3.975,4.33),(sign*.62,3.975,4.45),(0,3.975,4.43)])],.006,gold,'15')
    # Rosettes set in dark spandrels; ornament stays outside all glass openings.
    if i%2==0:
        rosette(a,0,3.958,4.37,.066)
        for sign in [-1,1]:
            fern(a,sign*.72,.66,2.87,.19,3.978,ma=bronze)
        for xx in [-.39,0,.39]:
            C('V2 | window dado recessed walnut',a,xx,3.922,.348,.35,.028,.22,wood_dark,'14',.007)
            line=arch(.32,.23,.34,.452,20)
            CV('V2 | window dado arched inlay',a,[[(x+xx,3.9,z) for x,z in line]],.0055,gold,'14',True)
        # Recessed carved reveal and three concentric bead moldings.
        for off,yy,rad,ma in [(.085,3.962,.012,ivory),(.17,3.98,.014,bronze),(.24,3.99,.009,gold_light)]:
            CV('V2 | layered window archivolt',a,[[(x,yy,z) for x,z in arch(.98+off,.55,3.52,4.25+off*.52)]],rad,ma,'15',True)

# Empty bookcases acquire rounded arch heads, carved stiles, split bays and paneled plinths.
for i in [1,3,5,7,11]:
    a=i*math.pi/6
    for o in list(collections['04'].objects):
        if o.name.startswith(f'Bookcase {i:02d}') and ('empty shelf 8' in o.name or 'pencil edge 8' in o.name):bpy.data.objects.remove(o,do_unlink=True)
    if i!=3:
        C('V2 | bookcase slender center stile',a,0,3.71,2.04,.039,.41,3.17,wood,'14',.008)
        C('V2 | bookcase center hairline inlay',a,0,3.49,2.07,.007,.008,3.15,gold,'14',.002)
    # Arches are relief ribbons, leaving upper shelves available for authors.
    for xc in [-.402,.402]:
        archline=bez([(xc-.389,3.488,3.11),(xc-.385,3.488,3.61),(xc-.19,3.488,3.64),(xc,3.488,3.67)])+bez([(xc,3.488,3.67),(xc+.19,3.488,3.64),(xc+.385,3.488,3.61),(xc+.389,3.488,3.11)])
        CV('V2 | bookcase carved arch head',a,[archline],.022,wood,'14')
        CV('V2 | bookcase gilt arch bead',a,[[(x,y-.026,z) for x,y,z in archline]],.005,gold_light,'14')
        branches=[]
        for sign in [-1,1]:
            for j in range(3):
                branches.append(bez([(xc,3.475,3.31),(xc+sign*.05,3.475,3.47),(xc+sign*(.12+j*.073),3.475,3.51),(xc+sign*(.13+j*.073),3.475,3.61)]))
        CV('V2 | bookcase botanical fan',a,branches,.006,gold,'14')
        fern(a,xc,3.36,.25,.22,3.469,'14')
    for sign in [-1,1]:
        fern(a,sign*.84,2.86,.66,.072,3.448,'14')
        for z in [.59,1.57,2.55]:
            # Repeated mortise collars give vertical joinery a handcrafted rhythm.
            C('V2 | carved stile collar',a,sign*.84,3.466,z,.090,.026,.041,gold,'14',.007)
        CV('V2 | pediment whiplash scroll',a,[bez([(0,3.723,3.85),(sign*.35,3.723,4.23),(sign*.69,3.723,3.80),(sign*.88,3.723,3.98)])],.010,gold,'14')
        fern(a,sign*.35,3.87,.29,.30,3.726,'14')
    rosette(a,0,3.714,4.025,.073,'14')
    # Cabinet panels occupy the existing low base, preserving every open shelf.
    for xc in [-.57,0,.57]:
        C('V2 | bookcase recessed field panel',a,xc,3.463,.30,.515,.017,.244,wood_dark,'14',.009)
        line=arch(.48,.186,.302,.42,24)
        CV('V2 | bookcase paneled plinth inlay',a,[[(x+xc,3.447,z) for x,z in line]],.005,gold,'14',True)
        fern(a,xc,.211,.176,.19,3.438,'14')
    # Dentil-like carved beads are below the existing crown, clear of the narrative.
    for j in range(22):
        C('V2 | bookcase crown carved bead',a,(j-10.5)*.079,3.475,3.708,.031,.035,.045,wood_dark,'14',.010)
    for j in range(10):
        rosette(a,(j-4.5)*.167,3.443,3.76,.019,'14')

# Six tall, caged opal lanterns with petal crowns replace the plain ball lights.
for i in range(0,12,2):
    a=(i+.5)*math.pi/6;radial=3.62;cx,cy,_=P(a,0,radial,0);z=2.27
    C('V2 | lantern embossed backplate',a,0,3.752,z,.104,.028,.72,bronze,'17',.045)
    CV('V2 | lantern swan-neck bracket',a,[bez([(0,3.75,z-.30),(0,3.45,z-.29),(0,3.54,z-.08),(0,radial,z-.02)])],.014,gold,'17')
    lathe('V2 | lantern opal cylinder',(cx,cy),[(.054,z-.19),(.072,z-.17),(.072,z+.17),(.054,z+.19)],glow,'17',32)
    lathe('V2 | lantern bottom repoussé cup',(cx,cy),[(.008,z-.29),(.029,z-.25),(.065,z-.215),(.087,z-.19),(.080,z-.17)],gold,'17',48)
    lathe('V2 | lantern petal canopy',(cx,cy),[(.082,z+.17),(.086,z+.20),(.068,z+.23),(.035,z+.27),(.012,z+.31)],gold,'17',48)
    for k in range(8):
        t=k*math.pi/4
        curve('V2 | lantern slender cage rib',[bez([(cx+.084*math.cos(t),cy+.084*math.sin(t),z-.19),(cx+.103*math.cos(t),cy+.103*math.sin(t),z-.06),(cx+.103*math.cos(t),cy+.103*math.sin(t),z+.06),(cx+.084*math.cos(t),cy+.084*math.sin(t),z+.20)])],.004,gold_light,'17')
    fern(a,0,z+.32,.24,.14,3.747,'17')
    data=bpy.data.lights.new('V2 | lantern warm pool','POINT');data.energy=7;data.color=(1,.69,.34);data.shadow_soft_size=.12
    ob=bpy.data.objects.new(data.name,data);collections['10'].objects.link(ob);ob.location=P(a,0,radial-.08,z)
# A pair of slim window seats is at the perimeter; meeting center remains unobstructed.
for i in [0,6]:
    a=i*math.pi/6
    C('V2 | window seat walnut rail',a,0,3.72,.38,.89,.40,.06,wood,'17',.023)
    C('V2 | window seat velvet cushion',a,0,3.69,.435,.83,.37,.065,velvet,'17',.026)
    C('V2 | window seat brass piping',a,0,3.491,.436,.80,.007,.007,gold,'17',.003)
    for sign in [-1,1]:
        for yy in [3.54,3.86]:
            CV('V2 | seat cabriole leg',a,[bez([(sign*.34,yy,.36),(sign*.28,yy,.24),(sign*.36,yy,.09),(sign*.39,yy,.045)])],.022,wood,'17')
        fern(a,sign*.34,.20,.19,.10,3.49,'17')

# The zenith receives a restrained gilt celestial rose; the painted figures remain unobscured.
def vault_z(r):return 4.88+1.32*math.sqrt(max(0,1-(r/4.025)**2))-.015
for r in [.20,.245,.77,.80,1.07]:ring('V2 | zenith engraved orbit',r,vault_z(r),.0048,gold,'18',160)
paths=[]
for k in range(12):
    t=k*math.pi/6
    for sign in [-1,1]:
        pts=[]
        for j in range(65):
            u=j/64;r=.245+u*.83;ang=t+sign*.14*math.sin(math.pi*u)
            pts.append((r*math.cos(ang),r*math.sin(ang),vault_z(r)))
        paths.append(pts)
    r=1.065
    sphere('V2 | celestial rose blue cabochon',(r*math.cos(t),r*math.sin(t),vault_z(r)-.004),(.024,.024,.008),blue_stone,'18')
curve('V2 | twelve-petal celestial rose',paths,.0055,gold_light,'18')
# A delicate running vine in the ceiling's dark lower band echoes the source mural borders.
for side in (0,1):
    for k in range(18):
        t=(k+.5)*math.pi/18+side*math.pi;paths=[]
        for sign in [-1,1]:
            pts=[]
            for j in range(33):
                u=j/32;ang=t+sign*.061*u;r=3.886-.04*math.sin(math.pi*u)
                pts.append((r*math.cos(ang),r*math.sin(ang),vault_z(r)-.009))
            paths.append(pts)
        curve('V2 | fresco border laurel stems',paths,.004,gold,'18')

# Punctuate the double doors with matching botanical relief parented to each hinge.
for hinge in [o for o in S.objects if o.name.startswith('Door hinge |')]:
    sign=-1 if 'left' in hinge.name else 1;a=3*math.pi/2
    before=set(S.objects)
    fern(a,sign*.408,1.00,1.12,.35,3.952,'14')
    rosette(a,sign*.408,3.946,.47,.108,'14')
    bpy.context.view_layer.update()
    for o in set(S.objects)-before:
        mw=o.matrix_world.copy();o.parent=hinge;o.matrix_world=mw

for ob in S.objects:
    if ob.type=='LIGHT':ob.visible_glossy=False;ob.visible_transmission=False
# Dedicated close-up camera makes the new relief easy to review.
camera('09 | V2 craftsmanship',(1.3,-1.95,2.62),(3.68,.55,3.38),37)
S.camera=bpy.data.objects['01 | Entrance interior']
S['version']='2.0 | reference-led architectural detailing'
S['v2_detail_notes']='Lobed acanthus capitals, turned profiles, botanical shelf arches, carved plinths, fern spandrels, running cornice ornament, caged opal lanterns, celestial zenith rose.'
S['v2_reference_priority']='multiview_2 LEFT window for tracery; upscaled_3eb8 and 70bf and a79a for joinery, capitals and botanical relief; conceptart1 for layered molding.'
S['clear_floor_radius_m']=2.9
# Update packed documentation, preserving the existing controls.
doc=bpy.data.texts.new('V2 · Reference-led detail additions')
doc.write('V2 preserves v1 scale, clear glazing, empty shelves, dome narrative, and meeting controls.\nNew editable detail collections: 14–18.\nThe GLB and web preview are derivatives; this .blend retains procedural shaders and editable ornament.\n')
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:im.pack()
S.render.resolution_x=1800;S.render.resolution_y=1440
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'XR_Guild_Library_v2.blend'),compress=True)
report={'version':2,'source':str(SOURCE/'XR_Guild_Library.blend'),'objects':len(S.objects),'new_detail_objects':sum(len(collections[c].objects) for c in ['14','15','16','17','18']),'width_m':8,'apex_m':6.2,'windows':6,'bookcases':5,'books':0,'new_collections':{c:len(collections[c].objects) for c in ['14','15','16','17','18']},'glass_transmission':glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value}
(ROOT/'evidence/v2_manifest.json').write_text(json.dumps(report,indent=2))
print('V2_BUILD_COMPLETE',json.dumps(report),flush=True)
