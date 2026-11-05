from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen,Request
from urllib.error import HTTPError
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE='https://xr-guild-library.exe.xyz/'
manifest=json.loads((ROOT/'evidence/release_manifest.json').read_text())
def verify(item):
 url=BASE+item['path']
 with urlopen(Request(url,headers={'Cache-Control':'no-cache'}),timeout=60) as response:
  body=response.read();actual=hashlib.sha256(body).hexdigest()
  return {'path':item['path'],'url':url,'status':response.status,'bytes':len(body),'sha256':actual,'expected_sha256':item['sha256'],'matches':actual==item['sha256'],'cache_control':response.headers.get('Cache-Control'),'content_type':response.headers.get('Content-Type')}
with ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(verify,manifest))
routes=[]
for path in ['', 'V1/', 'v2/', 'v3/', 'assets/does-not-exist.js']:
 try:
  with urlopen(BASE+path,timeout=30) as res:routes.append({'path':path,'status':res.status,'cache_control':res.headers.get('Cache-Control')})
 except HTTPError as err:routes.append({'path':path,'status':err.code})
cache_ok=all('immutable' in (f['cache_control'] or '') if f['path'].endswith(('.js','.css')) else 'no-cache' in (f['cache_control'] or '') if f['path'].endswith(('.html','.glb')) else True for f in files)
report={'base':BASE,'files':files,'routes':routes,'cache_policy_pass':cache_ok,'pass':all(f['matches'] and f['status']==200 for f in files) and [r['status'] for r in routes]==[200,200,200,200,404] and cache_ok}
(ROOT/'evidence/hosted_asset_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['pass']
