"""
Egress Width Rule - Singapore Fire Code.

Checks minimum width requirements for exit doors and corridors.
"""

from typing import List

import ifcopenshell

from rules.base import BaseRule, RuleResult, Violation
from extractors.spaces import SpaceExtractor
from extractors.doors import DoorExtractor


class EgressWidthRule(BaseRule):
    """
    Checks that egress routes meet minimum width requirements
    per Singapore Fire Code.
    """

    RULE_ID = "FS-002"
    CATEGORY = "fire_safety"

    def check(self, model: ifcopenshell.file) -> RuleResult:
        """Check egress width requirements."""
        violations: List[Violation] = []

        # Get parameters (in mm)
        min_door_width = self.get_param("min_door_width_mm", 850)
        min_corridor_width = self.get_param("min_corridor_width_mm", 1200)

        # Check doors
        door_extractor = DoorExtractor(model)
        doors = door_extractor.get_all_doors()

        for door in doors:
            # Get door width (try clear width first, then overall)
            width = door.clear_width or door.overall_width

            if width is None:
                # Try to estimate from bounding box
                if door.bounding_box:
                    # Width is typically the smaller horizontal dimension
                    width = min(door.bounding_box.width, door.bounding_box.depth)
                    # Convert to mm if in meters (heuristic: if < 10, assume meters)
                    if width < 10:
                        width = width * 1000

            if width is not None and width < min_door_width:
                violations.append(
                    Violation(
                        element_id=door.id,
                        element_type="IfcDoor",
                        element_name=door.name,
                        message=(
                            f"Door width ({width:.0f}mm) is less than "
                            f"minimum required ({min_door_width}mm)"
                        ),
                        location=(
                            {
                                "x": door.centroid[0],
                                "y": door.centroid[1],
                                "z": door.centroid[2],
                            }
                            if door.centroid
                            else None
                        ),
                        severity="error",
                        actual_value=round(width),
                        expected_value=min_door_width,
                    )
                )

        # Check corridors
        space_extractor = SpaceExtractor(model)
        corridors = space_extractor.get_corridors()

        for corridor in corridors:
            # Get corridor width from bounding box
            width = None
            if corridor.bounding_box:
                # Width is the smaller horizontal dimension
                width = min(corridor.bounding_box.width, corridor.bounding_box.depth)
                # Convert to mm if in meters
                if width < 100:
                    width = width * 1000

            if width is not None and width < min_corridor_width:
                violations.append(
                    Violation(
                        element_id=corridor.id,
                        element_type="IfcSpace",
                        element_name=corridor.name or corridor.long_name,
                        message=(
                            f"Corridor width ({width:.0f}mm) is less than "
                            f"minimum required ({min_corridor_width}mm)"
                        ),
                        location=(
                            {
                                "x": corridor.centroid[0],
                                "y": corridor.centroid[1],
                                "z": corridor.centroid[2],
                            }
                            if corridor.centroid
                            else None
                        ),
                        severity="error",
                        actual_value=round(width),
                        expected_value=min_corridor_width,
                    )
                )

        return self._create_result(
            passed=len(violations) == 0,
            violations=violations,
        )
