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
    parents_at_world_origin,
    safe_filename,
    selection_at_world_origin,
    split_selected_meshes,
)
from ..services.layout_service import group_members, group_roots
from ..utils.logging import get_logger

LOGGER = get_logger()


class OBJECT_OT_alb_export_glb(Operator):
    """Export the selected objects to one GLB file, placed on the world origin."""

    bl_idname = "object.alb_export_glb"
    bl_label = "Export GLB"
    bl_description = (
        "Ask for a file, then export the selected objects to one GLB with the shared preset. The "
        "selection is placed on the world origin first (origin bottom center + center, the same as "
        "Batch Export GLB) and put back where it was afterwards. Several separate objects move "
        "together, so they keep their layout relative to each other. With Keep Original Pivot on, "
        "the top-most parent is moved to the world origin instead, so the file keeps that parent's pivot"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(name="File Path", subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.glb", options={"HIDDEN"})
    check_existing: BoolProperty(default=True, options={"HIDDEN"})

    @classmethod
    def poll(cls, context: Context) -> bool:
        return len(context.selected_objects) > 0

    def invoke(self, context: Context, event):
        """Suggest <active object name>.glb next to the .blend file, then ask for the file."""
        if not self.filepath:
            active = context.active_object or context.selected_objects[0]
            folder = Path(bpy.path.abspath("//")) if bpy.data.filepath else Path.home()
            self.filepath = str(folder / f"{safe_filename(active.name)}.glb")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def check(self, context: Context) -> bool:
        """Keep the .glb extension on whatever name is typed in the file browser."""
        fixed = bpy.path.ensure_ext(self.filepath, ".glb")
        if fixed != self.filepath:
            self.filepath = fixed
            return True
        return False

    def execute(self, context: Context):
        settings = context.scene.alb_settings

        if not self.filepath:
            self.report({"ERROR"}, "Choose a file to export to.")
            return {"CANCELLED"}

        roots = group_roots(context.selected_objects)
        if not roots:
            self.report({"ERROR"}, "Select at least one object to export.")
            return {"CANCELLED"}

        filepath = Path(bpy.path.abspath(bpy.path.ensure_ext(self.filepath, ".glb")))
        keep_pivot = settings.export_keep_original_pivot
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with preserved_blender_context(context):
                members = [member for root in roots for member in group_members(root)]
                select_only(context, members, active=roots[0])
                placement = (
                    parents_at_world_origin(roots)
                    if keep_pivot
                    else selection_at_world_origin(roots)
                )
                with placement:
                    export_glb(str(filepath))
        except Exception as exc:
            LOGGER.error("Export GLB failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Export failed: {exc}"
            self.report({"ERROR"}, f"Export GLB failed: {exc}")
            return {"CANCELLED"}

        mode = "with original pivot" if keep_pivot else "at world origin"
        status = f"Exported {filepath.name} {mode}"
        settings.last_status = status
        self.report({"INFO"}, status)
        return {"FINISHED"}


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
        "as one file named after its top-most object. With Keep Original Pivot on, the top-most "
        "parent is moved to the world origin instead, so parts of one parent share its pivot. "
        "With Split Selected Meshes also on, every selected mesh is written to its own file"
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
        keep_pivot = settings.export_keep_original_pivot
        if keep_pivot and settings.export_split_selected_meshes:
            # Each selected mesh is its own file; zeroing its parent keeps the files aligned.
            units = split_selected_meshes(context.selected_objects)
        else:
            units = [(root, group_members(root)) for root in roots]
        exported: list[str] = []
        replaced = 0
        stripped = 0
        used_names: set[str] = set()

        try:
            with preserved_blender_context(context):
                for root, members in units:
                    filepath = directory / f"{_unique_name(safe_filename(root.name), used_names)}.glb"
                    if filepath.exists():
                        replaced += 1
                    select_only(context, members, active=root)
                    placement = (
                        parents_at_world_origin([root])
                        if keep_pivot
                        else centered_at_world_origin(root)
                    )
                    with (
                        placement,
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
