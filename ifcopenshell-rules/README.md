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

## Development Strategy: 12 Foundational Patterns

We've identified 12 foundational patterns that cover the majority of Singapore Code of Practice geometric checks. Each pattern establishes a reusable utility.

### Core Patterns to Establish

| Pattern | Utility Created | Rules It Unlocks |
|---------|-----------------|------------------|
| Width | `get_element_width()` | Door, corridor, stair, ramp width checks |
| Height | `get_space_height()` | Ceiling heights, handrail heights |
| Area | `get_space_area()` | Room minimums, floor areas |
| Gradient | `calculate_gradient()` | Ramps, stairs, accessible routes |
| Multi-dimension | `get_element_dimensions()` | Stair riser+tread+width, door height+width |
| Property | `validate_property()` | Fire ratings, materials, acoustic ratings |
| Counting | `count_by_storey()` | Exit count, parking count, toilet count |
| Ratio | `calculate_ratio()` | Window-to-floor, ventilation areas |
| Connectivity | `build_connectivity_graph()` | Travel distance, accessible routes |
| **Proximity** | `check_separation()` | Exit separation, element distances |
| **Clearance** | `check_clearance_zone()` | Door maneuvering, landing areas |
| **Containment** | `check_enclosure()` | Fire compartments, protected lobbies |

### The 12 Foundational Rules

| Priority | Rule ID | Name | Pattern | Phase |
|----------|---------|------|---------|-------|
| 1 | ACC-002 | Door Clear Width | Width | Done |
| 2 | ACC-001 | Corridor Width | Width | Done |
| 3 | ACC-003 | Ramp Gradient | Gradient | Phase 1 |
| 4 | BC-002 | Ceiling Height | Height | Phase 1 |
| 5 | FS-006 | Stair Dimensions | Multi-dimension | Phase 2 |
| 6 | FS-003 | Fire Door Rating | Property | Phase 2 |
| 7 | FS-004 | Exit Count per Floor | Counting | Phase 3 |
| 8 | FS-005 | Exit Separation | Proximity | Phase 3 |
| 9 | ACC-006 | Door Maneuvering Clearance | Clearance | Phase 4 |
| 10 | FS-008 | Fire Compartment Integrity | Containment | Phase 4 |
| 11 | FS-007 | Space Connectivity | Connectivity | Phase 5 |
| 12 | BC-004 | Window-to-Floor Ratio | Ratio | Phase 5 |

### Implementation Phases

- **Phase 1**: Basic measurements (gradient, height)
- **Phase 2**: Complex elements (multi-dimension, property validation)
- **Phase 3**: Spatial analysis (counting, proximity)
- **Phase 4**: Zone analysis (clearance, containment)
- **Phase 5**: Advanced analysis (connectivity, ratios)

---

## Rule Implementation Status

This table tracks the implementation status of each rule. **Dev team: please update as you work on rules.**

### Status Legend
- `Not Started` - Rule not yet implemented
- `In Progress` - Currently being developed
- `Implemented` - Code complete, needs testing
- `Needs Review` - Implementation needs verification against actual code requirements
- `Verified` - Tested and confirmed accurate

### Accuracy Legend
- `Exact` - Matches code requirement precisely
- `Approximate` - Simplified implementation (e.g., straight-line distance vs actual walking path)
- `Partial` - Only some aspects of the requirement implemented

### Implemented Rules

| Rule ID | Code Reference | Status | Complexity | Accuracy | Assignee | Notes | Last Updated |
|---------|----------------|--------|------------|----------|----------|-------|--------------|
| FS-001 | Fire Code 2018, Cl. 2.3 | Needs Review | Medium | Approximate | - | Uses straight-line distance, not actual walking path. Consider Level 2 pathfinding via space connectivity graph. | 2024-11-23 |
| FS-002 | Fire Code 2018, Cl. 2.4 | Implemented | Low | Partial | - | Checks door/corridor width. Does not yet calculate capacity based on Table 2.2A occupancy factors. | 2024-11-23 |
| ACC-001 | Accessibility Code 2019, Cl. 4.2 | Implemented | Medium | Exact | - | Corridor width from bounding box. Identifies corridors by space type or name pattern. | 2024-11-23 |
| ACC-002 | Accessibility Code 2019, Cl. 5.1 | Implemented | Low | Exact | - | Door clear opening width check. Main entrance detection by name keywords. | 2024-11-23 |
| BC-001 | URA Guidelines | Needs Review | Medium | Approximate | - | Requires IfcSite boundary definition. Uses bounding box comparison. | 2024-11-23 |

### Planned Rules (Prioritized by Pattern)

**Phase 1 - Basic Measurements**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| ACC-003 | Gradient | Accessibility Code 2019, Cl. 3.4 | **Ramp Gradient**: Kerb ramps max 1:10. General ramps per Table 5 (gradient varies by rise). Landings at top/bottom. Contrasting colour for rises >200 mm. | Not Started | - | - |
| BC-002 | Height | BCA Approved Document | **Ceiling Height**: Min 2.4 m floor-to-ceiling. Headroom min 2.0 m under beams/ducts. [Note: verify 2.4 m vs 2.6 m for specific building types] | Not Started | - | - |

**Phase 2 - Complex Elements**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| FS-006 | Multi-dimension | Fire Code, Cl. 2.2/2.3 | **Stair Dimensions**: Tread min 250 mm (275 mm non-industrial). Max width 2000 mm, min 1000 mm. Divide by handrails if >2000 mm. Landing every 18 risers. Uniform riser/tread per flight. | Not Started | - | - |
| FS-003 | Property | Fire Code, Cl. 3.9 | **Fire Door Rating**: Min 30-min FRP for doors to exits, protected staircases, lobbies. Min 1-hour for exit corridor doors. Self-closing device required. Test standard: BS 476-22 or SS 332:2018. | Not Started | - | - |

**Phase 3 - Spatial Analysis**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| FS-004 | Counting | Fire Code, Cl. 2.2 | **Exit Count**: Per Table 2.2A based on occupant load and Purpose Group. Each exit must serve ≥50% of occupant load. Exit width in 500 mm units. Min door width 850 mm. | Not Started | - | - |
| FS-005 | Proximity | Fire Code, Cl. 2.2 | **Exit Separation**: Required exits must be "remotely located" - min separation ≥ ½ diagonal distance of floor area served. | Not Started | - | - |

**Phase 4 - Zone Analysis**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| ACC-006 | Clearance | Accessibility Code 2019, Cl. 5.1 | **Door Maneuvering Clearance**: Min 1500 mm × 1500 mm clear floor space at accessible doors for wheelchair turning. Level landing required. | Not Started | - | - |
| FS-008 | Containment | Fire Code, Cl. 3.1 | **Fire Compartment Integrity**: All boundaries of fire compartment must be fire-rated. All openings must be protected with fire doors/dampers matching wall rating. | Not Started | - | - |

**Phase 5 - Advanced Analysis**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| FS-007 | Connectivity | Fire Code, Cl. 2.3 | **Travel Distance**: Max per Table 2.2A by Purpose Group. Example: 60 m (sprinklered office, two-way), 45 m (unsprinklered). Direct distance = ⅔ of max. Measured along actual path. | Not Started | - | - |
| BC-004 | Ratio | SS553:2016 | **Window Ratio**: [TBD - Singapore uses SS553:2016 for ventilation. Specific percentage not confirmed. Dev team to verify from standard.] | Not Started | - | - |

**Other Planned Rules (Uses Established Patterns)**

| Rule ID | Pattern | Code Reference | Requirement | Status | Assignee | Last Updated |
|---------|---------|----------------|-------------|--------|----------|--------------|
| ACC-004 | Width | Accessibility Code 2019, Cl. 3.4 | **Ramp Width**: Min 1200 mm clear width. Kerb ramps min 900 mm. | Not Started | - | - |
| ACC-005 | Connectivity | Accessibility Code 2019 | **Accessible Route**: Continuous accessible path from parking/drop-off to main entrance. Ramps where level changes >15 mm. | Not Started | - | - |
| BC-003 | Area | Building Control Reg | **Room Area**: [TBD - Not confirmed in Building Control Regs. May be HDB-specific. Dev team to verify from primary source.] | Not Started | - | - |

### Known Limitations

| Area | Limitation | Workaround/Future Plan |
|------|------------|------------------------|
| Travel Distance | Straight-line calculation underestimates actual walking distance | Implement space connectivity graph (Level 2 pathfinding) using IfcRelSpaceBoundary |
| Pathfinding | No true navigation mesh pathfinding | Consider external library or simplified graph approach |
| Occupancy Classification | Rules don't auto-detect building/space occupancy type | Requires manual config or property extraction |
| Unit Conversion | Assumes model units are meters/millimeters | Add unit detection from IfcProject |

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
