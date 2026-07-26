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
    return image


def create_bake_material(obj: Object, image: Image) -> tuple[Material, ShaderNodeTexImage]:
    """Create a material with an active image texture node for Blender's bake operator."""
    material = bpy.data.materials.new(name=f"{obj.name}_Diffuse")
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
