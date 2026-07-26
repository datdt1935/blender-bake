"""Cycles diffuse bake configuration."""

from __future__ import annotations

import bpy
from bpy.types import Scene


def configure_diffuse_bake(scene: Scene, margin: int, ray_distance: float) -> None:
    """Configure Cycles selected-to-active diffuse color baking."""
    scene.render.engine = "CYCLES"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = min(max(getattr(scene.cycles, "samples", 64), 1), 64)

    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.margin = margin
    bake.use_cage = False
    if hasattr(bake, "max_ray_distance"):
        bake.max_ray_distance = ray_distance
    if hasattr(bake, "cage_extrusion"):
        bake.cage_extrusion = 0.0
    if hasattr(bake, "target"):
        bake.target = "IMAGE_TEXTURES"
    if hasattr(bake, "use_pass_direct"):
        bake.use_pass_direct = False
    if hasattr(bake, "use_pass_indirect"):
        bake.use_pass_indirect = False
    if hasattr(bake, "use_pass_color"):
        bake.use_pass_color = True


def run_diffuse_bake(margin: int, ray_distance: float) -> None:
    """Run Blender's diffuse color bake operator."""
    kwargs = {
        "type": "DIFFUSE",
        "pass_filter": {"COLOR"},
        "use_clear": True,
        "margin": margin,
        "use_selected_to_active": True,
    }
    # Blender 4.x exposes max_ray_distance for selected-to-active ray search.
    kwargs["max_ray_distance"] = ray_distance
    bpy.ops.object.bake(**kwargs)
