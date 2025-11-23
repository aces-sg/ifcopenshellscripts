"""
IfcStair extraction utilities.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import ifcopenshell
import ifcopenshell.util.element

from geometry.clearance import get_bounding_box, BoundingBox
from geometry.distance import get_element_centroid


@dataclass
class StairData:
    """Extracted data from an IfcStair."""

    element: ifcopenshell.entity_instance
    id: int
    global_id: str
    name: Optional[str]
    stair_type: Optional[str]
    number_of_risers: Optional[int]
    number_of_treads: Optional[int]
    riser_height: Optional[float]
    tread_length: Optional[float]
    stair_width: Optional[float]
    is_external: bool
    centroid: Optional[tuple]
    bounding_box: Optional[BoundingBox]
    properties: Dict[str, Any] = field(default_factory=dict)
    storey: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "global_id": self.global_id,
            "name": self.name,
            "stair_type": self.stair_type,
            "number_of_risers": self.number_of_risers,
            "number_of_treads": self.number_of_treads,
            "riser_height": self.riser_height,
            "tread_length": self.tread_length,
            "stair_width": self.stair_width,
            "is_external": self.is_external,
            "storey": self.storey,
        }


class StairExtractor:
    """Extracts and caches IfcStair data from IFC models."""

    def __init__(self, model: ifcopenshell.file):
        self.model = model
        self._cache: Dict[int, StairData] = {}

    def get_all_stairs(self) -> List[StairData]:
        """Get all stairs in the model."""
        stairs = self.model.by_type("IfcStair")
        return [self.extract(stair) for stair in stairs]

    def get_stairs_by_storey(self, storey_name: str) -> List[StairData]:
        """Get all stairs on a specific storey."""
        all_stairs = self.get_all_stairs()
        return [s for s in all_stairs if s.storey == storey_name]

    def extract(self, stair: ifcopenshell.entity_instance) -> StairData:
        """Extract data from a single IfcStair."""
        stair_id = stair.id()

        if stair_id in self._cache:
            return self._cache[stair_id]

        # Get property sets
        psets = ifcopenshell.util.element.get_psets(stair)

        # Get stair dimensions from properties
        number_of_risers = None
        number_of_treads = None
        riser_height = None
        tread_length = None

        if "Pset_StairCommon" in psets:
            common = psets["Pset_StairCommon"]
            number_of_risers = common.get("NumberOfRiser")
            number_of_treads = common.get("NumberOfTreads")
            riser_height = common.get("RiserHeight")
            tread_length = common.get("TreadLength")

        # Check if external
        is_external = False
        if "Pset_StairCommon" in psets:
            is_external = psets["Pset_StairCommon"].get("IsExternal", False)

        # Get stair type
        stair_type = None
        if hasattr(stair, "PredefinedType"):
            stair_type = stair.PredefinedType
        elif hasattr(stair, "ShapeType"):
            stair_type = stair.ShapeType

        # Get storey
        storey = None
        try:
            container = ifcopenshell.util.element.get_container(stair)
            if container and container.is_a("IfcBuildingStorey"):
                storey = container.Name
        except Exception:
            pass

        # Get width from bounding box
        bbox = get_bounding_box(stair)
        stair_width = None
        if bbox:
            # Width is typically the smaller horizontal dimension
            stair_width = min(bbox.width, bbox.depth)

        data = StairData(
            element=stair,
            id=stair_id,
            global_id=stair.GlobalId,
            name=stair.Name,
            stair_type=stair_type,
            number_of_risers=number_of_risers,
            number_of_treads=number_of_treads,
            riser_height=riser_height,
            tread_length=tread_length,
            stair_width=stair_width,
            is_external=is_external,
            centroid=get_element_centroid(stair),
            bounding_box=bbox,
            properties=psets,
            storey=storey,
        )

        self._cache[stair_id] = data
        return data


class StairFlightExtractor:
    """Extracts IfcStairFlight data for detailed stair analysis."""

    def __init__(self, model: ifcopenshell.file):
        self.model = model

    def get_flights_for_stair(
        self, stair: ifcopenshell.entity_instance
    ) -> List[ifcopenshell.entity_instance]:
        """Get all stair flights that are part of a stair."""
        flights = []

        # Check decomposition relationship
        try:
            if hasattr(stair, "IsDecomposedBy"):
                for rel in stair.IsDecomposedBy or []:
                    for obj in rel.RelatedObjects:
                        if obj.is_a("IfcStairFlight"):
                            flights.append(obj)
        except Exception:
            pass

        return flights
