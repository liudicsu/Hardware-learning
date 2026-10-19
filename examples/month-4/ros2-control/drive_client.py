#!/usr/bin/env python3
"""Send one DriveDistance goal, print its feedback and result; optionally cancel it part-way.

usage: python3 drive_client.py <distance m> <speed m/s> [cancel after s]
       python3 drive_client.py 1.0 0.2          drive 1 m forward at 0.2 m/s
       python3 drive_client.py -1.0 0.2 2.0     drive backwards, cancel after 2 s"""
import sys
import time

import rclpy
from action_msgs.msg import GoalStatus
from m4_drive_interfaces.action import DriveDistance
from rclpy.action import ActionClient
from rclpy.node import Node


def main():
    distance, speed = float(sys.argv[1]), float(sys.argv[2])
    cancel_after = float(sys.argv[3]) if len(sys.argv) > 3 else None
    rclpy.init()
    node = Node('drive_client')
    client = ActionClient(node, DriveDistance, 'drive_distance')
    client.wait_for_server()

    def on_feedback(msg):
        fb = msg.feedback
        print(f'feedback: travelled {fb.travelled:.3f} m, remaining {fb.remaining:.3f} m')

    t0 = time.monotonic()
    future = client.send_goal_async(DriveDistance.Goal(distance=distance, speed=speed),
                                    feedback_callback=on_feedback)
    rclpy.spin_until_future_complete(node, future)
    handle = future.result()
    if not handle.accepted:
        print('goal rejected')
        return
    print(f'goal accepted: {distance} m at {speed} m/s')
    result_future = handle.get_result_async()
    while not result_future.done():
        rclpy.spin_once(node, timeout_sec=0.1)
        if cancel_after is not None and time.monotonic() - t0 > cancel_after:
            print(f'cancelling after {cancel_after} s')
            rclpy.spin_until_future_complete(node, handle.cancel_goal_async())
            cancel_after = None
    res = result_future.result()
    status = {GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED', GoalStatus.STATUS_CANCELED: 'CANCELED',
              GoalStatus.STATUS_ABORTED: 'ABORTED'}.get(res.status, str(res.status))
    print(f'result: {status}, travelled {res.result.travelled:.3f} m, reached {res.result.reached}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
