"""
Corridor Width Rule - BCA Accessibility Code.

Checks minimum corridor width for wheelchair accessibility.
"""

from typing import List

import ifcopenshell

from rules.base import BaseRule, RuleResult, Violation
from extractors.spaces import SpaceExtractor


class CorridorWidthRule(BaseRule):
    """
    Checks that corridors meet minimum width requirements
    for accessibility per BCA Accessibility Code.
    """

    RULE_ID = "ACC-001"
    CATEGORY = "accessibility"

    def check(self, model: ifcopenshell.file) -> RuleResult:
        """Check corridor width requirements."""
        violations: List[Violation] = []

        # Get parameters (in mm)
        min_width = self.get_param("min_width_mm", 1200)
        min_width_turning = self.get_param("min_width_turning_mm", 1500)

        # Get corridor identification patterns
        corridor_config = self.config.get("corridor_identification", {})
        space_types = corridor_config.get(
            "space_types", ["CORRIDOR", "HALLWAY", "PASSAGE"]
        )
        name_patterns = corridor_config.get(
            "name_patterns", ["corridor", "hallway", "passage"]
        )

        # Extract spaces
        space_extractor = SpaceExtractor(model)
        all_spaces = space_extractor.get_all_spaces()

        # Find corridors
        corridors = []
        for space in all_spaces:
            is_corridor = False

            # Check space type
            if space.space_type:
                for st in space_types:
                    if st.lower() in space.space_type.lower():
                        is_corridor = True
                        break

            # Check name
            if not is_corridor and space.name:
                for pattern in name_patterns:
                    if pattern.lower() in space.name.lower():
                        is_corridor = True
                        break

            # Check long name
            if not is_corridor and space.long_name:
                for pattern in name_patterns:
                    if pattern.lower() in space.long_name.lower():
                        is_corridor = True
                        break

            if is_corridor:
                corridors.append(space)

        # Check each corridor
        for corridor in corridors:
            width = None

            # Try to get width from bounding box
            if corridor.bounding_box:
                # Width is the smaller horizontal dimension
                width = min(corridor.bounding_box.width, corridor.bounding_box.depth)
                # Convert to mm if in meters (heuristic)
                if width < 100:
                    width = width * 1000

            if width is None:
                continue

            # Check minimum width
            if width < min_width:
                violations.append(
                    Violation(
                        element_id=corridor.id,
                        element_type="IfcSpace",
                        element_name=corridor.name or corridor.long_name,
                        message=(
                            f"Corridor width ({width:.0f}mm) is less than "
                            f"minimum required for accessibility ({min_width}mm)"
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
                        expected_value=min_width,
                    )
                )
            elif width < min_width_turning:
                # Warning if below turning width
                violations.append(
                    Violation(
                        element_id=corridor.id,
                        element_type="IfcSpace",
                        element_name=corridor.name or corridor.long_name,
                        message=(
                            f"Corridor width ({width:.0f}mm) is below recommended "
                            f"width for wheelchair turning ({min_width_turning}mm)"
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
                        severity="warning",
                        actual_value=round(width),
                        expected_value=min_width_turning,
                    )
                )

        return self._create_result(
            passed=all(v.severity != "error" for v in violations),
            violations=violations,
        )
