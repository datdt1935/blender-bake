"""Scene settings for Auto Lowpoly Baker."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class ALB_Settings(PropertyGroup):
    """User-facing settings stored on the active scene."""

    decimate_ratio: FloatProperty(
        name="Decimate Ratio",
        description="Fraction of geometry to keep on the generated low-poly copy",
        default=0.25,
        min=0.01,
        max=1.0,
        subtype="FACTOR",
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
    last_status: StringProperty(
        name="Status",
        description="Last Auto Baker status message",
        default="",
        options={"SKIP_SAVE"},
    )
