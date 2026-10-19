"""DriveDistance action server: drive straight for a commanded distance, using odometry.

control.launch.py starts it (on the simulator's clock in Gazebo). Send it a goal with
    python3 drive_client.py 1.0 0.2
or  ros2 action send_goal --feedback /drive_distance m4_drive_interfaces/action/DriveDistance \\
        "{distance: 1.0, speed: 0.2}"
Commands go to the diff_drive_controller as TwistStamped; progress comes from its odometry."""
import math
import threading

import rclpy
from geometry_msgs.msg import TwistStamped
from m4_drive_interfaces.action import DriveDistance
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

TOLERANCE = 0.005   # m: close enough to count as reached


class DriveDistanceServer(Node):
    def __init__(self):
        super().__init__('drive_distance')
        group = ReentrantCallbackGroup()   # odometry keeps arriving while a goal runs
        self.cmd = self.create_publisher(TwistStamped, 'diff_drive_controller/cmd_vel', 10)
        # queue depth 1: always act on the newest odometry, never on a backlog of old messages
        self.create_subscription(Odometry, 'diff_drive_controller/odom', self.on_odom, 1,
                                 callback_group=group)
        self.position = None
        self.velocity = 0.0
        self.new_odom = threading.Event()
        ActionServer(self, DriveDistance, 'drive_distance', self.execute,
                     goal_callback=self.on_goal, cancel_callback=lambda _: CancelResponse.ACCEPT,
                     callback_group=group)
        self.get_logger().info('waiting for odometry')

    def on_odom(self, msg):
        if self.position is None:
            self.get_logger().info('odometry received: accepting goals')
        self.position = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        self.velocity = msg.twist.twist.linear.x
        self.new_odom.set()

    def next_odom(self):
        self.new_odom.clear()
        self.new_odom.wait(timeout=0.5)

    def on_goal(self, goal):
        ok = goal.speed > 0.0 and self.position is not None
        return GoalResponse.ACCEPT if ok else GoalResponse.REJECT

    def send(self, speed):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_footprint'
        msg.twist.linear.x = speed
        self.cmd.publish(msg)

    def execute(self, goal_handle):
        target = abs(goal_handle.request.distance)
        speed = math.copysign(goal_handle.request.speed, goal_handle.request.distance)
        start = self.position
        feedback = DriveDistance.Feedback()
        result = DriveDistance.Result()
        last_feedback = self.get_clock().now()
        while rclpy.ok() and not goal_handle.is_cancel_requested:
            travelled = math.dist(start, self.position)
            remaining = target - travelled
            if remaining <= TOLERANCE:
                break
            # near the end, slow down: command the remaining distance as a speed (0.1 m -> 0.1 m/s),
            # never more than the goal's speed and never less than 0.02 m/s
            self.send(math.copysign(max(0.02, min(abs(speed), remaining)), speed))
            now = self.get_clock().now()
            if now - last_feedback >= Duration(seconds=0.5):   # feedback twice a second
                feedback.travelled, feedback.remaining = travelled, remaining
                goal_handle.publish_feedback(feedback)
                last_feedback = now
            self.next_odom()
        # stop, and wait until odometry says the robot is standing still (at most 1 s)
        self.send(0.0)
        for _ in range(50):
            self.next_odom()
            if abs(self.velocity) < 0.001:
                break
        # report where the robot really ended up, not where it was when we decided to stop
        result.travelled = math.dist(start, self.position)
        result.reached = target - result.travelled <= TOLERANCE
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
        else:
            goal_handle.succeed()
        return result


def main():
    rclpy.init()
    node = DriveDistanceServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
