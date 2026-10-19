// Processing node in C++: smooth /raw readings with an exponential moving average
// and publish them on /filtered. The smoothing factor is the parameter "alpha".
#include <memory>
#include <string>
#include <vector>

#include "m4_interfaces/msg/reading.hpp"
#include "rclcpp/rclcpp.hpp"

using m4_interfaces::msg::Reading;

class FilterNode : public rclcpp::Node
{
public:
  FilterNode()
  : Node("filter_node")
  {
    alpha_ = declare_parameter("alpha", 0.2);   // default; a launch file or YAML can override it
    // Reject bad values before they are applied (ros2 param set prints the reason).
    param_cb_ = add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter> & params) {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        for (const auto & p : params) {
          if (p.get_name() == "alpha") {
            double a = p.as_double();
            if (a <= 0.0 || a > 1.0) {
              result.successful = false;
              result.reason = "alpha must be in (0, 1]";
            } else {
              alpha_ = a;
              RCLCPP_INFO(get_logger(), "alpha is now %.2f", alpha_);
            }
          }
        }
        return result;
      });
    pub_ = create_publisher<Reading>("filtered", 10);
    sub_ = create_subscription<Reading>(
      "raw", 10, [this](const Reading & msg) {on_reading(msg);});
    RCLCPP_INFO(get_logger(), "filtering /raw -> /filtered, alpha %.2f", alpha_);
  }

private:
  void on_reading(const Reading & msg)
  {
    // y = y + alpha * (x - y); the first reading starts the filter.
    estimate_ = have_estimate_ ? estimate_ + alpha_ * (msg.value - estimate_) : msg.value;
    have_estimate_ = true;
    Reading out = msg;          // keep the header and sensor_id
    out.value = estimate_;
    pub_->publish(out);
  }

  double alpha_;
  double estimate_ = 0.0;
  bool have_estimate_ = false;
  rclcpp::Publisher<Reading>::SharedPtr pub_;
  rclcpp::Subscription<Reading>::SharedPtr sub_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_cb_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<FilterNode>());
  rclcpp::shutdown();
  return 0;
}
