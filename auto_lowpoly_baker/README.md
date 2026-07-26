# Auto Lowpoly Baker

Auto Lowpoly Baker is a Blender 4.2 LTS+ add-on that splits low-poly baking into two clear steps: create a prepared low-poly bake target, then bake material color from a chosen high-quality mesh to that low-quality mesh.

## Features

- Keeps the source high-poly object unchanged.
- Applies Decimate only on the duplicated low-poly mesh.
- Merges close vertices on the low-poly copy before and after Decimate.
- Generates UVs with Smart UV Project.
- Bakes diffuse color only, without direct or indirect lighting.
- Saves a PNG texture to a relative or absolute output folder.
- Optionally packs the baked image into the `.blend`.
- Restores active object, selection, mode, frame, render engine, and bake settings.
- Cleans temporary data on failure unless requested otherwise.
- Provides explicit **High Quality** and **Low Quality** object inputs so bake order is controlled by the add-on.
- Shows vertex counts for the High Quality and Low Quality meshes in the panel.
- Includes a one-click **Create Low Mesh & Bake** command for the full workflow.
- Includes a utility to set the selected mesh origin to bottom center and move that origin to world center.
- Includes a cleanup utility for unused materials and texture images referenced by those unused materials.

## Install

1. Build or download `auto_lowpoly_baker.zip`.
2. In Blender, open **Edit > Preferences > Add-ons > Install from Disk**.
3. Select the ZIP and enable **Auto Lowpoly Baker**.
4. Open **3D View > Sidebar > Auto Baker**.

## Settings

- **High Quality**: source high-poly mesh used during bake.
- **Low Quality**: generated or selected low-poly mesh used as the bake target.
- **Reduction Mode**: choose Ratio or Target Vertices for low-poly generation.
- **Decimate Ratio**: fraction of geometry kept on the low-poly copy.
- **Target Vertices**: approximate vertex limit used when Reduction Mode is Target Vertices.
- **Merge Distance**: distance threshold for merging duplicate or very close vertices.
- **Texture Resolution**: square PNG size.
- **UV Island Margin**: Smart UV Project island spacing.
- **Bake Margin**: pixel padding around UV islands.
- **Ray Distance**: selected-to-active search distance.
- **Output Directory**: texture folder. Relative paths such as `//textures` require a saved `.blend`.
- **Pack Image**: packs the saved image into the `.blend`.
- **Keep Temporary Data**: keeps generated data when an error occurs for debugging.

## Workflow

1. Save the `.blend` file if using a relative output folder.
2. Choose the source mesh in **High Quality**.
3. Adjust **Decimate Ratio**, **Texture Resolution**, and **UV Island Margin**.
4. For one-click processing, select the high mesh and click **Create Low Mesh & Bake**.
5. For step-by-step processing, click **Create Low Mesh**. The add-on creates `{ObjectName}_LOW`, assigns **Low Quality**, and creates the material/image bake target.
6. Adjust bake/output settings, then click **Bake**. The add-on selects High Quality first and makes Low Quality active before running selected-to-active bake.
7. Inspect `{ObjectName}_LOW` and `{ObjectName}_Diffuse.png`.

## Utility

Select a mesh and click **Origin Bottom Center + Center** to move its origin to the bottom center of its world-space bounding box, then move that origin to `(0, 0, 0)`.

Click **Clear Unused Data** to remove all unused materials and any texture images referenced only by those unused materials.

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

The smoke test registers and unregisters the add-on repeatedly, checks operator polls, creates a cube, creates the low mesh, runs a small bake, and verifies the PNG exists.

## Build ZIP

```bash
python scripts/build_zip.py
```

The release archive is written to `dist/auto_lowpoly_baker.zip`.

## Uninstall

In Blender, open **Edit > Preferences > Add-ons**, find **Auto Lowpoly Baker**, disable it, then remove it.
