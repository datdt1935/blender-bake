"""Helpers for preserving and restoring Blender context."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

import bpy
from bpy.types import Context, Object


def select_only(context: Context, objects: Iterable[Object], active: Object | None = None) -> None:
    """Select only the provided objects and set the active object."""
    bpy.ops.object.select_all(action="DESELECT")
    object_list = [obj for obj in objects if obj and obj.name in bpy.data.objects]
    for obj in object_list:
        obj.select_set(True)
    context.view_layer.objects.active = active if active else (object_list[-1] if object_list else None)


def ensure_object_mode(context: Context) -> None:
    """Switch the active object to Object Mode when possible."""
    active = context.active_object
    if active and active.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


@contextmanager
def preserved_blender_context(context: Context):
    """Preserve common UI-sensitive state while an operator manipulates Blender context."""
    scene = context.scene
    view_layer = context.view_layer
    active_object = context.active_object
    selected_objects = list(context.selected_objects)
    mode = active_object.mode if active_object else "OBJECT"
    render_engine = scene.render.engine
    frame_current = scene.frame_current
    bake_settings = _snapshot_bake_settings(scene)

    ensure_object_mode(context)
    try:
        yield
    finally:
        _restore_bake_settings(scene, bake_settings)
        scene.render.engine = render_engine
        scene.frame_set(frame_current)

        if context.object and context.object.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass

        bpy.ops.object.select_all(action="DESELECT")
        for obj in selected_objects:
            if obj and obj.name in bpy.data.objects:
                obj.select_set(True)
        if active_object and active_object.name in bpy.data.objects:
            view_layer.objects.active = active_object
            if mode != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode=mode)
                except RuntimeError:
                    bpy.ops.object.mode_set(mode="OBJECT")


def _snapshot_bake_settings(scene: bpy.types.Scene) -> dict[str, object]:
    bake = scene.render.bake
    names = (
        "use_selected_to_active",
        "margin",
        "max_ray_distance",
        "cage_extrusion",
        "use_cage",
        "target",
        "use_pass_direct",
        "use_pass_indirect",
        "use_pass_color",
    )
    return {name: getattr(bake, name) for name in names if hasattr(bake, name)}


def _restore_bake_settings(scene: bpy.types.Scene, values: dict[str, object]) -> None:
    bake = scene.render.bake
    for name, value in values.items():
        if hasattr(bake, name):
            setattr(bake, name, value)
