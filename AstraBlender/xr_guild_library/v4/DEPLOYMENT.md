# V4 walkthrough deployment

Published through Shelley on 2026-09-23 (America/Chicago) to the existing `xr-guild-library` exe.dev VM.

- V4: https://xr-guild-library.exe.xyz/
- V1 comparison: https://xr-guild-library.exe.xyz/V1/
- V3 comparison: https://xr-guild-library.exe.xyz/v3/
- V2 comparison: https://xr-guild-library.exe.xyz/v2/
- Service: nginx on port 8000; exe.dev supplies HTTPS.
- Live root: `/home/exedev/xr-library-release`.
- nginx configuration: `/etc/nginx/sites-available/xr-guild-library-v2` (legacy filename).
- Shelley conversation: `c7PG6RL` (window-border correction; original V4 publication `cBE6ASR`).
- Remote receipt: `/home/exedev/v4-window-border-deployment-receipt.json`.

V4 preserves the original 8 m interior width, 6.2 m apex, empty bookcases and V3 fine ornament. It adds fitted leaf edging, capital fillets, vine inlays, carved joinery and recessed panels. Dedicated inscription panels provide padding and clearance from the capitals. No geometric simplification was applied to the export.

The window-border correction updates V4 in place. The bulky grey casings, bronze outer reeds and jamb blocks were removed; the original slender gilt window borders were restored. Only the V4 GLB changed on the server. The root page, preview code, other editions and nginx configuration were unchanged. The prior model was backed up outside the public root.

## Publication and identity

The prior root page and nginx configuration were backed up under `/home/exedev/xr-library-v4-backups/`. Assets were copied before the root index was replaced atomically. Older assets remain available for cached pages. HTML and fixed-name GLBs revalidate; hashed JS/CSS use immutable caching, including V1, V2 and V3 paths.

V4 GLB: 17,706,732 bytes, SHA256 `8a533ed5163ca1bffa5850e5cbcbcb3d6d136a80531eb1df99a34de5527ded09`.

Preserved V3 GLB SHA256: `8f5a756d95d1487c93e7cd7b14f5784c0b64a968589dc122b4a0870957abba58`.

Preserved V2 GLB SHA256: `e095ed93ae34c34cdd2b691a87775f143033aa1f4e23d16f36280c379448eaa1`.

## Verification

Shelley reported successful publication, matching staged and published hashes for all 20 files, correct HTTP/cache behavior, and active/enabled nginx. Independent public HTTPS verification also matched all 20 files, confirmed all four version routes, and confirmed a missing asset returns 404. Receipts are in `evidence/shelley_deployment_receipt.json` and `evidence/hosted_asset_verification.json`.

Native dimensions, empty shelves, inscription padding and preservation of V3 fine ornament passed 17 checks. glTF validation reported zero errors and warnings; Meshopt coverage and texture-dimension notices remain informational. See `evidence/native_scale_verification.json` and `evidence/gltf_validation.json`.

All 17 desktop checks and 24 touch checks passed on the live HTTPS page with WebGPU active and zero runtime exceptions. Browser controls receipts are retained separately for local and hosted pages. The reused touch session stopped registering joystick gestures and was discarded; the successful hosted receipt uses a fresh Chrome session. Touch checks use mobile emulation with native multi-touch input. Physical phone performance is unverified.
