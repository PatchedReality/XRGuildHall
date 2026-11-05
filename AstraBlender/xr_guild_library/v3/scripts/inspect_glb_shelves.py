import bpy, math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'xr_guild_library/v3/evidence'
for key,file in [('fantasy','fantasy+library+interior+3d+model.glb'),('rotunda','ornate circular hall 3d model.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/file))
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True
 try:
  p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
  for d in p.devices:d.use=d.type=='METAL'
  s.cycles.device='GPU'
 except:pass
 s.world=bpy.data.worlds.new('Reference inspection');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
 s.view_settings.view_transform='Standard';s.render.resolution_x=1100;s.render.resolution_y=900;s.render.resolution_percentage=100
 for i,loc in enumerate([(0,-1.2,1.2),(0,1.2,1.2),(1.2,0,1.2),(-1.2,0,1.2)]):
  d=bpy.data.lights.new(str(i),'AREA');d.energy=18;d.size=1.5;o=bpy.data.objects.new(str(i),d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.2))-o.location).to_track_quat('-Z','Y').to_euler()
 c=bpy.data.cameras.new('Reference');o=bpy.data.objects.new('Reference',c);s.collection.objects.link(o);s.camera=o;c.type='ORTHO';c.ortho_scale=1.2
 for i,loc in enumerate([(0,-1,.72),(0,1,.72),(1,0,.72),(-1,0,.72)]):
  o.location=loc;o.rotation_euler=(Vector((0,0,.20))-o.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/f'reference_{key}_{i}.png');bpy.ops.render.render(write_still=True)
