"""
IfcSpace extraction utilities.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import ifcopenshell
import ifcopenshell.util.element

from geometry.clearance import get_bounding_box, BoundingBox
from geometry.distance import get_element_centroid


@dataclass
class SpaceData:
    """Extracted data from an IfcSpace."""

    element: ifcopenshell.entity_instance
    id: int
    global_id: str
    name: Optional[str]
    long_name: Optional[str]
    space_type: Optional[str]
    floor_area: Optional[float]
    height: Optional[float]
    centroid: Optional[tuple]
    bounding_box: Optional[BoundingBox]
    properties: Dict[str, Any] = field(default_factory=dict)
    storey: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "global_id": self.global_id,
            "name": self.name,
            "long_name": self.long_name,
            "space_type": self.space_type,
            "floor_area": self.floor_area,
            "height": self.height,
            "centroid": self.centroid,
            "storey": self.storey,
        }


class SpaceExtractor:
    """Extracts and caches IfcSpace data from IFC models."""

    def __init__(self, model: ifcopenshell.file):
        self.model = model
        self._cache: Dict[int, SpaceData] = {}

    def get_all_spaces(self) -> List[SpaceData]:
        """Get all spaces in the model."""
        spaces = self.model.by_type("IfcSpace")
        return [self.extract(space) for space in spaces]

    def get_spaces_by_storey(self, storey_name: str) -> List[SpaceData]:
        """Get all spaces on a specific storey."""
        all_spaces = self.get_all_spaces()
        return [s for s in all_spaces if s.storey == storey_name]

    def get_spaces_by_type(self, space_type: str) -> List[SpaceData]:
        """Get spaces of a specific type (e.g., 'CORRIDOR', 'OFFICE')."""
        all_spaces = self.get_all_spaces()
        return [
            s for s in all_spaces
            if s.space_type and space_type.lower() in s.space_type.lower()
        ]

    def extract(self, space: ifcopenshell.entity_instance) -> SpaceData:
        """Extract data from a single IfcSpace."""
        space_id = space.id()

        if space_id in self._cache:
            return self._cache[space_id]

        # Get property sets
        psets = ifcopenshell.util.element.get_psets(space)

        # Extract floor area
        floor_area = None
        if "Qto_SpaceBaseQuantities" in psets:
            floor_area = psets["Qto_SpaceBaseQuantities"].get("NetFloorArea")
            if floor_area is None:
                floor_area = psets["Qto_SpaceBaseQuantities"].get("GrossFloorArea")

        # Extract height
        height = None
        if "Qto_SpaceBaseQuantities" in psets:
            height = psets["Qto_SpaceBaseQuantities"].get("Height")

        # Get storey
        storey = None
        try:
            container = ifcopenshell.util.element.get_container(space)
            if container and container.is_a("IfcBuildingStorey"):
                storey = container.Name
        except Exception:
            pass

        # Get space type from PredefinedType or properties
        space_type = None
        if hasattr(space, "PredefinedType"):
            space_type = space.PredefinedType
        if space_type is None and "Pset_SpaceCommon" in psets:
            space_type = psets["Pset_SpaceCommon"].get("Category")

        data = SpaceData(
            element=space,
            id=space_id,
            global_id=space.GlobalId,
            name=space.Name,
            long_name=getattr(space, "LongName", None),
            space_type=space_type,
            floor_area=floor_area,
            height=height,
            centroid=get_element_centroid(space),
            bounding_box=get_bounding_box(space),
            properties=psets,
            storey=storey,
        )

        self._cache[space_id] = data
        return data

    def get_corridors(self) -> List[SpaceData]:
        """Get all corridor spaces."""
        return self.get_spaces_by_type("corridor")

    def get_rooms(self) -> List[SpaceData]:
        """Get all room spaces (excluding corridors, stairs, etc.)."""
        all_spaces = self.get_all_spaces()
        exclude_types = ["corridor", "stair", "elevator", "shaft", "toilet"]
        return [
            s for s in all_spaces
            if not any(
                t in (s.space_type or "").lower() or t in (s.name or "").lower()
                for t in exclude_types
            )
        ]
