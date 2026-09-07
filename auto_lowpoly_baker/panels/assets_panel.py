"""3D View sidebar UI for importing and normalizing GLB assets."""

from __future__ import annotations

from bpy.types import Context, Panel

from ..operators.asset_operator import OBJECT_OT_alb_import_glb_asset
from ..operators.layout_operator import (
    OBJECT_OT_alb_center_world,
    OBJECT_OT_alb_position_grid,
    OBJECT_OT_alb_position_grid_compact,
)


class VIEW3D_PT_alb_assets(Panel):
    """Assets panel in its own 3D View sidebar tab."""

    bl_label = "Assets"
    bl_idname = "VIEW3D_PT_alb_assets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Assets"

    def draw(self, context: Context) -> None:
        layout = self.layout
        settings = context.scene.alb_settings

        import_box = layout.box()
        import_box.label(text="Import GLB", icon="IMPORT")
        import_box.label(text="Drag .glb file(s) into the viewport, or:")
        import_box.operator(
            OBJECT_OT_alb_import_glb_asset.bl_idname,
            text="Select GLB File(s)...",
            icon="FILE_FOLDER",
        )
        import_box.label(text="Ctrl/Shift-click to import several at once.")
        import_box.separator()
        import_box.label(text=f"Keeps mesh '{settings.asset_mesh_name}'", icon="MESH_DATA")
        import_box.label(text=f"Applies material '{settings.asset_material_name}'", icon="MATERIAL")
        import_box.label(text=f"Moves to collection '{settings.asset_collection_name}'", icon="OUTLINER_COLLECTION")

        has_selection = len(context.selected_objects) > 0

        layout_box = layout.box()
        layout_box.label(text="Layout", icon="OBJECT_ORIGIN")

        grid_row = layout_box.row(align=True)
        grid_row.enabled = has_selection
        grid_row.operator(OBJECT_OT_alb_position_grid.bl_idname, icon="MESH_GRID")
        grid_row.operator(OBJECT_OT_alb_center_world.bl_idname, icon="WORLD")

        layout_box.separator()
        layout_box.prop(settings, "layout_spacing")
        layout_box.prop(settings, "layout_sort_by_size")
        compact_row = layout_box.row(align=True)
        compact_row.enabled = has_selection
        compact_row.operator(OBJECT_OT_alb_position_grid_compact.bl_idname, icon="MOD_ARRAY")

        advanced_box = layout.box()
        advanced_header = advanced_box.row()
        advanced_header.prop(
            settings,
            "asset_show_advanced",
            icon="TRIA_DOWN" if settings.asset_show_advanced else "TRIA_RIGHT",
            text="Advanced",
            emboss=False,
        )
        if settings.asset_show_advanced:
            advanced_box.prop(settings, "asset_mesh_name")
            advanced_box.prop(settings, "asset_material_name")
            advanced_box.prop(settings, "asset_collection_name")

        if settings.asset_last_status:
            layout.label(text=settings.asset_last_status, icon="INFO")
