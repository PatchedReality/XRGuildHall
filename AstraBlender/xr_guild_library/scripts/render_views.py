import bpy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['hero']
view=args[0]
S=bpy.context.scene
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL'
    prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='METAL'
    S.cycles.device='GPU'
    print('RENDER_USING_METAL',flush=True)
except Exception:
    S.cycles.device='CPU'
names={'hero':'01 | Entrance interior','detail':'02 | Window and bookcase','interface':'03 | Library interface','ceiling':'04 | Fresco','door':'05 | Meeting entrance','plan':'06 | Plan','elevated':'07 | Elevated interior','meeting':'01 | Entrance interior','tracery':'08 | Tracery straight on'}
S.camera=bpy.data.objects[names.get(view,names['hero'])]
S.cycles.samples=24 if 'draft' in args else 64
S.render.resolution_x=1100 if 'draft' in args else 1800
S.render.resolution_y=880 if 'draft' in args else 1440
if view!='hero' and 'draft' not in args:
    S.cycles.samples=32
    S.render.resolution_x=1400
    S.render.resolution_y=1120
if 'quick' in args:
    S.cycles.samples=16
    S.render.resolution_x=900
    S.render.resolution_y=720
if 'cpu' in args:
    S.cycles.device='CPU'
    print('RENDER_FORCE_CPU',flush=True)
S.render.resolution_percentage=100
S.render.use_persistent_data=True
S.render.image_settings.file_format='PNG'
if view=='interface':
    S.render.resolution_x=1000;S.render.resolution_y=1200
if view=='tracery':
    S.render.resolution_x=800;S.render.resolution_y=1100
if view=='plan':
    bpy.data.collections['06 Rotunda fresco'].hide_render=True
    S.render.resolution_x=S.render.resolution_y=1500
if view=='meeting':
    bpy.data.collections['11 Optional meeting furniture'].hide_render=False
    bpy.data.collections['11 Optional meeting furniture'].hide_viewport=False
    from mathutils import Vector
    S.camera.location=(0,-3.6,2.15)
    S.camera.rotation_euler=(Vector((0,.8,1.78))-S.camera.location).to_track_quat('-Z','Y').to_euler()
    S.camera.data.lens=17
if 'open' in args:S.frame_set(72)
S.render.filepath=str(ROOT/'renders'/f'{view}{"_draft" if "draft" in args else ""}{"_open" if "open" in args else ""}.png')
bpy.ops.render.render(write_still=True)
