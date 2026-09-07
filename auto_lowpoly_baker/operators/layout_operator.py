"""Operators for arranging selected objects: grid layout and world-center reset."""

from __future__ import annotations

import traceback

from bpy.types import Context, Operator

from ..services.layout_service import arrange_compact_grid, arrange_grid, center_on_world_origin
from ..utils.logging import get_logger

LOGGER = get_logger()


class OBJECT_OT_alb_position_grid(Operator):
    """Arrange all selected objects into an evenly spaced, non-overlapping grid."""

    bl_idname = "object.alb_position_grid"
    bl_label = "Position Grid"
    bl_description = "Arrange the selected objects into an evenly spaced grid with no overlap"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return len(context.selected_objects) > 0

    def execute(self, context: Context):
        objects = context.selected_objects
        try:
            arrange_grid(objects)
        except Exception as exc:
            LOGGER.error("Position Grid failed: %s\n%s", exc, traceback.format_exc())
            self.report({"ERROR"}, f"Position Grid failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Arranged {len(objects)} object(s) into a grid.")
        return {"FINISHED"}


class OBJECT_OT_alb_position_grid_compact(Operator):
    """Pack selected objects with 2D rectangle packing based on their bounding boxes."""

    bl_idname = "object.alb_position_grid_compact"
    bl_label = "Compact Grid"
    bl_description = (
        "Pack the selected objects on the XY plane using 2D rectangle packing sized from each "
        "object's bounding box: an exact edge-to-edge gap between neighbors, bottoms aligned to "
        "Z = 0, rotation/scale preserved, and the result centered on the world origin"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return len(context.selected_objects) > 0

    def execute(self, context: Context):
        objects = context.selected_objects
        settings = context.scene.alb_settings
        try:
            arrange_compact_grid(objects, spacing=settings.layout_spacing, sort_by_size=settings.layout_sort_by_size)
        except Exception as exc:
            LOGGER.error("Compact Grid failed: %s\n%s", exc, traceback.format_exc())
            self.report({"ERROR"}, f"Compact Grid failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Packed {len(objects)} object(s) into a compact layout.")
        return {"FINISHED"}


class OBJECT_OT_alb_center_world(Operator):
    """Move every selected object's origin to the world center."""

    bl_idname = "object.alb_center_world"
    bl_label = "Center World"
    bl_description = "Move all selected objects to the world center (0, 0, 0)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return len(context.selected_objects) > 0

    def execute(self, context: Context):
        objects = context.selected_objects
        try:
            center_on_world_origin(objects)
        except Exception as exc:
            LOGGER.error("Center World failed: %s\n%s", exc, traceback.format_exc())
            self.report({"ERROR"}, f"Center World failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Moved {len(objects)} object(s) to world center.")
        return {"FINISHED"}
