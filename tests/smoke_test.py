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


def check_batch_export(obj: bpy.types.Object) -> None:
    """Batch-export one object and verify the file lands on disk and the scene is left alone."""
    settings = bpy.context.scene.alb_settings
    obj.location = (7.0, -3.0, 5.0)
    # A duplicate-suffixed copy of the ignored material must be stripped from the export too.
    obj.data.materials.append(bpy.data.materials.new(f"{settings.export_ignore_material}.001"))
    bpy.context.view_layer.update()
    before = obj.matrix_world.copy()
    before_slots = [slot.material.name if slot.material else None for slot in obj.material_slots]

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    assert_true(bpy.ops.object.alb_batch_export_glb.poll(), "Batch export should poll with a selection")

    export_dir = tempfile.mkdtemp(prefix="alb_smoke_glb_")
    result = bpy.ops.object.alb_batch_export_glb(directory=export_dir)
    assert_true(result == {"FINISHED"}, f"Batch export returned {result}")

    exported = Path(export_dir) / f"{obj.name}.glb"
    assert_true(exported.exists(), f"Expected batch-exported GLB at {exported}")

    bpy.context.view_layer.update()
    drift = max(abs(obj.matrix_world[r][c] - before[r][c]) for r in range(4) for c in range(4))
    assert_true(drift < 1e-5, f"Batch export moved the object permanently (drift {drift})")

    after_slots = [slot.material.name if slot.material else None for slot in obj.material_slots]
    assert_true(after_slots == before_slots, f"Material slots not restored: {after_slots} != {before_slots}")


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
        assert_true(low.data.name == low.name, "Low-poly mesh data name should match object name")
        assert_true(settings.low_quality_object == low, "Low Quality field was not assigned")

        assert_true(bpy.ops.object.alb_bake_selected_pair.poll(), "Bake operator should poll with object pair")
        bake_result = bpy.ops.object.alb_bake_selected_pair()
        assert_true(bake_result == {"FINISHED"}, f"Bake operator returned {bake_result}")

        output = Path(settings.output_directory) / "SmokeHigh_Diffuse.png"
        assert_true(output.exists(), f"Expected baked PNG at {output}")

        check_batch_export(obj)

    finally:
        addon.unregister()

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
