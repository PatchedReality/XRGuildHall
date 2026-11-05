import bpy, json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[2]
report = {}
for filename in ['GuildHall-3DModels1.blend', 'fantasy+library+interior+3d+model.glb', 'ornate circular hall 3d model.glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if filename.endswith('.blend'):
        bpy.ops.wm.open_mainfile(filepath=str(root / filename))
    else:
        bpy.ops.import_scene.gltf(filepath=str(root / filename))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    report[filename] = {'units': bpy.context.scene.unit_settings.system, 'scale_length': bpy.context.scene.unit_settings.scale_length,
                        'bounds': [lo, hi], 'dimensions': [hi[i]-lo[i] for i in range(3)],
                        'objects': [{'name': o.name, 'dimensions': list(o.dimensions)} for o in objects[:40]]}
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL'
    prefs.get_devices()
    report['cycles_devices']=[{'name': d.name, 'type':d.type} for d in prefs.devices]
except Exception as e:
    report['cycles_devices']=str(e)
(root / 'xr_guild_library/evidence/reference_dimensions.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
