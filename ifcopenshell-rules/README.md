# IFC Rule Engine - Singapore Code of Practice

A geometric rule engine for validating IFC (Industry Foundation Classes) models against Singapore building codes and regulations.

## Quick Start

### Using Docker (Recommended)

```bash
cd ifcopenshell-rules
docker compose up
```

### Using Python Directly

```bash
cd ifcopenshell-rules
pip install -r requirements.txt
python3 main.py --ifc-path data/model.ifc --output outputs/compliance_report.json
```

## CLI Options

```
Usage: main.py [OPTIONS]

Options:
  --ifc-path PATH       Path to the IFC file to validate (required)
  --config-dir PATH     Directory containing rule configs (default: config)
  --output PATH         Output path for compliance report (default: outputs/compliance_report.json)
  --category TEXT       Rule category: all, fire_safety, accessibility, building_control
  --verbose             Enable verbose output
  --help                Show this message and exit
```

### Examples

```bash
# Check all rules
python3 main.py --ifc-path data/building.ifc --category all

# Check only fire safety rules
python3 main.py --ifc-path data/building.ifc --category fire_safety --verbose

# Check accessibility with custom output location
python3 main.py --ifc-path data/building.ifc --category accessibility --output outputs/accessibility_report.json
```

## Directory Structure

```
ifcopenshell-rules/
├── main.py                 # CLI entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── config/                 # Rule configuration files (YAML)
│   ├── fire_safety/
│   │   ├── travel_distance.yaml
│   │   └── egress.yaml
│   ├── accessibility/
│   │   ├── corridors.yaml
│   │   └── doors.yaml
│   └── building_control/
│       └── setbacks.yaml
│
├── rules/                  # Rule implementations
│   ├── base.py            # BaseRule class, RuleResult, Violation
│   ├── registry.py        # Rule discovery and registration
│   ├── fire_safety/
│   ├── accessibility/
│   └── building_control/
│
├── geometry/              # Geometry utilities
│   ├── distance.py        # Distance calculations
│   ├── area.py            # Area calculations
│   ├── clearance.py       # Bounding box, clearance checks
│   └── path.py            # Travel distance, path finding
│
├── extractors/            # IFC element extractors
│   ├── spaces.py          # IfcSpace extraction
│   ├── doors.py           # IfcDoor extraction
│   ├── walls.py           # IfcWall extraction
│   └── stairs.py          # IfcStair extraction
│
└── reporters/             # Output generation
    └── json_reporter.py   # JSON compliance report
```

## Available Rules

| Rule ID | Category | Name | Reference |
|---------|----------|------|-----------|
| FS-001 | Fire Safety | Maximum Travel Distance to Exit | Singapore Fire Code 2018, Clause 2.3 |
| FS-002 | Fire Safety | Minimum Egress Width | Singapore Fire Code 2018, Clause 2.4 |
| ACC-001 | Accessibility | Corridor Width Requirements | BCA Accessibility Code 2019, Clause 4.2 |
| ACC-002 | Accessibility | Door Clear Opening Width | BCA Accessibility Code 2019, Clause 5.1 |
| BC-001 | Building Control | Building Setback Requirements | URA Development Control Guidelines |

## Configuration Format

Rules are configured via YAML files. Each config file defines:

```yaml
# config/accessibility/corridors.yaml
rule_id: "ACC-001"
name: "Corridor Width Requirements"
description: |
  Ensures corridors meet minimum width requirements for
  accessibility and wheelchair passage.
reference: "BCA Accessibility Code 2019, Clause 4.2"

parameters:
  min_width_mm: 1200
  min_width_turning_mm: 1500
  min_width_passing_mm: 1800

# Optional: element identification
corridor_identification:
  space_types:
    - "CORRIDOR"
    - "HALLWAY"
  name_patterns:
    - "corridor"
    - "hallway"
```

## Adding New Rules

### 1. Create YAML Configuration

Create a new file in `config/<category>/<rule_name>.yaml`:

```yaml
rule_id: "FS-003"
name: "Fire Door Rating"
reference: "Singapore Fire Code 2018, Clause 3.1"

parameters:
  min_fire_rating_minutes: 60
```

### 2. Create Python Rule Class

Create `rules/<category>/<rule_name>.py`:

```python
from rules.base import BaseRule, RuleResult, Violation
from extractors.doors import DoorExtractor

class FireDoorRatingRule(BaseRule):
    RULE_ID = "FS-003"
    CATEGORY = "fire_safety"

    def check(self, model) -> RuleResult:
        violations = []
        min_rating = self.get_param("min_fire_rating_minutes", 60)

        door_extractor = DoorExtractor(model)
        fire_doors = door_extractor.get_fire_doors()

        for door in fire_doors:
            # Check fire rating logic here
            # Add violations as needed
            pass

        return self._create_result(
            passed=len(violations) == 0,
            violations=violations,
        )
```

### 3. Register the Rule

Update `rules/<category>/__init__.py`:

```python
from .fire_door_rating import FireDoorRatingRule
__all__ = [..., "FireDoorRatingRule"]
```

Update `rules/registry.py`:

```python
from .fire_safety.fire_door_rating import FireDoorRatingRule

RULE_CLASSES = {
    "fire_safety": [..., FireDoorRatingRule],
}

CONFIG_TO_RULE = {
    ...,
    "fire_door_rating.yaml": FireDoorRatingRule,
}
```

## Output Format

The JSON compliance report structure:

```json
{
  "report_metadata": {
    "generated_at": "2024-01-15T10:30:00",
    "generator": "IFC Rule Engine - Singapore Code of Practice",
    "generator_version": "1.0.0",
    "model_path": "data/building.ifc"
  },
  "summary": {
    "total_rules_checked": 5,
    "rules_passed": 3,
    "rules_failed": 2,
    "compliance_rate": 60.0,
    "total_violations": 4,
    "violations_by_severity": {
      "error": 3,
      "warning": 1,
      "info": 0
    }
  },
  "results_by_category": {
    "fire_safety": [...],
    "accessibility": [...],
    "building_control": [...]
  }
}
```

Each violation includes:
- `element_id` - IFC element ID
- `element_type` - IFC type (e.g., "IfcDoor")
- `element_name` - Element name if available
- `message` - Human-readable description
- `location` - XYZ coordinates
- `severity` - error, warning, or info
- `actual_value` - Measured value
- `expected_value` - Required value

## Dependencies

- **ifcopenshell** - IFC file parsing and geometry
- **click** - CLI framework
- **pyyaml** - YAML configuration parsing
- **numpy** - Numerical operations
- **shapely** - Geometric operations
- **pydantic** - Data validation
