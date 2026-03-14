# Robot Bridge Manager Python Package

## Overview
This Python package automatically generates a `.yaml` file specifying a ROS Gazebo bridge.
It does so by parsing a URDF (XML) file and looking for custom `<bridge>` tags within it.

## Installation

```bash
pip install .
```

## Usage

### Defining Bridge Components in URDF

To use this tool, you need to embed `<bridge>` tags within your URDF file.
Each `<bridge>` tag should define a single ROS-Gazebo bridge.

Example `<bridge>` tag:
```xml
<bridge
  ros_topic="/my_robot/cmd_vel"
  gz_topic="/model/my_robot/cmd_vel"
  ros_type="geometry_msgs/msg/Twist"
  gz_type="gz.msgs.Twist"
  direction="ros_to_gz"
/>
```

Attributes:
- `ros_topic`: The ROS 2 topic name.
- `gz_topic`: The Gazebo topic name.
- `ros_type`: The ROS 2 message type (e.g., `geometry_msgs/msg/Twist`).
- `gz_type`: The Gazebo message type.
- `direction`: The direction of the bridge. Can be `ros_to_gz`, `gz_to_ros`, or `bidirectional`.

### Generating the Bridge YAML

Once your URDF file contains the necessary `<bridge>` tags, you can use the `urdf-bridge-builder` command-line tool to generate the `bridge.yaml` file.

```bash
urdf-bridge-builder generate path/to/your_robot.urdf --output bridge.yaml
```

- `path/to/your_robot.urdf`: The path to your URDF file.
- `--output bridge.yaml` (optional): Specifies the output file name for the generated YAML. If not provided, it defaults to `bridge.yaml` in the current directory.

**Example:**
If `my_robot.urdf` contains:
```xml
<robot name="my_robot">
  <link name="base_link"/>
  <bridge ros_topic="/joint_states" gz_topic="/model/my_robot/joint_states" ros_type="sensor_msgs/msg/JointState" gz_type="gz.msgs.Model" direction="gz_to_ros"/>
  <bridge ros_topic="/cmd_vel" gz_topic="/model/my_robot/cmd_vel" ros_type="geometry_msgs/msg/Twist" gz_type="gz.msgs.Twist" direction="ros_to_gz"/>
</robot>
```

Running `urdf-bridge-builder generate my_robot.urdf` will create `bridge.yaml`:
```yaml
- ros_topic: /joint_states
  gz_topic: /model/my_robot/joint_states
  ros_type: sensor_msgs/msg/JointState
  gz_type: gz.msgs.Model
  direction: gz_to_ros
- ros_topic: /cmd_vel
  gz_topic: /model/my_robot/cmd_vel
  ros_type: geometry_msgs/msg/Twist
  gz_type: gz.msgs.Twist
  direction: ros_to_gz
```

This `bridge.yaml` file can then be used with `ros_gz_bridge`.

## Development

### Running Tests

To run the unit tests, ensure you have `pytest` installed and run it from the project root:

```bash
pip install pytest
pytest urdf-bridge-builder/src/tests/
```
