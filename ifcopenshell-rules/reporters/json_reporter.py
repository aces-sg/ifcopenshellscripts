"""
JSON report generator for compliance results.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from rules.base import RuleResult


class JSONReporter:
    """Generates JSON compliance reports."""

    def __init__(self):
        self.include_metadata = True
        self.include_passed_rules = True

    def generate(
        self,
        model_path: str,
        results: List[RuleResult],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Generate a JSON compliance report.

        Args:
            model_path: Path to the IFC model
            results: List of rule results
            metadata: Optional additional metadata

        Returns:
            Dictionary ready for JSON serialization
        """
        # Calculate summary statistics
        total_rules = len(results)
        passed_rules = sum(1 for r in results if r.passed)
        failed_rules = total_rules - passed_rules
        total_violations = sum(len(r.violations) for r in results)

        # Categorize results
        results_by_category: Dict[str, List[dict]] = {}
        for result in results:
            category = result.category
            if category not in results_by_category:
                results_by_category[category] = []

            if self.include_passed_rules or not result.passed:
                results_by_category[category].append(result.to_dict())

        # Count violations by severity
        severity_counts = {"error": 0, "warning": 0, "info": 0}
        for result in results:
            for violation in result.violations:
                severity = violation.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "IFC Rule Engine - Singapore Code of Practice",
                "generator_version": "1.0.0",
                "model_path": model_path,
            },
            "summary": {
                "total_rules_checked": total_rules,
                "rules_passed": passed_rules,
                "rules_failed": failed_rules,
                "compliance_rate": (
                    round(passed_rules / total_rules * 100, 1) if total_rules > 0 else 0
                ),
                "total_violations": total_violations,
                "violations_by_severity": severity_counts,
            },
            "results_by_category": results_by_category,
        }

        if metadata and self.include_metadata:
            report["report_metadata"].update(metadata)

        return report

    def generate_summary(self, results: List[RuleResult]) -> dict:
        """
        Generate a minimal summary report.

        Args:
            results: List of rule results

        Returns:
            Summary dictionary
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)

        failed_rules = [
            {"rule_id": r.rule_id, "name": r.name, "violations": len(r.violations)}
            for r in results
            if not r.passed
        ]

        return {
            "total_rules": total,
            "passed": passed,
            "failed": total - passed,
            "compliance_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "failed_rules": failed_rules,
        }

    def format_violation_message(
        self, result: RuleResult, include_location: bool = True
    ) -> List[str]:
        """
        Format violations as human-readable messages.

        Args:
            result: Rule result with violations
            include_location: Whether to include location info

        Returns:
            List of formatted message strings
        """
        messages = []

        for v in result.violations:
            msg = f"[{v.severity.upper()}] {result.rule_id}: {v.message}"
            if v.element_name:
                msg += f" (Element: {v.element_name})"
            if include_location and v.location:
                loc = v.location
                msg += f" @ ({loc.get('x', 0):.2f}, {loc.get('y', 0):.2f}, {loc.get('z', 0):.2f})"
            messages.append(msg)

        return messages
