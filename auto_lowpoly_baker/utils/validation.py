"""Validation helpers for bake requests."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Context


class ValidationError(Exception):
    """Raised when a user-facing bake precondition is not satisfied."""


def validate_mesh_object(obj: bpy.types.Object | None, label: str) -> bpy.types.Object:
    """Validate a mesh object pointer selected in the UI."""
    if obj is None:
        raise ValidationError(f"Choose a {label} mesh object.")
    if obj.name not in bpy.data.objects:
        raise ValidationError(f"The selected {label} object no longer exists.")
    if obj.type != "MESH":
        raise ValidationError(f"{label} must be a mesh object.")
    if obj.library or obj.data.library:
        raise ValidationError(f"{label} is linked from a library. Make a local copy first.")
    if obj.hide_get() or obj.hide_viewport:
        raise ValidationError(f"{label} is hidden. Unhide it before baking.")
    if not obj.data.polygons:
        raise ValidationError(f"{label} has no polygons.")
    return obj


def validate_create_lowmesh_request(context: Context, settings) -> bpy.types.Object:
    """Validate input for the low-poly creation step."""
    source = settings.high_quality_object or context.active_object
    return validate_mesh_object(source, "High Quality")


def validate_existing_bake_request(context: Context, settings) -> tuple[bpy.types.Object, bpy.types.Object]:
    """Validate input for baking an existing high-to-low object pair."""
    high = validate_mesh_object(settings.high_quality_object, "High Quality")
    low = validate_mesh_object(settings.low_quality_object or context.active_object, "Low Quality")
    if high == low:
        raise ValidationError("High Quality and Low Quality must be different objects.")
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

    return high, low


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
