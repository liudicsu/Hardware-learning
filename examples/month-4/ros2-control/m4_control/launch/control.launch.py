"""m4bot through ros2_control: controller manager, three controllers, the DriveDistance server.

ros2 launch m4_control control.launch.py                          # Gazebo window and RViz
ros2 launch m4_control control.launch.py headless:=true           # Gazebo, no windows
ros2 launch m4_control control.launch.py hardware:=mock headless:=true   # no simulator"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (Command, EqualsSubstitution, LaunchConfiguration,
                                  NotEqualsSubstitution, PythonExpression)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('m4_control')
    world = os.path.join(get_package_share_directory('m4_gazebo'), 'worlds', 'obstacles.sdf')
    controllers = os.path.join(share, 'config', 'controllers.yaml')
    sim_rviz = os.path.join(get_package_share_directory('m4_gazebo'), 'rviz', 'sim.rviz')
    hardware = LaunchConfiguration('hardware')
    headless = LaunchConfiguration('headless')
    in_gazebo = EqualsSubstitution(hardware, 'gazebo')
    sim_time = ParameterValue(in_gazebo, value_type=bool)   # Gazebo has its own clock
    robot_description = ParameterValue(
        Command(['xacro ', os.path.join(share, 'urdf', 'm4bot_control.urdf.xacro'),
                 ' hardware:=', hardware]), value_type=str)
    gz_args = [PythonExpression(["'-s -r --headless-rendering ' if '", headless,
                                 "' == 'true' else '-r '"]), world]

    def spawner(name, *args):
        return Node(package='controller_manager', executable='spawner', arguments=[name, *args])

    return LaunchDescription([
        DeclareLaunchArgument('hardware', default_value='gazebo', description='gazebo or mock'),
        DeclareLaunchArgument('headless', default_value='false', description='true = no windows'),
        DeclareLaunchArgument('rviz_config', default_value=sim_rviz, description='RViz view'),
        DeclareLaunchArgument('drive_params', default_value=controllers,
                              description='more diff_drive_controller parameters (Lesson 6)'),
        # robot_state_publisher: the same node as in Lessons 3 and 4
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description, 'use_sim_time': sim_time}]),
        # Gazebo: the controller manager runs inside Gazebo, started by gz_ros2_control
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': gz_args}.items(), condition=IfCondition(in_gazebo)),
        Node(package='ros_gz_sim', executable='create', condition=IfCondition(in_gazebo),
             arguments=['-topic', 'robot_description', '-name', 'm4bot', '-z', '0.01']),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             condition=IfCondition(in_gazebo),
             parameters=[{'config_file': os.path.join(share, 'config', 'bridge.yaml'),
                          'use_sim_time': True}]),
        # mock hardware: the controller manager runs as its own node
        Node(package='controller_manager', executable='ros2_control_node',
             parameters=[controllers], remappings=[('~/robot_description', '/robot_description')],
             condition=IfCondition(NotEqualsSubstitution(hardware, 'gazebo'))),
        # load and start the three controllers named in controllers.yaml
        spawner('joint_state_broadcaster'),
        spawner('diff_drive_controller', '--param-file', LaunchConfiguration('drive_params')),
        spawner('head_controller'),
        # RViz, by default with Lesson 4's view: the robot, the laser points and the camera image
        Node(package='rviz2', executable='rviz2', condition=UnlessCondition(headless),
             arguments=['-d', LaunchConfiguration('rviz_config')],
             parameters=[{'use_sim_time': sim_time}]),
        # the DriveDistance action server from this lesson
        Node(package='m4_control', executable='drive_distance',
             parameters=[{'use_sim_time': sim_time}]),
    ])
