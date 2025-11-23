"""
Clearance and bounding box utilities.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import ifcopenshell
import ifcopenshell.geom
import numpy as np


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def width(self) -> float:
        """Width along X axis."""
        return self.max_x - self.min_x

    @property
    def depth(self) -> float:
        """Depth along Y axis."""
        return self.max_y - self.min_y

    @property
    def height(self) -> float:
        """Height along Z axis."""
        return self.max_z - self.min_z

    @property
    def center(self) -> Tuple[float, float, float]:
        """Center point of bounding box."""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        )

    def to_dict(self) -> dict:
        return {
            "min": {"x": self.min_x, "y": self.min_y, "z": self.min_z},
            "max": {"x": self.max_x, "y": self.max_y, "z": self.max_z},
        }


def get_bounding_box(
    element: ifcopenshell.entity_instance,
    settings: Optional[ifcopenshell.geom.settings] = None,
) -> Optional[BoundingBox]:
    """
    Get the axis-aligned bounding box of an IFC element.

    Args:
        element: IFC element
        settings: Optional geometry settings

    Returns:
        BoundingBox or None if geometry cannot be computed
    """
    if settings is None:
        settings = ifcopenshell.geom.settings()

    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        verts = shape.geometry.verts
        vertices = np.array(verts).reshape(-1, 3)

        return BoundingBox(
            min_x=float(vertices[:, 0].min()),
            min_y=float(vertices[:, 1].min()),
            min_z=float(vertices[:, 2].min()),
            max_x=float(vertices[:, 0].max()),
            max_y=float(vertices[:, 1].max()),
            max_z=float(vertices[:, 2].max()),
        )
    except Exception:
        return None


def check_clearance(
    element1: ifcopenshell.entity_instance,
    element2: ifcopenshell.entity_instance,
    min_clearance: float,
) -> Tuple[bool, Optional[float]]:
    """
    Check if two elements have minimum clearance between them.

    Args:
        element1: First IFC element
        element2: Second IFC element
        min_clearance: Minimum required clearance

    Returns:
        Tuple of (passes_check, actual_clearance)
    """
    bbox1 = get_bounding_box(element1)
    bbox2 = get_bounding_box(element2)

    if bbox1 is None or bbox2 is None:
        return (True, None)  # Cannot check, assume pass

    # Calculate minimum distance between bounding boxes
    # This is a simplified check using axis-aligned boxes
    dx = max(0, max(bbox1.min_x - bbox2.max_x, bbox2.min_x - bbox1.max_x))
    dy = max(0, max(bbox1.min_y - bbox2.max_y, bbox2.min_y - bbox1.max_y))
    dz = max(0, max(bbox1.min_z - bbox2.max_z, bbox2.min_z - bbox1.max_z))

    clearance = np.sqrt(dx**2 + dy**2 + dz**2)

    return (clearance >= min_clearance, float(clearance))


def get_opening_width(door: ifcopenshell.entity_instance) -> Optional[float]:
    """
    Get the clear opening width of a door.

    Args:
        door: IfcDoor element

    Returns:
        Opening width in model units or None
    """
    # Try to get from OverallWidth attribute
    if hasattr(door, "OverallWidth") and door.OverallWidth:
        return float(door.OverallWidth)

    # Try to get from property sets
    try:
        import ifcopenshell.util.element
        psets = ifcopenshell.util.element.get_psets(door)

        for pset_name, pset_data in psets.items():
            for key, value in pset_data.items():
                if "width" in key.lower() and isinstance(value, (int, float)):
                    return float(value)
    except Exception:
        pass

    # Fallback to bounding box
    bbox = get_bounding_box(door)
    if bbox:
        # Assume door width is the smaller of width/depth
        return min(bbox.width, bbox.depth)

    return None
