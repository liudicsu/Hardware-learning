"""Navigate in a saved map: Lesson 5's robot, SLAM Toolbox in localization mode, and Nav2.

ros2 launch m4_nav nav.launch.py map:=$HOME/maps/room                  # Gazebo window and RViz
ros2 launch m4_nav nav.launch.py map:=$HOME/maps/room headless:=true   # no windows
map: the pose graph saved with /slam_toolbox/serialize_map, without the .posegraph extension"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    share = get_package_share_directory('m4_nav')

    def include(package, launch_file, **args):
        path = os.path.join(get_package_share_directory(package), 'launch', launch_file)
        return IncludeLaunchDescription(PythonLaunchDescriptionSource(path),
                                        launch_arguments=args.items())

    # put the map given on the command line into SLAM Toolbox's parameters
    slam_params = RewrittenYaml(
        source_file=os.path.join(share, 'config', 'slam_localization.yaml'),
        param_rewrites={'map_file_name': LaunchConfiguration('map')}, convert_types=True)

    return LaunchDescription([
        DeclareLaunchArgument('map', description='saved pose graph, without .posegraph'),
        DeclareLaunchArgument('headless', default_value='false'),
        include('m4_control', 'control.launch.py', headless=LaunchConfiguration('headless'),
                rviz_config=os.path.join(share, 'rviz', 'nav.rviz'),
                drive_params=os.path.join(share, 'config', 'odom_calibration.yaml')),
        include('slam_toolbox', 'localization_launch.py', use_sim_time='true',
                slam_params_file=slam_params),
        # Nav2's planner, controller, behaviours and BT navigator, with m4bot's parameters
        include('nav2_bringup', 'navigation_launch.py', use_sim_time='true',
                params_file=os.path.join(share, 'config', 'nav2.yaml')),
    ])
