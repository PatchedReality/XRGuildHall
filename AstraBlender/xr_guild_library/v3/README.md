# XR Guild Library V3

V3 applies the revised aesthetics directly to the original V2 library: **8 m across the inside walls, 6.2 m to the painted apex**, with a 4.88 m dome spring. The larger Area 1 main hall in `GuildHall-3DModels1.blend` is a different space and does not determine this library's dimensions.

The native model reuses all 4,790 V2 objects, retaining the clear window tracery, sculpted labradorite capitals, botanical carving, gilt ornaments, mosaic, fresco and articulated doors. The five empty walnut cases remain approximately 4.25 m high and 1.92 m wide, with eight tiers at 0.40 m pitch and two broad bays on the ordinary cases. The north case retains its wider embedded library screen opening. There are 43 shelf meshes; the screen's side shelves are separate pieces. The doorway, interface, benches and optional 2.26 m-diameter meeting table retain their original human dimensions. Walking views use a 1.70 m eye height.

The revised palette uses figured walnut, warm charcoal/umber walls, gilt brass, legible gold lettering and pale stone. Green is concentrated in the labradorite columns and stone inlay. The painted ceiling extends closer to the zenith. Large topic titles and PAST / PRESENT / FUTURE use raised gold geometry, with flat letter-face normals in the GLB. Windows retain fully clear glazing and the clean left-window gilt pattern from the supplied multiview reference.

The two multiview images inform window detail only. They and the event diagram are excluded from the human-scale shelf estimates.

## Deliverables

- `XR_Guild_Library_v3.blend`: editable Blender 5.2 model with packed artwork, organized collections, cameras and animated doors.
- `web_preview/public/assets/XR_Guild_Library_v3.glb`: optimized glTF binary with embedded textures, Meshopt compression, separate door pivots, optional furniture and library URL metadata.
- `web_preview/`: Three.js WebGPU walkthrough source, with labeled WebGL 2 fallback.
- `renders/hero.png`: native Blender interior render.
- `evidence/`: dimensional audit, export, validation and browser verification.

## Walkthrough

Public address: https://xr-guild-library.exe.xyz/

V2 comparison: https://xr-guild-library.exe.xyz/v2/

Desktop: WASD or arrow keys to walk, mouse to look, Shift to move faster, E to use a nearby door or search screen, Escape to release mouse capture. Dragging also changes the view outside pointer lock. View buttons jump to the entrance, fresco, craftsmanship, library screen and meeting furniture at the same eye height.

Mobile: left thumbstick to move, swipe to look, contextual interaction button, faster-walking toggle and Pause. The toolbar scrolls horizontally. “Read labels” opens a high-contrast, scrollable panel containing the full subject names and links.

The GLB contains the room. The walkthrough supplies lighting, collision, navigation and a separate outdoor landscape. Other GLB consumers must implement those behaviors; hinge angles, furniture grouping and the library URL are preserved in glTF extras.

## Rebuild

From `web_preview`, run `npm ci` and `npm run dev` or `npm run build`. Serve `dist` over HTTPS or localhost for WebGPU.

`scripts/build_v3.py` opens the neighboring `v2/XR_Guild_Library_v2.blend` and applies the aesthetic changes without scaling the architecture. It uses helper functions from `../scripts/build_library.py`. `scripts/export_glb.py` produces the uncompressed derivative and reuses the V2 baked wood/stone textures. The optimization command is in the web preview README. The delivery archive includes these dependencies.

Browser touch tests use Chrome mobile emulation with native multi-touch events; physical iOS/Android performance has not been tested.
