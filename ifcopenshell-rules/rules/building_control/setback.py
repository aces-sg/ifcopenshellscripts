"""
Setback Rule - URA Development Control Guidelines.

Checks building setback from property boundaries.
"""

from typing import List, Optional, Tuple

import ifcopenshell
import ifcopenshell.util.element

from rules.base import BaseRule, RuleResult, Violation
from geometry.clearance import get_bounding_box


class SetbackRule(BaseRule):
    """
    Checks that building maintains required setback distances
    from property boundaries per URA guidelines.
    """

    RULE_ID = "BC-001"
    CATEGORY = "building_control"

    def check(self, model: ifcopenshell.file) -> RuleResult:
        """Check setback requirements."""
        violations: List[Violation] = []

        # Get parameters (in meters)
        front_setback = self.get_param("front_setback_m", 7.5)
        side_setback = self.get_param("side_setback_m", 3.0)
        rear_setback = self.get_param("rear_setback_m", 3.0)

        # Get site information
        sites = model.by_type("IfcSite")
        if not sites:
            # Cannot check without site information
            result = self._create_result(passed=True, violations=[])
            result.metadata["note"] = "No IfcSite found - setback check skipped"
            return result

        site = sites[0]

        # Try to get site boundary
        site_boundary = self._get_site_boundary(site, model)

        if site_boundary is None:
            result = self._create_result(passed=True, violations=[])
            result.metadata["note"] = "Site boundary not defined - setback check skipped"
            return result

        # Get building bounding box
        buildings = model.by_type("IfcBuilding")
        if not buildings:
            result = self._create_result(passed=True, violations=[])
            result.metadata["note"] = "No IfcBuilding found - setback check skipped"
            return result

        # Get overall building footprint from external walls
        external_walls = []
        for wall in model.by_type("IfcWall"):
            psets = ifcopenshell.util.element.get_psets(wall)
            if "Pset_WallCommon" in psets:
                if psets["Pset_WallCommon"].get("IsExternal", False):
                    external_walls.append(wall)

        if not external_walls:
            # Use all walls if no external walls marked
            external_walls = list(model.by_type("IfcWall"))

        if not external_walls:
            result = self._create_result(passed=True, violations=[])
            result.metadata["note"] = "No walls found - setback check skipped"
            return result

        # Calculate building extents
        building_bounds = self._get_combined_bounds(external_walls)

        if building_bounds is None:
            result = self._create_result(passed=True, violations=[])
            result.metadata["note"] = "Could not compute building bounds"
            return result

        # Check setbacks (simplified: compare bounding boxes)
        min_x, min_y, max_x, max_y = building_bounds
        site_min_x, site_min_y, site_max_x, site_max_y = site_boundary

        # Front setback (assume front is min_y)
        actual_front = min_y - site_min_y
        if actual_front < front_setback:
            violations.append(
                Violation(
                    element_id=buildings[0].id(),
                    element_type="IfcBuilding",
                    element_name=buildings[0].Name,
                    message=(
                        f"Front setback ({actual_front:.2f}m) is less than "
                        f"required ({front_setback}m)"
                    ),
                    severity="error",
                    actual_value=round(actual_front, 2),
                    expected_value=front_setback,
                )
            )

        # Rear setback (assume rear is max_y)
        actual_rear = site_max_y - max_y
        if actual_rear < rear_setback:
            violations.append(
                Violation(
                    element_id=buildings[0].id(),
                    element_type="IfcBuilding",
                    element_name=buildings[0].Name,
                    message=(
                        f"Rear setback ({actual_rear:.2f}m) is less than "
                        f"required ({rear_setback}m)"
                    ),
                    severity="error",
                    actual_value=round(actual_rear, 2),
                    expected_value=rear_setback,
                )
            )

        # Left side setback
        actual_left = min_x - site_min_x
        if actual_left < side_setback:
            violations.append(
                Violation(
                    element_id=buildings[0].id(),
                    element_type="IfcBuilding",
                    element_name=buildings[0].Name,
                    message=(
                        f"Left side setback ({actual_left:.2f}m) is less than "
                        f"required ({side_setback}m)"
                    ),
                    severity="error",
                    actual_value=round(actual_left, 2),
                    expected_value=side_setback,
                )
            )

        # Right side setback
        actual_right = site_max_x - max_x
        if actual_right < side_setback:
            violations.append(
                Violation(
                    element_id=buildings[0].id(),
                    element_type="IfcBuilding",
                    element_name=buildings[0].Name,
                    message=(
                        f"Right side setback ({actual_right:.2f}m) is less than "
                        f"required ({side_setback}m)"
                    ),
                    severity="error",
                    actual_value=round(actual_right, 2),
                    expected_value=side_setback,
                )
            )

        return self._create_result(
            passed=len(violations) == 0,
            violations=violations,
        )

    def _get_site_boundary(
        self, site: ifcopenshell.entity_instance, model: ifcopenshell.file
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Get site boundary as (min_x, min_y, max_x, max_y).

        Returns None if boundary cannot be determined.
        """
        # Try to get from site geometry
        bbox = get_bounding_box(site)
        if bbox:
            return (bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)

        # Try to get from property sets
        psets = ifcopenshell.util.element.get_psets(site)
        if "Pset_SiteCommon" in psets:
            # Some models store site dimensions
            pass

        return None

    def _get_combined_bounds(
        self, elements: List[ifcopenshell.entity_instance]
    ) -> Optional[Tuple[float, float, float, float]]:
        """Get combined XY bounds of multiple elements."""
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        found_any = False

        for element in elements:
            bbox = get_bounding_box(element)
            if bbox:
                found_any = True
                min_x = min(min_x, bbox.min_x)
                min_y = min(min_y, bbox.min_y)
                max_x = max(max_x, bbox.max_x)
                max_y = max(max_y, bbox.max_y)

        if not found_any:
            return None

        return (min_x, min_y, max_x, max_y)
