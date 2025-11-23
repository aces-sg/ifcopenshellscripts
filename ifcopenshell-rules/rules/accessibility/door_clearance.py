"""
Door Clearance Rule - BCA Accessibility Code.

Checks minimum clear opening width for doors.
"""

from typing import List

import ifcopenshell

from rules.base import BaseRule, RuleResult, Violation
from extractors.doors import DoorExtractor


class DoorClearanceRule(BaseRule):
    """
    Checks that doors provide adequate clear opening width
    for wheelchair access per BCA Accessibility Code.
    """

    RULE_ID = "ACC-002"
    CATEGORY = "accessibility"

    def check(self, model: ifcopenshell.file) -> RuleResult:
        """Check door clearance requirements."""
        violations: List[Violation] = []

        # Get parameters (in mm)
        min_clear_width = self.get_param("min_clear_width_mm", 850)
        min_main_entrance_width = self.get_param("min_main_entrance_width_mm", 900)

        # Get excluded door types
        exclude_types = self.config.get("exclude_door_types", ["TRAPDOOR", "GATE"])

        # Extract doors
        door_extractor = DoorExtractor(model)
        doors = door_extractor.get_all_doors()

        for door in doors:
            # Skip excluded types
            if door.door_type and door.door_type.upper() in exclude_types:
                continue

            # Get door clear width
            width = door.clear_width or door.overall_width

            if width is None:
                # Try to estimate from bounding box
                if door.bounding_box:
                    width = min(door.bounding_box.width, door.bounding_box.depth)
                    # Convert to mm if in meters
                    if width < 10:
                        width = width * 1000

            if width is None:
                continue

            # Determine required width
            # Main entrance doors need wider opening
            is_main_entrance = False
            if door.name:
                entrance_keywords = ["main", "entrance", "entry", "lobby"]
                is_main_entrance = any(
                    kw in door.name.lower() for kw in entrance_keywords
                )

            required_width = (
                min_main_entrance_width if is_main_entrance else min_clear_width
            )

            # Check width
            if width < required_width:
                door_desc = "Main entrance door" if is_main_entrance else "Door"
                violations.append(
                    Violation(
                        element_id=door.id,
                        element_type="IfcDoor",
                        element_name=door.name,
                        message=(
                            f"{door_desc} clear width ({width:.0f}mm) is less than "
                            f"minimum required for accessibility ({required_width}mm)"
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
                        expected_value=required_width,
                    )
                )

        return self._create_result(
            passed=len(violations) == 0,
            violations=violations,
        )
