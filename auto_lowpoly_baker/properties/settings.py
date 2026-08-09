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
