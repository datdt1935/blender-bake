# Auto Lowpoly Baker

Auto Lowpoly Baker is a Blender 4.2 LTS+ add-on that duplicates the active high-poly mesh, creates a decimated low-poly copy, generates UVs, creates a diffuse bake target, bakes material color in Cycles, and saves the result as PNG.

## Features

- Keeps the source high-poly object unchanged.
- Applies Decimate only on the duplicated low-poly mesh.
- Generates UVs with Smart UV Project.
- Bakes diffuse color only, without direct or indirect lighting.
- Saves a PNG texture to a relative or absolute output folder.
- Optionally packs the baked image into the `.blend`.
- Restores active object, selection, mode, frame, render engine, and bake settings.
- Cleans temporary data on failure unless requested otherwise.

## Install

1. Build or download `auto_lowpoly_baker.zip`.
2. In Blender, open **Edit > Preferences > Add-ons > Install from Disk**.
3. Select the ZIP and enable **Auto Lowpoly Baker**.
4. Select a mesh object and open **3D View > Sidebar > Auto Baker**.

## Settings

- **Decimate Ratio**: fraction of geometry kept on the low-poly copy.
- **Texture Resolution**: square PNG size.
- **UV Island Margin**: Smart UV Project island spacing.
- **Bake Margin**: pixel padding around UV islands.
- **Ray Distance**: selected-to-active search distance.
- **Output Directory**: texture folder. Relative paths such as `//textures` require a saved `.blend`.
- **Pack Image**: packs the saved image into the `.blend`.
- **Keep Temporary Data**: keeps generated data when an error occurs for debugging.

## Workflow

1. Save the `.blend` file if using a relative output folder.
2. Select one high-poly mesh with material colors.
3. Adjust Auto Baker settings.
4. Click **Create Lowpoly & Bake**.
5. Inspect the generated `{ObjectName}_LOW` mesh and `{ObjectName}_Diffuse.png`.

## Troubleshooting

- If the bake misses areas, increase **Ray Distance**.
- If unrelated surfaces bleed into the texture, reduce **Ray Distance**.
- If relative output paths fail, save the `.blend` file first.
- Smart UV Project is automatic; production assets may benefit from manual UVs.
- Baking uses Cycles temporarily and restores the previous render engine afterward.

## Project Structure

```text
auto_lowpoly_baker/
  __init__.py
  operators/
  panels/
  properties/
  services/
  utils/
  blender_manifest.toml
  README.md
  CHANGELOG.md
  LICENSE
tests/
  smoke_test.py
scripts/
  build_zip.py
```

## Test

Run from the repository root with Blender available on `PATH`:

```bash
blender --background --factory-startup --python tests/smoke_test.py
```

The smoke test registers and unregisters the add-on repeatedly, checks operator polling, and runs a small bake on a generated cube.

## Build ZIP

```bash
python scripts/build_zip.py
```

The release archive is written to `dist/auto_lowpoly_baker.zip`.

## Uninstall

In Blender, open **Edit > Preferences > Add-ons**, find **Auto Lowpoly Baker**, disable it, then remove it.
