from pathlib import Path
from typing import Dict, List, Any
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

def generate_from_urdf_string(urdf_content: str) -> str:
    """
    Runs the full bridge configuration generation pipeline from a URDF string.

    Args:
        urdf_content: The URDF content as a string.

    Returns:
        A string containing the generated YAML content.

    Raises:
        ET.ParseError: If the URDF string is not well-formed XML.
        ValueError: If any required attribute is missing from a <bridge> tag.
    """
    xml_root = parse_urdf_string(urdf_content)
    bridge_elements = extract_bridge_tags(xml_root)
    
    if not bridge_elements:
        logger.info("No <bridge> tags found in the provided URDF string.")
        return ""

    bridges = [parse_bridge_tag(elem) for elem in bridge_elements]
    return generate_bridge_yaml(bridges)
