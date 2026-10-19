#!/usr/bin/env python3
"""Publish /joint_states for m4bot with the head at a chosen pan and tilt (in degrees).

usage: python3 pose_head.py PAN_DEG TILT_DEG
Stands in for joint_state_publisher_gui when you want exact angles from the terminal.
On the real robot, the motor driver publishes /joint_states instead."""
import math
import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState


def main():
    pan, tilt = (math.radians(float(a)) for a in sys.argv[1:3])
    rclpy.init()
    node = Node('pose_head')
    pub = node.create_publisher(JointState, 'joint_states', 10)

    def tick():
        msg = JointState()
        msg.header.stamp = node.get_clock().now().to_msg()   # robot_state_publisher needs a stamp
        msg.name = ['left_wheel_joint', 'right_wheel_joint', 'pan_joint', 'tilt_joint']
        msg.position = [0.0, 0.0, pan, tilt]
        pub.publish(msg)

    node.create_timer(0.1, tick)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
