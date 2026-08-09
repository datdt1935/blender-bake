# Changelog

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
