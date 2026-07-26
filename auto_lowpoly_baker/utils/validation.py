"""Validation helpers for bake requests."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Context


class ValidationError(Exception):
    """Raised when a user-facing bake precondition is not satisfied."""


def validate_bake_request(context: Context, settings) -> None:
    """Validate active object, mesh data, render support, and output path."""
    obj = context.active_object
    if obj is None:
        raise ValidationError("Select one high-poly mesh object before baking.")
    if obj.type != "MESH":
        raise ValidationError("The active object must be a mesh.")
    if obj.library or obj.data.library:
        raise ValidationError("Linked library objects cannot be baked. Make a local copy first.")
    if obj.hide_get() or obj.hide_viewport:
        raise ValidationError("The active mesh is hidden. Unhide it before baking.")
    if not obj.data.polygons:
        raise ValidationError("The active mesh has no polygons to bake.")
    _ensure_cycles_can_be_selected(context)

    output_directory = settings.output_directory.strip()
    if not output_directory:
        raise ValidationError("Choose an output directory for the PNG texture.")
    if output_directory.startswith("//") and not bpy.data.filepath:
        raise ValidationError("Save the .blend file before using a relative output directory like //textures.")

    absolute_dir = Path(bpy.path.abspath(output_directory)).expanduser()
    parent = absolute_dir if absolute_dir.exists() else absolute_dir.parent
    if not parent.exists():
        raise ValidationError(f"Output parent folder does not exist: {parent}")


def _ensure_cycles_can_be_selected(context: Context) -> None:
    """Verify Cycles by selecting it directly, then restore the original engine."""
    scene = context.scene
    original_engine = scene.render.engine
    try:
        scene.render.engine = "CYCLES"
    except TypeError as exc:
        raise ValidationError(
            "Cycles render engine is not available. Enable/install Cycles or use a Blender build that includes it."
        ) from exc
    finally:
        try:
            scene.render.engine = original_engine
        except TypeError:
            pass
