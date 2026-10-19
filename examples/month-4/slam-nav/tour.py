#!/usr/bin/env python3
"""Drive m4bot along a fixed tour of the obstacles room, so SLAM Toolbox sees every corner.

usage: python3 tour.py        (with slam.launch.py running)
The same thing you would do with teleop_twist_keyboard, but repeatable: it turns on the spot and
drives between waypoints, steering by odometry. It prints the odometry pose at each waypoint."""
import math

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter

# (x, y) in the odom frame, which starts where the robot was spawned: the room's centre
WAYPOINTS = [(1.4, 1.4), (-1.2, -1.2), (0.0, 0.0)]


class Tour(Node):
    def __init__(self):
        # stamp commands with the simulator's clock, like every node in a simulation
        super().__init__('tour', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.cmd = self.create_publisher(TwistStamped, 'diff_drive_controller/cmd_vel', 10)
        self.create_subscription(Odometry, 'diff_drive_controller/odom', self.on_odom, 1)
        self.pose = None

    def on_odom(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose = (p.x, p.y, yaw)

    def send(self, v, w):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x, msg.twist.angular.z = v, w
        self.cmd.publish(msg)

    def step(self):
        rclpy.spin_once(self, timeout_sec=0.05)

    def turn_to(self, target):
        while True:
            self.step()
            err = math.atan2(math.sin(target - self.pose[2]), math.cos(target - self.pose[2]))
            if abs(err) < 0.02:
                break
            self.send(0.0, max(-0.6, min(0.6, 2.0 * err)))   # slow turns keep the scans sharp
        self.send(0.0, 0.0)

    def drive_to(self, x, y):
        while True:
            self.step()
            dx, dy = x - self.pose[0], y - self.pose[1]
            if math.hypot(dx, dy) < 0.05:
                break
            err = math.atan2(dy, dx) - self.pose[2]
            err = math.atan2(math.sin(err), math.cos(err))
            self.send(min(0.25, math.hypot(dx, dy)), 2.0 * err)
        self.send(0.0, 0.0)

    def run(self):
        while self.pose is None:
            self.step()
        print('spin once on the spot')
        for target in (math.pi / 2, math.pi, -math.pi / 2, 0.0):
            self.turn_to(target)
        for x, y in WAYPOINTS:
            self.turn_to(math.atan2(y - self.pose[1], x - self.pose[0]))
            self.drive_to(x, y)
            print(f'at waypoint ({x:.1f}, {y:.1f}): odom x {self.pose[0]:.2f} y {self.pose[1]:.2f}')
        self.turn_to(0.0)
        print(f'done, facing +x again: yaw {math.degrees(self.pose[2]):.0f} deg')


def main():
    rclpy.init()
    node = Tour()
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
