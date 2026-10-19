"""A first ROS 2 node: publish a counter on /hello twice a second."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class HelloNode(Node):
    def __init__(self):
        super().__init__('hello_node')            # the name shown by `ros2 node list`
        self.pub = self.create_publisher(String, 'hello', 10)   # topic, queue depth
        self.count = 0
        self.timer = self.create_timer(0.5, self.tick)          # call tick() every 0.5 s

    def tick(self):
        msg = String()
        msg.data = f'hello #{self.count}'
        self.pub.publish(msg)
        self.get_logger().info(f'published "{msg.data}"')
        self.count += 1


def main():
    rclpy.init()
    node = HelloNode()
    try:
        rclpy.spin(node)                          # run callbacks until Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
