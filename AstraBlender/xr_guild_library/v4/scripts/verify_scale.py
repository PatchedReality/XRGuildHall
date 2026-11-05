import bpy,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'XR_Guild_Library_v4.blend'))
bpy.data.collections['11 Optional meeting furniture'].hide_viewport=False
bpy.context.view_layer.update()
def bounds(ob):
    points=[ob.matrix_world@v.co for v in ob.data.vertices] if ob.type=='MESH' else [ob.matrix_world@Vector(v) for v in ob.bound_box]
    return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)],'size':[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]}
S=bpy.context.scene
names=['Twelve-sided foundation | 8 m across flats','Rotunda | painted interior vault']
selected={o.name:bounds(o) for o in S.objects if o.name in names or 'Door leaf' in o.name or o.name.startswith('Meeting table | walnut top') or o.name.startswith('Interface |')}
glass=bpy.data.materials['Clear architectural glass | transparent, not frosted'].node_tree.nodes['Principled BSDF']
floor=selected[names[0]];vault=selected[names[1]]
cases=[o for o in S.objects if any(c.name.startswith('04 ') for c in o.users_collection) and o.type in {'MESH','CURVE'}]
case_bounds=[bounds(o) for o in cases]
case_height=max(b['max'][2] for b in case_bounds)
shelves=[o for o in cases if ('empty shelf' in o.name or 'empty side shelf' in o.name)]
case_checks={'bookcase_height_4_25m':abs(case_height-4.247)<.03,'two_bays':S['shelf_bays']==2,'eight_rows':S['shelf_rows']==8,'empty_shelf_meshes_43':len(shelves)==43}
checks={**case_checks,'inside_width_matches':abs(floor['size'][0]-8.0)<.001,'apex_matches':abs(vault['max'][2]-6.2)<.001,'transparent_windows':glass.inputs['Transmission Weight'].default_value==1,'no_green_plaster_surfaces':all(ma.name!='Deep malachite green plaster' for o in S.objects if o.type in {'MESH','CURVE','FONT'} for ma in o.data.materials),'nine_large_gold_callouts':sum(o.name.startswith('V4 | large gold topic') for o in S.objects)==9,'all_walking_cameras_human_height':all(abs(o.location.z-1.7)<.001 for o in S.objects if o.type=='CAMERA' and not o.name.startswith(('06','07','08')))}
manifest=json.loads((ROOT/'evidence/build_manifest.json').read_text())
checks['inscriptions_have_padding']=all(t['horizontal_padding_m']>=.189 and t['vertical_padding_m']>=.04 for t in manifest['inscriptions'])
checks['no_duplicate_case_headings']=not any('bookcase wall heading' in o.name for o in S.objects)
checks['books_remain_absent']=S['books']==0
checks['original_capital_leaves_preserved']=sum('acanthus row' in o.name for o in S.objects)==288
checks['fine_leaf_edging_present']=sum(o.name.startswith('V4 | acanthus scalloped leaf edging') for o in S.objects)==288
checks['original_bookcase_fans_preserved']=sum(o.name.startswith('V2 | bookcase botanical fan') for o in S.objects)==10
with bpy.data.libraries.load(str(ROOT.parent/'v3/XR_Guild_Library_v3.blend'),link=False) as (original,_):
 fine_names=[n for n in original.objects if n.startswith(('V2 | capital','V2 | bookcase botanical','V2 | engraved fern leaflet','V2 | branching fern stems','V2 | eight-petal','V2 | cabochon','V2 | pediment whiplash'))]
checks['v3_fine_ornament_preserved']=all(name in S.objects for name in fine_names)
report={'source':'Original library brief / V2','native_unit_scale':S.unit_settings.scale_length,'bookcase_floor_to_crown_m':case_height,'empty_shelves':len(shelves),'shelf_rows':S['shelf_rows'],'shelf_bays':S['shelf_bays'],'native_bounds':selected,'glass_transmission':glass.inputs['Transmission Weight'].default_value,'checks':checks,'pass':all(checks.values())}
(ROOT/'evidence/native_scale_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['pass']:raise RuntimeError('Scale verification failed')
