"""Auto Lowpoly Baker add-on entrypoint."""

from __future__ import annotations

import bpy

from .operators.asset_operator import ALB_FH_import_glb, OBJECT_OT_alb_import_glb_asset
from .operators.bake_operator import (
    OBJECT_OT_alb_bake_selected_pair,
    OBJECT_OT_alb_clear_unused_generated_data,
    OBJECT_OT_alb_create_lowmesh,
    OBJECT_OT_alb_create_lowmesh_and_bake,
    OBJECT_OT_alb_origin_bottom_center_to_world,
    OBJECT_OT_alb_reset_config,
    OBJECT_OT_alb_reset_pose,
)
from .operators.export_operator import OBJECT_OT_alb_batch_export_glb, OBJECT_OT_alb_export_glb
from .operators.layout_operator import (
    OBJECT_OT_alb_center_world,
    OBJECT_OT_alb_position_grid,
    OBJECT_OT_alb_position_grid_compact,
)
from .panels.assets_panel import VIEW3D_PT_alb_assets
from .panels.main_panel import VIEW3D_PT_alb_auto_baker
from .properties.settings import ALB_Settings

bl_info = {
    "name": "Auto Lowpoly Baker",
    "author": "OpenAI",
    "version": (1, 19, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Auto Baker / Assets",
    "description": "Create a decimated low-poly copy and bake material color to a PNG texture",
    "category": "Object",
}

CLASSES = (
    ALB_Settings,
    OBJECT_OT_alb_create_lowmesh,
    OBJECT_OT_alb_bake_selected_pair,
    OBJECT_OT_alb_create_lowmesh_and_bake,
    OBJECT_OT_alb_origin_bottom_center_to_world,
    OBJECT_OT_alb_clear_unused_generated_data,
    OBJECT_OT_alb_reset_config,
    OBJECT_OT_alb_reset_pose,
    VIEW3D_PT_alb_auto_baker,
    OBJECT_OT_alb_import_glb_asset,
    ALB_FH_import_glb,
    OBJECT_OT_alb_position_grid,
    OBJECT_OT_alb_position_grid_compact,
    OBJECT_OT_alb_center_world,
    OBJECT_OT_alb_export_glb,
    OBJECT_OT_alb_batch_export_glb,
    VIEW3D_PT_alb_assets,
)


def register() -> None:
    """Register add-on classes and scene properties."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.alb_settings = bpy.props.PointerProperty(type=ALB_Settings)


def unregister() -> None:
    """Unregister add-on classes and scene properties."""
    if hasattr(bpy.types.Scene, "alb_settings"):
        del bpy.types.Scene.alb_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
