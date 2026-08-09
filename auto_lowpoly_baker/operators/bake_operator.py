"""Operators for the two-step low-poly bake workflow."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy
from mathutils import Vector
from bpy.types import Context, Operator

from ..services.bake_service import configure_diffuse_bake, run_diffuse_bake
from ..services.context_service import preserved_blender_context, select_only
from ..services.material_service import (
    create_bake_image,
    create_bake_material,
    ensure_active_bake_node,
    pack_image,
    save_image_png,
)
from ..services.mesh_service import create_lowpoly_copy, smart_uv_unwrap
from ..utils.logging import get_logger
from ..utils.validation import (
    ValidationError,
    validate_create_lowmesh_request,
    validate_existing_bake_request,
)

LOGGER = get_logger()


class OBJECT_OT_alb_create_lowmesh(Operator):
    """Create the low-poly bake target, UVs, material, and image."""

    bl_idname = "object.alb_create_lowmesh"
    bl_label = "Create Low Mesh"
    bl_description = "Create a low-poly duplicate with UVs, material, and a bake image"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        settings = getattr(context.scene, "alb_settings", None)
        obj = settings.high_quality_object if settings else context.active_object
        obj = obj or context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        created = {
            "low_object": None,
            "low_mesh": None,
            "material": None,
            "image": None,
        }

        try:
            source = validate_create_lowmesh_request(context, settings)
            settings.high_quality_object = source
            settings.last_status = "Creating low mesh..."

            with preserved_blender_context(context):
                low = create_lowpoly_copy(
                    context,
                    source,
                    settings.decimate_ratio,
                    settings.merge_distance,
                    settings.reduction_mode,
                    settings.target_vertex_count,
                )
                created["low_object"] = low
                created["low_mesh"] = low.data

                smart_uv_unwrap(context, low, settings.uv_island_margin)

                image = create_bake_image(source.name, settings.texture_resolution)
                created["image"] = image

                material, _texture_node = create_bake_material(low, image)
                created["material"] = material

                low["auto_baker_source"] = source.name
                low["auto_baker_texture"] = image.name
                settings.low_quality_object = low

            settings.last_status = f"Created low mesh: {created['low_object'].name}"
            self.report({"INFO"}, f"Created {created['low_object'].name}. Now run Bake.")
            return {"FINISHED"}

        except ValidationError as exc:
            settings.last_status = f"Validation failed: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        except Exception as exc:
            LOGGER.error("Create low mesh failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Failed: {exc}"
            if not settings.keep_temporary_data:
                _cleanup_created_data(created)
            self.report({"ERROR"}, f"Create low mesh failed: {exc}")
            return {"CANCELLED"}


class OBJECT_OT_alb_bake_selected_pair(Operator):
    """Bake diffuse color from the selected high object to the low object."""

    bl_idname = "object.alb_bake_selected_pair"
    bl_label = "Bake"
    bl_description = "Bake diffuse color from High Quality to Low Quality"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        settings = getattr(context.scene, "alb_settings", None)
        if not settings:
            return False
        high = settings.high_quality_object
        low = settings.low_quality_object or context.active_object
        return (
            high is not None
            and low is not None
            and high != low
            and high.type == "MESH"
            and low.type == "MESH"
        )

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        saved_path = None

        try:
            high, low = validate_existing_bake_request(context, settings)
            settings.high_quality_object = high
            settings.low_quality_object = low
            settings.last_status = "Baking..."

            with preserved_blender_context(context):
                image = ensure_active_bake_node(low)

                configure_diffuse_bake(
                    context.scene,
                    margin=settings.bake_margin,
                    ray_distance=settings.ray_distance,
                )

                # Selected-to-active baking requires source selected first and low target active.
                select_only(context, [high, low], low)
                run_diffuse_bake(
                    margin=settings.bake_margin,
                    ray_distance=settings.ray_distance,
                )

                saved_path = save_image_png(image, high.name, settings.output_directory)
                if settings.pack_image:
                    pack_image(image)

                low["auto_baker_source"] = high.name
                low["auto_baker_texture"] = image.name
                low["auto_baker_texture_path"] = str(saved_path)

            settings.last_status = f"Finished: {Path(saved_path).name}"
            self.report({"INFO"}, f"Baked {high.name} to {low.name}; saved {saved_path}")
            return {"FINISHED"}

        except ValidationError as exc:
            settings.last_status = f"Validation failed: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        except Exception as exc:
            LOGGER.error("Bake failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Failed: {exc}"
            if saved_path and not settings.keep_temporary_data:
                try:
                    Path(saved_path).unlink(missing_ok=True)
                except OSError:
                    LOGGER.warning("Could not remove partial bake output: %s", saved_path)
            self.report({"ERROR"}, f"Bake failed: {exc}")
            return {"CANCELLED"}


class OBJECT_OT_alb_create_lowmesh_and_bake(Operator):
    """Run the low-mesh creation step and the bake step in one click."""

    bl_idname = "object.alb_create_lowmesh_and_bake"
    bl_label = "Create Low Mesh & Bake"
    bl_description = "Create the low mesh, then bake High Quality to Low Quality"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.active_object
        settings = getattr(context.scene, "alb_settings", None)
        high = obj if obj and obj.type == "MESH" else (settings.high_quality_object if settings else None)
        return high is not None and high.type == "MESH"

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        active = context.active_object
        if active and active.type == "MESH":
            settings.high_quality_object = active

        create_result = bpy.ops.object.alb_create_lowmesh()
        if create_result != {"FINISHED"}:
            self.report({"ERROR"}, "Create Low Mesh failed; bake was not started.")
            return {"CANCELLED"}

        bake_result = bpy.ops.object.alb_bake_selected_pair()
        if bake_result != {"FINISHED"}:
            self.report({"ERROR"}, "Low mesh was created, but bake failed.")
            return {"CANCELLED"}

        self.report({"INFO"}, "Created low mesh and baked texture.")
        return {"FINISHED"}


class OBJECT_OT_alb_origin_bottom_center_to_world(Operator):
    """Set active mesh origin to bottom center, then move it to the world origin."""

    bl_idname = "object.alb_origin_bottom_center_to_world"
    bl_label = "Origin Bottom Center + Center"
    bl_description = "Set the selected mesh origin to bottom center, then move that origin to world center"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: Context):
        obj = context.active_object
        settings = context.scene.alb_settings

        try:
            with preserved_blender_context(context):
                if obj.data.users > 1:
                    obj.data = obj.data.copy()

                bottom_center = _world_bottom_center(obj)
                old_matrix = obj.matrix_world.copy()
                origin_matrix = old_matrix.copy()
                origin_matrix.translation = bottom_center

                # Keep the mesh visually in place while moving the object's origin.
                obj.data.transform(origin_matrix.inverted() @ old_matrix)
                obj.matrix_world = origin_matrix

                centered_matrix = obj.matrix_world.copy()
                centered_matrix.translation = Vector((0.0, 0.0, 0.0))
                obj.matrix_world = centered_matrix
                obj.data.update()

            settings.last_status = f"Origin set and centered: {obj.name}"
            self.report({"INFO"}, f"Set origin to bottom center and moved {obj.name} to world center.")
            return {"FINISHED"}

        except Exception as exc:
            LOGGER.error("Set origin failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Origin failed: {exc}"
            self.report({"ERROR"}, f"Set origin failed: {exc}")
            return {"CANCELLED"}


class OBJECT_OT_alb_clear_unused_generated_data(Operator):
    """Remove unused materials and their unused texture images."""

    bl_idname = "object.alb_clear_unused_generated_data"
    bl_label = "Clear Unused Data"
    bl_description = "Remove unused materials and texture images referenced only by those materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        candidate_images = set()
        removed_materials = 0
        removed_images = 0

        for material in list(bpy.data.materials):
            if material.users == 0:
                candidate_images.update(_texture_images_from_material(material))
                bpy.data.materials.remove(material)
                removed_materials += 1

        for image in candidate_images:
            if image.name in bpy.data.images and image.users == 0:
                bpy.data.images.remove(image)
                removed_images += 1

        settings.last_status = f"Cleared unused data: {removed_materials} materials, {removed_images} textures"
        self.report(
            {"INFO"},
            f"Cleared {removed_materials} unused materials and {removed_images} texture images.",
        )
        return {"FINISHED"}


class OBJECT_OT_alb_reset_config(Operator):
    """Reset Auto Baker configuration values to their add-on defaults."""

    bl_idname = "object.alb_reset_config"
    bl_label = "Reset Config"
    bl_description = "Reset Auto Baker config values to defaults while keeping selected High/Low objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        settings = context.scene.alb_settings
        reset_property_names = (
            "decimate_ratio",
            "reduction_mode",
            "target_vertex_count",
            "merge_distance",
            "texture_resolution",
            "uv_island_margin",
            "bake_margin",
            "ray_distance",
            "output_directory",
            "pack_image",
            "keep_temporary_data",
        )

        for name in reset_property_names:
            if hasattr(settings, name):
                settings.property_unset(name)

        settings.last_status = "Config reset to defaults"
        self.report({"INFO"}, "Auto Baker config reset to defaults.")
        return {"FINISHED"}


class OBJECT_OT_alb_reset_pose(Operator):
    """Reset the selected object's rig to its default pose."""

    bl_idname = "object.alb_reset_pose"
    bl_label = "Reset Pose"
    bl_description = "Reset the rig of the selected object to its default pose by clearing pose bone transforms"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return find_reset_pose_armature(context) is not None

    def execute(self, context: Context):
        settings = context.scene.alb_settings

        try:
            armature = find_reset_pose_armature(context)
            if armature is None:
                raise ValidationError("Select a rig (armature) or an object bound to one.")
            if armature.hide_viewport or armature.hide_get():
                raise ValidationError(f"Armature '{armature.name}' is hidden. Unhide it before resetting the pose.")

            # Remember the user's selection and mode so we can restore them afterwards.
            prev_active = context.view_layer.objects.active
            prev_mode = prev_active.mode if prev_active else "OBJECT"
            prev_selected = list(context.selected_objects)

            if context.object and context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            # Optionally uncheck active animation tracks so the pose returns to rest, not the animated pose.
            muted_tracks = 0
            if settings.reset_pose_disable_anim:
                muted_tracks = _disable_active_animations(armature)

            # Make the armature the sole active object, enter Pose Mode, and clear transforms.
            select_only(context, [armature], armature)
            bpy.ops.object.mode_set(mode="POSE")
            try:
                bpy.ops.pose.select_all(action="SELECT")
                bpy.ops.pose.user_transforms_clear()
            finally:
                bpy.ops.object.mode_set(mode="OBJECT")

            # Restore the user's prior selection and mode.
            select_only(context, prev_selected, prev_active)
            if prev_active and prev_active.name in bpy.data.objects and prev_mode != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode=prev_mode)
                except RuntimeError:
                    pass

            if muted_tracks:
                settings.last_status = f"Reset pose: {armature.name} (unchecked {muted_tracks} anim)"
                self.report({"INFO"}, f"Reset pose for {armature.name}; unchecked {muted_tracks} active animation(s).")
            else:
                settings.last_status = f"Reset pose: {armature.name}"
                self.report({"INFO"}, f"Reset pose for {armature.name}.")
            return {"FINISHED"}

        except ValidationError as exc:
            settings.last_status = f"Reset pose failed: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        except Exception as exc:
            LOGGER.error("Reset pose failed: %s\n%s", exc, traceback.format_exc())
            settings.last_status = f"Reset pose failed: {exc}"
            self.report({"ERROR"}, f"Reset pose failed: {exc}")
            return {"CANCELLED"}


def find_reset_pose_armature(context: Context) -> bpy.types.Object | None:
    """Resolve the armature to reset from the active or selected objects."""
    candidates: list[bpy.types.Object] = []
    active = context.active_object
    if active is not None:
        candidates.append(active)
    candidates.extend(context.selected_objects)

    seen: set[str] = set()
    for obj in candidates:
        if obj is None or obj.name in seen:
            continue
        seen.add(obj.name)
        armature = _armature_from_object(obj)
        if armature is not None:
            return armature
    return None


def _disable_active_animations(armature: bpy.types.Object) -> int:
    """Uncheck (mute) the rig's active NLA animation tracks and clear its active action.

    Returns the number of animation sources that were disabled so a pose reset lands on the
    rest state instead of the currently animated pose.
    """
    anim = armature.animation_data
    if anim is None:
        return 0

    disabled = 0
    for track in anim.nla_tracks:
        if not track.mute:
            track.mute = True
            disabled += 1

    if anim.action is not None:
        anim.action = None
        disabled += 1

    return disabled


def _armature_from_object(obj: bpy.types.Object | None) -> bpy.types.Object | None:
    """Return the armature tied to an object: itself, an Armature modifier, or its parent."""
    if obj is None:
        return None
    if obj.type == "ARMATURE":
        return obj
    for modifier in getattr(obj, "modifiers", ()):
        if modifier.type == "ARMATURE" and modifier.object and modifier.object.type == "ARMATURE":
            return modifier.object
    parent = obj.parent
    if parent is not None and parent.type == "ARMATURE":
        return parent
    return None


def _cleanup_created_data(created: dict[str, object]) -> None:
    """Remove temporary datablocks created by a failed create-lowmesh operation."""
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


def _world_bottom_center(obj: bpy.types.Object) -> Vector:
    """Return the bottom-center point of an object's local bounding box in world space."""
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_x = min(corner.x for corner in world_corners)
    max_x = max(corner.x for corner in world_corners)
    min_y = min(corner.y for corner in world_corners)
    max_y = max(corner.y for corner in world_corners)
    min_z = min(corner.z for corner in world_corners)
    return Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, min_z))


def _texture_images_from_material(material: bpy.types.Material) -> set[bpy.types.Image]:
    """Collect texture images referenced by a material's node tree."""
    if not material.use_nodes:
        return set()
    return {
        node.image
        for node in material.node_tree.nodes
        if (
            node.bl_idname == "ShaderNodeTexImage"
            and getattr(node, "image", None)
            and node.image.name in bpy.data.images
        )
    }
