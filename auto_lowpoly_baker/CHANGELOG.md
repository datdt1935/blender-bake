# Changelog

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
