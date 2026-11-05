# XR Guild Library — Version 2

V2 adds architectural craftsmanship from the supplied references while preserving the 12-sided plan, 8 m interior width, 6.2 m dome apex, six clear windows, five empty bookcases, reachable collection interface, and open meeting center.

Open **XR_Guild_Library_v2.blend** for the editable model. Version 1 remains unchanged in the parent directory. The preview is in **web_preview**; see its README for running the WebGPU walkthrough. The browser GLB is **web_preview/public/assets/XR_Guild_Library_v2.glb**.

The hosted walkthrough is **https://xr-guild-library.exe.xyz/**. See `DEPLOYMENT.md` for host and service details.

## Reference-led changes

- Double rows of lobed acanthus leaves, chased ribs and rolled volutes on all twelve capitals; turned bases and neck moldings.
- Paired carved shelf arches, botanical fans, center stiles, cornice beads, rosettes, and recessed walnut base panels. Shelves remain empty.
- Layered window archivolts, botanical spandrel relief, and paneled window bases. The gilt glazing pattern remains based on the cleaner left window in `multiview_2_55c62bef-40e3-4bd8-be88-16bdbe1d5351.webp`.
- Continuous honeysuckle cornice, six caged opal lanterns, and two slim perimeter window seats.
- Refined green labradorite with subtle blue feldspar and veins; a twelve-petal gilt celestial rose in the dome zenith and a laurel border beneath the fresco.
- Matching botanical relief on the hinged double doors.

Joinery and ornament are informed primarily by `upscaled_3eb8b54b-f24b-47d7-b9c3-d847625335af.webp`, `upscaled_70bf4eed-2fc5-4845-9db7-d581df5d90cb.webp`, and `upscaled_a79a8a44-8549-47bf-8ff4-efd14029b4a3.webp`; layered moldings also draw on `libraryxrguildconceptart1.webp`. The supplied reference models are not incorporated into this geometry.

New editable detail is grouped in collections **14–18**. Collection **11** contains the optional table and eight chairs; it is hidden by default. Collection **13** is preview landscape context, excluded from the GLB. The existing floor mosaic and narrative fresco remain packed in the Blender file.

## Controls and review

In Blender, frame **1** closes the doors and frame **72** opens them. Run the packed `library_controls.py` text for the sidebar controls. Nothing auto-runs. The collection screen stores `https://library.xrguild.org/` as its destination; the browser preview implements that link.

- `renders/hero.png`: overall v2 interior.
- `renders/craft.png`: the new joinery, capital, lantern, and window surround.
- `evidence/verification.json`: scene dimensions, clear glazing, packed textures, lettering and door checks.
- `evidence/gltf_validation.json`: GLB validator results.
- `evidence/browser_verification.json`: browser control and renderer checks.

The standalone Blender file and GLB need no external texture paths. Rebuilding v2 with `scripts/build_v2.py` uses the unchanged v1 Blender file and the v1 helper script in the parent directory. The original fresco and mosaic artwork was generated during v1; its prompts are preserved in `../textures/final_asset_prompts.txt`.
