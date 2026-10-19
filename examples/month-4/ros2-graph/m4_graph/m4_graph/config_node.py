"""Configuration node: a /set_alpha service that checks a new smoothing factor and then
sets the filter node's "alpha" parameter through that node's own parameter service."""
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rcl_interfaces.msg import Parameter, ParameterType
from rcl_interfaces.srv import SetParameters

from m4_interfaces.srv import SetAlpha


class ConfigNode(Node):
    def __init__(self):
        super().__init__('config_node')
        self.target = self.declare_parameter('target_node', 'filter_node').value
        # Every node offers <name>/set_parameters; this client calls the filter's one.
        # It gets its own callback group so its reply can arrive while on_set_alpha waits.
        self.client = self.create_client(SetParameters, f'/{self.target}/set_parameters',
                                         callback_group=MutuallyExclusiveCallbackGroup())
        self.create_service(SetAlpha, 'set_alpha', self.on_set_alpha)
        self.get_logger().info(f'/set_alpha ready (configures /{self.target})')

    def on_set_alpha(self, request, response):
        if not 0.0 < request.alpha <= 1.0:
            response.accepted = False
            response.message = f'rejected: alpha {request.alpha} is outside (0, 1]'
            return response
        param = Parameter(name='alpha')
        param.value.type = ParameterType.PARAMETER_DOUBLE
        param.value.double_value = request.alpha
        if not self.client.wait_for_service(timeout_sec=2.0):
            response.accepted = False
            response.message = f'/{self.target} is not running'
            return response
        result = self.client.call(SetParameters.Request(parameters=[param]))   # blocks this callback only
        ok = result.results[0].successful
        response.accepted = ok
        response.message = (f'alpha set to {request.alpha} on /{self.target}' if ok
                            else 'rejected by filter: ' + result.results[0].reason)
        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = ConfigNode()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())   # two threads: service + client reply
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
