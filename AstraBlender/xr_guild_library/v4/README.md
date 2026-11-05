# XR Guild Library V4

V4 adds architectural depth and fine ornament to the preserved V3 library, at the original **8 m interior width and 6.2 m apex**. All five bookcases remain empty, with eight shelf tiers and two broad bays on the ordinary cases. The embedded library screen retains its wider opening.

V3's acanthus capital leaves, midribs, side veins, rolled volutes, cabinet fans, ferns, scrolls, rosettes and cabochons are preserved. New details include fitted scalloped leaf edging, twisted capital fillets, climbing vine inlays, carved shelf arches and corbels, recessed burr walnut panels and branching dado marquetry. The window border correction restores the original slender gold borders, retaining the gilt tracery and clear glazing. The bulky grey window casings and jamb blocks have been removed.

The wood and labradorite materials are revised, with darker walnut and a finer mineral pattern. Topic inscriptions occupy dedicated fascia panels with at least 19 cm side padding and 4 cm vertical padding; crowded duplicate headings above the cases have been removed. The fresco and mandala retain their artwork.

## Deliverables

- `XR_Guild_Library_v4.blend`: editable native model with packed artwork.
- `web_preview/public/assets/XR_Guild_Library_v4.glb`: compressed binary glTF with embedded textures, separate door hinges and optional furniture.
- `web_preview/`: Three.js WebGPU preview, with WebGL 2 fallback, WASD/mouse controls and mobile thumbstick/swipe controls.
- `renders/hero.png` and `renders/craft.png`: Blender views.
- `evidence/`: native dimensions/detail preservation, export validation and browser checks.

The stable preview address is https://xr-guild-library.exe.xyz/. Original V1 is available at `/V1/`, V2 at `/v2/`, and V3 at `/v3/`.

## Controls

Desktop: WASD/arrows to move, mouse look, Shift to walk faster, E to use nearby doors or the library interface, Escape to release the pointer. Mobile: left thumbstick, swipe to look, contextual interaction button and Pause. View buttons, door and meeting-layout controls work on both. “Read labels” exposes all nine full topic names and resource links.

The room GLB carries model geometry, material textures, hinge metadata and the resource URL. The preview supplies movement, collision, lighting, door behavior and the separate outdoor backdrop. Other GLB consumers must supply those behaviors.

## Rebuild

Run Blender in background with `scripts/build_v4.py`, then `scripts/export_glb.py`. The generator reads the preserved sibling `v3/XR_Guild_Library_v3.blend` and geometry helpers in `../scripts/build_library.py`. The delivery archive includes those dependencies. Existing material atlases live in `textures/`; revised walnut, labradorite, burr panels and fresco are baked during export.

From `web_preview`, run `npm ci` and `npm run dev` or `npm run build`. Geometric simplification is disabled to preserve thin ornament and lettering. GLB compression uses Meshopt and WebP textures.

Validation focuses on visual comparisons, native dimensions/detail preservation, glTF validity and desktop/mobile controls. Mobile checks use Chrome touch emulation; physical phone performance is not measured.
