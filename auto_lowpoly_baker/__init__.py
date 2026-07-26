"""Auto Lowpoly Baker add-on entrypoint."""

from __future__ import annotations

import bpy

from .operators.bake_operator import OBJECT_OT_alb_auto_bake
from .panels.main_panel import VIEW3D_PT_alb_auto_baker
from .properties.settings import ALB_Settings

bl_info = {
    "name": "Auto Lowpoly Baker",
    "author": "OpenAI",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Auto Baker",
    "description": "Create a decimated low-poly copy and bake material color to a PNG texture",
    "category": "Object",
}

CLASSES = (
    ALB_Settings,
    OBJECT_OT_alb_auto_bake,
    VIEW3D_PT_alb_auto_baker,
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
