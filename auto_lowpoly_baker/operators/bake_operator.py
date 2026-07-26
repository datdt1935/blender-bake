"""Main operator for creating a low-poly copy and baking diffuse color."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy
from bpy.types import Context, Operator

from ..services.bake_service import configure_diffuse_bake, run_diffuse_bake
from ..services.context_service import preserved_blender_context, select_only
from ..services.material_service import create_bake_image, create_bake_material, pack_image, save_image_png
from ..services.mesh_service import create_lowpoly_copy, smart_uv_unwrap
from ..utils.logging import get_logger
from ..utils.validation import ValidationError, validate_bake_request

LOGGER = get_logger()


class OBJECT_OT_alb_auto_bake(Operator):
    """Duplicate the active mesh, decimate it, unwrap it, and bake diffuse color."""

    bl_idname = "object.alb_auto_bake"
    bl_label = "Create Lowpoly & Bake"
    bl_description = "Duplicate the active high-poly mesh, create a low-poly copy, and bake diffuse color"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        source = context.active_object
        created = {
            "low_object": None,
            "low_mesh": None,
            "material": None,
            "image": None,
            "saved_path": None,
        }

        try:
            validate_bake_request(context, settings)
            settings.last_status = "Baking..."

            with preserved_blender_context(context):
                low = create_lowpoly_copy(context, source, settings.decimate_ratio)
                created["low_object"] = low
                created["low_mesh"] = low.data

                smart_uv_unwrap(context, low, settings.uv_island_margin)

                image = create_bake_image(source.name, settings.texture_resolution)
                created["image"] = image

                material, _texture_node = create_bake_material(low, image)
                created["material"] = material

                configure_diffuse_bake(
                    context.scene,
                    margin=settings.bake_margin,
                    ray_distance=settings.ray_distance,
                )

                select_only(context, [source, low], low)
                run_diffuse_bake(
                    margin=settings.bake_margin,
                    ray_distance=settings.ray_distance,
                )

                saved_path = save_image_png(image, source.name, settings.output_directory)
                created["saved_path"] = saved_path

                if settings.pack_image:
                    pack_image(image)

                low["auto_baker_source"] = source.name
                low["auto_baker_texture"] = image.name
                low["auto_baker_texture_path"] = str(saved_path)

            settings.last_status = f"Finished: {Path(created['saved_path']).name}"
            self.report({"INFO"}, f"Created {created['low_object'].name}; saved {created['saved_path']}")
            return {"FINISHED"}

        except ValidationError as exc:
            settings.last_status = f"Validation failed: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        except Exception as exc:
            LOGGER.error("Auto bake failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Failed: {exc}"
            if not settings.keep_temporary_data:
                self._cleanup_created_data(created)
            self.report({"ERROR"}, f"Auto bake failed: {exc}")
            return {"CANCELLED"}

    @staticmethod
    def _cleanup_created_data(created: dict[str, object]) -> None:
        """Remove temporary datablocks created by a failed operation."""
        low = created.get("low_object")
        if low and low.name in bpy.data.objects:
            bpy.data.objects.remove(low, do_unlink=True)

        mesh = created.get("low_mesh")
        if mesh and mesh.name in bpy.data.meshes and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

        material = created.get("material")
        if material and material.name in bpy.data.materials and material.users == 0:
            bpy.data.materials.remove(material)

        image = created.get("image")
        if image and image.name in bpy.data.images and image.users == 0:
            bpy.data.images.remove(image)

        saved_path = created.get("saved_path")
        if saved_path:
            try:
                Path(saved_path).unlink(missing_ok=True)
            except OSError:
                LOGGER.warning("Could not remove partial bake output: %s", saved_path)
