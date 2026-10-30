"""Scene settings for Auto Lowpoly Baker."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup


class ALB_Settings(PropertyGroup):
    """User-facing settings stored on the active scene."""

    high_quality_object: PointerProperty(
        name="High Quality",
        description="Source high-poly mesh used as the bake source",
        type=bpy.types.Object,
    )
    low_quality_object: PointerProperty(
        name="Low Quality",
        description="Generated or selected low-poly mesh used as the bake target",
        type=bpy.types.Object,
    )
    decimate_ratio: FloatProperty(
        name="Decimate Ratio",
        description="Fraction of geometry to keep on the generated low-poly copy",
        default=0.25,
        min=0.01,
        max=1.0,
        subtype="FACTOR",
    )
    reduction_mode: EnumProperty(
        name="Reduction Mode",
        description="Choose whether low-poly reduction is driven by ratio or target vertex count",
        default="RATIO",
        items=(
            ("RATIO", "Ratio", "Use Decimate Ratio"),
            ("TARGET_VERTICES", "Target Vertices", "Compute Decimate Ratio from the requested vertex count"),
        ),
    )
    target_vertex_count: IntProperty(
        name="Target Vertices",
        description="Approximate maximum vertex count for the generated low-poly mesh",
        default=5000,
        min=3,
        max=10_000_000,
    )
    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Merge vertices closer than this distance before and after Decimate",
        default=0.0001,
        min=0.0,
        max=1.0,
        precision=5,
    )
    texture_resolution: EnumProperty(
        name="Texture Resolution",
        description="Width and height of the generated square diffuse texture",
        default="2048",
        items=(
            ("128", "128", "128 x 128"),
            ("256", "256", "256 x 256"),
            ("512", "512", "512 x 512"),
            ("1024", "1024", "1024 x 1024"),
            ("2048", "2048", "2048 x 2048"),
            ("4096", "4096", "4096 x 4096"),
            ("8192", "8192", "8192 x 8192"),
        ),
    )
    uv_island_margin: FloatProperty(
        name="UV Island Margin",
        description="Margin used by Smart UV Project when unwrapping the low-poly copy",
        default=0.02,
        min=0.0,
        max=0.5,
    )
    bake_margin: IntProperty(
        name="Bake Margin",
        description="Pixel padding around UV islands in the baked texture",
        default=16,
        min=0,
        max=128,
    )
    ray_distance: FloatProperty(
        name="Ray Distance",
        description="Maximum distance used to find the high-poly surface during selected-to-active bake",
        default=0.05,
        min=0.0,
        max=10.0,
        precision=3,
    )
    output_directory: StringProperty(
        name="Output Directory",
        description="Folder for the baked PNG; use // for a path relative to the saved .blend file",
        default="//textures",
        subtype="DIR_PATH",
    )
    pack_image: BoolProperty(
        name="Pack Image",
        description="Pack the baked PNG into the .blend file after saving it",
        default=False,
    )
    keep_temporary_data: BoolProperty(
        name="Keep Temporary Data",
        description="Keep generated objects, materials, and images if baking fails",
        default=False,
    )
    reset_pose_disable_anim: BoolProperty(
        name="Uncheck Active Animations",
        description=(
            "When resetting the pose, uncheck (mute) the rig's active animation tracks so the pose "
            "returns to its rest state instead of the animated pose"
        ),
        default=True,
    )
    last_status: StringProperty(
        name="Status",
        description="Last Auto Baker status message",
        default="",
        options={"SKIP_SAVE"},
    )
    asset_mesh_name: StringProperty(
        name="Mesh Name",
        description="Name of the mesh object to keep after importing a GLB asset; every other imported object is deleted",
        default="Mesh",
    )
    asset_material_name: StringProperty(
        name="Material Name",
        description="Existing material applied to the kept mesh after import",
        default="MaterialAll",
    )
    asset_collection_name: StringProperty(
        name="Collection Name",
        description="Collection the kept mesh is moved into after import",
        default="Objects",
    )
    asset_show_advanced: BoolProperty(
        name="Advanced",
        description="Show advanced options for customizing the GLB import behavior",
        default=False,
    )
    asset_last_status: StringProperty(
        name="Asset Status",
        description="Last Assets tab status message",
        default="",
        options={"SKIP_SAVE"},
    )
    export_ignore_material: StringProperty(
        name="Ignore Material",
        description=(
            "Material stripped from the objects before Batch Export GLB writes them, and put "
            "back afterwards, so it never ends up in the exported file. Blender's duplicate "
            "suffix is ignored, so Assets_Palette also matches Assets_Palette.001. Leave the "
            "field empty to export every material"
        ),
        default="Assets_Palette",
    )
    export_keep_original_pivot: BoolProperty(
        name="Keep Original Pivot",
        description=(
            "Export in parent (local) space with a shared pivot. The top-most parent of each "
            "selected object (for example an Empty) is moved to the world origin for the export "
            "and put back afterwards; no object origin is changed. Parts exported from the same "
            "parent all share that parent's pivot, so placing them at one transform in the engine "
            "rebuilds them exactly as in Blender. A top-level object is exported around its own "
            "origin. When off, every group is re-centered on its bounding-box bottom center"
        ),
        default=True,
    )
    export_split_selected_meshes: BoolProperty(
        name="Split Selected Meshes",
        description=(
            "Batch Export GLB only, with Keep Original Pivot on. Every selected mesh is written "
            "to its own <mesh name>.glb holding only that mesh, with its top-most parent (for "
            "example an Empty) moved to the world origin. Unselected parts are left out. Each "
            "file loads at 0, 0, 0 and the parts still line up with each other as in Blender. "
            "A selected Empty is skipped when something under it is selected too; selected on "
            "its own it is still exported as one file with everything under it"
        ),
        default=True,
    )
    layout_spacing: FloatProperty(
        name="Compact Spacing",
        description="Exact edge-to-edge gap between neighboring object bounding boxes used by Compact Grid",
        default=0.1,
        min=0.0,
        subtype="DISTANCE",
    )
    layout_sort_by_size: BoolProperty(
        name="Sort Largest to Smallest",
        description=(
            "Order objects by bounding-box size (largest first, left to right) before packing "
            "them with Compact Grid, for a more visually balanced layout. When off, objects "
            "are packed in their current selection order"
        ),
        default=True,
    )
