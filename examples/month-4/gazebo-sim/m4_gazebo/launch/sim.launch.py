"""m4bot in the obstacles world: Gazebo, the robot, the ROS-Gazebo bridge (+ RViz).

ros2 launch m4_gazebo sim.launch.py                   # Gazebo window and RViz
ros2 launch m4_gazebo sim.launch.py headless:=true    # no windows (servers, CI)"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('m4_gazebo')
    world = os.path.join(share, 'worlds', 'obstacles.sdf')
    gz_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    robot_description = ParameterValue(
        Command(['xacro ', os.path.join(share, 'urdf', 'm4bot_gz.urdf.xacro')]), value_type=str)
    headless = LaunchConfiguration('headless')

    def gazebo(gz_args, condition):
        return IncludeLaunchDescription(PythonLaunchDescriptionSource(gz_launch),
                                        launch_arguments={'gz_args': gz_args}.items(),
                                        condition=condition)

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = server only, no Gazebo window and no RViz'),
        # -r: start running at once; -s: server only; --headless-rendering: sensors without a display
        gazebo(f'-r {world}', UnlessCondition(headless)),
        gazebo(f'-s -r --headless-rendering {world}', IfCondition(headless)),
        # the same robot_state_publisher as Lesson 3, but on the simulator's clock
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description, 'use_sim_time': True}]),
        # put the robot into the running world, from the robot_description topic
        Node(package='ros_gz_sim', executable='create',
             arguments=['-topic', 'robot_description', '-name', 'm4bot', '-z', '0.01']),
        # Gazebo topics <-> ROS 2 topics, as listed in bridge.yaml
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             parameters=[{'config_file': os.path.join(share, 'config', 'bridge.yaml'),
                          'use_sim_time': True}]),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', os.path.join(share, 'rviz', 'sim.rviz')],
             parameters=[{'use_sim_time': True}], condition=UnlessCondition(headless)),
    ])
