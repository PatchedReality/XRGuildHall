# XR Guild Library WebGPU walkthrough

Run `npm ci`, then `npm run dev` (localhost:4175). `npm run build` creates a static `dist` release. Serve over HTTPS or localhost. The model is already embedded in `public/assets/XR_Guild_Library_v3.glb`.

Three.js uses WebGPU when available, with a visible WebGL 2 fallback. The preview includes desktop pointer lock, WASD, drag look, native touch thumbstick and swipe look, proximity interactions, collision boundaries, optional meeting furniture and a readable inscriptions panel. Walking viewpoints stay at 1.70 m.

The GLB retains real meter dimensions: 8 m interior width, 6.2 m apex. The source Blender scene keeps its editable objects; the export combines static geometry by material and preserves door pivots, the interface and optional furniture as separate groups.

To optimize an exported uncompressed model:

```
npx gltf-transform optimize ../evidence/room_uncompressed.glb ../evidence/room_textures_optimized.glb --compress false --flatten false --join false --palette false --instance false --simplify false --texture-size 3072 --texture-compress webp
npx gltf-transform meshopt ../evidence/room_textures_optimized.glb public/assets/XR_Guild_Library_v3.glb --level medium --quantize-position 16 --quantize-normal 12
node validate-glb.mjs
npm run build
```

The static site is deployed through Shelley at https://xr-guild-library.exe.xyz/. The V2 comparison is retained at `/v2/`.

Keep geometric simplification disabled: it removes fine letter strokes. The 16-bit position precision preserves thin, closely spaced gilt and text surfaces.
