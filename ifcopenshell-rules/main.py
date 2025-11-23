#!/usr/bin/env python3
"""
IFC Rule Engine - Singapore Code of Practice Compliance Checker

Validates IFC models against Singapore building codes including:
- Fire Safety Code
- BCA Accessibility Code
- Building Control regulations
"""

import json
import click
from pathlib import Path
from typing import Optional

import ifcopenshell

from rules.registry import RuleRegistry
from reporters.json_reporter import JSONReporter


@click.command()
@click.option(
    "--ifc-path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the IFC file to validate",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("config"),
    help="Directory containing rule configuration files",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("outputs/compliance_report.json"),
    help="Output path for compliance report",
)
@click.option(
    "--category",
    type=click.Choice(["all", "fire_safety", "accessibility", "building_control"]),
    default="all",
    help="Rule category to check",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def main(
    ifc_path: Path,
    config_dir: Path,
    output: Path,
    category: str,
    verbose: bool,
) -> None:
    """
    Validate an IFC model against Singapore Code of Practice rules.
    """
    click.echo(f"Loading IFC model: {ifc_path}")
    model = ifcopenshell.open(str(ifc_path))

    click.echo(f"IFC Schema: {model.schema}")
    click.echo(f"Total elements: {len(list(model))}")

    # Initialize rule registry and load rules
    registry = RuleRegistry(config_dir)

    if category == "all":
        categories = ["fire_safety", "accessibility", "building_control"]
    else:
        categories = [category]

    click.echo(f"\nRunning rules for categories: {', '.join(categories)}")

    # Execute rules
    results = []
    for cat in categories:
        rules = registry.get_rules_by_category(cat)
        if verbose:
            click.echo(f"\n  Category: {cat} ({len(rules)} rules)")

        for rule in rules:
            if verbose:
                click.echo(f"    Checking: {rule.name}")
            result = rule.check(model)
            results.append(result)

    # Generate report
    reporter = JSONReporter()
    report = reporter.generate(
        model_path=str(ifc_path),
        results=results,
    )

    # Write output
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(report, f, indent=2)

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    click.echo(f"\n{'='*50}")
    click.echo(f"Compliance Report: {output}")
    click.echo(f"Rules checked: {len(results)}")
    click.echo(f"Passed: {passed}")
    click.echo(f"Failed: {failed}")

    if failed > 0:
        click.echo("\nFailed rules:")
        for r in results:
            if not r.passed:
                click.echo(f"  - {r.rule_id}: {r.name}")


if __name__ == "__main__":
    main()
