#!/usr/bin/env python3
"""Read five LaserScans from /scan and summarise them: what the lidar sees, in numbers.

usage: python3 scan_probe.py        (with the simulation running)
Each range is averaged over the five scans, which takes out most of the sensor noise."""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def summarise(scans):
    scan = scans[0]
    n = len(scan.ranges)
    ranges = [sum(s.ranges[i] for s in scans) / len(scans) for i in range(n)]
    angle = lambda i: math.degrees(scan.angle_min + i * scan.angle_increment)
    valid = [(r, i) for i, r in enumerate(ranges) if scan.range_min <= r <= scan.range_max]
    ahead = min(range(n), key=lambda i: abs(angle(i)))         # the beam closest to 0 degrees
    print(f'frame_id: {scan.header.frame_id}')
    print(f'beams: {n}, from {angle(0):.1f} to {angle(n - 1):.1f} deg, '
          f'step {math.degrees(scan.angle_increment):.2f} deg')
    print(f'range limits: {scan.range_min:.2f} to {scan.range_max:.2f} m')
    print(f'beams with a hit: {len(valid)}, without (inf): {n - len(valid)}')
    print(f'straight ahead ({angle(ahead):.1f} deg): {ranges[ahead]:.2f} m')
    r, i = min(valid)
    # a round object returns almost the same range over several beams: report their middle
    near = [j for d, j in valid if d <= r + 0.02 and abs(angle(j) - angle(i)) < 20]
    print(f'nearest hit: {r:.2f} m, centred at {sum(angle(j) for j in near) / len(near):.0f} deg')


def main():
    rclpy.init()
    node = Node('scan_probe')
    got = []
    node.create_subscription(LaserScan, 'scan', got.append, qos_profile_sensor_data)
    while rclpy.ok() and len(got) < 5:
        rclpy.spin_once(node, timeout_sec=0.5)
    summarise(got[:5])
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
