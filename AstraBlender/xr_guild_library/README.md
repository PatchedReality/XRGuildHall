# XR Guild Library

Open **XR_Guild_Library.blend** in Blender 5.2 or later. All textures and the lettering font are packed into the file. The supplied reference files are unchanged; no geometry from them is included in this model.

## Room

- Twelve-sided room, **8.0 m across interior wall flats** (26.25 ft), 8.28 m corner to corner. The brief equates 24 ft with 8 m; this model follows its metric dimension. For an exact 24-foot width, scale the room's horizontal axes by 0.9144.
- Ceiling apex **6.2 m / 20.34 ft**; wall cornice approximately 4.85 m.
- Six tall arched windows with **clear transparent glass**, twelve green labradorite columns, botanical gilt tracery, five walnut bookcases with empty shelves and dark green patterned backing.
- The gilt pattern follows the **left window of multiview_2**: linked large and small roundels, an almond-shaped opening below the main circle, paired lower arches, swept side loops, fine crossing curves and a flared central mullion foot. The left window was used to resolve details washed out in the center window. Openings are 0.98 m wide by 3.70 m tall.
- Symmetrical green, ivory and brass stone mandala, with a 2.9 m clear central radius in the unfurnished room.
- Painterly fresco: sepia optical history, emerald present-day VR, and blue shared futures. Its panoramic scenes repeat on opposite halves of the dome, fading into a dark mineral-blue zenith.
- Nine gilt topic labels transcribed from the current [XR Guild Library categories](https://library.xrguild.org/) on September 23, 2026. Capitalization and line breaks are adapted for architectural lettering.
- Eight chairs and a round walnut meeting table are included in **11 Optional meeting furniture**, hidden by default.

## Controls

The doors are closed at **frame 1**, fully open at **frame 72**, and closed again at **frame 168**. Each leaf has a separate hinge pivot and opens 100 degrees outward. Clear doorway width is approximately 1.63 m, with a 2.48 m rectangular passage below the fixed fanlight.

For convenient controls, open the Scripting workspace, choose the packed **library_controls.py** text, and press **Run Script**. The 3D View's **N sidebar → XR Guild** then provides:

- Open XR Guild Library in the default browser.
- Open/close the meeting doors.
- Show/hide the table and chairs.

No script runs automatically. The controls also exist as a separate file under `scripts/`.

The bookshelf display sits at 1.405 m center height. It is a modeled interface with readable search and topic affordances, URL metadata, and an interaction anchor. The Blender control opens the live library website. Typing/searching inside the screen, pointer interaction, shared meeting state and room privacy require integration in the destination XR application. Closing the modeled door does not implement audio isolation or access control.

## Organization

Numbered collections separate architecture, columns, windows, shelves, floor, fresco, lettering, interface, doors, lighting, optional furniture and interaction anchors. Components remain editable. Cameras include entrance interior, window/bookcase detail, interface, fresco, door, plan, elevated interior, and a front-on tracery detail. **13 Exterior preview landscape** supplies a lake, tree line and distant ridges for views through the transparent windows; it is separate render context to disable or replace when placing the room into another world.

The native Blender materials use procedural walnut and stone shaders. This is an artist-editable Blender asset; it has not been baked, optimized, exported or tested in a headset/runtime.

## Files and provenance

- `XR_Guild_Library.blend` — self-contained native scene.
- `renders/` — previews rendered from the actual Blender geometry.
- `scripts/build_library.py` — reproducible scene generator.
- `scripts/render_views.py` — camera render helper.
- `scripts/library_controls.py` — optional local controls.
- `evidence/model_manifest.json` and `evidence/verification.json` — dimensions, counts and door/control checks.
- `textures/immersive_eras_fresco_v2.png` and `textures/stone_mandala.png` — final imagegen artwork, generated using the supplied images as visual references. `textures/final_asset_prompts.txt` records the prompts and generation method.

The original flat fresco experiment is not used by the final model. Reference `.glb` models have normalized bounds of approximately one metre and were treated as proportion references, not reliable real-world unit measurements.

To rebuild from this folder:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_library.py
```

To render an interior preview:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b XR_Guild_Library.blend --python scripts/render_views.py -- hero
```
