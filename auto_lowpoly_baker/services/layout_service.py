"""Object layout helpers: grid arrangement and world-center reset.

Layout treats a parented hierarchy (and a collection-instance empty) as one rigid group: only
the top-most object of each group is moved, so children keep their relative position inside the
group, and the group's footprint is the bounding box of everything it contains.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from bpy.types import Object
from mathutils import Matrix, Vector

# Object types that contribute a real bounding box. Everything else (empties, lights, cameras,
# armatures) only contributes its origin, so it never inflates a group's footprint.
_GEOMETRY_TYPES = {
    "MESH",
    "CURVE",
    "SURFACE",
    "META",
    "FONT",
    "VOLUME",
    "POINTCLOUD",
    "LATTICE",
    "GPENCIL",
    "GREASEPENCIL",
}


def _descendants(obj: Object) -> list[Object]:
    """Return every object parented under ``obj``, at any depth."""
    recursive = getattr(obj, "children_recursive", None)
    if recursive is not None:
        return list(recursive)

    result: list[Object] = []
    stack = list(getattr(obj, "children", ()))
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(getattr(child, "children", ()))
    return result


def _is_visible(obj: Object) -> bool:
    """Return whether the object is currently shown in the viewport."""
    if getattr(obj, "hide_viewport", False):
        return False
    try:
        return bool(obj.visible_get())
    except Exception:
        # Objects outside the active view layer cannot report visibility; assume visible.
        return True


def _object_corners(obj: Object, matrix: Matrix) -> list[Vector]:
    """Return the object's bounding-box corners transformed by ``matrix``."""
    if getattr(obj, "type", None) not in _GEOMETRY_TYPES:
        return []
    bound_box = getattr(obj, "bound_box", None)
    if not bound_box:
        return []
    return [matrix @ Vector(corner) for corner in bound_box]


def _instance_corners(obj: Object, matrix: Matrix) -> list[Vector]:
    """Return bounding-box corners for the collection an empty instances, if it instances one."""
    collection = getattr(obj, "instance_collection", None)
    if collection is None:
        return []

    offset = Matrix.Translation(-Vector(collection.instance_offset))
    corners: list[Vector] = []
    for member in collection.all_objects:
        corners.extend(_object_corners(member, matrix @ offset @ member.matrix_world))
    return corners


def group_members(obj: Object) -> list[Object]:
    """Return the object plus every descendant that moves rigidly with it."""
    return [obj, *_descendants(obj)]


def _world_bounds(obj: Object) -> tuple[Vector, Vector]:
    """Return the (min, max) world-space bounding box of an object and its whole hierarchy.

    Hidden members are ignored so invisible geometry never inflates the footprint; when every
    member is hidden they are used anyway rather than collapsing the group to a point.
    """
    members = group_members(obj)
    visible = [member for member in members if _is_visible(member)]

    corners: list[Vector] = []
    for member in visible or members:
        matrix = member.matrix_world
        corners.extend(_object_corners(member, matrix))
        corners.extend(_instance_corners(member, matrix))

    if not corners:
        origin = obj.matrix_world.translation.copy()
        return origin, origin.copy()

    min_corner = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    max_corner = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return min_corner, max_corner


def world_bottom_center(obj: Object) -> Vector:
    """Return the bottom-center point of the world bounding box of an object and its hierarchy."""
    min_corner, max_corner = _world_bounds(obj)
    return Vector(
        (
            (min_corner.x + max_corner.x) * 0.5,
            (min_corner.y + max_corner.y) * 0.5,
            min_corner.z,
        )
    )


def combined_bottom_center(objects: Iterable[Object]) -> Vector:
    """Return the bottom-center point of the bounding box around several groups together."""
    bounds = [_world_bounds(obj) for obj in objects]
    min_corner = Vector((min(b[0].x for b in bounds), min(b[0].y for b in bounds), min(b[0].z for b in bounds)))
    max_corner = Vector((max(b[1].x for b in bounds), max(b[1].y for b in bounds), max(b[1].z for b in bounds)))
    return Vector(
        (
            (min_corner.x + max_corner.x) * 0.5,
            (min_corner.y + max_corner.y) * 0.5,
            min_corner.z,
        )
    )


def _has_ancestor_in(obj: Object, candidates: set[Object]) -> bool:
    """Return whether any ancestor of ``obj`` is part of ``candidates``."""
    ancestor = obj.parent
    visited: set[Object] = {obj}
    while ancestor is not None and ancestor not in visited:
        if ancestor in candidates:
            return True
        visited.add(ancestor)
        ancestor = ancestor.parent
    return False


def group_roots(objects: Iterable[Object]) -> list[Object]:
    """Reduce a selection to the top-most object of each parented hierarchy.

    An object whose parent (or any further ancestor) is also in the selection is dropped: moving
    the ancestor already carries it along, and moving it separately would break its relative
    position inside the group. Input order is preserved and duplicates are removed.
    """
    unique: list[Object] = []
    selection: set[Object] = set()
    for obj in objects:
        if obj is None or obj in selection:
            continue
        selection.add(obj)
        unique.append(obj)

    return [obj for obj in unique if not _has_ancestor_in(obj, selection)]


def _move_group(obj: Object, offset: Vector) -> None:
    """Translate a group by moving only its root; children follow through parenting."""
    matrix = obj.matrix_world.copy()
    matrix.translation += offset
    obj.matrix_world = matrix


def arrange_grid(objects: Sequence[Object], margin: float = 1.0) -> None:
    """Arrange objects on an evenly spaced XY grid so their bounding boxes never overlap.

    Parented hierarchies move as a unit: only each group's root is placed, and the cell size is
    driven by the full bounding box of every group.
    """
    roots = group_roots(objects)
    if not roots:
        return

    bounds = {obj: _world_bounds(obj) for obj in roots}
    footprint = max(
        max(max_corner.x - min_corner.x, max_corner.y - min_corner.y) for min_corner, max_corner in bounds.values()
    )
    cell_size = max(footprint, 0.001) + margin

    columns = math.ceil(math.sqrt(len(roots)))
    ordered = sorted(roots, key=lambda obj: obj.name)

    for index, obj in enumerate(ordered):
        column = index % columns
        row = index // columns
        min_corner, max_corner = bounds[obj]
        current_center_x = (min_corner.x + max_corner.x) * 0.5
        current_center_y = (min_corner.y + max_corner.y) * 0.5
        target_x = column * cell_size
        target_y = -row * cell_size

        _move_group(obj, Vector((target_x - current_center_x, target_y - current_center_y, 0.0)))


def arrange_compact_grid(objects: Sequence[Object], spacing: float = 0.1, sort_by_size: bool = True) -> None:
    """Pack objects on the XY plane with shelf-based 2D rectangle packing.

    Each group's footprint is the world-space bounding box of its root plus every child parented
    under it, so a multi-mesh asset is packed as a single block and its parts never shift
    relative to each other. Groups are packed edge-to-edge with an exact ``spacing`` gap between
    neighbors (no wasted uniform-cell space), rotation and scale are untouched, every group's
    bounding-box bottom is placed at Z = 0, and the whole packed layout is re-centered on the
    world origin.

    When ``sort_by_size`` is enabled, groups are ordered by bounding-box area (largest first)
    before packing, so big objects land toward the top-left and shrink left to right / row to
    row. When disabled, groups are packed in the order they were given.
    """
    roots = group_roots(objects)
    if not roots:
        return

    items = []
    for obj in roots:
        min_corner, max_corner = _world_bounds(obj)
        width = max_corner.x - min_corner.x
        depth = max_corner.y - min_corner.y
        items.append(
            {
                "obj": obj,
                "width": width,
                "depth": depth,
                "area": width * depth,
                "center_x": (min_corner.x + max_corner.x) * 0.5,
                "center_y": (min_corner.y + max_corner.y) * 0.5,
                "min_z": min_corner.z,
            }
        )

    # Aim for a roughly square bin so the result reads as a compact block rather than a strip.
    total_area = sum((item["width"] + spacing) * (item["depth"] + spacing) for item in items)
    target_width = max(math.sqrt(total_area), 0.001)

    # Shelf packing fills each shelf left to right until it would exceed the target width, then
    # starts a new shelf sized to its own tallest occupant. Sorting largest-area-first is the
    # classic shelf-packing heuristic and also reads well visually (big objects up front).
    ordered = sorted(items, key=lambda item: item["area"], reverse=True) if sort_by_size else items

    placements: list[tuple[dict, float, float]] = []
    x_cursor = 0.0
    y_cursor = 0.0
    shelf_height = 0.0
    shelf_has_items = False

    for item in ordered:
        if shelf_has_items and x_cursor + spacing + item["width"] > target_width:
            y_cursor += shelf_height + spacing
            x_cursor = 0.0
            shelf_height = 0.0
            shelf_has_items = False

        if shelf_has_items:
            x_cursor += spacing

        placements.append((item, x_cursor, y_cursor))
        x_cursor += item["width"]
        shelf_height = max(shelf_height, item["depth"])
        shelf_has_items = True

    min_x = min(x for _, x, _ in placements)
    max_x = max(x + item["width"] for item, x, _ in placements)
    min_y = min(y for _, _, y in placements)
    max_y = max(y + item["depth"] for item, _, y in placements)
    offset_x = -(min_x + max_x) * 0.5
    offset_y = -(min_y + max_y) * 0.5

    for item, x, y in placements:
        target_center_x = x + item["width"] * 0.5 + offset_x
        target_center_y = y + item["depth"] * 0.5 + offset_y

        _move_group(
            item["obj"],
            Vector(
                (
                    target_center_x - item["center_x"],
                    target_center_y - item["center_y"],
                    -item["min_z"],
                )
            ),
        )


def center_on_world_origin(objects: Sequence[Object]) -> None:
    """Move every group's root origin to the world center (0, 0, 0), keeping rotation and scale.

    Children parented under a moved object are left alone so they keep their relative position.
    """
    for obj in group_roots(objects):
        matrix = obj.matrix_world.copy()
        matrix.translation = Vector((0.0, 0.0, 0.0))
        obj.matrix_world = matrix
