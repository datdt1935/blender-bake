"""Image and material helpers for bake targets."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Image, Material, Object, ShaderNodeTexImage


def create_bake_image(source_name: str, resolution: str) -> Image:
    """Create a generated image datablock for the bake target."""
    size = int(resolution)
    image = bpy.data.images.new(
        name=f"{source_name}_Diffuse",
        width=size,
        height=size,
        alpha=True,
        float_buffer=False,
    )
    image.generated_color = (0.0, 0.0, 0.0, 0.0)
    image["auto_baker_created"] = True
    return image


def create_bake_material(obj: Object, image: Image) -> tuple[Material, ShaderNodeTexImage]:
    """Create a material with an active image texture node for Blender's bake operator."""
    material = bpy.data.materials.new(name=f"{obj.name}_Diffuse")
    material["auto_baker_created"] = True
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (120, 0)
    texture = nodes.new("ShaderNodeTexImage")
    texture.location = (-280, 0)
    texture.image = image
    texture.interpolation = "Linear"
    texture.name = "BAKE_TARGET"
    texture.label = "Bake Target"

    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Roughness"].default_value = 0.5

    obj.data.materials.clear()
    obj.data.materials.append(material)
    nodes.active = texture
    texture.select = True
    return material, texture


def find_bake_image(obj: Object) -> Image | None:
    """Find the active bake image on a low-poly object's material."""
    image_name = obj.get("auto_baker_texture")
    if image_name:
        image = bpy.data.images.get(str(image_name))
        if image:
            return image

    for material in obj.data.materials:
        if not material or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeTexImage" and getattr(node, "image", None):
                if node.name == "BAKE_TARGET" or node.label == "Bake Target":
                    material.node_tree.nodes.active = node
                    node.select = True
                    return node.image
    return None


def ensure_active_bake_node(obj: Object) -> Image:
    """Ensure Blender's bake operator has an active image texture node on the target object."""
    image = find_bake_image(obj)
    if not image:
        raise RuntimeError("Low Quality object has no bake image. Run Create Low Mesh first.")
    return image


def save_image_png(image: Image, source_name: str, output_directory: str) -> Path:
    """Save the image as PNG in the configured output directory."""
    absolute_dir = Path(bpy.path.abspath(output_directory)).expanduser()
    absolute_dir.mkdir(parents=True, exist_ok=True)
    safe_name = bpy.path.clean_name(source_name)
    path = absolute_dir / f"{safe_name}_Diffuse.png"
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return path


def pack_image(image: Image) -> None:
    """Pack a saved image into the .blend file."""
    image.pack()
