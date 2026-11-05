from pathlib import Path
import shutil,hashlib,json,tarfile,struct
root=Path(__file__).resolve().parents[1];stage=root/'release_staging';site=stage/'site'
shutil.rmtree(stage,ignore_errors=True)
shutil.copytree(root/'web_preview/dist',site)
shutil.copytree(root.parent/'v2/web_preview/dist',site/'v2')
manifest=[{'path':p.relative_to(site).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(site.rglob('*')) if p.is_file()]
(stage/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'evidence/release_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tarfile.open(root/'xr-library-v3-release.tar.gz','w:gz') as tf:
 tf.add(site,arcname='site');tf.add(stage/'release-manifest.json',arcname='release-manifest.json')
p=root/'web_preview/public/assets/XR_Guild_Library_v3.glb';b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n])
report={'file':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'scene':j.get('scenes'),'meshes':len(j['meshes']),'nodes':len(j['nodes']),'textures':len(j['textures']),'glass':[m for m in j['materials'] if m.get('extensions',{}).get('KHR_materials_transmission')],'controls':[nd for nd in j['nodes'] if nd.get('extras')],'material_names':[m['name'] for m in j['materials']],'dimensions':'V2 library: 8 m across inside walls, 6.2 m apex','optimization':'No geometric simplification; Meshopt medium, 16-bit positions, 12-bit normals; WebP textures'}
(root/'evidence/optimized_glb_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'files':len(manifest),'glb_bytes':len(b),'archive_bytes':(root/'xr-library-v3-release.tar.gz').stat().st_size,'model_sha256':report['sha256']},indent=2))
