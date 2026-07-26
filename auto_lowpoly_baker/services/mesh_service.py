"""Mesh creation, decimation, and UV helpers."""

from __future__ import annotations

import bpy
import bmesh
from bpy.types import Context, Object

from .context_service import select_only


def create_lowpoly_copy(
    context: Context,
    source: Object,
    decimate_ratio: float,
    merge_distance: float,
    reduction_mode: str,
    target_vertex_count: int,
) -> Object:
    """Create a separate low-poly object by applying Decimate to a duplicate mesh."""
    low = source.copy()
    low.data = source.data.copy()
    low.animation_data_clear()
    low_name = f"{source.name}_LOW"
    low.name = low_name
    low.data.name = low_name
    context.collection.objects.link(low)

    removed_before = merge_by_distance(low, merge_distance)
    input_vertex_count = len(low.data.vertices)
    effective_ratio = _effective_decimate_ratio(
        decimate_ratio,
        input_vertex_count,
        reduction_mode,
        target_vertex_count,
    )

    select_only(context, [low], low)
    _apply_decimate_modifier(low, effective_ratio)
    removed_after = merge_by_distance(low, merge_distance)
    _limit_vertices_with_extra_decimate_passes(
        context,
        low,
        reduction_mode,
        target_vertex_count,
        merge_distance,
    )
    low.data.update()
    low["auto_baker_merged_vertices"] = removed_before + removed_after
    low["auto_baker_input_vertices"] = input_vertex_count
    low["auto_baker_output_vertices"] = len(low.data.vertices)
    low["auto_baker_decimate_ratio"] = effective_ratio
    if reduction_mode == "TARGET_VERTICES":
        low["auto_baker_target_vertices"] = target_vertex_count
    return low


def merge_by_distance(obj: Object, distance: float) -> int:
    """Merge duplicate or very close vertices on mesh data and return the removed count."""
    if distance <= 0.0:
        return 0

    mesh = obj.data
    before_count = len(mesh.vertices)
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=distance)
        bm.to_mesh(mesh)
    finally:
        bm.free()

    mesh.update()
    return max(before_count - len(mesh.vertices), 0)


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


def _effective_decimate_ratio(
    decimate_ratio: float,
    input_vertex_count: int,
    reduction_mode: str,
    target_vertex_count: int,
) -> float:
    """Return the Decimate ratio for ratio mode or target-vertices mode."""
    if reduction_mode != "TARGET_VERTICES" or input_vertex_count <= 0:
        return max(0.01, min(decimate_ratio, 1.0))
    if target_vertex_count >= input_vertex_count:
        return 1.0
    return max(0.01, min(target_vertex_count / input_vertex_count, 1.0))


def _apply_decimate_modifier(obj: Object, ratio: float) -> None:
    """Apply one Collapse Decimate modifier pass."""
    modifier = obj.modifiers.new(name="Auto Baker Decimate", type="DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = max(0.01, min(ratio, 1.0))
    modifier.use_collapse_triangulate = False
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def _limit_vertices_with_extra_decimate_passes(
    context: Context,
    obj: Object,
    reduction_mode: str,
    target_vertex_count: int,
    merge_distance: float,
) -> None:
    """Run a few extra decimate passes when target-vertices mode is still above target."""
    if reduction_mode != "TARGET_VERTICES":
        return

    previous_count = len(obj.data.vertices)
    for _index in range(3):
        current_count = len(obj.data.vertices)
        if current_count <= target_vertex_count or current_count <= 3:
            return
        if current_count >= previous_count and _index > 0:
            return

        previous_count = current_count
        ratio = max(0.01, min(target_vertex_count / current_count, 1.0))
        select_only(context, [obj], obj)
        _apply_decimate_modifier(obj, ratio)
        merge_by_distance(obj, merge_distance)
