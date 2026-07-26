"""3D View sidebar UI for Auto Lowpoly Baker."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel

from ..operators.bake_operator import OBJECT_OT_alb_auto_bake


class VIEW3D_PT_alb_auto_baker(Panel):
    """Auto Baker panel in the 3D View sidebar."""

    bl_label = "Auto Baker"
    bl_idname = "VIEW3D_PT_alb_auto_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auto Baker"

    def draw(self, context: Context) -> None:
        layout = self.layout
        settings = context.scene.alb_settings
        active = context.active_object
        has_valid_mesh = active is not None and active.type == "MESH"

        input_box = layout.box()
        input_box.label(text="Input", icon="OBJECT_DATA")
        if has_valid_mesh:
            input_box.label(text=active.name, icon="MESH_DATA")
        else:
            input_box.label(text="Select one mesh object", icon="ERROR")

        mesh_box = layout.box()
        mesh_box.label(text="Low-poly", icon="MOD_DECIM")
        mesh_box.prop(settings, "decimate_ratio")
        mesh_box.prop(settings, "uv_island_margin")

        bake_box = layout.box()
        bake_box.label(text="Bake", icon="RENDER_STILL")
        bake_box.prop(settings, "texture_resolution")
        bake_box.prop(settings, "bake_margin")
        bake_box.prop(settings, "ray_distance")

        output_box = layout.box()
        output_box.label(text="Output", icon="FILE_IMAGE")
        output_box.prop(settings, "output_directory")
        output_box.prop(settings, "pack_image")
        output_box.prop(settings, "keep_temporary_data")

        row = layout.row()
        row.enabled = has_valid_mesh
        row.operator(OBJECT_OT_alb_auto_bake.bl_idname, icon="RENDER_STILL")

        if settings.last_status:
            layout.label(text=settings.last_status, icon="INFO")
