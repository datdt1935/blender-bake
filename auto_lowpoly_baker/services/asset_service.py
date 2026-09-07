"""Import and normalization helpers for the Assets tab."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import bpy
from bpy.types import Collection, Context, Object

_TRAILING_SUFFIX_RE = re.compile(r"\.\d{3}$")


def _base_name(name: str) -> str:
    """Strip a Blender ``.001``-style duplicate suffix from a datablock name."""
    return _TRAILING_SUFFIX_RE.sub("", name)


def derive_asset_name(filepath: str) -> str:
    """Derive a clean asset name from a GLB file name.

    Source files carry a trailing hash id after the real name, e.g.
    ``Asset_BasementMedium.bdde813465453426.glb`` -> ``Asset_BasementMedium``.
    """
    stem = Path(filepath).stem
    return stem.split(".")[0]


def rename_asset(obj: Object, name: str) -> None:
    """Rename the object and its mesh data to the derived asset name."""
    obj.name = name
    obj.data.name = name


def rename_with_prefix(objects: Iterable[Object], prefix: str) -> None:
    """Prefix every object's name with ``prefix`` (used to tag a failed import's leftovers)."""
    for obj in objects:
        if obj is not None and obj.name in bpy.data.objects:
            obj.name = f"{prefix}_{obj.name}"


def import_gltf_objects(filepath: str) -> list[Object]:
    """Import a glTF/GLB file and return the objects it created."""
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=filepath)
    return [obj for name, obj in bpy.data.objects.items() if name not in before]


def keep_only_named_mesh(imported: Iterable[Object], mesh_name: str) -> Object | None:
    """Delete every imported object except the mesh matching ``mesh_name``.

    Returns the kept mesh, or ``None`` if no match was found. On failure, the imported objects
    are left untouched (not deleted) so the caller can tag them for inspection.
    """
    imported = list(imported)
    keep = next(
        (obj for obj in imported if obj.type == "MESH" and _base_name(obj.name) == mesh_name),
        None,
    )

    if keep is None:
        return None

    _remove_objects(obj for obj in imported if obj is not keep)
    return keep


def _remove_objects(objects: Iterable[Object]) -> None:
    for obj in objects:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def apply_named_material(obj: Object, material_name: str) -> bool:
    """Replace all of the mesh's material slots with an existing material by name."""
    material = bpy.data.materials.get(material_name)
    if material is None:
        return False
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    return True


def move_to_collection(context: Context, obj: Object, collection_name: str) -> Collection:
    """Link the object into (creating if needed) the named collection, unlinking it elsewhere."""
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)

    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)
    return collection
