"""Blender background smoke test for Auto Lowpoly Baker."""

from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path

import bpy


def fail(message: str) -> None:
    print(f"SMOKE TEST FAILED: {message}")
    sys.exit(1)


def assert_true(value: bool, message: str) -> None:
    if not value:
        fail(message)


def reset_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_test_mesh() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "SmokeHigh"
    material = bpy.data.materials.new("SmokeHighMaterial")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.2, 0.1, 1.0)
    obj.data.materials.append(material)
    return obj


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    addon = importlib.import_module("auto_lowpoly_baker")
    addon.register()
    addon.unregister()
    addon.register()

    try:
        reset_scene()
        assert_true(not bpy.ops.object.alb_create_lowmesh.poll(), "Create operator should not poll without a mesh")
        assert_true(not bpy.ops.object.alb_bake_selected_pair.poll(), "Bake operator should not poll without object pair")
        assert_true(not bpy.ops.object.alb_create_lowmesh_and_bake.poll(), "One-click operator should not poll without a mesh")
        assert_true(not bpy.ops.object.alb_origin_bottom_center_to_world.poll(), "Origin operator should not poll without a mesh")

        obj = create_test_mesh()
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        assert_true(bpy.ops.object.alb_origin_bottom_center_to_world.poll(), "Origin operator should poll with active mesh")

        settings = bpy.context.scene.alb_settings
        settings.high_quality_object = obj
        settings.decimate_ratio = 1.0
        settings.texture_resolution = "128"
        settings.bake_margin = 2
        settings.ray_distance = 0.1
        settings.output_directory = tempfile.mkdtemp(prefix="alb_smoke_")
        settings.pack_image = False
        settings.keep_temporary_data = False

        assert_true(bpy.ops.object.alb_create_lowmesh.poll(), "Create operator should poll with High Quality mesh")
        create_result = bpy.ops.object.alb_create_lowmesh()
        assert_true(create_result == {"FINISHED"}, f"Create operator returned {create_result}")

        low = bpy.data.objects.get("SmokeHigh_LOW")
        assert_true(low is not None, "Low-poly object was not created")
        assert_true(settings.low_quality_object == low, "Low Quality field was not assigned")

        assert_true(bpy.ops.object.alb_bake_selected_pair.poll(), "Bake operator should poll with object pair")
        bake_result = bpy.ops.object.alb_bake_selected_pair()
        assert_true(bake_result == {"FINISHED"}, f"Bake operator returned {bake_result}")

        output = Path(settings.output_directory) / "SmokeHigh_Diffuse.png"
        assert_true(output.exists(), f"Expected baked PNG at {output}")

    finally:
        addon.unregister()

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
