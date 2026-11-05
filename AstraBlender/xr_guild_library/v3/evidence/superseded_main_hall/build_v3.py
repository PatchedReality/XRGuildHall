"""Reference-sized V3. Reuse V2 craft, retaining human-scale fixtures."""
import ast, bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
V2=ROOT.parent/'v2'
reference=json.loads((V2/'evidence/reference_blend_measured_dimensions.json').read_text())
WIDTH=reference['hall_inside_width_m']; HEIGHT=reference['floor_top_to_apex_m']; R=WIDTH/2
DOME_BASE=reference['DomeDRAFT']['min'][2]-reference['Platform.001']['max'][2]
SX=WIDTH/8; DELTA=R-4
BOOK_X=2.1; BOOK_Z=4.2/4.247; BOOK_HEIGHT=4.2
bpy.ops.wm.open_mainfile(filepath=str(V2/'XR_Guild_Library_v2.blend'))
S=bpy.context.scene;S.frame_set(1)
collections={c.name[:2]:c for c in S.collection.children}
collections['11'].hide_viewport=False;collections['11'].hide_render=False
bpy.context.view_layer.update()
materials={'gold':'Gilt brass | gently aged','gold_light':'Polished gold leaf edges','wood':'Handcrafted figured walnut','wood_dark':'Walnut endgrain and recess','ivory':'Warm ivory limestone','green_stone':'Verde antique marble','glass':'Clear architectural glass | transparent, not frosted','wall':'Deep malachite green plaster','bronze':'Patinated bronze recesses'}
for key,name in materials.items():globals()[key]=bpy.data.materials[name]
font=next((f for f in bpy.data.fonts if 'Baskerville' in f.name),bpy.data.fonts.get('Bfont'))
module=ast.parse((ROOT.parent/'scripts/build_library.py').read_text())
names={'move','mesh','cube','cyl','curve','ring','sphere','bez','P','C','CV','arch','panel','txt','camera'}
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'geometry_helpers','exec'))
def zmap(z):
    # Human-height dados; reference dome spring and apex, measured above the floor.
    if z<=.55:return z
    if z<=4.88:return .55+(z-.55)*(DOME_BASE-.55)/(4.88-.55)
    return DOME_BASE+(z-4.88)*(HEIGHT-DOME_BASE)/1.32

def center(ob):
    if ob.type=='MESH':pts=[v.co for v in ob.data.vertices]
    elif ob.type=='CURVE':pts=[Vector(p.co[:3]) for s in ob.data.splines for p in s.points]
    else:return ob.matrix_world.translation.copy()
    if not pts:return ob.matrix_world.translation.copy()
    lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
    return ob.matrix_world@((lo+hi)/2)

def warp(ob,fn,bevel=1):
    mw=ob.matrix_world.copy()
    if ob.data.users>1:ob.data=ob.data.copy()
    if ob.type=='MESH':
        for v in ob.data.vertices:v.co=fn(mw@v.co)
        ob.data.update()
    elif ob.type=='CURVE':
        for spline in ob.data.splines:
            for p in spline.points:p.co=(*fn(mw@Vector(p.co[:3])),p.co[3])
            for p in spline.bezier_points:
                p.co=fn(mw@p.co);p.handle_left=fn(mw@p.handle_left);p.handle_right=fn(mw@p.handle_right)
        ob.data.bevel_depth*=bevel
    else:return
    ob.matrix_world=Matrix.Identity(4)
    for mod in ob.modifiers:
        if mod.type=='BEVEL':mod.width*=min(bevel,2)

original=list(S.objects);reused=0;removed=0
for ob in original:
    col=next((c.name[:2] for c in ob.users_collection),'')
    if ob.type in {'CAMERA','LIGHT'} or col=='13':
        bpy.data.objects.remove(ob,do_unlink=True);removed+=1;continue
    if ob.parent and ob.parent.name.startswith('Door hinge |'):continue
    if ob.name.startswith('Door hinge |'):
        ob.location.y-=DELTA;continue
    if col=='11':continue
    if col=='09':bpy.data.objects.remove(ob,do_unlink=True);removed+=1;continue
    if col=='04' and any(x in ob.name for x in ['empty shelf','empty side shelf','pencil edge','walnut partition']):
        bpy.data.objects.remove(ob,do_unlink=True);removed+=1;continue
    if col=='14' and any(x in ob.name for x in ['slender center stile','center hairline','carved arch head','gilt arch bead','botanical fan']):
        bpy.data.objects.remove(ob,do_unlink=True);removed+=1;continue
    if col=='12':
        if 'Library' in ob.name:ob.location.y+=DELTA
        elif 'Door' in ob.name:ob.location.y-=DELTA
        continue
    if col=='08':ob.location.y+=DELTA;continue
    if ob.type not in {'MESH','CURVE','FONT'}:continue
    c=center(ob);angle=round(math.atan2(c.y,c.x)/(math.pi/6))*math.pi/6
    bay=round(angle/(math.pi/6))%12
    bookcase=col=='04' or (col=='14' and bay in [1,3,5,7,11])
    if col=='17':
        # Lanterns attach to the enlarged columns; seats stay at normal height.
        if 'seat' in ob.name:
            angle=round(math.atan2(c.y,c.x)/(math.pi/6))*math.pi/6
            shift=Vector((DELTA*math.cos(angle),DELTA*math.sin(angle),0))
        else:
            angle=(round(math.atan2(c.y,c.x)/(math.pi/6)-.5)+.5)*math.pi/6
            shift=Vector((3.75*(SX-1)*math.cos(angle),3.75*(SX-1)*math.sin(angle),0))
        warp(ob,lambda p:p+shift);reused+=1;continue
    def transform(p):
        if bookcase:
            t=-math.sin(angle)*p.x+math.cos(angle)*p.y;r=math.cos(angle)*p.x+math.sin(angle)*p.y
            return Vector(P(angle,t*BOOK_X,r+DELTA,p.z*BOOK_Z))
        return Vector((p.x*SX,p.y*SX,p.z if col=='05' else zmap(p.z)))
    if ob.type=='FONT':
        mw=ob.matrix_world.copy();pos=transform(mw.translation)
        ob.matrix_world=Matrix.Diagonal((SX,SX,(DOME_BASE-.55)/4.33,1))@mw;ob.matrix_world.translation=pos
    else:warp(ob,transform,1.15 if bookcase else SX)
    reused+=1

# Full bookcases follow the accepted human-scale estimate from the room images.
# Three broad bays and eight tiers replace the rejected 26-by-8 grid.
count=0;pitch=.39; shelf_width=1.61*BOOK_X; n=3; cell=shelf_width/n
for bay in [1,3,5,7,11]:
    a=bay*math.pi/6
    C(f'V3 | bay {bay:02d} grounded bookcase plinth',a,0,R-.28,.08,1.87*BOOK_X,.51,.16,wood_dark,'04',.014)
    for k in range(1,n):
        x=-shelf_width/2+k*cell
        C(f'V3 | bay {bay:02d} shelf divider {k}',a,x,R-.29,2.015,.044,.42,3.09,wood,'04',.007)
        C(f'V3 | bay {bay:02d} divider gilt inlay {k}',a,x,R-.51,2.015,.007,.010,3.09,gold,'04',.002)
    for row in range(8):
        z=.47+row*pitch
        for k in range(n):
            x=-shelf_width/2+(k+.5)*cell
            if bay==3 and k==1 and .70<z<2.40:continue
            sh=C(f'V3 | bay {bay:02d} empty shelf {row:02d}-{k}',a,x,R-.27,z,cell-.022,.40,.044,wood,'04',.006)
            sh['purpose']='Empty shelf reserved for authors and resources'
            C(f'V3 | bay {bay:02d} shelf gilt edge {row:02d}-{k}',a,x,R-.479,z+.005,cell-.025,.009,.009,gold,'04',.002)
            count+=1
    for k in range(n):
        xc=-shelf_width/2+(k+.5)*cell;w=cell-.048
        archline=arch(w,3.18,3.35,3.61)
        CV(f'V3 | bay {bay:02d} carved arch head {k}',a,[[(x+xc,R-.493,z) for x,z in archline[2:]]],.021,wood,'04')
        CV(f'V3 | bay {bay:02d} gilt arch bead {k}',a,[[(x+xc,R-.517,z) for x,z in archline[2:]]],.0045,gold_light,'04')

# Rebuild the monumental portal around the retained human-scale moving doors.
a=3*math.pi/2;portal_w=1.65*SX;spring=zmap(2.64);top=zmap(3.60)
for w,depth,radius,ma in [(portal_w+.10,R-.05,.07,green_stone),(portal_w,R-.12,.025,gold)]:
    CV('V3 | monumental entrance archivolt',a,[[(x,depth,z) for x,z in arch(w,0,spring,top)]],radius,ma,'09',True)
side_w=(portal_w-1.65)/2
for sign in [-1,1]:
    C('V3 | entrance paneled side pier',a,sign*(.825+side_w/2),R+.10,1.82,side_w,.22,3.64,wood_dark,'09',.02)
    for j in range(3):
        xc=sign*(.825+side_w*(j+.5)/3)
        CV('V3 | entry panel gilt arch',a,[[(x+xc,R-.022,z) for x,z in arch(side_w/3-.12,.16,2.7,3.42)]],.011,gold,'09',True)
CV('V3 | human doorway arch',a,[[(x,R-.12,z) for x,z in arch(1.65,0,2.64,3.6)]],.022,gold,'09',True)
panel('V3 | human doorway fanlight',a,arch(1.63,2.48,2.64,3.6),R+.055,.012,glass,'09')
panel('V3 | tall portal clear transom',a,arch(portal_w,3.60,spring,top),R+.06,.012,glass,'09')
C('V3 | portal transom rail',a,0,R-.02,3.62,portal_w,.16,.10,wood,'09',.015)
for x in [-2.4,-1.6,-.8,0,.8,1.6,2.4]:
    CV('V3 | portal branching gilt',a,[bez([(x,R-.04,3.65),(x,R-.04,5.0),(x*.85,R-.04,spring-.3),(x*.55,R-.04,top-1.2)])],.017,gold,'09')

# Accessible gilded topic plaques repeat the overhead lettering at reading height.
labels=['ETHICS & RESPONSIBILITY','IMMERSIVE TECHNOLOGIES','RESEARCH & DISCOVERY','DESIGN & EXPERIENCE','THE XR GUILD COLLECTION']
for bay,label in zip([1,3,5,7,11],labels):
    a=bay*math.pi/6
    C('V3 | eye-level topic plaque',a,-1.19,R-.55,.275,.96,.055,.26,green_stone,'07',.025)
    txt('V3 | human-scale topic',label,a,-1.19,R-.589,.275,.045,gold_light,'07',.84)

# Prominent architectural callouts follow the large gilt headings in the references.
# Keep full subject names as secondary lettering, with large, readable bay titles.
headline=gold_light.copy();headline.name='V3 | high contrast architectural gold'
bs= headline.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.72,.48,.17,1)
bs.inputs['Metallic'].default_value=.40;bs.inputs['Roughness'].default_value=.42
bs.inputs['Emission Color'].default_value=(.45,.27,.06,1);bs.inputs['Emission Strength'].default_value=.16
short_titles=['AI ETHICS','IMMERSIVE RESEARCH','RESPONSIBILITY','XR INDUSTRY','NEUROTECHNOLOGY','MIND & PRIVACY','XR & WELLBEING','PRIVACY & POLICY','SECURITY & SAFETY']
for ob in list(S.objects):
    if ob.type!='FONT':continue
    if ob.name.startswith('Rotunda |'):
        ob.data.body=ob.data.body.split(' · ')[0];ob.data.size=.95;ob.scale=(1,1,1);ob.data.materials.clear();ob.data.materials.append(headline)
        ob.data.extrude=.006;ob.data.bevel_depth=.002
    elif ob.name.startswith('Frieze |'):
        ob.data.size=.65 if 'title' in ob.name else .40;ob.scale=(1,1,1)
        ob.data.materials.clear();ob.data.materials.append(headline)
for bay,title in zip([0,1,2,4,5,6,7,8,10],short_titles):
    a=bay*math.pi/6
    # Backing aligns with the existing frieze, leaving the glass fully clear.
    C('V3 | gold callout dark backing',a,0,R-.70,15.58,7.50,.065,1.10,green_stone,'07',.025)
    txt('V3 | large gold topic '+title,title,a,0,R-.742,15.71,.55,headline,'07',7.1)
    old=next((o for o in S.objects if o.type=='FONT' and o.name.startswith('Topic |') and abs((math.atan2(o.location.y,o.location.x)-a+math.pi)%math.tau-math.pi)<.02),None)
    if old:
        old.location.z=15.26;old.location.x,old.location.y,_=P(a,0,R-.75,0)
        old.data.size=.16;old.scale=(1,1,1);old.data.materials.clear();old.data.materials.append(headline)

# Large wall inscriptions sit above the human-scale cases, as in the room references.
for bay,title,subtitle in [(1,'IMMERSIVE RESEARCH','DISCOVER · EXPLORE · UNDERSTAND'),(3,'THE XR GUILD LIBRARY','RESOURCES · RESEARCH · COMMUNITY'),(5,'ETHICS & RESPONSIBILITY','IMAGINE · REFLECT · CARE'),(7,'MIND & EXPERIENCE','CREATE · CONNECT · BELONG'),(11,'PRIVACY & SAFETY','TRUST · RESPECT · PROTECT')]:
    a=bay*math.pi/6
    txt('V3 | bookcase wall heading '+title,title,a,0,R-.12,5.48,.55,headline,'07',6.20)
    txt('V3 | bookcase wall subtitle '+title,subtitle,a,0,R-.12,4.93,.22,headline,'07',5.80)
    CV('V3 | bookcase inscription arch',a,[[(x,R-.11,z) for x,z in arch(6.35,4.63,5.57,6.46)[2:]]],.012,gold,'07')

# Raised lettering keeps its front face clear of the wall in real-time depth buffers.
for ob in S.objects:
    if ob.type=='FONT' and headline in ob.data.materials[:]:
        ob.data.extrude=.018;ob.data.bevel_depth=.002;ob.data.bevel_resolution=1

# Reference palette: walnut and dark warm panels dominate; green is an accent.
charcoal=bpy.data.materials.new('V3 | warm charcoal architectural panels');charcoal.use_nodes=True
b=charcoal.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.026,.018,.013,1);b.inputs['Roughness'].default_value=.78
for ob in S.objects:
    if ob.type not in {'MESH','CURVE','FONT'}:continue
    col=next((c.name[:2] for c in ob.users_collection),'')
    for i,ma in enumerate(ob.data.materials):
        if ma==wall:ob.data.materials[i]=charcoal
        elif ma==green_stone and ('cornice' in ob.name.lower() or 'gold callout dark backing' in ob.name):ob.data.materials[i]=wood_dark if 'cornice' in ob.name.lower() else charcoal
for name,color in [('Forest green damask backing',(.036,.019,.010,1)),('Silk fern damask',(.10,.064,.026,1))]:
    ma=bpy.data.materials.get(name)
    if ma:
        b=ma.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=color
fresco=bpy.data.objects['Rotunda | painted interior vault'].data.materials[0]
for n in fresco.node_tree.nodes:
    if n.type=='MAP_RANGE':n.inputs['From Min'].default_value=.045;n.inputs['From Max'].default_value=.12
    if n.type=='MIX_RGB':n.inputs[1].default_value=(.012,.016,.029,1)
S['v3_palette']='Warm walnut, charcoal umber architectural fields, gilt, pale stone moldings. Green retained mainly in labradorite columns and stone inlay. Painted dome extends closer to zenith.'

# Lights and cameras for the enlarged hall; camera eye height is not scaled.
def area(name,location,target,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    ob=bpy.data.objects.new(name,d);collections['10'].objects.link(ob);ob.location=location;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.visible_glossy=False;ob.visible_transmission=False
for i in range(6):
    a=i*math.pi/3
    area(f'V3 | window daylight {i}',P(a,0,R-.20,7.0),(0,0,3.0),1800,5.0,(.73,.88,1))
area('V3 | rotunda warm fill',(0,0,10),(0,0,HEIGHT),1600,12,(1,.86,.65))
area('V3 | room diffuse fill',(0,-5,12),(0,4,0),1800,15,(1,.87,.72))
camera('01 | Entrance interior',(0,-14.6,1.7),(0,7,8.5),19)
camera('02 | Window and bookcase',(10,-7,1.7),(R,0,5),22)
camera('03 | Library interface',(.3,R-2.6,1.7),(0,R-.6,1.65),28)
camera('04 | Fresco',(0,0,1.7),(0,0,HEIGHT),15)
camera('05 | Meeting entrance',(0,-11.0,1.7),(0,-R,3.2),24)
plan=camera('06 | Plan',(0,0,45),(0,0,0),35);plan.data.type='ORTHO';plan.data.ortho_scale=39
camera('07 | Elevated interior',(-8,-10,7),(0,3,8),20)
camera('09 | V3 craftsmanship',(7,12,1.7),(7.7,13.5,4.5),24)
S.camera=bpy.data.objects['01 | Entrance interior']
collections['11'].hide_viewport=True;collections['11'].hide_render=True
S['version']='3.0 | reference Blender hall scale';S['width_m']=WIDTH;S['apex_m']=HEIGHT;S['dome_spring_m']=DOME_BASE;S['clear_floor_radius_m']=14.9
S['specification']=f'12 sides | {WIDTH:.2f} m interior width | {HEIGHT:.2f} m floor-to-apex | human-scale fixtures'
S['reference_policy']='Dimensions measured from Area1-Blockout2 in GuildHall-3DModels1.blend. V2 artwork and modeled ornament reused; reference geometry not imported.'
S['shelf_pitch_m']=pitch;S['bookcase_height_m']=BOOK_HEIGHT;S['bookcase_width_m']=1.92*BOOK_X;S['shelf_rows']=8;S['shelf_bays']=3
floor=bpy.data.objects['Twelve-sided foundation | 8 m across flats'];floor.name='Twelve-sided foundation | reference width';floor['inside_width_m']=WIDTH
for t in list(bpy.data.texts):
    if 'control' in t.name.lower():t.clear();t.write((ROOT/'scripts/library_controls.py').read_text())
doc=bpy.data.texts.new('V3 | scale and reuse');doc.write(S['specification']+'\n'+S['reference_policy']+'\nDoor leaves, furniture, reachable interface and benches retain V2 human dimensions.\n')
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:image.pack()
bpy.context.view_layer.update()
S.render.resolution_x=1600;S.render.resolution_y=1100;S.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'XR_Guild_Library_v3.blend'),compress=True)
report={'width_m':WIDTH,'apex_m':HEIGHT,'dome_spring_m':DOME_BASE,'reference':'GuildHall-3DModels1.blend / Area1-Blockout2','reused_detail_objects':reused,'new_empty_shelves':count,'objects':len(S.objects),'shelf_pitch_m':pitch,'bookcase_height_m':BOOK_HEIGHT,'bookcase_width_m':1.92*BOOK_X,'shelf_rows':8,'shelf_bays':3,'door_leaf_height_m':2.48,'table_diameter_m':2.26,'eye_height_m':1.7,'source_v2_unchanged':True}
(ROOT/'evidence/build_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('V3_BUILD_COMPLETE',json.dumps(report),flush=True)
