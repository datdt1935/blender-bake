"""glTF export helpers shared by the Export GLB buttons.

Both the single-file exporter in the panel and the batch exporter write GLB with the same
:data:`GLB_EXPORT_CONFIG` preset, so a batch export is byte-for-byte the settings a user would
get from clicking Export GLB once per object.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Iterable, Iterator

import bpy
from bpy.types import Object

from .layout_service import combined_bottom_center, group_members, group_roots, world_bottom_center

# glTF export preset applied to Blender's native exporter.
# GLB, selected-only, +Y up, UVs + Normals, materials exported as WebP (quality 30),
# shape keys + skinning, and Draco mesh compression.
GLB_EXPORT_CONFIG = {
    "export_format": "GLB",
    "export_copyright": "",
    # Include
    "use_selection": True,
    "use_visible": False,
    "use_renderable": False,
    "use_active_collection": False,
    "use_active_scene": False,
    "export_extras": False,
    "export_cameras": False,
    "export_lights": False,
    # Transform
    "export_yup": True,
    # Mesh
    "export_apply": False,
    "export_texcoords": True,
    "export_normals": True,
    "export_tangents": False,
    "export_attributes": False,
    "use_mesh_edges": False,
    "use_mesh_vertices": False,
    "export_shared_accessors": False,
    # Material
    "export_materials": "EXPORT",
    "export_image_format": "WEBP",
    "export_image_quality": 30,
    "export_image_add_webp": False,
    "export_image_webp_fallback": False,
    # Data
    "export_morph": True,
    "export_skins": True,
    # Draco compression
    "export_draco_mesh_compression_enable": True,
    "export_draco_mesh_compression_level": 6,
    "export_draco_position_quantization": 14,
    "export_draco_normal_quantization": 10,
    "export_draco_texcoord_quantization": 12,
    "export_draco_color_quantization": 10,
    "export_draco_generic_quantization": 12,
}

# Characters Windows forbids in a file name, plus control characters.
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Blender's duplicate suffix: ``Assets_Palette.001`` is the same material as ``Assets_Palette``.
_DUPLICATE_SUFFIX = re.compile(r"\.\d{3}$")


def safe_filename(name: str) -> str:
    """Turn an object name into a file name that is valid on every supported platform."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name).strip().rstrip(".")
    return cleaned or "object"


def supported_config() -> dict[str, object]:
    """Return the preset without keys the installed Blender's glTF exporter does not know."""
    properties = bpy.ops.export_scene.gltf.get_rna_type().properties
    return {name: value for name, value in GLB_EXPORT_CONFIG.items() if name in properties}


def export_glb(filepath: str) -> None:
    """Write the current selection to ``filepath`` using the shared preset."""
    bpy.ops.export_scene.gltf(filepath=filepath, **supported_config())


def base_name(name: str) -> str:
    """Strip Blender's ``.001`` duplicate suffix from a datablock name."""
    return _DUPLICATE_SUFFIX.sub("", name)


@contextmanager
def materials_stripped(objects: Iterable[Object], ignore_name: str) -> Iterator[int]:
    """Empty every material slot holding ``ignore_name`` for the block, then fill them back in.

    The slots themselves are kept, so only the material assignment changes; the exporter writes
    those primitives without a material. Yields how many slots were emptied. An empty
    ``ignore_name`` strips nothing.

    Slots linked to mesh data are shared with linked duplicates, which lose the material for the
    duration of the export as well; they are restored either way.
    """
    target = base_name(ignore_name.strip())
    cleared: list[tuple[Object, int, bpy.types.Material]] = []

    if target:
        for obj in objects:
            for index, slot in enumerate(getattr(obj, "material_slots", ())):
                material = slot.material
                if material is not None and base_name(material.name) == target:
                    cleared.append((obj, index, material))
                    slot.material = None

    try:
        yield len(cleared)
    finally:
        for obj, index, material in reversed(cleared):
            obj.material_slots[index].material = material


@contextmanager
def centered_at_world_origin(root: Object) -> Iterator[None]:
    """Sit a group on the world origin for the duration of the block, then put it back.

    The bottom center of the group's bounding box is moved to (0, 0, 0). When the root is a
    lone mesh its origin is moved to that bottom center first, so the exported node transform
    is identity instead of carrying the object's old pivot offset - the same result as running
    Origin Bottom Center + Center by hand. A parented hierarchy is moved by its root only, so
    children keep their relative position.

    Mesh data is transformed in place and transformed back afterwards, so a mesh shared by
    linked duplicates is briefly offset for the other users too; it is restored either way.
    """
    old_matrix = root.matrix_world.copy()
    bottom_center = world_bottom_center(root)
    # Moving the origin means rewriting vertex coordinates, which only works when the root owns
    # all the geometry being exported; a hierarchy is placed by translating the root instead.
    mesh = root.data if root.type == "MESH" and not root.children else None
    delta = None

    if mesh is not None:
        origin_matrix = old_matrix.copy()
        origin_matrix.translation = bottom_center
        delta = origin_matrix.inverted() @ old_matrix
        # Keep the mesh visually in place while the object's origin moves to the bottom center.
        mesh.transform(delta, shape_keys=True)
        root.matrix_world = origin_matrix

    centered = root.matrix_world.copy()
    centered.translation -= bottom_center
    root.matrix_world = centered
    bpy.context.view_layer.update()

    try:
        yield
    finally:
        if delta is not None:
            mesh.transform(delta.inverted(), shape_keys=True)
            mesh.update()
        root.matrix_world = old_matrix
        bpy.context.view_layer.update()


def split_selected_meshes(selected: Iterable[Object]) -> list[tuple[Object, list[Object]]]:
    """Turn a selection into export units where every selected mesh is a file of its own.

    Each selected mesh becomes one unit holding only that mesh - its unselected children are
    left out, so only what is selected is split off. Any other selected object (usually an
    Empty) is skipped when something under it is selected too, because it only serves as the
    pivot; selected on its own it stays one unit with its whole hierarchy, as before.
    Returns ``(root, members)`` pairs in selection order.
    """
    chosen: list[Object] = []
    for obj in selected:
        if obj is not None and obj not in chosen:
            chosen.append(obj)
    chosen_set = set(chosen)

    units: list[tuple[Object, list[Object]]] = [(obj, [obj]) for obj in chosen if obj.type == "MESH"]
    others = [
        obj
        for obj in chosen
        if obj.type != "MESH" and not any(child in chosen_set for child in obj.children_recursive)
    ]
    units.extend((root, group_members(root)) for root in group_roots(others))
    return units


def top_ancestor(obj: Object) -> Object:
    """Return the top-most parent of ``obj``, or ``obj`` itself when it has no parent."""
    while obj.parent is not None:
        obj = obj.parent
    return obj


@contextmanager
def parents_at_world_origin(roots: Iterable[Object]) -> Iterator[None]:
    """Export in parent space: move the top-most parent of each root to (0, 0, 0), then back.

    This is the "zero out the parent" trick. glTF writes selected children in world space, so
    the shared parent (usually an Empty) is translated to the world origin for the block. Every
    part exported from the same parent then shares that parent's pivot. Only the translation is
    zeroed; rotation and scale are kept, and no object origin or mesh data is touched. A root with
    no parent is its own anchor, so it is exported around its own origin.
    """
    anchors: list[Object] = []
    for root in roots:
        anchor = top_ancestor(root)
        if anchor not in anchors:
            anchors.append(anchor)

    old_matrices = [(anchor, anchor.matrix_world.copy()) for anchor in anchors]
    for anchor, matrix in old_matrices:
        moved = matrix.copy()
        moved.translation = (0.0, 0.0, 0.0)
        anchor.matrix_world = moved
    bpy.context.view_layer.update()

    try:
        yield
    finally:
        for anchor, matrix in old_matrices:
            anchor.matrix_world = matrix
        bpy.context.view_layer.update()


@contextmanager
def selection_at_world_origin(roots: list[Object]) -> Iterator[None]:
    """Sit one or more groups on the world origin for the block, then put them back.

    A single group is handled by :func:`centered_at_world_origin`, so it matches Batch Export
    exactly. Several groups are moved together: the bottom center of their combined bounding box
    goes to (0, 0, 0) and they keep their layout relative to each other.
    """
    if len(roots) == 1:
        with centered_at_world_origin(roots[0]):
            yield
        return

    old_matrices = [(root, root.matrix_world.copy()) for root in roots]
    offset = combined_bottom_center(roots)
    for root, matrix in old_matrices:
        moved = matrix.copy()
        moved.translation -= offset
        root.matrix_world = moved
    bpy.context.view_layer.update()

    try:
        yield
    finally:
        for root, matrix in old_matrices:
            root.matrix_world = matrix
        bpy.context.view_layer.update()
