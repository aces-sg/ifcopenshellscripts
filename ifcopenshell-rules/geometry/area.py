"""
Area calculation utilities.
"""

from typing import Optional

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


def calculate_area(vertices: list, is_3d: bool = False) -> float:
    """
    Calculate area of a polygon from vertices using the shoelace formula.

    Args:
        vertices: List of (x, y) or (x, y, z) tuples
        is_3d: If True, project to XY plane first

    Returns:
        Area in square model units
    """
    if len(vertices) < 3:
        return 0.0

    # Use only x, y coordinates
    if is_3d:
        vertices = [(v[0], v[1]) for v in vertices]

    n = len(vertices)
    area = 0.0

    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]

    return abs(area) / 2.0


def get_floor_area(
    space: ifcopenshell.entity_instance,
) -> Optional[float]:
    """
    Get the floor area of an IfcSpace.

    Args:
        space: IfcSpace element

    Returns:
        Floor area in square model units, or None if not available
    """
    # Try to get from quantities first
    try:
        psets = ifcopenshell.util.element.get_psets(space)
        for pset_name, pset_data in psets.items():
            if "Area" in pset_name or "Quantities" in pset_name:
                for key, value in pset_data.items():
                    if "area" in key.lower() and isinstance(value, (int, float)):
                        return float(value)
    except Exception:
        pass

    # Fallback: try to compute from geometry
    try:
        settings = ifcopenshell.geom.settings()
        shape = ifcopenshell.geom.create_shape(settings, space)
        # This is a simplified approach - proper area calculation
        # would require analyzing the floor polygon
        return None
    except Exception:
        return None


def get_space_net_area(space: ifcopenshell.entity_instance) -> Optional[float]:
    """
    Get the net floor area of an IfcSpace (excluding walls, columns).

    Args:
        space: IfcSpace element

    Returns:
        Net floor area or None
    """
    psets = ifcopenshell.util.element.get_psets(space)

    # Look for NetFloorArea in base quantities
    if "Qto_SpaceBaseQuantities" in psets:
        return psets["Qto_SpaceBaseQuantities"].get("NetFloorArea")

    # Look in other quantity sets
    for pset_name, pset_data in psets.items():
        if "net" in pset_name.lower() and "area" in pset_name.lower():
            for key, value in pset_data.items():
                if isinstance(value, (int, float)):
                    return float(value)

    return None
