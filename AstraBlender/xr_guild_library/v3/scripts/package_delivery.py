from pathlib import Path
import zipfile,json,hashlib
r=Path(__file__).resolve().parents[1];base=r.parent.parent
out=r.parent/'XR_Guild_Library_v3_delivery.zip'
paths=[r/'XR_Guild_Library_v3.blend',r/'README.md',r/'DEPLOYMENT.md',r/'renders/hero.png',r.parent/'v2/XR_Guild_Library_v2.blend',r.parent/'scripts/build_library.py']
for name in ['build_v3.py','export_glb.py','verify_scale.py','render_views.py','library_controls.py','stage_release.py','verify_hosted.py']:
 paths.append(r/'scripts'/name)
paths.extend(p for p in (r/'textures').rglob('*') if p.is_file())
paths.extend(p for p in (r/'web_preview').rglob('*') if p.is_file() and not any(x in p.relative_to(r/'web_preview').parts for x in ['node_modules','.DS_Store']) and p.name!='test-controls.js')
paths.extend(p for p in (r.parent/'v2/web_preview/dist').rglob('*') if p.is_file())
for name in ['build_manifest.json','optimized_glb_manifest.json','native_scale_verification.json','gltf_validation.json','release_manifest.json','shelley_deployment_receipt.json','hosted_asset_verification.json','desktop_hosted.json','mobile_hosted.json']:
 paths.append(r/'evidence'/name)
for name in ['desktop_hosted_entrance.png','desktop_hosted_craft.png','mobile_hosted_portrait.png']:
 paths.append(r/'evidence'/name)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(paths)):z.write(p,p.relative_to(base))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
manifest={'archive':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(set(paths)),'native_blend_sha256':hashlib.sha256((r/'XR_Guild_Library_v3.blend').read_bytes()).hexdigest(),'glb_sha256':hashlib.sha256((r/'web_preview/public/assets/XR_Guild_Library_v3.glb').read_bytes()).hexdigest()}
(r/'evidence/delivery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
