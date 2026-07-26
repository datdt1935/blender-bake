# Auto Lowpoly Baker

This repository contains a production-oriented Blender 4.2 LTS+ add-on package for automatic low-poly diffuse baking.

## Requirement Analysis

- **Goal**: select one high-poly mesh, create a low-poly duplicate, unwrap it, bake material color to a diffuse PNG, and keep the original object unchanged.
- **Input**: one active editable mesh object, add-on settings from `Scene.alb_settings`, and an output directory.
- **Output**: `{ObjectName}_LOW`, a new material, a bake image datablock, and `{ObjectName}_Diffuse.png`.
- **Workflow**: select mesh, configure **3D View > Sidebar > Auto Baker**, click **Create Lowpoly & Bake**.
- **Preconditions**: Blender 4.2+, Cycles available, active object is a local mesh with polygons, `.blend` saved when using `//` paths.
- **Changed Blender data**: new object, mesh, material, image, optional packed image, PNG file.
- **Preserved data**: source object mesh/materials, active object, selection, mode, frame, render engine, and bake settings.
- **Failure handling**: validation errors are reported; temporary datablocks are removed unless **Keep Temporary Data** is enabled.
- **Context risk**: UV unwrap, modifier apply, and bake require `bpy.ops`, so those calls run inside a context-preservation layer.

## Assumptions

- Target version is Blender 4.2 LTS or newer.
- The package is installable as a standard add-on ZIP and also includes `blender_manifest.toml` for extension-style metadata.
- Baking uses Cycles selected-to-active diffuse color only.
- No external Python packages are required.

## Architecture

- `auto_lowpoly_baker/__init__.py`: registration and `bl_info`.
- `properties/settings.py`: scene settings.
- `panels/main_panel.py`: sidebar UI.
- `operators/bake_operator.py`: user-facing operator and cleanup orchestration.
- `services/context_service.py`: mode, selection, active object, frame, render engine, and bake setting preservation.
- `services/mesh_service.py`: duplicate, Decimate modifier, Smart UV Project.
- `services/material_service.py`: bake image, low-poly material, PNG save, image pack.
- `services/bake_service.py`: Cycles diffuse bake configuration and bake call.
- `utils/validation.py`: preflight checks with user-readable errors.
- `utils/logging.py`: add-on logger.

## File Tree

```text
auto_lowpoly_baker/
  __init__.py
  operators/bake_operator.py
  panels/main_panel.py
  properties/settings.py
  services/
  utils/
  blender_manifest.toml
  README.md
  CHANGELOG.md
  LICENSE
tests/smoke_test.py
scripts/build_zip.py
```

## Build

```bash
python scripts/build_zip.py
```

The ZIP is written to `dist/auto_lowpoly_baker.zip`.

## Test

```bash
blender --background --factory-startup --python tests/smoke_test.py
```

The smoke test registers/unregisters the add-on, checks operator polling, creates a cube, runs a small bake, and verifies the PNG exists.

## Important Blender APIs Used

- `bpy.utils.register_class`, `bpy.props.PointerProperty`
- `bpy.ops.object.modifier_apply`
- `bpy.ops.uv.smart_project`
- `bpy.ops.object.bake`
- `Scene.render.bake`
- `bpy.data.images.new`, `Image.save`, `Image.pack`
- material node APIs via `Material.node_tree`
