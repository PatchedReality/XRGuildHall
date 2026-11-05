"""Apply V3 aesthetics directly to V2, preserving the original library dimensions."""
import ast,bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; V2=ROOT.parent/'v2'
bpy.ops.wm.open_mainfile(filepath=str(V2/'XR_Guild_Library_v2.blend'))
S=bpy.context.scene;S.frame_set(1)
collections={c.name[:2]:c for c in S.collection.children}
WIDTH=8.0;HEIGHT=6.2;DOME_BASE=4.88
original_count=len(S.objects)
materials={'gold':'Gilt brass | gently aged','gold_light':'Polished gold leaf edges','wood':'Handcrafted figured walnut','wood_dark':'Walnut endgrain and recess','ivory':'Warm ivory limestone','green_stone':'Verde antique marble','wall':'Deep malachite green plaster'}
for key,name in materials.items():globals()[key]=bpy.data.materials[name]
font=next((f for f in bpy.data.fonts if 'Baskerville' in f.name),bpy.data.fonts.get('Bfont'))
module=ast.parse((ROOT.parent/'scripts/build_library.py').read_text())
names={'move','mesh','cube','cyl','curve','bez','P','C','CV','arch','txt'}
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'geometry_helpers','exec'))

# Keep the tall V2 cases, eight shelf tiers and two broad bays. The north case
# retains its wide human-height screen opening. Ground the existing base panels.
for bay in [1,3,5,7,11]:
    C(f'V3 | bookcase {bay:02d} grounded plinth',bay*math.pi/6,0,3.72,.08,1.87,.51,.16,wood_dark,'04',.014)

# Warm architectural fields, walnut joinery and pale stone; labradorite remains
# the principal green accent. Reuse every existing carving and clear window.
charcoal=bpy.data.materials.new('V3 | warm charcoal architectural panels');charcoal.use_nodes=True
b=charcoal.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.026,.018,.013,1);b.inputs['Roughness'].default_value=.78
for ob in S.objects:
    if ob.type not in {'MESH','CURVE','FONT'}:continue
    for i,ma in enumerate(ob.data.materials):
        if ma==wall:ob.data.materials[i]=charcoal
        elif ma==green_stone and 'cornice' in ob.name.lower():ob.data.materials[i]=wood_dark
for name,color in [('Forest green damask backing',(.036,.019,.010,1)),('Silk fern damask',(.10,.064,.026,1))]:
    ma=bpy.data.materials.get(name)
    if ma:ma.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=color
fresco=bpy.data.objects['Rotunda | painted interior vault'].data.materials[0]
for node in fresco.node_tree.nodes:
    if node.type=='MAP_RANGE':node.inputs['From Min'].default_value=.045;node.inputs['From Max'].default_value=.12
    if node.type=='MIX_RGB':node.inputs[1].default_value=(.012,.016,.029,1)

# Solid raised gold faces avoid thin, faceted real-time lettering. Short titles
# are architectural callouts; original full topics/URLs remain object metadata
# and are readable in the walkthrough's inscriptions panel.
headline=gold_light.copy();headline.name='V3 | high contrast architectural gold'
b=headline.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(.72,.48,.17,1)
b.inputs['Metallic'].default_value=.40;b.inputs['Roughness'].default_value=.42
b.inputs['Emission Color'].default_value=(.45,.27,.06,1);b.inputs['Emission Strength'].default_value=.16
short_titles={0:'AI ETHICS',1:'IMMERSIVE RESEARCH',2:'RESPONSIBILITY',4:'XR INDUSTRY',5:'NEUROTECHNOLOGY',6:'MIND & PRIVACY',7:'XR & WELLBEING',8:'PRIVACY & POLICY',10:'SECURITY & SAFETY'}
def letter_style(ob,size,width):
    ob.data.size=size;ob.scale=(1,1,1);ob.data.space_character=1.08
    ob.data.materials.clear();ob.data.materials.append(headline)
    ob.data.extrude=.003;ob.data.bevel_depth=.0006;ob.data.bevel_resolution=1
    bpy.context.view_layer.update()
    w=max(v[0] for v in ob.bound_box)-min(v[0] for v in ob.bound_box)
    if w>width:ob.scale=(width/w,)*3
for ob in list(S.objects):
    if ob.type!='FONT':continue
    if ob.name.startswith('Topic |'):
        bay=round(math.atan2(ob.location.y,ob.location.x)/(math.pi/6))%12
        ob.data.body=short_titles[bay];ob.name='V3 | large gold topic '+short_titles[bay]
        letter_style(ob,.155,1.89)
    elif ob.name.startswith('Rotunda |'):
        ob.data.body=ob.data.body.split(' · ')[0];letter_style(ob,.22,1.80)
    elif ob.name.startswith('Frieze |'):
        ob.data.body={'Frieze | library title':'XR GUILD LIBRARY','Frieze | gathering':'THINK TOGETHER','Frieze | collection':'IMAGINATION & CARE'}[ob.name]
        letter_style(ob,.15,1.89)
    elif ob.name.startswith('Door |') or ob.name=='Library interface | carved lintel':
        letter_style(ob,ob.data.size,1.60)
for bay,title in [(1,'IMMERSIVE RESEARCH'),(3,'THE XR GUILD LIBRARY'),(5,'ETHICS & RESPONSIBILITY'),(7,'MIND & EXPERIENCE'),(11,'PRIVACY & SAFETY')]:
    ob=txt('V3 | bookcase wall heading '+title,title,bay*math.pi/6,0,3.90,4.34,.155,headline,'07',1.54)
    letter_style(ob,.155,1.54)

# Preserve V2 lighting and cameras, keeping all walking views at eye height.
for name in ['03 | Library interface','04 | Fresco','09 | V2 craftsmanship']:
    ob=bpy.data.objects[name];ob.location.z=1.7
    target={'03 | Library interface':(0,3.6,1.60),'04 | Fresco':(0,0,6.2),'09 | V2 craftsmanship':(3.68,.55,3.38)}[name]
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['09 | V2 craftsmanship'].name='09 | V3 craftsmanship'
S.camera=bpy.data.objects['01 | Entrance interior']
collections['11'].hide_viewport=True;collections['11'].hide_render=True
S['version']='3.0 | original library scale, revised aesthetics'
S['width_m']=WIDTH;S['apex_m']=HEIGHT;S['dome_spring_m']=DOME_BASE;S['clear_floor_radius_m']=2.7
S['specification']='12 sides | 8.0 m interior width | 6.2 m apex | six clear windows | five empty cases | closable doors'
S['reference_policy']='Use original library brief and V2 dimensions. Area1-Blockout2 is a separate main hall and does not set this library scale. Multiview references inform window gilt only.'
S['v3_palette']='Warm walnut and charcoal umber fields, gilt, pale stone; green concentrated in labradorite columns and inlaid stone; fresco extends toward zenith.'
S['shelf_pitch_m']=.4;S['bookcase_height_m']=4.247;S['bookcase_width_m']=1.92;S['shelf_rows']=8;S['shelf_bays']=2
for t in list(bpy.data.texts):
    if 'control' in t.name.lower():t.clear();t.write((ROOT/'scripts/library_controls.py').read_text())
doc=bpy.data.texts.new('V3 | scale and reuse');doc.write(S['specification']+'\n'+S['reference_policy']+'\n'+S['v3_palette']+'\n')
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:im.pack()
bpy.context.view_layer.update()
S.render.resolution_x=1600;S.render.resolution_y=1100;S.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'XR_Guild_Library_v3.blend'),compress=True)
shelves=[o for o in collections['04'].objects if 'empty shelf' in o.name or 'empty side shelf' in o.name]
report={'width_m':WIDTH,'apex_m':HEIGHT,'dome_spring_m':DOME_BASE,'reference':'Original library brief / V2','reused_v2_objects':original_count,'new_objects':len(S.objects)-original_count,'empty_shelf_meshes':len(shelves),'objects':len(S.objects),'shelf_pitch_m':.4,'bookcase_height_m':4.247,'bookcase_width_m':1.92,'shelf_rows':8,'shelf_bays':2,'door_leaf_height_m':2.48,'table_diameter_m':2.26,'eye_height_m':1.7,'source_v2_unchanged':True}
(ROOT/'evidence/build_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('V3_BUILD_COMPLETE',json.dumps(report),flush=True)
