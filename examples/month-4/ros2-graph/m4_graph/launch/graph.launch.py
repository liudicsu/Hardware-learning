"""Start the whole Lesson 2 graph: sensor -> filter (C++) -> aggregator, plus the config node.

ros2 launch m4_graph graph.launch.py rate:=10.0 summary_topic:=stats"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    params = os.path.join(get_package_share_directory('m4_graph'), 'config', 'aggregator.yaml')
    rate = LaunchConfiguration('rate')
    summary_topic = LaunchConfiguration('summary_topic')
    return LaunchDescription([
        DeclareLaunchArgument('rate', default_value='5.0', description='sensor rate in Hz'),
        DeclareLaunchArgument('summary_topic', default_value='summary',
                              description='where the aggregator publishes'),
        Node(package='m4_graph', executable='sensor_node',
             parameters=[{'rate': rate}]),
        Node(package='m4_graph_cpp', executable='filter_node',
             parameters=[params]),
        Node(package='m4_graph', executable='aggregator_node',
             parameters=[params],
             remappings=[('input', 'filtered'), ('summary', summary_topic)]),
        Node(package='m4_graph', executable='config_node'),
    ])
