"""Mesh creation, decimation, and UV helpers."""

from __future__ import annotations

import bpy
from bpy.types import Context, Object

from .context_service import select_only


def create_lowpoly_copy(context: Context, source: Object, decimate_ratio: float) -> Object:
    """Create a separate low-poly object by applying Decimate to a duplicate mesh."""
    low = source.copy()
    low.data = source.data.copy()
    low.animation_data_clear()
    low.name = f"{source.name}_LOW"
    low.data.name = f"{source.data.name}_LOW"
    context.collection.objects.link(low)

    select_only(context, [low], low)
    modifier = low.modifiers.new(name="Auto Baker Decimate", type="DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = decimate_ratio
    modifier.use_collapse_triangulate = False
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    low.data.update()
    return low


def smart_uv_unwrap(context: Context, obj: Object, island_margin: float) -> None:
    """Generate a UV map on the object using Blender's Smart UV Project operator."""
    select_only(context, [obj], obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=1.15192,
        island_margin=island_margin,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    if not obj.data.uv_layers:
        raise RuntimeError("Smart UV Project did not create a UV map")
