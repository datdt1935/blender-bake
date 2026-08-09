"""3D View sidebar UI for Auto Lowpoly Baker."""

from __future__ import annotations

from bpy.types import Context, Panel

from ..build_info import BUILD_NUMBER
from ..operators.bake_operator import (
    OBJECT_OT_alb_bake_selected_pair,
    OBJECT_OT_alb_clear_unused_generated_data,
    OBJECT_OT_alb_create_lowmesh,
    OBJECT_OT_alb_create_lowmesh_and_bake,
    OBJECT_OT_alb_origin_bottom_center_to_world,
    OBJECT_OT_alb_reset_config,
    OBJECT_OT_alb_reset_pose,
    find_reset_pose_armature,
)

# glTF export preset applied to Blender's native exporter when the button is clicked.
# GLB, selected-only, +Y up, UVs + Normals, materials exported as WebP (quality 30),
# shape keys + skinning, and Draco mesh compression.
GLB_EXPORT_CONFIG = {
    "export_format": "GLB",
    "export_copyright": "",
    # Include
    "use_selection": True,
    "use_visible": False,
    "use_renderable": False,
    "use_active_collection": False,
    "use_active_scene": False,
    "export_extras": False,
    "export_cameras": False,
    "export_lights": False,
    # Transform
    "export_yup": True,
    # Mesh
    "export_apply": False,
    "export_texcoords": True,
    "export_normals": True,
    "export_tangents": False,
    "export_attributes": False,
    "use_mesh_edges": False,
    "use_mesh_vertices": False,
    "export_shared_accessors": False,
    # Material
    "export_materials": "EXPORT",
    "export_image_format": "WEBP",
    "export_image_quality": 30,
    "export_image_add_webp": False,
    "export_image_webp_fallback": False,
    # Data
    "export_morph": True,
    "export_skins": True,
    # Draco compression
    "export_draco_mesh_compression_enable": True,
    "export_draco_mesh_compression_level": 6,
    "export_draco_position_quantization": 14,
    "export_draco_normal_quantization": 10,
    "export_draco_texcoord_quantization": 12,
    "export_draco_color_quantization": 10,
    "export_draco_generic_quantization": 12,
}


class VIEW3D_PT_alb_auto_baker(Panel):
    """Auto Baker panel in the 3D View sidebar."""

    bl_label = f"Auto Baker v{BUILD_NUMBER}"
    bl_idname = "VIEW3D_PT_alb_auto_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auto Baker"

    def draw(self, context: Context) -> None:
        layout = self.layout
        settings = context.scene.alb_settings
        active = context.active_object
        high = settings.high_quality_object or active
        low = settings.low_quality_object
        has_valid_high = high is not None and high.type == "MESH"
        has_valid_low = low is not None and low.type == "MESH"

        input_box = layout.box()
        input_box.label(text="Objects", icon="OBJECT_DATA")
        input_box.prop(settings, "high_quality_object")
        input_box.prop(settings, "low_quality_object")
        if has_valid_high:
            input_box.label(text=f"High: {high.name} | Vertices: {_vertex_count(high)}", icon="MESH_DATA")
        else:
            input_box.label(text="Choose a High Quality mesh", icon="ERROR")
        if has_valid_low:
            input_box.label(text=f"Low: {low.name} | Vertices: {_vertex_count(low)}", icon="MESH_DATA")

        mesh_box = layout.box()
        mesh_box.label(text="Low Mesh Config", icon="MOD_DECIM")
        mesh_box.prop(settings, "reduction_mode")
        if settings.reduction_mode == "TARGET_VERTICES":
            mesh_box.prop(settings, "target_vertex_count")
        else:
            mesh_box.prop(settings, "decimate_ratio")
        mesh_box.prop(settings, "merge_distance")
        mesh_box.prop(settings, "uv_island_margin")

        bake_box = layout.box()
        bake_box.label(text="Bake Config", icon="RENDER_STILL")
        bake_box.prop(settings, "texture_resolution")
        bake_box.prop(settings, "bake_margin")
        bake_box.prop(settings, "ray_distance")

        action_box = layout.box()
        action_box.label(text="Actions", icon="PLAY")
        one_click_row = action_box.row()
        one_click_row.enabled = has_valid_high
        one_click_row.operator(OBJECT_OT_alb_create_lowmesh_and_bake.bl_idname, icon="RENDER_STILL")

        create_row = action_box.row()
        create_row.enabled = has_valid_high
        create_row.operator(OBJECT_OT_alb_create_lowmesh.bl_idname, icon="MOD_DECIM")

        bake_row = action_box.row()
        bake_row.enabled = has_valid_high and has_valid_low and high != low
        bake_row.operator(OBJECT_OT_alb_bake_selected_pair.bl_idname, icon="RENDER_STILL")

        util_box = layout.box()
        util_box.label(text="Utilities", icon="PIVOT_BOUNDBOX")
        util_row = util_box.row()
        util_row.enabled = active is not None and active.type == "MESH"
        util_row.operator(OBJECT_OT_alb_origin_bottom_center_to_world.bl_idname, icon="OBJECT_ORIGIN")
        util_box.operator(OBJECT_OT_alb_reset_config.bl_idname, icon="LOOP_BACK")
        util_box.operator(OBJECT_OT_alb_clear_unused_generated_data.bl_idname, icon="TRASH")

        rig_box = layout.box()
        rig_box.label(text="Rig", icon="ARMATURE_DATA")
        rig_box.prop(settings, "reset_pose_disable_anim")
        reset_pose_row = rig_box.row()
        reset_pose_row.enabled = find_reset_pose_armature(context) is not None
        reset_pose_row.operator(OBJECT_OT_alb_reset_pose.bl_idname, icon="POSE_HLT")

        export_box = layout.box()
        export_box.label(text="Export", icon="EXPORT")
        export_row = export_box.row()
        export_row.enabled = len(context.selected_objects) > 0
        # Open Blender's native glTF exporter with the preset config pre-filled.
        export_op = export_row.operator("export_scene.gltf", text="Export GLB", icon="EXPORT")
        for prop_name, prop_value in GLB_EXPORT_CONFIG.items():
            setattr(export_op, prop_name, prop_value)

        if settings.last_status:
            layout.label(text=settings.last_status, icon="INFO")


def _vertex_count(obj) -> int:
    """Return vertex count for UI display."""
    return len(obj.data.vertices) if obj and obj.type == "MESH" else 0
