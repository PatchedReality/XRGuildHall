from pathlib import Path
import hashlib, json, shutil, tarfile

root = Path(__file__).resolve().parents[1]
stage = root / 'release_staging'
site = stage / 'site'
shutil.rmtree(stage, ignore_errors=True)
shutil.copytree(root / 'web_preview/dist', site / 'V1')
manifest = [
    {'path': p.relative_to(site).as_posix(), 'bytes': p.stat().st_size,
     'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in sorted(site.rglob('*')) if p.is_file()
]
for path in [stage / 'release-manifest.json', root / 'evidence/release_manifest.json']:
    path.write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(root / 'xr-library-v1-release.tar.gz', 'w:gz') as archive:
    archive.add(site, arcname='site')
    archive.add(stage / 'release-manifest.json', arcname='release-manifest.json')
identity = json.loads((root / 'evidence/source_identity.json').read_text())
assert hashlib.sha256(Path(identity['source']).read_bytes()).hexdigest() == identity['sha256']
print(json.dumps({'files': len(manifest), 'original_blend_unchanged': True,
                  'archive_bytes': (root / 'xr-library-v1-release.tar.gz').stat().st_size}))
