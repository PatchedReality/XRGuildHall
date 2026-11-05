import bpy,json,statistics
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'GuildHall-3DModels1.blend'))
s=bpy.context.scene;bpy.context.view_layer.update()
def bounds(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
people=[{'name':o.name,'bounds':bounds(o),'scale':list(o.scale),'collections':[c.name for c in o.users_collection]} for o in bpy.data.objects if o.type=='MESH' and 'human' in o.name.lower()]
collection_report=[]
for c in bpy.data.collections:
 collection_report.append({'name':c.name,'children':[ch.name for ch in c.children],'direct_objects':[o.name for o in c.objects],'hidden_viewport':c.hide_viewport,'hidden_render':c.hide_render})
items={o.name:{**bounds(o),'scale':list(o.scale),'collections':[c.name for c in o.users_collection]} for o in bpy.data.objects if o.type=='MESH' and o.name in ['Bay Wall','Bay Wall.006','Dome','DomeDRAFT','Platform','Platform.001','Column','Column.012','Window Cutter','Stage-REDO-size11-98m','Stage.001']}
heights=[p['bounds']['size'][2] for p in people]
report={'source':str(ROOT/'GuildHall-3DModels1.blend'),'unit_system':s.unit_settings.system,'metres_per_unit':s.unit_settings.scale_length,'people_count':len(people),'human_height_range_m':[min(heights),max(heights)],'human_height_median_m':statistics.median(heights),'sample_people':[next(p for p in people if p['name'].startswith(prefix)) for prefix in ['5ft human','6ft human']],'named_5ft_m':5*.3048,'architecture':items,'spawn_world':list(bpy.data.objects['VR_Spawn_Entrance'].matrix_world.translation),'collections':collection_report,'view_layer_collections':[{'name':c.name,'excluded':c.exclude} for c in bpy.context.view_layer.layer_collection.children]}
(ROOT/'xr_guild_library/v3/evidence/reference_human_scale_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['collections','architecture']},indent=2))
for name,x in items.items():print(name,x)
for c in collection_report:
 if 'Blockout' in c['name'] or 'People' in c['name']:print(c)
