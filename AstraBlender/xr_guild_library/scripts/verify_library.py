"""Read-only scene verification, including the evaluated door motion."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
S=bpy.context.scene
report={}
report['blender_version']=bpy.app.version_string
report['object_count']=len(S.objects)
report['units']=S.unit_settings.system
report['scale_length']=S.unit_settings.scale_length
report['windows']=len([o for o in S.objects if o.name.startswith('Window ') and 'clear glass glazing' in o.name])
gl=bpy.data.materials['Clear architectural glass | transparent, not frosted'].node_tree.nodes['Principled BSDF']
report['glass']={'transmission':gl.inputs['Transmission Weight'].default_value,'roughness':gl.inputs['Roughness'].default_value,'emission':gl.inputs['Emission Strength'].default_value}
report['bookcases']=len([o for o in S.objects if 'wallpaper backing' in o.name])
report['base_floor_dimensions']=list(bpy.data.objects['Twelve-sided foundation | 8 m across flats'].dimensions)
report['ceiling_apex']=max(v.co.z for v in bpy.data.objects['Rotunda | painted interior vault'].data.vertices)
report['packed_images']=[{'name':i.name,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images if i.source=='FILE']
report['optional_furniture_hidden']=bpy.data.collections['11 Optional meeting furniture'].hide_render
report['shelf_objects']=len([o for o in S.objects if '| empty shelf' in o.name or '| empty side shelf' in o.name])
report['library_url']=bpy.data.objects['Library interface | interactive display']['url']
report['topic_labels']=len([o for o in S.objects if o.name.startswith('Topic |')])
report['all_text_faces_room']=all((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(Vector((-o.location.x,-o.location.y,0)).normalized())>.99 for o in S.objects if o.type=='FONT')
report['fresco_caption_count']=len([o for o in S.objects if o.type=='FONT' and o.name.startswith('Rotunda |')])
report['door_states']={}
for f in [1,72,168]:
    S.frame_set(f);bpy.context.view_layer.update()
    report['door_states'][str(f)]={'opening':S['door_open'],'hinges_degrees':{},'leaf_world_bounds':{}}
    for o in S.objects:
        if o.name.startswith('Door hinge |'):
            report['door_states'][str(f)]['hinges_degrees'][o.name]=math.degrees(o.rotation_euler.z)
        if o.name.startswith('Door leaf |'):
            vs=[o.matrix_world @ Vector(c) for c in o.bound_box]
            report['door_states'][str(f)]['leaf_world_bounds'][o.name]=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
assert report['windows']==6
assert report['glass']['transmission']==1
assert report['glass']['roughness']<.02
assert report['glass']['emission']==0
assert report['bookcases']==5
assert report['topic_labels']==9
assert report['all_text_faces_room']
assert report['fresco_caption_count']==6
assert report['library_url']=='https://library.xrguild.org/'
assert abs(report['ceiling_apex']-6.2)<.001
assert all(i['packed'] for i in report['packed_images'])
assert all(abs(v)<1e-6 for v in report['door_states']['1']['hinges_degrees'].values())
assert all(abs(abs(v)-100)<.01 for v in report['door_states']['72']['hinges_degrees'].values())
# Open leaves must lie outside the south wall, not intrude into the meeting area.
assert all(b[1][1]<-3.97 for b in report['door_states']['72']['leaf_world_bounds'].values())
# Optional sidebar registers and can toggle furnishing and doors without errors.
ns={'__name__':'__main__'}
exec((ROOT/'scripts/library_controls.py').read_text(),ns)
bpy.ops.xrguild.toggle_furniture()
assert not bpy.data.collections['11 Optional meeting furniture'].hide_render
bpy.ops.xrguild.toggle_furniture()
assert bpy.data.collections['11 Optional meeting furniture'].hide_render
bpy.ops.xrguild.toggle_door()
assert S.frame_current==72
bpy.ops.xrguild.toggle_door()
assert S.frame_current==1
report['controls_verified']=['registration','toggle_furniture','toggle_door']
report['url_opener']='Operator registered; external browser launch intentionally not invoked by verification.'
report['status']='PASS'
(ROOT/'evidence/verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
