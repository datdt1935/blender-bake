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
- Includes a **Reset Pose** button that resets the rig of the selected object to its default pose.
- Includes an **Export GLB** button that exports the selected objects to a Draco-compressed `.glb` with WebP textures using a fixed preset.

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

In the **Rig** section, select an object and click **Reset Pose** to reset its rig to the default pose. The add-on finds the armature from the active or selected object — the armature itself, a mesh bound by an Armature modifier, or a rig parent — enters Pose Mode, clears the pose bone transforms, then restores your previous selection and mode.

Enable **Uncheck Active Animations** (on by default) so Reset Pose first mutes the rig's active NLA animation tracks and clears its active action. Without this, an active animation drives the pose back to the animated frame instead of the rest pose.

In the **Export** section, select the objects to export and click **Export GLB**, then pick the destination `.glb` file. The selection is placed on the world origin first (origin bottom center + center, the same as **Batch Export GLB**), exported with a fixed preset — GLB binary, selected objects only, +Y up, UVs and Normals, materials as WebP (quality 30), shape keys and skinning, and Draco mesh compression (level 6; quantization position 14, normal 10, texcoord 12, color 10, generic 12) — and then put back where it was. Several separate objects are moved together, so they keep their layout relative to each other.

To split parts out of a model built as an Empty with several child meshes, turn on **Keep Original Pivot** and **Split Selected Meshes**, select the meshes you want and click **Batch Export GLB**. Each selected mesh is written to its own `<mesh name>.glb` (unselected parts are left out) with the Empty moved to the world origin, so every file loads at 0, 0, 0 and the parts stay aligned when loaded together.

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
  reinstall.py
  install_blender.py
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

The release archive is written to `dist/auto_lowpoly_baker.zip`. Each build auto-increments the build number in `build_info.py`, which is shown in the panel title (for example, `Auto Baker v1`).

## Reinstall into Blender

After building, reinstall the ZIP into your local Blender (removes the old copy, installs and enables the new build):

```bash
python scripts/reinstall.py
```

Close the Blender GUI first, then reopen it afterwards to pick up the new build. If `blender.exe` is not found automatically, set `BLENDER_EXE` to its path, for example `set BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"`.

## Uninstall

In Blender, open **Edit > Preferences > Add-ons**, find **Auto Lowpoly Baker**, disable it, then remove it.
