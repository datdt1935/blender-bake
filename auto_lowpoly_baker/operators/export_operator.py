"""Operators for exporting selected objects as GLB files."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator

from ..services.context_service import preserved_blender_context, select_only
from ..services.export_service import (
    centered_at_world_origin,
    export_glb,
    materials_stripped,
    safe_filename,
)
from ..services.layout_service import group_members, group_roots
from ..utils.logging import get_logger

LOGGER = get_logger()


class OBJECT_OT_alb_batch_export_glb(Operator):
    """Export every selected object to its own GLB file inside a chosen folder."""

    bl_idname = "object.alb_batch_export_glb"
    bl_label = "Batch Export GLB"
    bl_description = (
        "Ask for a folder, then export each selected object to its own <object name>.glb using the "
        "same preset as Export GLB. Every object is placed on the world origin first (origin bottom "
        "center + center) and put back where it was afterwards, so each file holds the object at "
        "0, 0, 0 instead of its position in the scene. Material slots holding the Ignore Material "
        "are emptied for the export and filled back in afterwards. A parented hierarchy is exported "
        "as one file named after its top-most object"
    )
    bl_options = {"REGISTER", "UNDO"}

    directory: StringProperty(
        name="Folder",
        description="Folder the GLB files are written to",
        subtype="DIR_PATH",
    )
    filter_folder: BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context: Context) -> bool:
        return len(context.selected_objects) > 0

    def invoke(self, context: Context, event):
        """Ask for the destination folder before anything is exported."""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: Context):
        settings = context.scene.alb_settings

        if not self.directory:
            self.report({"ERROR"}, "Choose a folder to export into.")
            return {"CANCELLED"}

        roots = group_roots(context.selected_objects)
        if not roots:
            self.report({"ERROR"}, "Select at least one object to export.")
            return {"CANCELLED"}

        directory = Path(bpy.path.abspath(self.directory))
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            LOGGER.error("Batch Export GLB failed to open %s: %s", directory, exc)
            settings.last_status = f"Batch export failed: {exc}"
            self.report({"ERROR"}, f"Cannot use folder {directory}: {exc}")
            return {"CANCELLED"}

        ignore_material = settings.export_ignore_material
        exported: list[str] = []
        replaced = 0
        stripped = 0
        used_names: set[str] = set()

        try:
            with preserved_blender_context(context):
                for root in roots:
                    filepath = directory / f"{_unique_name(safe_filename(root.name), used_names)}.glb"
                    if filepath.exists():
                        replaced += 1
                    members = group_members(root)
                    select_only(context, members, active=root)
                    with (
                        centered_at_world_origin(root),
                        materials_stripped(members, ignore_material) as slots_cleared,
                    ):
                        export_glb(str(filepath))
                    stripped += slots_cleared
                    exported.append(filepath.name)
        except Exception as exc:
            LOGGER.error("Batch Export GLB failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Batch export failed after {len(exported)} file(s): {exc}"
            self.report({"ERROR"}, f"Batch Export GLB failed after {len(exported)} file(s): {exc}")
            return {"CANCELLED"}

        overwritten = f", {replaced} overwritten" if replaced else ""
        ignored = f", {stripped} '{ignore_material}' slot(s) left out" if stripped else ""
        status = f"Exported {len(exported)} GLB file(s) to {directory}{overwritten}{ignored}"
        settings.last_status = status
        self.report({"INFO"}, status)
        return {"FINISHED"}


def _unique_name(stem: str, used: set[str]) -> str:
    """Keep two objects whose names clean up to the same file name from overwriting each other."""
    candidate = stem
    index = 1
    while candidate.casefold() in used:
        index += 1
        candidate = f"{stem}_{index}"
    used.add(candidate.casefold())
    return candidate
