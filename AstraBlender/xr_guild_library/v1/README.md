# V1 archive walkthrough

The preview at https://xr-guild-library.exe.xyz/V1/ uses a new GLB export of the preserved original `../XR_Guild_Library.blend`. The native source is read without being saved or modified. Its SHA256 is recorded in `evidence/source_identity.json`.

The model retains V1 geometry, original materials, clear glazing, original text and empty bookshelves. Material color textures are freshly baked from V1. Curves and text are tessellated for glTF, and static geometry is combined by material. There is no geometric simplification. WebP textures and Meshopt compression reduce the download size.

The current walkthrough shell supplies WebGPU rendering (with WebGL 2 fallback), WASD/mouse controls, mobile thumbstick/swipe controls, door behavior, optional meeting furniture and an exterior backdrop. Those controls are reused; this is an archival model comparison, not a reconstruction of an old web page. The Current V4 link returns to the main site.

To rebuild, run Blender in background with `scripts/export_glb.py`, then compress the exported GLB using the same no-simplification settings as V4. In `web_preview`, run `npm ci` and `npm run build`. The original native model is required as the sibling path above.
