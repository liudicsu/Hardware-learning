"""bringup.launch.py: the Panda arm from moveit_resources on ros2_control mock hardware.

Starts robot_state_publisher, the controller manager with mock_components/GenericSystem
(commands are copied straight to the joint states: no physics, no motors) and the arm and
hand controllers. No RViz and no move_group: pick_place.py brings its own MoveIt (MoveItPy).
Usage: ros2 launch bringup.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    config = (MoveItConfigsBuilder("moveit_resources_panda")
              .robot_description(file_path="config/panda.urdf.xacro",
                                 mappings={"ros2_control_hardware_type": "mock_components"})
              .to_moveit_configs())
    controllers = os.path.join(get_package_share_directory("moveit_resources_panda_moveit_config"),
                               "config", "ros2_controllers.yaml")
    spawn = lambda name: Node(package="controller_manager", executable="spawner",
                              arguments=[name, "--controller-manager", "/controller_manager"])
    return LaunchDescription([
        Node(package="tf2_ros", executable="static_transform_publisher",
             arguments=["--frame-id", "world", "--child-frame-id", "panda_link0"]),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[config.robot_description]),
        Node(package="controller_manager", executable="ros2_control_node",
             parameters=[controllers],
             remappings=[("/controller_manager/robot_description", "/robot_description")]),
        spawn("joint_state_broadcaster"), spawn("panda_arm_controller"), spawn("panda_hand_controller"),
    ])
