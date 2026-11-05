# V2 walkthrough deployment

Public walkthrough: https://xr-guild-library.exe.xyz/

Deployed on 2026-09-23 (America/Chicago), using Shelley on a new exe.dev VM named `xr-guild-library-v2`. The VM has 2 CPUs, 2 GB memory and a 10 GB disk. Only the completed static production build is served; the Blender master and source files remain local.

- Host management: `ssh xr-guild-library.exe.xyz`
- Shelley: https://xr-guild-library.shelley.exe.xyz
- Service: `nginx.service`, active and enabled to start on boot.
- Content root: `/home/exedev/xr-library-release`
- HTTP port: `8000`; exe.dev supplies public HTTPS.
- Site configuration: `/etc/nginx/sites-available/xr-guild-library-v2`
- Remote deployment receipt: `/home/exedev/deployment-receipt.json`

The GLB is available at https://xr-guild-library.exe.xyz/assets/XR_Guild_Library_v2.glb. Its SHA256 is `e095ed93ae34c34cdd2b691a87775f143033aa1f4e23d16f36280c379448eaa1`.

Shelley installed and configured nginx without modifying the build. HTML and the fixed-name GLB revalidate; hashed JavaScript/CSS have immutable cache headers. Text assets use gzip. Directory listings are disabled. The site is publicly accessible; Shelley and SSH retain their account authentication.

## Verification

All five hosted files returned HTTP 200 and matched local SHA256 hashes. The hosted walkthrough was exercised in Chrome 148 on macOS with WebGPU active: pointer lock, WASD, mouse look, collision boundaries, resource-link interaction, door controls, meeting furniture, and the fresco/craftsmanship viewpoints passed. Browser console errors: zero. WebGL 2 remains the application's labeled fallback for devices without WebGPU.

Receipts are in `evidence/shelley_deployment_receipt.json`, `evidence/hosted_asset_verification.json`, and `evidence/hosted_browser_verification.json`. The hosted screenshot is `evidence/hosted_walkthrough.png`.

Future updates should replace only the static content root with the output of `npm run build` run inside `web_preview`, then verify the public files and browser controls again. No Node.js application process is needed on the host.

## Mobile controls update

The touch-control update uses a left thumbstick for walking, screen swipes for looking, context interaction, a speed toggle, and pause/resume. Layouts support portrait, landscape, and phone safe areas. Multi-touch tests use native Chrome DevTools touch events in mobile emulation; physical iOS/Android device behavior and performance have not been tested. Desktop controls were regression-tested. Model geometry and GLB content are unchanged.

The mobile update was published through Shelley on the same host, with the previous HTML backed up outside the public root and older hashed assets retained. See `evidence/shelley_mobile_deployment_receipt.json`, `evidence/mobile_hosted_asset_verification.json`, and `evidence/mobile_hosted.json` for the update receipts.

## Text readability update

Published through Shelley on the renamed `xr-guild-library` VM. The update enlarges UI text and touch targets and adds a scrollable “Read labels” panel with full topic names and links. The native V2 model and its GLB are unchanged. Published HTML and every asset matched the local production hashes over public HTTPS. Receipts: `evidence/shelley_readability_deployment_receipt.json` and `evidence/readability_hosted_asset_verification.json`.
