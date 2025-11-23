"""
IfcWall extraction utilities.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import ifcopenshell
import ifcopenshell.util.element

from geometry.clearance import get_bounding_box, BoundingBox
from geometry.distance import get_element_centroid


@dataclass
class WallData:
    """Extracted data from an IfcWall."""

    element: ifcopenshell.entity_instance
    id: int
    global_id: str
    name: Optional[str]
    wall_type: Optional[str]
    is_external: bool
    is_load_bearing: bool
    fire_rating: Optional[str]
    thickness: Optional[float]
    height: Optional[float]
    length: Optional[float]
    centroid: Optional[tuple]
    bounding_box: Optional[BoundingBox]
    properties: Dict[str, Any] = field(default_factory=dict)
    storey: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "global_id": self.global_id,
            "name": self.name,
            "wall_type": self.wall_type,
            "is_external": self.is_external,
            "is_load_bearing": self.is_load_bearing,
            "fire_rating": self.fire_rating,
            "thickness": self.thickness,
            "height": self.height,
            "length": self.length,
            "storey": self.storey,
        }


class WallExtractor:
    """Extracts and caches IfcWall data from IFC models."""

    def __init__(self, model: ifcopenshell.file):
        self.model = model
        self._cache: Dict[int, WallData] = {}

    def get_all_walls(self) -> List[WallData]:
        """Get all walls in the model."""
        walls = self.model.by_type("IfcWall")
        return [self.extract(wall) for wall in walls]

    def get_external_walls(self) -> List[WallData]:
        """Get all external walls."""
        all_walls = self.get_all_walls()
        return [w for w in all_walls if w.is_external]

    def get_fire_rated_walls(self) -> List[WallData]:
        """Get all fire-rated walls."""
        all_walls = self.get_all_walls()
        return [w for w in all_walls if w.fire_rating]

    def get_walls_by_storey(self, storey_name: str) -> List[WallData]:
        """Get all walls on a specific storey."""
        all_walls = self.get_all_walls()
        return [w for w in all_walls if w.storey == storey_name]

    def extract(self, wall: ifcopenshell.entity_instance) -> WallData:
        """Extract data from a single IfcWall."""
        wall_id = wall.id()

        if wall_id in self._cache:
            return self._cache[wall_id]

        # Get property sets
        psets = ifcopenshell.util.element.get_psets(wall)

        # Check if external
        is_external = False
        if "Pset_WallCommon" in psets:
            is_external = psets["Pset_WallCommon"].get("IsExternal", False)

        # Check if load bearing
        is_load_bearing = False
        if "Pset_WallCommon" in psets:
            is_load_bearing = psets["Pset_WallCommon"].get("LoadBearing", False)

        # Get fire rating
        fire_rating = None
        if "Pset_WallCommon" in psets:
            fire_rating = psets["Pset_WallCommon"].get("FireRating")

        # Get dimensions from quantities
        thickness = None
        height = None
        length = None
        if "Qto_WallBaseQuantities" in psets:
            quantities = psets["Qto_WallBaseQuantities"]
            thickness = quantities.get("Width")
            height = quantities.get("Height")
            length = quantities.get("Length")

        # Get wall type
        wall_type = None
        if hasattr(wall, "PredefinedType"):
            wall_type = wall.PredefinedType

        # Get storey
        storey = None
        try:
            container = ifcopenshell.util.element.get_container(wall)
            if container and container.is_a("IfcBuildingStorey"):
                storey = container.Name
        except Exception:
            pass

        # Get bounding box for dimension fallback
        bbox = get_bounding_box(wall)
        if bbox and thickness is None:
            # Estimate thickness as minimum horizontal dimension
            thickness = min(bbox.width, bbox.depth)
        if bbox and height is None:
            height = bbox.height

        data = WallData(
            element=wall,
            id=wall_id,
            global_id=wall.GlobalId,
            name=wall.Name,
            wall_type=wall_type,
            is_external=is_external,
            is_load_bearing=is_load_bearing,
            fire_rating=fire_rating,
            thickness=thickness,
            height=height,
            length=length,
            centroid=get_element_centroid(wall),
            bounding_box=bbox,
            properties=psets,
            storey=storey,
        )

        self._cache[wall_id] = data
        return data
