from pathlib import Path
from typing import Dict, List, Any, Union, Optional
import xml.etree.ElementTree as ET
import yaml
import logging

logger = logging.getLogger(__name__)

class BridgeConfig:
    """Represents a single bridge configuration."""
    def __init__(self, ros_topic: str, gz_topic: str, ros_type: str, gz_type: str, direction: str):
        self.ros_topic = ros_topic
        self.gz_topic = gz_topic
        self.ros_type = ros_type
        self.gz_type = gz_type
        self.direction = direction

    def to_dict(self) -> Dict[str, str]:
        """Converts the bridge config to a dictionary suitable for YAML."""
        return {
            "ros_topic": self.ros_topic,
            "gz_topic": self.gz_topic,
            "ros_type": self.ros_type,
            "gz_type": self.gz_type,
            "direction": self.direction,
        }

    def get_ros_gz_bridge_direction(self) -> str:
        """Converts the internal direction string to the ros_gz_bridge launch parameter format."""
        return self.direction.upper()

def parse_urdf(urdf_path: Path) -> ET.Element:
    """
    Parses a URDF (XML) file and returns its root element.

    Args:
        urdf_path: Path to the URDF file.

    Returns:
        The root element of the parsed XML tree.

    Raises:
        FileNotFoundError: If the URDF path does not exist.
        ET.ParseError: If the URDF file is not well-formed XML.
    """
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF file not found: {urdf_path}")
    
    try:
        tree = ET.parse(urdf_path)
        return tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Error parsing URDF file {urdf_path}: {e}")
        raise

def extract_bridge_tags(xml_root: ET.Element) -> List[ET.Element]:
    """
    Extracts all <bridge> tags from the given XML root.

    Args:
        xml_root: The root element of the URDF XML tree.

    Returns:
        A list of <bridge> ET.Element objects.
    """
    return xml_root.findall(".//bridge")

def parse_bridge_tag(bridge_element: ET.Element) -> BridgeConfig:
    """
    Parses a single <bridge> XML element and extracts bridge configuration.

    The <bridge> tag is expected to have attributes:
    - `ros_topic`: The ROS topic name.
    - `gz_topic`: The Gazebo topic name.
    - `ros_type`: The ROS message type (e.g., 'std_msgs/msg/String').
    - `gz_type`: The Gazebo message type (e.g., 'std_msgs/msg/String').
    - `direction`: The bridge direction ('ros_to_gz', 'gz_to_ros', 'bidirectional').

    Args:
        bridge_element: The <bridge> XML element.

    Returns:
        A BridgeConfig object containing the extracted information.

    Raises:
        ValueError: If any required attribute is missing from the <bridge> tag.
    """
    required_attrs = ["ros_topic", "gz_topic", "ros_type", "gz_type", "direction"]
    for attr in required_attrs:
        if attr not in bridge_element.attrib:
            raise ValueError(f"Missing required attribute '{attr}' in bridge tag: {ET.tostring(bridge_element, encoding='unicode')}")
    
    return BridgeConfig(
        ros_topic=bridge_element.attrib["ros_topic"],
        gz_topic=bridge_element.attrib["gz_topic"],
        ros_type=bridge_element.attrib["ros_type"],
        gz_type=bridge_element.attrib["gz_type"],
        direction=bridge_element.attrib["direction"],
    )

def generate_bridge_yaml(bridges: List[BridgeConfig]) -> str:
    """
    Generates the YAML content for ros_urdf_bridge from a list of BridgeConfig objects.

    Args:
        bridges: A list of BridgeConfig objects.

    Returns:
        A string containing the generated YAML content.
    """
    bridge_dicts = [b.to_dict() for b in bridges]
    return yaml.dump(bridge_dicts, sort_keys=False, default_flow_style=False)

def generate_launch_params(
    bridges: List[BridgeConfig], bridge_name_prefix: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generates a list of dictionaries suitable for ros_gz_bridge launch parameters.

    Args:
        bridges: A list of BridgeConfig objects.
        bridge_name_prefix: An optional prefix to use for generated bridge names.

    Returns:
        A list of dictionaries representing the launch parameters.
    """
    if not bridges:
        return []

    params_list = []
    bridge_names = []

    for i, bridge in enumerate(bridges):
        # Sanitize ros_topic to create a unique bridge name base.
        # Example: /joint_states -> joint_states
        base_name_suffix = bridge.ros_topic.strip('/').replace('/', '_').replace('-', '_')
        
        # Prepend the optional bridge_name_prefix
        if bridge_name_prefix:
            current_bridge_base_name = f"{bridge_name_prefix}_{base_name_suffix}" if base_name_suffix else bridge_name_prefix
        else:
            current_bridge_base_name = base_name_suffix

        current_bridge_name = f"{current_bridge_base_name}_bridge" if current_bridge_base_name else f"unnamed_bridge_{i}"
        
        # Ensure uniqueness in case multiple bridges have identical sanitized names
        original_bridge_name = current_bridge_name
        k = 0
        while current_bridge_name in bridge_names:
            current_bridge_name = f"{original_bridge_name}_{k}"
            k += 1

        bridge_names.append(current_bridge_name)

        params_list.extend([
            {f"bridges.{current_bridge_name}.ros_topic_name": bridge.ros_topic},
            {f"bridges.{current_bridge_name}.gz_topic_name": bridge.gz_topic},
            {f"bridges.{current_bridge_name}.ros_type_name": bridge.ros_type},
            {f"bridges.{current_bridge_name}.gz_type_name": bridge.gz_type},
            {f"bridges.{current_bridge_name}.direction": bridge.get_ros_gz_bridge_direction()},
        ])
        
        # Optional parameters could be added here if desired:
        # {f"bridges.{current_bridge_name}.lazy": "False"},
        # {f"bridges.{current_bridge_name}.qos_profile": "SENSOR_DATA"},

    # Prepend the bridge_names list as the first parameter
    params_list.insert(0, {"bridge_names": bridge_names})
    
    return params_list


def parse_urdf_string(urdf_content: str) -> ET.Element:
    """
    Parses a URDF (XML) string and returns its root element.

    Args:
        urdf_content: The URDF content as a string.

    Returns:
        The root element of the parsed XML tree.

    Raises:
        ET.ParseError: If the URDF string is not well-formed XML.
    """
    try:
        return ET.fromstring(urdf_content)
    except ET.ParseError as e:
        logger.error(f"Error parsing URDF string: {e}")
        raise

def generate_from_urdf_string(
    urdf_content: str, output_format: str = "yaml", bridge_name: Optional[str] = None
) -> Union[str, List[Dict[str, str]]]:
    """
    Runs the full bridge configuration generation pipeline from a URDF string.

    Args:
        urdf_content: The URDF content as a string.
        output_format: The desired output format ('yaml' or 'launch_params').
                       'yaml' returns a string, 'launch_params' returns a list of dictionaries.
        bridge_name: An optional prefix to use for generated bridge names when output_format is 'launch_params'.

    Returns:
        A string containing the generated YAML content if output_format is 'yaml',
        or a list of dictionaries if output_format is 'launch_params'.

    Raises:
        ET.ParseError: If the URDF string is not well-formed XML.
        ValueError: If any required attribute is missing from a <bridge> tag.
        ValueError: If an unknown output_format is requested.
    """
    xml_root = parse_urdf_string(urdf_content)
    bridge_elements = extract_bridge_tags(xml_root)
    
    if not bridge_elements:
        logger.info("No <bridge> tags found in the provided URDF string.")
        # Return empty list for launch_params, empty string for yaml
        return [] if output_format == "launch_params" else ""

    bridges = [parse_bridge_tag(elem) for elem in bridge_elements]
    
    if output_format == "yaml":
        return generate_bridge_yaml(bridges)
    elif output_format == "launch_params":
        return generate_launch_params(bridges, bridge_name_prefix=bridge_name)
    else:
        raise ValueError(f"Unknown output_format: {output_format}. Expected 'yaml' or 'launch_params'.")
