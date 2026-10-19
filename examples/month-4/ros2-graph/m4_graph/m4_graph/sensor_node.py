"""Sensor publisher: a fake temperature sensor on /raw (no hardware needed).

The values are a slow wave plus noise from a fixed random seed, so every run publishes
the same sequence of numbers."""
import math
import random

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from m4_interfaces.msg import Reading


class SensorNode(Node):
    def __init__(self):
        super().__init__('sensor_node')
        self.rate = self.declare_parameter('rate', 5.0).value          # Hz
        self.sensor_id = self.declare_parameter('sensor_id', 'temp0').value
        self.pub = self.create_publisher(Reading, 'raw', 10)
        self.rng = random.Random(7)
        self.k = 0
        self.create_timer(1.0 / self.rate, self.tick)
        self.get_logger().info(f'publishing /raw at {self.rate:.1f} Hz')

    def tick(self):
        msg = Reading()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'sensor_link'
        msg.sensor_id = self.sensor_id
        msg.value = 21.0 + 0.5 * math.sin(2 * math.pi * self.k / 50) + self.rng.gauss(0, 0.2)
        self.pub.publish(msg)
        self.k += 1


def main():
    rclpy.init()
    node = SensorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
