"""Optional Blender controls. Run once in the Text Editor; no auto-execution."""
import bpy
import webbrowser

class XRGUILD_OT_open_library(bpy.types.Operator):
    bl_idname='xrguild.open_library'
    bl_label='Open XR Guild Library'
    bl_description='Open library.xrguild.org in your default web browser'
    def execute(self,context):
        webbrowser.open('https://library.xrguild.org/')
        return {'FINISHED'}

class XRGUILD_OT_door(bpy.types.Operator):
    bl_idname='xrguild.toggle_door'
    bl_label='Open / close meeting doors'
    def execute(self,context):
        context.scene.frame_set(1 if context.scene.frame_current==72 else 72)
        return {'FINISHED'}

class XRGUILD_OT_furniture(bpy.types.Operator):
    bl_idname='xrguild.toggle_furniture'
    bl_label='Show / hide meeting table and chairs'
    def execute(self,context):
        c=bpy.data.collections.get('11 Optional meeting furniture')
        if c:
            c.hide_viewport=not c.hide_viewport;c.hide_render=c.hide_viewport
        return {'FINISHED'}

class XRGUILD_PT_library(bpy.types.Panel):
    bl_label='XR Guild Library'
    bl_idname='XRGUILD_PT_library'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='XR Guild'
    def draw(self,context):
        l=self.layout
        l.label(text='8 m library / 6.2 m apex')
        l.operator('xrguild.open_library',icon='URL')
        l.operator('xrguild.toggle_door',icon='OUTLINER_OB_EMPTY')
        l.operator('xrguild.toggle_furniture',icon='OUTLINER_COLLECTION')
        l.label(text='Closed: frame 1 | Open: frame 72')

classes=(XRGUILD_OT_open_library,XRGUILD_OT_door,XRGUILD_OT_furniture,XRGUILD_PT_library)
def register():
    for cls in classes:
        prior=getattr(bpy.types,cls.__name__,None)
        if prior:
            try:bpy.utils.unregister_class(prior)
            except RuntimeError:pass
        bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):
        prior=getattr(bpy.types,cls.__name__,None)
        if prior:bpy.utils.unregister_class(prior)
if __name__=='__main__':register()
