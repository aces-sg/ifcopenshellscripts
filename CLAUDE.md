# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docker-based BIM (Building Information Modeling) toolkit with four independent modules for processing IFC (Industry Foundation Classes) files and point clouds.

## Modules

| Module | Purpose | Base Image |
|--------|---------|------------|
| `ifcopenshell-clash` | Detect clashes between two IFC files | Python 3.12 slim |
| `ifcopenshell-merge` | Merge multiple IFC files | Python 3.10 slim |
| `ifcopenshell-convert` | Convert IFC to OBJ/FBX via Blender | Python 3.11 + Blender 4.3 |
| `ifcopenshell-rules` | Singapore Code of Practice compliance checker | Python 3.12 slim |
| `potree` | Convert LAS/LAZ to Potree format | Ubuntu 20.04 (C++ build) |

## Running Modules

```bash
# Via Docker (recommended)
cd <module-name> && docker compose up

# Examples with CLI options
# Clash detection
python3 main.py --file-a test1.ifc --file-b test2.ifc --selector-b IfcWall --mode intersection

# Merge IFC files
python3 main.py file1.ifc file2.ifc file3.ifc -o outputs/merged.ifc

# Convert IFC to OBJ/FBX
python3 main.py --ifc-path data/ifc/test1.ifc --output outputs/file.obj

# Point cloud to Potree
python3 main.py --input_file_path ./data/test.las --method poisson

# Rule compliance check (Singapore Code of Practice)
python3 main.py --ifc-path data/test.ifc --config-dir config --category all --output outputs/compliance_report.json
```

## Project Rules

1. **Never hardcode input file paths** - Use CLI parameters or environment variables
2. **All outputs go to the `outputs/` folder** - This is a strict requirement
3. **Use Click framework** - All CLI interfaces use Click for argument parsing

## Architecture

- **Zero inter-module dependencies** - Each module is self-contained
- **Docker platform:** `linux/amd64` (specified in all docker-compose files)
- **Volume mounting:** Input data in `data/`, outputs in `outputs/`
- **Entry point:** Each module has `main.py` as its entry point

## Key Dependencies

- **ifcopenshell** - Core BIM library (clash, merge, convert, rules)
- **ifcpatch** - IFC patching/modification (merge)
- **bpy + Bonsai addon** - Blender Python API for IFC import (convert)
- **PotreeConverter** - C++ tool built from source (potree)
- **pyyaml** - Rule configuration parsing (rules)

## Rule Engine Architecture (ifcopenshell-rules)

The rule engine validates IFC models against Singapore building codes:

```
ifcopenshell-rules/
├── config/           # YAML rule configs (parameters, thresholds)
│   ├── fire_safety/
│   ├── accessibility/
│   └── building_control/
├── rules/            # Python rule implementations
│   ├── base.py       # BaseRule class - inherit for new rules
│   └── registry.py   # Rule discovery
├── geometry/         # Geometry utilities (distance, area, clearance)
├── extractors/       # IFC element extraction (spaces, doors, walls, stairs)
└── reporters/        # Output generation (JSON)
```

### Adding New Rules

1. Create YAML config in `config/<category>/<rule>.yaml` with rule_id, parameters
2. Create Python class in `rules/<category>/<rule>.py` inheriting from `BaseRule`
3. Implement `check(model) -> RuleResult` method
4. Register in `rules/registry.py`
