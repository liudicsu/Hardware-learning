"""Action client for /collect: send a goal, print the feedback, optionally cancel.

usage: ros2 run m4_graph collect_client <samples> [--cancel-after N]"""
import argparse

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from m4_interfaces.action import Collect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('samples', type=int)
    parser.add_argument('--cancel-after', type=int, default=0, help='cancel after N feedback messages')
    args = parser.parse_args()

    rclpy.init()
    node = Node('collect_client')
    client = ActionClient(node, Collect, 'collect')
    client.wait_for_server()
    state = {'feedback': 0, 'handle': None}

    def on_feedback(msg):
        fb = msg.feedback
        print(f'feedback: {fb.received}/{args.samples}, latest {fb.latest:.2f}')
        state['feedback'] += 1
        if args.cancel_after and state['feedback'] == args.cancel_after and state['handle']:
            print('requesting cancel')
            state['handle'].cancel_goal_async()

    goal = client.send_goal_async(Collect.Goal(samples=args.samples), feedback_callback=on_feedback)
    rclpy.spin_until_future_complete(node, goal)
    state['handle'] = goal.result()
    if not state['handle'].accepted:
        print('goal rejected')
        return
    result = state['handle'].get_result_async()
    rclpy.spin_until_future_complete(node, result)
    status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(result.result().status, 'unknown')
    r = result.result().result
    print(f'{status}: {r.received} readings, mean {r.mean:.2f}')
    node.destroy_node()
    rclpy.try_shutdown()
