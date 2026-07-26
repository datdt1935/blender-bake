# Changelog

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
