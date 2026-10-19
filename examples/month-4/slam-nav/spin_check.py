#!/usr/bin/env python3
"""Check odometry's heading against the lidar: spin m4bot one full turn by odometry, then ask the
lidar how far it really turned.

usage: python3 spin_check.py        (with control.launch.py or slam.launch.py running)
If odometry is right, the room looks the same to the lidar before and after one turn. If not, the
two scans are rotated against each other, and the rotation is the odometry's heading error."""
import math

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class SpinCheck(Node):
    def __init__(self):
        super().__init__('spin_check', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.cmd = self.create_publisher(TwistStamped, 'diff_drive_controller/cmd_vel', 10)
        self.create_subscription(Odometry, 'diff_drive_controller/odom', self.on_odom, 1)
        self.scans = []
        self.create_subscription(LaserScan, 'scan', self.scans.append, qos_profile_sensor_data)
        self.yaw = None

    def on_odom(self, msg):
        q = msg.pose.pose.orientation
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    def send(self, w):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.angular.z = w
        self.cmd.publish(msg)

    def average_scan(self, count=5):
        """Mean of the next `count` scans; beams without a hit count as the lidar's maximum range."""
        self.scans.clear()
        while len(self.scans) < count:
            rclpy.spin_once(self, timeout_sec=0.1)
        top = self.scans[0].range_max
        return [sum(min(s.ranges[i], top) for s in self.scans) / count
                for i in range(len(self.scans[0].ranges))]

    def settle(self, seconds):
        end = self.get_clock().now().nanoseconds + seconds * 1e9
        while self.get_clock().now().nanoseconds < end:
            self.send(0.0)
            rclpy.spin_once(self, timeout_sec=0.05)

    def run(self):
        while self.yaw is None:
            rclpy.spin_once(self, timeout_sec=0.1)
        before = self.average_scan()
        turned, last = 0.0, self.yaw
        while turned < 2 * math.pi - 0.002:              # one full turn, counted by odometry
            remaining = 2 * math.pi - turned
            self.send(max(0.05, min(0.5, 2.0 * remaining)))
            rclpy.spin_once(self, timeout_sec=0.05)
            step = math.atan2(math.sin(self.yaw - last), math.cos(self.yaw - last))
            turned, last = turned + step, self.yaw
        self.settle(1.0)
        after = self.average_scan()
        turned += math.atan2(math.sin(self.yaw - last), math.cos(self.yaw - last))
        error = best_shift(before, after)
        odom_deg, real_deg = math.degrees(turned), math.degrees(turned) + error
        print(f'odometry says: {odom_deg:.1f} deg')
        print(f'lidar says:    {real_deg:.1f} deg  (scans rotated by {error:+.1f} deg)')
        print(f'odometry / real = {odom_deg / real_deg:.3f}')


def best_shift(before, after, step=0.1, limit=60.0):
    """The angle (deg) that turns the `before` scan into the `after` one, to `step` degrees.

    A robot that turned d degrees too far sees every wall d degrees further clockwise, so
    after(theta) = before(theta + d). Beams are 1 degree apart; in between we interpolate."""
    n = len(before)

    def at(scan, deg):
        i = math.floor(deg) % n
        f = deg - math.floor(deg)
        return scan[i] * (1 - f) + scan[(i + 1) % n] * f

    def cost(d):
        return sum(abs(after[i] - at(before, i + d)) for i in range(n))

    shifts = [k * step - limit for k in range(int(2 * limit / step) + 1)]
    return min(shifts, key=cost)


def main():
    rclpy.init()
    node = SpinCheck()
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
