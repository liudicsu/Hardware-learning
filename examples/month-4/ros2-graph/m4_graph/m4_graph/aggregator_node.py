"""Aggregator: a /summary topic every `window` readings, and a /collect action that
gathers a requested number of readings, with feedback and cancellation."""
import threading

import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from m4_interfaces.action import Collect
from m4_interfaces.msg import Reading, Summary


class AggregatorNode(Node):
    def __init__(self):
        super().__init__('aggregator_node')
        self.window = self.declare_parameter('window', 10).value
        self.values = []
        self.collectors = []            # one list per running /collect goal
        self.new_reading = threading.Condition()
        group = ReentrantCallbackGroup()  # let the action run while readings arrive
        self.pub = self.create_publisher(Summary, 'summary', 10)
        self.create_subscription(Reading, 'input', self.on_reading, 10, callback_group=group)
        ActionServer(self, Collect, 'collect', self.execute, callback_group=group,
                     cancel_callback=self.on_cancel)
        self.get_logger().info(f'window {self.window}, listening on {self.resolve_topic_name("input")}')

    def on_reading(self, msg):
        self.values.append(msg.value)
        if len(self.values) == self.window:
            v = self.values
            self.pub.publish(Summary(count=len(v), mean=sum(v) / len(v),
                                     minimum=min(v), maximum=max(v)))
            self.values = []
        with self.new_reading:
            for c in self.collectors:
                c.append(msg.value)
            self.new_reading.notify_all()

    def on_cancel(self, goal_handle):
        with self.new_reading:
            self.new_reading.notify_all()   # wake execute() so it sees the request at once
        return CancelResponse.ACCEPT

    def execute(self, goal_handle):
        want = goal_handle.request.samples
        got = []
        with self.new_reading:
            self.collectors.append(got)
        try:
            sent = 0
            while sent < want:
                with self.new_reading:
                    self.new_reading.wait_for(
                        lambda: len(got) > sent or goal_handle.is_cancel_requested, timeout=0.5)
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    self.get_logger().info(f'collect canceled after {sent} readings')
                    return self.result(got[:sent])
                while sent < min(len(got), want):
                    sent += 1
                    goal_handle.publish_feedback(Collect.Feedback(received=sent, latest=got[sent - 1]))
            goal_handle.succeed()
            return self.result(got[:want])
        finally:
            with self.new_reading:
                self.collectors.remove(got)

    @staticmethod
    def result(values):
        mean = sum(values) / len(values) if values else 0.0
        return Collect.Result(received=len(values), mean=mean)


def main():
    rclpy.init()
    node = AggregatorNode()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
