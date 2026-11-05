import bpy,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=bpy.context.scene
for view,extra in [('hero',[]),('detail',[]),('interface',[]),('door',['draft','open']),('meeting',[]),('plan',['draft'])]:
    S.frame_set(1)
    bpy.data.collections['06 Rotunda fresco'].hide_render=False
    bpy.data.collections['11 Optional meeting furniture'].hide_render=True
    bpy.data.collections['11 Optional meeting furniture'].hide_viewport=True
    sys.argv=['render_views.py','--',view]+extra
    print('GALLERY_VIEW_START',view,flush=True)
    runpy.run_path(str(ROOT/'scripts/render_views.py'),run_name='__main__')
    print('GALLERY_VIEW_COMPLETE',view,flush=True)
