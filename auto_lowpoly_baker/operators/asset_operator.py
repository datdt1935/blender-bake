"""Operators for the Assets tab: import a GLB and normalize it into the project."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy
from bpy.props import CollectionProperty, StringProperty
from bpy.types import Context, Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper

from ..services.asset_service import (
    apply_named_material,
    derive_asset_name,
    import_gltf_objects,
    keep_only_named_mesh,
    move_to_collection,
    rename_asset,
    rename_with_prefix,
)
from ..utils.logging import get_logger

LOGGER = get_logger()


class OBJECT_OT_alb_import_glb_asset(Operator, ImportHelper):
    """Import a GLB asset, keep only its named mesh, and normalize material/collection."""

    bl_idname = "object.alb_import_glb_asset"
    bl_label = "Import GLB Asset"
    bl_description = (
        "Import one or more GLB files (Ctrl/Shift-click to multi-select). For each file, keep "
        "only the configured mesh, apply the configured material, and move it into the "
        "configured collection"
    )
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".glb"
    filter_glob: StringProperty(default="*.glb;*.gltf", options={"HIDDEN"})

    # Declaring directory + files (matching Blender's own glTF importer) makes the file
    # browser allow multi-selecting files; they're also what the viewport drag-and-drop
    # (FileHandler) drop fills in. A single click-through fills filepath instead.
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: CollectionProperty(type=OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        filepaths = self._resolve_filepaths()
        if not filepaths:
            self.report({"ERROR"}, "No GLB file selected.")
            return {"CANCELLED"}

        imported_count = 0
        failed_files: list[str] = []
        for filepath in filepaths:
            if self._import_one(context, settings, filepath, failed_files):
                imported_count += 1

        if failed_files:
            self.report(
                {"WARNING"},
                f"No mesh named '{settings.asset_mesh_name}' found in: {', '.join(failed_files)}. "
                "Their objects were kept and renamed with the file name for inspection.",
            )

        if imported_count == 0 and not failed_files:
            return {"CANCELLED"}

        status = f"Imported {imported_count}/{len(filepaths)} asset(s)"
        if failed_files:
            status += f"; {len(failed_files)} missing '{settings.asset_mesh_name}': {', '.join(failed_files)}"
        settings.asset_last_status = status
        return {"FINISHED"}

    def _resolve_filepaths(self) -> list[str]:
        if self.files:
            return [str(Path(self.directory) / f.name) for f in self.files if f.name]
        return [self.filepath] if self.filepath else []

    def _import_one(self, context: Context, settings, filepath: str, failed_files: list[str]) -> bool:
        file_label = Path(filepath).name
        asset_name = derive_asset_name(filepath)

        try:
            settings.asset_last_status = f"Importing {file_label}..."
            imported = import_gltf_objects(filepath)
            mesh_obj = keep_only_named_mesh(imported, settings.asset_mesh_name)

            if mesh_obj is None:
                rename_with_prefix(imported, asset_name)
                failed_files.append(file_label)
                self.report(
                    {"WARNING"},
                    f"No mesh named '{settings.asset_mesh_name}' in {file_label}; "
                    f"kept {len(imported)} object(s) prefixed with '{asset_name}_'.",
                )
                return False

            rename_asset(mesh_obj, asset_name)

            if not apply_named_material(mesh_obj, settings.asset_material_name):
                self.report(
                    {"WARNING"},
                    f"Material '{settings.asset_material_name}' not found; kept imported material(s).",
                )

            move_to_collection(context, mesh_obj, settings.asset_collection_name)
            bpy.data.orphans_purge(do_recursive=True)

            settings.asset_last_status = f"Imported '{mesh_obj.name}'"
            self.report({"INFO"}, f"Imported '{mesh_obj.name}' from {file_label}.")
            return True

        except Exception as exc:
            LOGGER.error("Import GLB asset failed: %s\n%s", exc, traceback.format_exc())
            settings.asset_last_status = f"Import failed: {exc}"
            self.report({"ERROR"}, f"Import GLB asset failed: {exc}")
            return False


class ALB_FH_import_glb(bpy.types.FileHandler):
    """Let Blender's viewport drag-and-drop hand .glb/.gltf files to the asset importer."""

    bl_idname = "ALB_FH_import_glb"
    bl_label = "Import GLB Asset"
    bl_import_operator = OBJECT_OT_alb_import_glb_asset.bl_idname
    bl_file_extensions = ".glb;.gltf"

    @classmethod
    def poll_drop(cls, context: Context) -> bool:
        return context.area is not None and context.area.type == "VIEW_3D"
