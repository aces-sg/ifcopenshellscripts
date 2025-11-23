"""
Distance calculation utilities.
"""

import math
from typing import Optional, Tuple

import ifcopenshell
import ifcopenshell.geom
import numpy as np


def calculate_distance(
    point1: Tuple[float, float, float],
    point2: Tuple[float, float, float],
) -> float:
    """
    Calculate Euclidean distance between two 3D points.

    Args:
        point1: First point (x, y, z)
        point2: Second point (x, y, z)

    Returns:
        Distance in model units
    """
    return math.sqrt(
        (point2[0] - point1[0]) ** 2
        + (point2[1] - point1[1]) ** 2
        + (point2[2] - point1[2]) ** 2
    )


def calculate_distance_2d(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> float:
    """
    Calculate Euclidean distance between two 2D points.

    Args:
        point1: First point (x, y)
        point2: Second point (x, y)

    Returns:
        Distance in model units
    """
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def get_element_centroid(
    element: ifcopenshell.entity_instance,
    settings: Optional[ifcopenshell.geom.settings] = None,
) -> Optional[Tuple[float, float, float]]:
    """
    Get the centroid of an IFC element.

    Args:
        element: IFC element
        settings: Optional geometry settings

    Returns:
        Centroid coordinates (x, y, z) or None if geometry cannot be computed
    """
    if settings is None:
        settings = ifcopenshell.geom.settings()

    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        verts = shape.geometry.verts
        # Vertices are stored as flat array [x1,y1,z1,x2,y2,z2,...]
        vertices = np.array(verts).reshape(-1, 3)
        centroid = vertices.mean(axis=0)
        return tuple(centroid)
    except Exception:
        return None


def get_element_location(
    element: ifcopenshell.entity_instance,
) -> Optional[Tuple[float, float, float]]:
    """
    Get the placement location of an IFC element.

    Args:
        element: IFC element with ObjectPlacement

    Returns:
        Location coordinates (x, y, z) or None
    """
    try:
        placement = element.ObjectPlacement
        if placement and placement.RelativePlacement:
            location = placement.RelativePlacement.Location
            if location:
                return (location.Coordinates[0], location.Coordinates[1], location.Coordinates[2])
    except Exception:
        pass
    return None
