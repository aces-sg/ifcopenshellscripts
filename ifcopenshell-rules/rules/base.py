"""
Base classes for rule definitions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

import yaml
import ifcopenshell


@dataclass
class Violation:
    """Represents a single rule violation."""

    element_id: int
    element_type: str
    element_name: Optional[str]
    message: str
    location: Optional[dict] = None  # {"x": float, "y": float, "z": float}
    severity: str = "error"  # error, warning, info
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "element_name": self.element_name,
            "message": self.message,
            "location": self.location,
            "severity": self.severity,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
        }


@dataclass
class RuleResult:
    """Result of a rule check."""

    rule_id: str
    name: str
    category: str
    reference: str
    passed: bool
    violations: list[Violation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category,
            "reference": self.reference,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "metadata": self.metadata,
        }


class BaseRule(ABC):
    """
    Abstract base class for all compliance rules.

    Rules are configured via YAML files and implement geometric checks
    against IFC models.
    """

    # Override in subclasses
    RULE_ID: str = ""
    CATEGORY: str = ""

    def __init__(self, config_path: Optional[Path] = None):
        self.config: dict = {}
        self.name: str = ""
        self.reference: str = ""
        self.parameters: dict = {}

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Load rule configuration from YAML file."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.name = self.config.get("name", self.__class__.__name__)
        self.reference = self.config.get("reference", "")
        self.parameters = self.config.get("parameters", {})

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value from config."""
        return self.parameters.get(key, default)

    @abstractmethod
    def check(self, model: ifcopenshell.file) -> RuleResult:
        """
        Execute the rule check against an IFC model.

        Args:
            model: The IFC model to check

        Returns:
            RuleResult containing pass/fail status and any violations
        """
        pass

    def _create_result(
        self, passed: bool, violations: list[Violation] = None
    ) -> RuleResult:
        """Helper to create a RuleResult."""
        return RuleResult(
            rule_id=self.RULE_ID,
            name=self.name,
            category=self.CATEGORY,
            reference=self.reference,
            passed=passed,
            violations=violations or [],
        )
