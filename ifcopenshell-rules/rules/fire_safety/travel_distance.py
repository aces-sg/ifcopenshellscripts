"""
Travel Distance Rule - Singapore Fire Code.

Checks maximum travel distance from any point to nearest exit.
"""

from typing import List

import ifcopenshell

from rules.base import BaseRule, RuleResult, Violation
from extractors.spaces import SpaceExtractor
from extractors.doors import DoorExtractor
from geometry.distance import calculate_distance


class TravelDistanceRule(BaseRule):
    """
    Checks that travel distance to nearest exit does not exceed
    maximum allowed distance per Singapore Fire Code.
    """

    RULE_ID = "FS-001"
    CATEGORY = "fire_safety"

    def check(self, model: ifcopenshell.file) -> RuleResult:
        """Check travel distances for all spaces."""
        violations: List[Violation] = []

        # Get parameters
        max_sprinklered = self.get_param("max_distance_sprinklered_m", 60)
        max_unsprinklered = self.get_param("max_distance_unsprinklered_m", 45)
        default_sprinklered = self.get_param("default_sprinklered", True)

        # For simplicity, use sprinklered value
        # A full implementation would check building properties
        max_distance = max_sprinklered if default_sprinklered else max_unsprinklered

        # Convert to model units (assuming meters)
        max_distance_units = max_distance

        # Extract spaces and doors
        space_extractor = SpaceExtractor(model)
        door_extractor = DoorExtractor(model)

        spaces = space_extractor.get_all_spaces()
        doors = door_extractor.get_all_doors()

        # Filter to external doors (potential exits)
        exit_doors = [d for d in doors if d.is_external]

        # If no external doors found, use all doors as potential exits
        if not exit_doors:
            exit_doors = doors

        if not exit_doors:
            # No doors found - cannot check
            return self._create_result(
                passed=True,
                violations=[],
            )

        # Get exit door locations
        exit_locations = []
        for door in exit_doors:
            if door.centroid:
                exit_locations.append((door, door.centroid))

        if not exit_locations:
            return self._create_result(passed=True, violations=[])

        # Check each space
        for space in spaces:
            if space.centroid is None:
                continue

            # Find nearest exit
            min_distance = float("inf")
            nearest_exit = None

            for door, exit_loc in exit_locations:
                distance = calculate_distance(space.centroid, exit_loc)
                if distance < min_distance:
                    min_distance = distance
                    nearest_exit = door

            # Check if distance exceeds maximum
            if min_distance > max_distance_units:
                violations.append(
                    Violation(
                        element_id=space.id,
                        element_type="IfcSpace",
                        element_name=space.name or space.long_name,
                        message=(
                            f"Travel distance to nearest exit ({min_distance:.1f}m) "
                            f"exceeds maximum allowed ({max_distance_units}m)"
                        ),
                        location={
                            "x": space.centroid[0],
                            "y": space.centroid[1],
                            "z": space.centroid[2],
                        },
                        severity="error",
                        actual_value=round(min_distance, 2),
                        expected_value=max_distance_units,
                    )
                )

        return self._create_result(
            passed=len(violations) == 0,
            violations=violations,
        )
