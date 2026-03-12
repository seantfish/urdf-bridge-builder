# Modular Bridge Manager Python Package

## Overview
This Python package automatically generates a `.yaml` file specifying a ROS Gazebo bridge.
It does so by parsing a generated URDF (XML) file and looking for <bridge> tags.

## Requirements

### Core Features
1. Parse URDF for <bridge> tags
2. Extract ROS and Gazebo topics, types, and directionality from the tags
3. Generates a bridge YAML file from the information in the tags

### Bridge Generation
- Automatically collects bridges from all components
- Outputs:
  - `bridge.yaml` for `ros_gz_bridge`
  - optional command interface `gz-bridge-builder path/to/urdf`

### Python Package Layout

gz-bridge-builder/src/
  __init__.py
  app.py # CLI interface impleented with typer (slim)
  core.py # parsing, aggregation, and generation
  tests/
    test_generator.py
pyproject.toml
README.md

### Testing
- Include unit tests with pytest for:
  - parsing a URDF
  - generating a bridge YAML

### Documentation
- README should include usage example
- Explain how to define XML components and generate bridge configs
