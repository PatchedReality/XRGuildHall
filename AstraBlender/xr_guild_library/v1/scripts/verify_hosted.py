from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import hashlib, json

root = Path(__file__).resolve().parents[1]
base = 'https://xr-guild-library.exe.xyz/'
manifest = json.loads((root / 'evidence/release_manifest.json').read_text())
files = []
for item in manifest:
    with urlopen(Request(base + item['path'], headers={'Cache-Control': 'no-cache'}), timeout=60) as response:
        body = response.read()
        cache = response.headers.get('Cache-Control', '')
        suffix = Path(item['path']).suffix
        cache_ok = ('immutable' in cache if suffix in {'.js', '.css'} else
                    'no-cache' in cache if suffix in {'.html', '.glb'} else True)
        files.append({**item, 'matches': hashlib.sha256(body).hexdigest() == item['sha256'],
                      'status': response.status, 'cache': cache, 'cache_ok': cache_ok})
routes = []
for path in ['V1', 'V1/', 'v1', 'v1/', 'V1/missing.js']:
    try:
        with urlopen(base + path, timeout=30) as response:
            routes.append({'path': path, 'status': response.status, 'final_url': response.url})
    except HTTPError as error:
        routes.append({'path': path, 'status': error.code})
preserved = []
for item in json.loads((root / 'evidence/existing_pages_before.json').read_text()):
    with urlopen(Request(base + item['path'], headers={'Cache-Control': 'no-cache'}), timeout=30) as response:
        preserved.append({**item, 'unchanged': hashlib.sha256(response.read()).hexdigest() == item['sha256']})
report = {'files': files, 'routes': routes, 'existing_pages': preserved}
report['pass'] = (all(x['matches'] and x['status'] == 200 and x['cache_ok'] for x in files)
                  and all(x['status'] == 200 and x['final_url'] == base + 'V1/' for x in routes[:-1])
                  and routes[-1]['status'] == 404 and all(x['unchanged'] for x in preserved))
(root / 'evidence/hosted_verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert report['pass']
