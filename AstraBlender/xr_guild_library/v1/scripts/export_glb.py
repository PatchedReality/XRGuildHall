"""Build a compact GLB derivative with baked procedural color textures.
The editable Blender source is never modified. Curves/text are tessellated only
in this export scene; static pieces are joined by material to reduce draw calls.
"""
import bpy, math, json, re, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web_preview/public/assets';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'XR_Guild_Library.blend'))
source=bpy.context.scene;source.frame_set(1)
WIDTH=float(bpy.data.objects['Twelve-sided foundation | 8 m across flats']['inside_width_m'])
_vault=bpy.data.objects['Rotunda | painted interior vault']
APEX=max((_vault.matrix_world @ v.co).z for v in _vault.data.vertices)
source_collections={o.name:next((c.name[:2] for c in o.users_collection),'') for o in source.objects}
source.objects.update() if hasattr(source.objects,'update') else None
original_materials=list(bpy.data.materials)
texture_dir=ROOT/'textures';texture_dir.mkdir(exist_ok=True)
# Bake materials on a canonical box: Generated coordinates are normalized per
# object in the source, so each mesh can reuse the same six-face material atlas.
def box_uv(o):
    me=o.data
    uv=me.uv_layers.get('PBR') or me.uv_layers.new(name='PBR')
    lo=Vector([min(v.co[k] for v in me.vertices) for k in range(3)])
    hi=Vector([max(v.co[k] for v in me.vertices) for k in range(3)])
    size=hi-lo
    for p in me.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));side=int(p.normal[axis]>=0);tile=axis*2+side
        axes=[k for k in range(3) if k!=axis]
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            u=(co[axes[0]]-lo[axes[0]])/max(size[axes[0]],1e-6)
            v=(co[axes[1]]-lo[axes[1]])/max(size[axes[1]],1e-6)
            uv.data[li].uv=((tile%3+.012+.976*u)/3,(tile//3+.012+.976*v)/2)
    me.uv_layers.active=uv;uv.active_render=True

def cylinder_uv(o):
    me=o.data;uv=me.uv_layers.get('PBR') or me.uv_layers.new(name='PBR')
    lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices)
    cx=(max(v.co.x for v in me.vertices)+min(v.co.x for v in me.vertices))/2
    cy=(max(v.co.y for v in me.vertices)+min(v.co.y for v in me.vertices))/2
    for p in me.polygons:
        vals=[]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co;vals.append(((math.atan2(v.y-cy,v.x-cx)/math.tau)%1,(v.z-lo)/max(hi-lo,1e-6)))
        seam=max(x for x,y in vals)-min(x for x,y in vals)>.5
        for li,(u,v) in zip(p.loop_indices,vals):uv.data[li].uv=(u+(1 if seam and u<.5 else 0),.01+.98*v)
    me.uv_layers.active=uv;uv.active_render=True

bake_scene=bpy.data.scenes.new('PBR texture baking');bpy.context.window.scene=bake_scene
bake_scene.render.engine='CYCLES';bake_scene.cycles.samples=1
bake_scene.render.bake.margin=4
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    bake_scene.cycles.device='GPU'
except Exception:bake_scene.cycles.device='CPU'
bake_scene.view_settings.view_transform='Standard'
replacement={};mapping={};bake_report=[]
def pbr_copy(ma,image=None):
    new=bpy.data.materials.new(ma.name+' | glTF PBR');new.use_nodes=True
    n,l=new.node_tree.nodes,new.node_tree.links;b=n['Principled BSDF'];old=ma.node_tree.nodes.get('Principled BSDF')
    if old:
        for key in ['Base Color','Metallic','Roughness','IOR','Transmission Weight','Coat Weight','Coat Roughness','Emission Color','Emission Strength','Alpha']:
            b.inputs[key].default_value=old.inputs[key].default_value
    if image:
        tex=n.new('ShaderNodeTexImage');tex.image=image;l.new(tex.outputs['Color'],b.inputs['Base Color'])
        if ma.name.startswith('Fresco'):
            l.new(tex.outputs['Color'],b.inputs['Emission Color'])
    new.diffuse_color=b.inputs['Base Color'].default_value
    new.use_backface_culling=False
    return new

def fresh_bake(o,ma,size,filename):
    work=ma.copy();o.data.materials.clear();o.data.materials.append(work)
    n,l=work.node_tree.nodes,work.node_tree.links;b=n.get('Principled BSDF');out=n.get('Material Output')
    emit=n.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=1
    if b.inputs['Base Color'].is_linked:l.new(b.inputs['Base Color'].links[0].from_socket,emit.inputs['Color'])
    else:emit.inputs['Color'].default_value=b.inputs['Base Color'].default_value
    l.new(emit.outputs[0],out.inputs['Surface'])
    im=bpy.data.images.new(filename,width=size[0],height=size[1],alpha=False)
    im.colorspace_settings.name='sRGB';target=n.new('ShaderNodeTexImage');target.image=im;n.active=target
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.bake(type='EMIT')
    im.filepath_raw=str(texture_dir/(filename+'.png'));im.file_format='PNG';im.save();im.pack()
    bpy.data.objects.remove(o,do_unlink=True);bpy.data.materials.remove(work)
    return im


def emit_bake(o,ma,size,filename):
    return fresh_bake(o,ma,size,filename)

for ma in original_materials:
    if ma.name.startswith('Exterior'):continue
    old=ma.node_tree.nodes.get('Principled BSDF') if ma.use_nodes else None
    if not old:continue
    if ma.name.startswith('Fresco') or ma.name.startswith('Mandala'):
        continue
    linked=old.inputs['Base Color'].is_linked
    should_bake=linked and not any(s in ma.name.lower() for s in ['brass','gilt','gold'])
    if should_bake:
        kind='cylinder' if ma.name.startswith('Labradorite') else 'box'
        if kind=='cylinder':
            bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.5,depth=1);o=bpy.context.object;cylinder_uv(o);size=(1536,3072)
        else:
            bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;box_uv(o);size=(1536,1024)
        print('BAKING',ma.name,flush=True)
        filename=re.sub(r'[^a-z0-9]+','_',ma.name.lower()).strip('_')
        im=emit_bake(o,ma,size,filename)
        replacement[ma.name]=pbr_copy(ma,im);mapping[ma.name]=kind
        bake_report.append({'material':ma.name,'texture':filename+'.png','size':size})
    else:replacement[ma.name]=pbr_copy(ma)

# Floor uses its original symmetric UV map and packed image directly.
ma=next(m for m in original_materials if m.name.startswith('Mandala | veined'))
im=next(n.image for n in ma.node_tree.nodes if n.type=='TEX_IMAGE')
replacement[ma.name]=pbr_copy(ma,im)
# Bake the actual fresco, including its radial transition at the zenith.
original=bpy.data.objects['Rotunda | painted interior vault'];ma=original.data.materials[0]
o=bpy.data.objects.new('Fresco bake',original.data.copy());bake_scene.collection.objects.link(o)
o.matrix_world=original.matrix_world
work=ma.copy();o.data.materials.clear();o.data.materials.append(work)
for n in list(work.node_tree.nodes):
    if n.type=='TEX_IMAGE':
        uvn=work.node_tree.nodes.new('ShaderNodeUVMap');uvn.uv_map=o.data.uv_layers.active.name;work.node_tree.links.new(uvn.outputs[0],n.inputs['Vector'])
uv=o.data.uv_layers.new(name='PBR fresco planar')
for li,loop in enumerate(o.data.loops):
    v=o.data.vertices[loop.vertex_index].co;uv.data[li].uv=(.5+v.x/(8.1*(WIDTH/8)),.5+v.y/(8.1*(WIDTH/8)))
o.data.uv_layers.active=uv;uv.active_render=True
print('BAKING Fresco planar atlas',flush=True)
im=emit_bake(o,work,(3072,3072),'fresco_baked')
replacement[ma.name]=pbr_copy(ma,im);mapping[ma.name]='fresco'
bake_report.append({'material':ma.name,'texture':'fresco_baked.png','size':[3072,3072]})

# Evaluate all editable details into a clean export scene.
bpy.context.window.scene=source
furniture=bpy.data.collections['11 Optional meeting furniture'];furniture.hide_viewport=False;furniture.hide_render=False
bpy.context.view_layer.update()
# Curves are small relief; reducing bevel tessellation preserves their outlines.
for ob in source.objects:
    if ob.type=='CURVE':ob.data.bevel_resolution=min(ob.data.bevel_resolution,1)
    if ob.type=='FONT':ob.data.resolution_u=4;ob.data.bevel_depth=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
export_scene=bpy.data.scenes.new('XR Guild Library v1 | GLB')
groups={};empties={}
for label in ['Architecture','Optional_Meeting_Furniture','Door_Left','Door_Right','Interface']:
    e=bpy.data.objects.new(label,None);export_scene.collection.objects.link(e);empties[label]=e
    if label=='Optional_Meeting_Furniture':e['optional_furniture']=True
for side,sign in [('Left',-1),('Right',1)]:
    old=bpy.data.objects['Door hinge | '+side.lower()];e=empties['Door_'+side];e.matrix_world=old.matrix_world;e['door_hinge']=side.lower();e['open_angle_degrees']=sign*100
empties['Interface']['url']='https://library.xrguild.org/'
object_count=0
for ob in list(source.objects):
    col=source_collections[ob.name]
    if ob.type not in {'MESH','CURVE','FONT'} or col in {'10','12','13'}:continue
    group='Optional_Meeting_Furniture' if col=='11' else 'Architecture'
    if col=='08':group='Interface'
    if ob.parent and ob.parent.name.startswith('Door hinge |'):group='Door_Left' if 'left' in ob.parent.name else 'Door_Right'
    evaluated=ob.evaluated_get(dg)
    me=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg)
    if not me.vertices or not me.materials:bpy.data.meshes.remove(me);continue
    new=bpy.data.objects.new(ob.name,me);export_scene.collection.objects.link(new);new.matrix_world=ob.matrix_world
    new['flat_lettering']=ob.type=='FONT'
    ma=me.materials[0];kind=mapping.get(ma.name)
    if kind=='box':box_uv(new)
    elif kind=='cylinder':cylinder_uv(new)
    elif kind=='fresco':
        uv=me.uv_layers.new(name='PBR fresco planar')
        for li,loop in enumerate(me.loops):
            v=me.vertices[loop.vertex_index].co;uv.data[li].uv=(.5+v.x/(8.1*(WIDTH/8)),.5+v.y/(8.1*(WIDTH/8)))
        me.uv_layers.active=uv;uv.active_render=True
    # Remove unused UV maps so the GLB doesn't carry duplicate attributes.
    if me.uv_layers:
        active=me.uv_layers.active.name
        for uvold in list(me.uv_layers):
            if uvold.name!=active:me.uv_layers.remove(uvold)
    material_name=ma.name
    for slot in range(len(me.materials)):
        me.materials[slot]=replacement.get(me.materials[slot].name,me.materials[slot])
    groups.setdefault((group,material_name),[]).append(new);object_count+=1
    if object_count%500==0:print('CONVERTED',object_count,flush=True)

bpy.context.window.scene=export_scene
def combine(objects,name):
    # Build one world-space mesh directly. Operator selection/join repeatedly
    # reevaluates thousands of detailed objects and is needlessly expensive.
    nv=sum(len(o.data.vertices) for o in objects);nl=sum(len(o.data.loops) for o in objects);nf=sum(len(o.data.polygons) for o in objects)
    verts=np.empty((nv,3),dtype=np.float32);loops=np.empty(nl,dtype=np.int32)
    starts=np.empty(nf,dtype=np.int32);totals=np.empty(nf,dtype=np.int32);smooth=np.empty(nf,dtype=np.bool_)
    uv=np.zeros((nl,2),dtype=np.float32);normals=np.empty((nl,3),dtype=np.float32)
    vi=li=fi=0
    for ob in objects:
        me=ob.data;v=len(me.vertices);l=len(me.loops);f=len(me.polygons)
        co=np.empty((v,3),dtype=np.float32);me.vertices.foreach_get('co',co.ravel())
        matrix=np.array(ob.matrix_world,dtype=np.float32);verts[vi:vi+v]=co@matrix[:3,:3].T+matrix[:3,3]
        ix=np.empty(l,dtype=np.int32);me.loops.foreach_get('vertex_index',ix);loops[li:li+l]=ix+vi
        ps=np.empty(f,dtype=np.int32);me.polygons.foreach_get('loop_start',ps);starts[fi:fi+f]=ps+li
        pt=np.empty(f,dtype=np.int32);me.polygons.foreach_get('loop_total',pt);totals[fi:fi+f]=pt
        sm=np.empty(f,dtype=np.bool_);me.polygons.foreach_get('use_smooth',sm);smooth[fi:fi+f]=sm
        if me.uv_layers.active:
            temp=np.empty((l,2),dtype=np.float32);me.uv_layers.active.data.foreach_get('uv',temp.ravel());uv[li:li+l]=temp
        ns=np.empty((l,3),dtype=np.float32)
        if ob.get('flat_lettering'):
            face_normals=np.empty((f,3),dtype=np.float32);me.polygons.foreach_get('normal',face_normals.ravel())
            ns=np.repeat(face_normals,pt,axis=0);smooth[fi:fi+f]=False
        else:me.corner_normals.foreach_get('vector',ns.ravel())
        ns=ns@np.linalg.inv(matrix[:3,:3]);ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-8);normals[li:li+l]=ns
        vi+=v;li+=l;fi+=f
    me=bpy.data.meshes.new(name);me.vertices.add(nv);me.vertices.foreach_set('co',verts.ravel());me.loops.add(nl);me.loops.foreach_set('vertex_index',loops)
    me.polygons.add(nf);me.polygons.foreach_set('loop_start',starts);me.polygons.foreach_set('loop_total',totals);me.polygons.foreach_set('use_smooth',smooth)
    me.update(calc_edges=True)
    layer=me.uv_layers.new(name='PBR');layer.data.foreach_set('uv',uv.ravel())
    me.normals_split_custom_set(normals.tolist());me.materials.append(objects[0].data.materials[0])
    joined=bpy.data.objects.new(name,me);export_scene.collection.objects.link(joined)
    bpy.data.batch_remove(ids=objects)
    return joined
for (group,material),objects in groups.items():
    print('MERGING',group,material,len(objects),flush=True)
    o=combine(objects,group+' | '+material)
    mw=o.matrix_world.copy();o.parent=empties[group];o.matrix_world=mw
export_scene.unit_settings.system='METRIC';export_scene['width_m']=WIDTH;export_scene['apex_m']=APEX
bpy.ops.object.select_all(action='SELECT')
path=OUT/'XR_Guild_Library_v1.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=False,use_active_scene=True,export_apply=False,export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_texcoords=True,export_normals=True)
triangles=sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in export_scene.objects if ob.type=='MESH')
report={'file':str(path),'bytes':path.stat().st_size,'triangles':triangles,'mesh_count':len(groups),'source_objects_converted':object_count,'width_m':WIDTH,'apex_m':APEX,'baked_materials':bake_report,'glass_transmission':1,'geometry_note':'Curves and type tessellated, static parts joined by material; original V1 source untouched.'}
(ROOT/'evidence/glb_manifest.json').write_text(json.dumps(report,indent=2))
print('GLB_EXPORT_COMPLETE',json.dumps(report),flush=True)
