from pathlib import Path
import pytest
import xml.etree.ElementTree as ET
import yaml

from urdf_bridge_builder import core

# Define a temporary URDF content for testing
TEST_URDF_CONTENT = """
<robot name="test_robot">
  <link name="base_link"/>
  <bridge ros_topic="/joint_states" gz_topic="/model/test_robot/joint_states" ros_type="sensor_msgs/msg/JointState" gz_type="gz.msgs.Model" direction="gz_to_ros"/>
  <bridge ros_topic="/cmd_vel" gz_topic="/model/test_robot/cmd_vel" ros_type="geometry_msgs/msg/Twist" gz_type="gz.msgs.Twist" direction="ros_to_gz"/>
  <link name="end_effector"/>
  <bridge ros_topic="/feedback" gz_topic="/model/test_robot/feedback" ros_type="std_msgs/msg/String" gz_type="gz.msgs.StringMsg" direction="bidirectional"/>
</robot>
"""

INVALID_URDF_CONTENT = """
<robot name="test_robot">
  <link name="base_link"/>
  <bridge ros_topic="/joint_states" gz_topic="/model/test_robot/joint_states" ros_type="sensor_msgs/msg/JointState" gz_type="gz.msgs.Model"/> <!-- Missing direction -->
</robot>
"""

def create_temp_urdf_file(tmp_path: Path, content: str) -> Path:
    """Helper to create a temporary URDF file."""
    urdf_file = tmp_path / "test.urdf"
    urdf_file.write_text(content)
    return urdf_file

def test_parse_urdf_success(tmp_path: Path):
    """Test successful URDF parsing."""
    urdf_file = create_temp_urdf_file(tmp_path, TEST_URDF_CONTENT)
    root = core.parse_urdf(urdf_file)
    assert root.tag == "robot"
    assert root.attrib["name"] == "test_robot"

def test_parse_urdf_file_not_found():
    """Test URDF parsing with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        core.parse_urdf(Path("non_existent.urdf"))

def test_parse_urdf_invalid_xml(tmp_path: Path):
    """Test URDF parsing with invalid XML."""
    urdf_file = create_temp_urdf_file(tmp_path, "<robot><link></robot>") # Malformed XML
    with pytest.raises(ET.ParseError):
        core.parse_urdf(urdf_file)

def test_extract_bridge_tags():
    """Test extraction of bridge tags."""
    root = ET.fromstring(TEST_URDF_CONTENT)
    bridges = core.extract_bridge_tags(root)
    assert len(bridges) == 3
    assert bridges[0].tag == "bridge"
    assert bridges[1].attrib["ros_topic"] == "/cmd_vel"

def test_parse_bridge_tag_success():
    """Test parsing a well-formed bridge tag."""
    bridge_element = ET.fromstring('<bridge ros_topic="/test" gz_topic="/gz_test" ros_type="std_msgs/msg/String" gz_type="std_msgs/msg/String" direction="ros_to_gz"/>')
    config = core.parse_bridge_tag(bridge_element)
    assert config.ros_topic == "/test"
    assert config.gz_topic == "/gz_test"
    assert config.ros_type == "std_msgs/msg/String"
    assert config.gz_type == "std_msgs/msg/String"
    assert config.direction == "ros_to_gz"

def test_parse_bridge_tag_missing_attribute():
    """Test parsing a bridge tag with a missing attribute."""
    bridge_element = ET.fromstring('<bridge ros_topic="/test" gz_topic="/gz_test" ros_type="std_msgs/msg/String" gz_type="std_msgs/msg/String"/>') # Missing direction
    with pytest.raises(ValueError, match="Missing required attribute 'direction'"):
        core.parse_bridge_tag(bridge_element)

def test_generate_bridge_yaml():
    """Test generation of YAML content."""
    bridge_configs = [
        core.BridgeConfig("/joint_states", "/model/test_robot/joint_states", "sensor_msgs/msg/JointState", "sensor_msgs/msg/JointState", "gz_to_ros"),
        core.BridgeConfig("/cmd_vel", "/model/test_robot/cmd_vel", "geometry_msgs/msg/Twist", "geometry_msgs/msg/Twist", "ros_to_gz"),
    ]
    yaml_output = core.generate_bridge_yaml(bridge_configs)
    
    expected_yaml = """\
- ros_topic: /joint_states
  gz_topic: /model/test_robot/joint_states
  ros_type: sensor_msgs/msg/JointState
  gz_type: gz.msgs.Model
  direction: gz_to_ros
- ros_topic: /cmd_vel
  gz_topic: /model/test_robot/cmd_vel
  ros_type: geometry_msgs/msg/Twist
  gz_type: gz.msgs.Twist
  direction: ros_to_gz
"""
    assert yaml_output == expected_yaml
    # Also verify it's valid YAML
    loaded_yaml = yaml.safe_load(yaml_output)
    assert isinstance(loaded_yaml, list)
    assert len(loaded_yaml) == 2
    assert loaded_yaml[0]["ros_topic"] == "/joint_states"
    assert loaded_yaml[0]["ros_type"] == "sensor_msgs/msg/JointState"
    assert loaded_yaml[0]["gz_type"] == "sensor_msgs/msg/JointState"
    assert loaded_yaml[1]["direction"] == "ros_to_gz"
    assert loaded_yaml[1]["ros_type"] == "geometry_msgs/msg/Twist"
    assert loaded_yaml[1]["gz_type"] == "geometry_msgs/msg/Twist"

def test_app_generate_success(tmp_path: Path):
    """Test the full app generation flow."""
    urdf_file = create_temp_urdf_file(tmp_path, TEST_URDF_CONTENT)
    output_yaml = tmp_path / "output.yaml"

    # Mock typer.echo and typer.exit to prevent actual console output/exit during test
    from typer.testing import CliRunner
    runner = CliRunner()
    
    from urdf_bridge_builder.app import app as cli_app
    result = runner.invoke(cli_app, ["generate", str(urdf_file), "--output", str(output_yaml)])

    assert result.exit_code == 0
    assert "Successfully generated bridge YAML" in result.stdout
    assert output_yaml.exists()

    with open(output_yaml, 'r') as f:
        content = f.read()
    
    loaded_yaml = yaml.safe_load(content)
    assert len(loaded_yaml) == 3
    assert loaded_yaml[0]["ros_topic"] == "/joint_states"
    assert loaded_yaml[2]["direction"] == "bidirectional"

def test_app_generate_no_bridge_tags(tmp_path: Path):
    """Test app behavior when no bridge tags are found."""
    urdf_file = create_temp_urdf_file(tmp_path, "<robot name='empty'/>")
    output_yaml = tmp_path / "empty.yaml"

    from typer.testing import CliRunner
    runner = CliRunner()
    from urdf_bridge_builder.app import app as cli_app
    result = runner.invoke(cli_app, ["generate", str(urdf_file), "--output", str(output_yaml)])

    assert result.exit_code == 0 # Should exit cleanly if no bridges found
    assert "No <bridge> tags found" in result.stdout
    assert not output_yaml.exists() # No file should be created

def test_app_generate_invalid_urdf(tmp_path: Path):
    """Test app behavior with an invalid URDF file (missing attribute)."""
    urdf_file = create_temp_urdf_file(tmp_path, INVALID_URDF_CONTENT)
    output_yaml = tmp_path / "invalid.yaml"

    from typer.testing import CliRunner
    runner = CliRunner()
    from urdf_bridge_builder.app import app as cli_app
    result = runner.invoke(cli_app, ["generate", str(urdf_file), "--output", str(output_yaml)])

    assert result.exit_code == 1
    assert "Missing required attribute 'direction' in bridge tag" in result.stderr
    assert not output_yaml.exists() # No file should be created

def test_app_generate_urdf_not_found(tmp_path: Path):
    """Test app behavior when URDF file is not found."""
    non_existent_urdf = tmp_path / "non_existent.urdf"
    output_yaml = tmp_path / "output.yaml"

    from typer.testing import CliRunner
    runner = CliRunner()
    from urdf_bridge_builder.app import app as cli_app
    result = runner.invoke(cli_app, ["generate", str(non_existent_urdf), "--output", str(output_yaml)])

    assert result.exit_code == 1
    assert "URDF file not found" in result.stderr
    assert not output_yaml.exists() # No file should be created
