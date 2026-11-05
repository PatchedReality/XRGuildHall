# XR Guild Library · V2 walkthrough

A Three.js preview of the detailed v2 Blender room. The GLB includes its textures and uses metres. WebGPU is selected when available; the top-right badge reports the actual backend. WebGL 2 is a labeled fallback.

Run with Node 22.12 or newer:

```sh
npm ci
npm run dev
```

Open http://127.0.0.1:4173. Select **Enter the library**, then use **WASD** and the mouse. **Shift** moves faster, **Esc** releases the mouse, **R** returns to the entrance, and **E** interacts with the doors or collection screen when looking at them nearby. Dragging the view also works without mouse capture. The toolbar provides entrance, fresco and craftsmanship viewpoints, door and meeting furniture toggles, fullscreen, and a GLB download.

On phones and tablets, tap **Enter the library** to show touch controls. Drag the left thumbstick to walk and swipe the room with the other thumb to look; both work together. **Walk faster** toggles speed. Aim at a door or the collection screen and tap the context button to interact. **Pause** returns to the instructions. The tool strip scrolls horizontally on narrow screens. Movement clears on touch cancellation, rotation, pause, or leaving the page.

The collection screen opens https://library.xrguild.org/ in a new tab. Walking is constrained by the room walls, shelving, columns and the optional meeting layout. The preview landscape is generated separately and is not included in the room GLB.

Build the portable static page with `npm run build`. Serve the resulting `dist` directory over HTTP on localhost, or HTTPS when hosted. Opening `index.html` directly through `file://` will not work. The build contains the model, textures and JavaScript; it requires no CDN. The deployed walkthrough is available at https://xr-guild-library.exe.xyz/. Shelley configured nginx on a dedicated exe.dev VM; see `../DEPLOYMENT.md` for the deployment details.

## Asset pipeline

The editable master is `../XR_Guild_Library_v2.blend`. Run `../scripts/export_glb.py` in Blender to bake procedural color textures and tessellate the room into a glTF export scene. The source Blender file remains unchanged. Curves and lettering are converted for the GLB; static pieces are joined by material. Furniture and door pivots remain separate.

To apply the same browser compression after re-exporting:

```sh
cp public/assets/XR_Guild_Library_v2.glb ../evidence/room_uncompressed.glb
npx gltf-transform optimize ../evidence/room_uncompressed.glb public/assets/XR_Guild_Library_v2.glb --compress meshopt --flatten false --join false --palette false --instance false --simplify-error 0.00004 --texture-size 3072 --texture-compress webp
node validate-glb.mjs
```

The GLB requires `EXT_meshopt_compression` and WebP texture support. Its glass uses `KHR_materials_transmission`. Three.js supplies the decoder locally. The Blender master retains procedural bump and material complexity; the GLB uses baked color and PBR values for real-time rendering. Lighting differs from the Cycles still renders.

Renderer documentation: [Three.js WebGPURenderer](https://threejs.org/docs/pages/WebGPURenderer.html).
