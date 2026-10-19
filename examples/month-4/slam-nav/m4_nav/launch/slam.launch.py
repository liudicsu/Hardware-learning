"""Map the room: m4bot through ros2_control in Gazebo (Lesson 5) plus SLAM Toolbox in mapping mode.

ros2 launch m4_nav slam.launch.py                  # Gazebo window and RViz
ros2 launch m4_nav slam.launch.py headless:=true   # no windows"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = get_package_share_directory('m4_nav')

    def include(package, launch_file, **args):
        path = os.path.join(get_package_share_directory(package), 'launch', launch_file)
        return IncludeLaunchDescription(PythonLaunchDescriptionSource(path),
                                        launch_arguments=args.items())

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        # the robot, its controllers and the sensors from Lesson 5, with calibrated odometry
        include('m4_control', 'control.launch.py', headless=LaunchConfiguration('headless'),
                rviz_config=os.path.join(share, 'rviz', 'nav.rviz'),
                drive_params=os.path.join(share, 'config', 'odom_calibration.yaml')),
        # SLAM Toolbox's own launch file, with our parameters
        include('slam_toolbox', 'online_async_launch.py', use_sim_time='true',
                slam_params_file=os.path.join(share, 'config', 'slam.yaml')),
    ])
