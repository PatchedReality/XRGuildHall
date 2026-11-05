"""Correct existing outward-facing text without rebuilding geometry."""
import bpy,math
from mathutils import Vector
S=bpy.context.scene
changed=[]
for o in S.objects:
    if o.type!='FONT':continue
    inward=Vector((-o.location.x,-o.location.y,0)).normalized()
    normal=o.matrix_world.to_quaternion()@Vector((0,0,1))
    if normal.dot(inward)<0:
        o.rotation_euler.z-=math.pi
        changed.append(o.name)
S.frame_set(1)
for degrees,label in [(150,'PAST · OPTICAL WORLDS'),(90,'PRESENT · SHARED PRESENCE'),(30,'FUTURE · POSSIBLE WORLDS')]:
    original=bpy.data.objects.get('Rotunda | '+label)
    if not original:continue
    for side in (0,180):
        name=original.name+(' | opposite' if side else '')
        o=bpy.data.objects.get(name)
        if o is None:
            o=original.copy();o.name=name
            bpy.data.collections['06 Rotunda fresco'].objects.link(o)
        a=math.radians(degrees+side)
        o.location=(3.785*math.cos(a),3.785*math.sin(a),5.13)
        o.rotation_euler=(math.pi/2,0,a-math.pi/2)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
print('LETTERING_CORRECTED',len(changed))
