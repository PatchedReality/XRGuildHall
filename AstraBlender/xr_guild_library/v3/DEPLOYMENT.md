# V3 walkthrough deployment

Public walkthrough: https://xr-guild-library.exe.xyz/

Original V2 comparison: https://xr-guild-library.exe.xyz/v2/

Published through Shelley on 2026-09-23 (America/Chicago) to the existing `xr-guild-library` exe.dev VM. The site uses the original 8 m × 6.2 m library dimensions with revised aesthetics. The VM was not recreated.

- Service: nginx on port 8000; exe.dev supplies HTTPS.
- Live root: `/home/exedev/xr-library-release`.
- Configuration: `/etc/nginx/sites-available/xr-guild-library-v2` (legacy filename).
- Shelley: https://xr-guild-library.shelley.exe.xyz/
- Remote receipt: `/home/exedev/v3-deployment-receipt.json`.

The prior root page and nginx configuration were backed up outside the public root. Assets were copied first, then the root index was replaced atomically. Older root assets remain for cached V2 pages. HTML and fixed-name GLBs revalidate; hashed JS/CSS use immutable caching. Both `/` and `/v2/` resolve their indexes, and missing assets return 404.

## Model identity

V3 GLB: 14,071,500 bytes, SHA256 `8f5a756d95d1487c93e7cd7b14f5784c0b64a968589dc122b4a0870957abba58`.

V2 GLB remains unchanged: SHA256 `e095ed93ae34c34cdd2b691a87775f143033aa1f4e23d16f36280c379448eaa1`.

V3 preserves geometric detail during optimization; simplification removed thin letter strokes. Meshopt compression uses 16-bit positions and 12-bit normals with embedded WebP textures. glTF validation reports zero errors and warnings; unsupported-validator Meshopt coverage and non-power-of-two texture dimensions are informational notices.

## Evidence

Shelley's service, publication and localhost HTTP checks are in `evidence/shelley_deployment_receipt.json`. Independent public HTTPS checks are in `evidence/hosted_asset_verification.json`: all ten files returned 200 and matched the release manifest, with correct cache policies and 404 behavior.

Desktop and mobile browser receipts are `evidence/desktop_hosted.json` and `evidence/mobile_hosted.json`. Touch input uses Chrome mobile emulation and native multi-touch events; physical phone performance is unverified. Local counterparts and dimensional validation are also retained in `evidence/`.

All 17 desktop checks and 24 touch checks passed on the live HTTPS page with WebGPU active and zero runtime exceptions. Touch verification used a fresh Chrome session; focus emulation holds the test page active while native touch events drive the actual controls.
