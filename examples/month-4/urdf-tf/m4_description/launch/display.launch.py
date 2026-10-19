"""Show m4bot: robot_state_publisher + a joint state source (+ RViz).

ros2 launch m4_description display.launch.py                         # sliders and RViz
ros2 launch m4_description display.launch.py joints:=zero rviz:=false # headless, all joints at 0
ros2 launch m4_description display.launch.py joints:=none rviz:=false # no joint states at all"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, EqualsSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('m4_description')
    xacro_file = os.path.join(share, 'urdf', 'robot.urdf.xacro')
    # run xacro at launch time; the result is the robot_description string
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
    joints = LaunchConfiguration('joints')
    return LaunchDescription([
        DeclareLaunchArgument('joints', default_value='gui',
                              description='gui = sliders, zero = all joints at 0, none = no joint states'),
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz'),
        # turns joint positions + the URDF into TF transforms
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}]),
        # invents joint positions - on a real robot, the hardware driver publishes them instead
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             condition=IfCondition(EqualsSubstitution(joints, 'gui'))),
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             condition=IfCondition(EqualsSubstitution(joints, 'zero'))),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', os.path.join(share, 'rviz', 'display.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
