#!/usr/bin/env python3
"""Save one frame from /camera/image_raw as a PNG, and print what the image header says.

usage: python3 snap_camera.py [out.png]      (needs Pillow: pip install pillow)"""
import sys

import rclpy
from PIL import Image as PILImage
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'camera.png'
    rclpy.init()
    node = Node('snap_camera')
    got = []
    node.create_subscription(Image, 'camera/image_raw', got.append, qos_profile_sensor_data)
    while rclpy.ok() and not got:
        rclpy.spin_once(node, timeout_sec=0.5)
    img = got[0]
    print(f'frame_id: {img.header.frame_id}, {img.width} x {img.height}, encoding {img.encoding}')
    PILImage.frombytes('RGB', (img.width, img.height), bytes(img.data)).save(out)
    print(f'saved {out}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
