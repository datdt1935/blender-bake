# Changelog

## 1.19.0

- Added a **Split Selected Meshes** checkbox to the Export box, on by default and active while **Keep Original Pivot** is on. **Batch Export GLB** then writes every selected mesh to its own `<mesh name>.glb` holding only that mesh, with its top-most parent (for example an Empty) moved to the world origin. Unselected parts are left out. Each file loads at 0, 0, 0 and the parts line up with each other exactly as in Blender.
- A selected Empty is skipped when something under it is selected too; selected on its own it is still exported as one file with everything under it.

## 1.18.0

- Added a **Keep Original Pivot** checkbox to the Export box, on by default. **Export GLB** and **Batch Export GLB** then export in parent (local) space with a shared pivot: the top-most parent of each selected object (for example an Empty) is moved to the world origin for the export and put back afterwards, instead of re-centering each object on its bounding-box bottom center. Parts exported from the same parent share its pivot, so placing them at one transform in the engine rebuilds them exactly as in Blender.
- Only the parent's location is zeroed; rotation, scale, object origins and mesh data are left untouched. A top-level object with no parent is exported around its own origin. Turn the option off to get the previous bottom-center behavior.

## 1.17.0

- **Export GLB** now places the selection on the world origin before it writes the file, the same way **Batch Export GLB** does (origin bottom center + center), and puts the objects back where they were afterwards. Several separate objects are moved together, so they keep their layout relative to each other.
- **Export GLB** now asks for the `.glb` file directly and exports with the shared preset, instead of opening Blender's native glTF export window. Children of a selected parent are exported with it.

## 1.16.0

- Added an **Ignore Material** field to the Export box, defaulting to `Assets_Palette`. **Batch Export GLB** empties every material slot holding that material before it writes a file, so the palette material never ends up in the exported GLB, and fills the slots back in afterwards - the object is left exactly as it was.
- Blender's duplicate suffix is ignored when matching, so `Assets_Palette.001` (what a GLB import usually creates) is stripped as well. Clearing the field exports every material.

## 1.15.0

- Added a **Batch Export GLB** button under the existing **Export GLB** button. It asks for a destination folder, then writes every selected object to its own `<object name>.glb` in that folder, so a whole selection exports in one click instead of one file at a time.
- Each object is placed on the world origin before it is written — origin moved to the bounding-box bottom center, then that origin moved to (0, 0, 0) — so every exported file holds the asset at 0, 0, 0 rather than at its position in the scene. The scene is restored exactly as it was once the export finishes.
- A parented hierarchy is exported as a single file named after its top-most object, and its children keep their relative position inside the file.
- Both export buttons now share one glTF preset (`services/export_service.py`), so a batch export is identical to clicking **Export GLB** once per object.

## 1.14.0

- **Position Grid**, **Compact Grid**, and **Center World** now treat a parented hierarchy as one rigid group: only the top-most object of each group is moved, so the child meshes inside an asset (for example `Assets_PlantBanana` and its `Assets_PlantBanana_Alpha_Cards` child) keep their exact relative position instead of being scattered individually.
- Layout footprints are now measured from the whole group — the root plus every child parented under it — so a multi-mesh asset is packed and spaced by its real size and no longer overlaps its neighbors. Bounds also cover the geometry instanced by a collection-instance empty, and an empty or other non-geometry parent is sized from its children.
- Hidden objects inside a group no longer inflate its footprint; they still move along with the group.
- Compact Grid's Z alignment now drops the lowest point of the entire group to Z = 0 rather than only the selected object's own mesh.

## 1.13.0

- Added a **Sort Largest to Smallest** checkbox (default on) for Compact Grid: when enabled, objects are ordered by bounding-box area before packing, so larger objects land first (top-left, shrinking left to right / row to row) for a more visually balanced layout. When off, objects pack in their current selection order.

## 1.12.0

- Reworked **Compact Grid** to use real 2D rectangle (shelf) packing based on each object's world-space bounding box, instead of a row/column grid: objects are packed edge-to-edge with an exact gap (Compact Spacing, default now 0.1m), rotation and scale are preserved, every object's bounding-box bottom is aligned to Z = 0, and the packed layout is centered on the world origin.

## 1.11.1

- Fixed the **Compact Grid** button doing nothing: the operator class was never registered in `__init__.py`, so it silently failed to run.

## 1.11.0

- When an imported GLB has no mesh named the configured Mesh Name (default `Mesh`), the importer no longer discards it silently: its objects are kept in the scene, each renamed with the file's derived asset name prefixed on front (e.g. `Asset_BasementMedium_Cube`) so you can find and fix the source file. After importing multiple files, a summary warning lists every file that was missing the expected mesh.

## 1.10.1

- Reverted **Position Grid** to its original uniform-cell behavior (fixed margin, not tied to the Spacing field).
- **Compact Spacing** (formerly "Spacing") now only drives **Compact Grid**, which packs each row/column to fit its objects' bounding boxes with just that configured gap between them.

## 1.10.0

- Added a **Compact Grid** button on the Assets tab: like Position Grid, but each row/column is only as large as its occupants instead of a single uniform cell, so objects sit closer together while still never overlapping.
- Added a **Spacing** field (default 0.5m) on the Assets tab that controls the gap between objects for both Position Grid and Compact Grid.
- Clarified that **Select GLB File(s)...** already supports importing multiple GLBs at once (Ctrl/Shift-click in the file browser); relabeled the button and added a hint so this is discoverable.

## 1.9.0

- Added a **Position Grid** button on the Assets tab: arranges all selected objects into an evenly spaced grid on the XY plane, sized from each object's bounding box so nothing overlaps.
- Added a **Center World** button on the Assets tab: moves every selected object's origin back to the world center (0, 0, 0).

## 1.8.1

- The Assets tab importer now renames the kept mesh (object and mesh data) from the GLB file name, dropping any trailing hash-id segment after the first dot — e.g. `Asset_BasementMedium.bdde813465453426.glb` becomes `Asset_BasementMedium`.

## 1.8.0

- Added an **Assets** sidebar tab (separate from Auto Baker) for importing GLB assets. Click **Select GLB File...** (or drag a `.glb`/`.gltf` file into the 3D Viewport) to import: the importer keeps only the mesh object named `Mesh`, deletes every other imported object, applies the existing material named `MaterialAll` to it, and moves it into the `Objects` collection (created if missing).
- Added an **Advanced** section on the Assets tab to customize the mesh name to keep, the material name to apply, and the target collection name.

## 1.7.0

- Added an **Export GLB** button that opens Blender's native glTF exporter pre-filled with a fixed preset: GLB binary, selected-only, +Y up, UVs and Normals, materials exported as WebP (quality 30), shape keys and skinning, and Draco mesh compression (level 6; quantization position 14, normal 10, texcoord 12, color 10, generic 12). You can review or adjust the settings in the standard export window before exporting.

## 1.6.0

- Added a **Reset Pose** button that resets the rig of the selected object to its default pose. It resolves the armature from the active/selected object (the armature itself, an Armature modifier, or a rig parent), switches to Pose Mode, clears pose bone transforms, and restores the previous selection and mode.
- Added an **Uncheck Active Animations** option (default on) for Reset Pose. When enabled it mutes the rig's active NLA animation tracks and clears its active action before resetting, so the pose lands on the rest state instead of the animated pose.
- Added a build number to the **Auto Baker** panel title (for example, `Auto Baker v1`). The number starts at 1 and auto-increments on every `scripts/build_zip.py` run.

## 1.5.1

- Added Reset Config utility button to restore configuration defaults.

## 1.5.0

- Removed the Output panel from the sidebar.
- Changed Clear Unused Data to remove every unused material and texture images referenced by those unused materials.

## 1.4.0

- Added utility button to remove unused Auto Baker generated materials and texture images.
- Tagged newly generated Auto Baker materials and images for safer cleanup.

## 1.3.0

- Added High/Low vertex count display in the sidebar.
- Added Target Vertices reduction mode with extra decimate passes to better respect the requested vertex limit.

## 1.2.0

- Added a one-click Create Low Mesh & Bake operator.
- Added explicit origin utility for bottom-center origin and world-center placement.
- Added Merge Distance optimization before and after Decimate when creating low meshes.

## 1.1.0

- Refactored into a modular Blender 4.2+ add-on package.
- Added safer context restoration and bake setting restoration.
- Added PNG output, optional image packing, failure cleanup, manifest, smoke test, and build script.

## 1.0.0

- Initial single-file auto low-poly diffuse bake workflow.
