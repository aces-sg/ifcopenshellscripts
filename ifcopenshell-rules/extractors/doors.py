"""
IfcDoor extraction utilities.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import ifcopenshell
import ifcopenshell.util.element

from geometry.clearance import get_bounding_box, get_opening_width, BoundingBox
from geometry.distance import get_element_centroid, get_element_location


@dataclass
class DoorData:
    """Extracted data from an IfcDoor."""

    element: ifcopenshell.entity_instance
    id: int
    global_id: str
    name: Optional[str]
    door_type: Optional[str]
    overall_width: Optional[float]
    overall_height: Optional[float]
    clear_width: Optional[float]
    clear_height: Optional[float]
    is_external: bool
    is_fire_rated: bool
    fire_rating: Optional[str]
    centroid: Optional[tuple]
    location: Optional[tuple]
    bounding_box: Optional[BoundingBox]
    properties: Dict[str, Any] = field(default_factory=dict)
    storey: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "global_id": self.global_id,
            "name": self.name,
            "door_type": self.door_type,
            "overall_width": self.overall_width,
            "overall_height": self.overall_height,
            "clear_width": self.clear_width,
            "is_external": self.is_external,
            "is_fire_rated": self.is_fire_rated,
            "fire_rating": self.fire_rating,
            "storey": self.storey,
        }


class DoorExtractor:
    """Extracts and caches IfcDoor data from IFC models."""

    def __init__(self, model: ifcopenshell.file):
        self.model = model
        self._cache: Dict[int, DoorData] = {}

    def get_all_doors(self) -> List[DoorData]:
        """Get all doors in the model."""
        doors = self.model.by_type("IfcDoor")
        return [self.extract(door) for door in doors]

    def get_external_doors(self) -> List[DoorData]:
        """Get all external doors."""
        all_doors = self.get_all_doors()
        return [d for d in all_doors if d.is_external]

    def get_fire_doors(self) -> List[DoorData]:
        """Get all fire-rated doors."""
        all_doors = self.get_all_doors()
        return [d for d in all_doors if d.is_fire_rated]

    def get_doors_by_storey(self, storey_name: str) -> List[DoorData]:
        """Get all doors on a specific storey."""
        all_doors = self.get_all_doors()
        return [d for d in all_doors if d.storey == storey_name]

    def extract(self, door: ifcopenshell.entity_instance) -> DoorData:
        """Extract data from a single IfcDoor."""
        door_id = door.id()

        if door_id in self._cache:
            return self._cache[door_id]

        # Get property sets
        psets = ifcopenshell.util.element.get_psets(door)

        # Extract dimensions
        overall_width = getattr(door, "OverallWidth", None)
        overall_height = getattr(door, "OverallHeight", None)

        # Try to get clear width from properties
        clear_width = get_opening_width(door)

        # Check if external
        is_external = False
        if "Pset_DoorCommon" in psets:
            is_external = psets["Pset_DoorCommon"].get("IsExternal", False)

        # Check fire rating
        is_fire_rated = False
        fire_rating = None
        if "Pset_DoorCommon" in psets:
            fire_rating = psets["Pset_DoorCommon"].get("FireRating")
            is_fire_rated = fire_rating is not None and fire_rating != ""

        # Get door type
        door_type = None
        if hasattr(door, "PredefinedType"):
            door_type = door.PredefinedType

        # Get storey
        storey = None
        try:
            container = ifcopenshell.util.element.get_container(door)
            if container and container.is_a("IfcBuildingStorey"):
                storey = container.Name
        except Exception:
            pass

        data = DoorData(
            element=door,
            id=door_id,
            global_id=door.GlobalId,
            name=door.Name,
            door_type=door_type,
            overall_width=overall_width,
            overall_height=overall_height,
            clear_width=clear_width,
            clear_height=None,  # Would need more detailed extraction
            is_external=is_external,
            is_fire_rated=is_fire_rated,
            fire_rating=fire_rating,
            centroid=get_element_centroid(door),
            location=get_element_location(door),
            bounding_box=get_bounding_box(door),
            properties=psets,
            storey=storey,
        )

        self._cache[door_id] = data
        return data
