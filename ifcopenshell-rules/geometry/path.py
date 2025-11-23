"""
Path and travel distance utilities for egress calculations.
"""

from typing import Optional, Tuple, List

import ifcopenshell


def calculate_travel_distance(
    start_point: Tuple[float, float, float],
    end_point: Tuple[float, float, float],
    waypoints: Optional[List[Tuple[float, float, float]]] = None,
) -> float:
    """
    Calculate travel distance between two points, optionally through waypoints.

    This is a simplified calculation using straight-line distances.
    For more accurate results, use path-finding algorithms with
    space boundaries.

    Args:
        start_point: Starting location (x, y, z)
        end_point: Destination (x, y, z)
        waypoints: Optional intermediate points

    Returns:
        Total travel distance in model units
    """
    import math

    points = [start_point]
    if waypoints:
        points.extend(waypoints)
    points.append(end_point)

    total_distance = 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        # Use 2D distance (horizontal travel)
        distance = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        total_distance += distance

    return total_distance


def find_shortest_path(
    model: ifcopenshell.file,
    start_space: ifcopenshell.entity_instance,
    target_type: str = "IfcDoor",
) -> Optional[Tuple[float, List]]:
    """
    Find shortest path from a space to nearest element of target type.

    This is a simplified implementation that finds the nearest target
    element by straight-line distance. A full implementation would use
    proper graph-based path finding through connected spaces.

    Args:
        model: IFC model
        start_space: Starting IfcSpace
        target_type: IFC type to find (e.g., "IfcDoor" for exits)

    Returns:
        Tuple of (distance, path) or None if no path found
    """
    from .distance import get_element_centroid, calculate_distance

    start_centroid = get_element_centroid(start_space)
    if start_centroid is None:
        return None

    # Find all target elements
    targets = model.by_type(target_type)
    if not targets:
        return None

    # Find nearest target
    min_distance = float("inf")
    nearest_target = None

    for target in targets:
        target_centroid = get_element_centroid(target)
        if target_centroid:
            distance = calculate_distance(start_centroid, target_centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_target = target

    if nearest_target is None:
        return None

    # Return simplified path (direct line)
    target_centroid = get_element_centroid(nearest_target)
    return (min_distance, [start_centroid, target_centroid])


def get_connected_spaces(
    space: ifcopenshell.entity_instance,
    model: ifcopenshell.file,
) -> List[ifcopenshell.entity_instance]:
    """
    Get spaces connected to the given space through doors or openings.

    Args:
        space: IfcSpace to analyze
        model: IFC model

    Returns:
        List of connected IfcSpace elements
    """
    connected = []

    # Get space boundaries
    try:
        if hasattr(space, "BoundedBy"):
            for boundary in space.BoundedBy or []:
                related_element = boundary.RelatedBuildingElement
                if related_element and related_element.is_a("IfcDoor"):
                    # Find space on other side of door
                    for other_boundary in model.by_type("IfcRelSpaceBoundary"):
                        if (
                            other_boundary.RelatedBuildingElement == related_element
                            and other_boundary.RelatingSpace != space
                        ):
                            connected.append(other_boundary.RelatingSpace)
    except Exception:
        pass

    return connected
