"""Object layout helpers: grid arrangement and world-center reset."""

from __future__ import annotations

import math
from typing import Sequence

from bpy.types import Object
from mathutils import Vector


def _world_bounds(obj: Object) -> tuple[Vector, Vector]:
    """Return the (min, max) world-space axis-aligned bounding box corners for an object."""
    bound_box = getattr(obj, "bound_box", None)
    if not bound_box:
        origin = obj.matrix_world.translation.copy()
        return origin, origin.copy()

    corners = [obj.matrix_world @ Vector(corner) for corner in bound_box]
    min_corner = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    max_corner = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return min_corner, max_corner


def arrange_grid(objects: Sequence[Object], margin: float = 1.0) -> None:
    """Arrange objects on an evenly spaced XY grid so their bounding boxes never overlap."""
    objects = [obj for obj in objects if obj is not None]
    if not objects:
        return

    bounds = {obj.name: _world_bounds(obj) for obj in objects}
    footprint = max(
        max(max_corner.x - min_corner.x, max_corner.y - min_corner.y) for min_corner, max_corner in bounds.values()
    )
    cell_size = max(footprint, 0.001) + margin

    columns = math.ceil(math.sqrt(len(objects)))
    ordered = sorted(objects, key=lambda obj: obj.name)

    for index, obj in enumerate(ordered):
        column = index % columns
        row = index // columns
        min_corner, max_corner = bounds[obj.name]
        current_center_x = (min_corner.x + max_corner.x) * 0.5
        current_center_y = (min_corner.y + max_corner.y) * 0.5
        target_x = column * cell_size
        target_y = -row * cell_size

        matrix = obj.matrix_world.copy()
        matrix.translation.x += target_x - current_center_x
        matrix.translation.y += target_y - current_center_y
        obj.matrix_world = matrix


def arrange_compact_grid(objects: Sequence[Object], spacing: float = 0.1, sort_by_size: bool = True) -> None:
    """Pack objects on the XY plane with shelf-based 2D rectangle packing.

    Each object's footprint is its world-space bounding-box width/depth. Objects are packed
    edge-to-edge with an exact ``spacing`` gap between neighbors (no wasted uniform-cell space),
    rotation and scale are untouched, every object's bounding-box bottom is placed at Z = 0,
    and the whole packed layout is re-centered on the world origin.

    When ``sort_by_size`` is enabled, objects are ordered by bounding-box area (largest first)
    before packing, so big objects land toward the top-left and shrink left to right / row to
    row. When disabled, objects are packed in the order they were given.
    """
    objects = [obj for obj in objects if obj is not None]
    if not objects:
        return

    items = []
    for obj in objects:
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
        obj = item["obj"]
        target_center_x = x + item["width"] * 0.5 + offset_x
        target_center_y = y + item["depth"] * 0.5 + offset_y

        matrix = obj.matrix_world.copy()
        matrix.translation.x += target_center_x - item["center_x"]
        matrix.translation.y += target_center_y - item["center_y"]
        matrix.translation.z += -item["min_z"]
        obj.matrix_world = matrix


def center_on_world_origin(objects: Sequence[Object]) -> None:
    """Move every object's origin to the world center (0, 0, 0), keeping rotation and scale."""
    for obj in objects:
        if obj is None:
            continue
        matrix = obj.matrix_world.copy()
        matrix.translation = Vector((0.0, 0.0, 0.0))
        obj.matrix_world = matrix
