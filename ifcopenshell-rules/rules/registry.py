"""
Rule registry for discovering and managing rules.
"""

from pathlib import Path
from typing import Optional

from .base import BaseRule

# Import rule implementations
from .fire_safety.travel_distance import TravelDistanceRule
from .fire_safety.egress import EgressWidthRule
from .accessibility.corridor_width import CorridorWidthRule
from .accessibility.door_clearance import DoorClearanceRule
from .building_control.setback import SetbackRule


# Map of rule classes by category
RULE_CLASSES: dict[str, list[type[BaseRule]]] = {
    "fire_safety": [TravelDistanceRule, EgressWidthRule],
    "accessibility": [CorridorWidthRule, DoorClearanceRule],
    "building_control": [SetbackRule],
}

# Map of config file names to rule classes
CONFIG_TO_RULE: dict[str, type[BaseRule]] = {
    "travel_distance.yaml": TravelDistanceRule,
    "egress.yaml": EgressWidthRule,
    "corridors.yaml": CorridorWidthRule,
    "doors.yaml": DoorClearanceRule,
    "setbacks.yaml": SetbackRule,
}


class RuleRegistry:
    """
    Registry for discovering and instantiating rules.

    Scans config directory for rule configurations and instantiates
    corresponding rule classes.
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self._rules: dict[str, list[BaseRule]] = {
            "fire_safety": [],
            "accessibility": [],
            "building_control": [],
        }
        self._load_rules()

    def _load_rules(self) -> None:
        """Load all rules from config directory."""
        for category in self._rules.keys():
            category_dir = self.config_dir / category
            if not category_dir.exists():
                continue

            for config_file in category_dir.glob("*.yaml"):
                rule_class = CONFIG_TO_RULE.get(config_file.name)
                if rule_class:
                    rule = rule_class(config_path=config_file)
                    self._rules[category].append(rule)

    def get_rules_by_category(self, category: str) -> list[BaseRule]:
        """Get all rules for a category."""
        return self._rules.get(category, [])

    def get_all_rules(self) -> list[BaseRule]:
        """Get all registered rules."""
        all_rules = []
        for rules in self._rules.values():
            all_rules.extend(rules)
        return all_rules

    def get_rule_by_id(self, rule_id: str) -> Optional[BaseRule]:
        """Get a specific rule by its ID."""
        for rules in self._rules.values():
            for rule in rules:
                if rule.RULE_ID == rule_id:
                    return rule
        return None
