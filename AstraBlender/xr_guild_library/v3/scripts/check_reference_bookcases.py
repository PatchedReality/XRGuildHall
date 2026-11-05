import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
bpy.ops.wm.open_mainfile(filepath=str(root/'GuildHall-3DModels1.blend'))
report={'source':'GuildHall-3DModels1.blend','scenes':[s.name for s in bpy.data.scenes],'collections':[c.name for c in bpy.data.collections],'total_objects':len(bpy.data.objects),'named_shelf_objects':[o.name for o in bpy.data.objects if any(w in o.name.lower() for w in ['book','shelf','shelv','library'])],'non_human_meshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in bpy.data.objects if o.type=='MESH' and 'human' not in o.name.lower()]}
(root/'xr_guild_library/v3/evidence/reference_blend_bookcase_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
