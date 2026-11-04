// so101_system_skeleton.cpp — illustrative only; NOT built by this site's CI.
// Inherit hardware_interface::SystemInterface and export PLUGINLIB_EXPORT_CLASS
// in your own package. Method list matches control.ros.org Jazzy guide.
#if 0  // open in your Jazzy package — left disabled so a stray compile does nothing
#include "hardware_interface/system_interface.hpp"
#include "so101_hw/fake_bus.hpp"

namespace so101_hw {

class So101System : public hardware_interface::SystemInterface {
public:
  hardware_interface::CallbackReturn on_init(
      const hardware_interface::HardwareInfo & /*info*/) override {
    return hardware_interface::CallbackReturn::SUCCESS;
  }
  hardware_interface::CallbackReturn on_configure(
      const rclcpp_lifecycle::State &) override {
    return hardware_interface::CallbackReturn::SUCCESS;
  }
  hardware_interface::CallbackReturn on_activate(
      const rclcpp_lifecycle::State &) override {
    return hardware_interface::CallbackReturn::SUCCESS;
  }
  hardware_interface::CallbackReturn on_deactivate(
      const rclcpp_lifecycle::State &) override {
    return hardware_interface::CallbackReturn::SUCCESS;
  }
  hardware_interface::return_type read(
      const rclcpp::Time &, const rclcpp::Duration &) override {
    bus_.read();
    return hardware_interface::return_type::OK;
  }
  hardware_interface::return_type write(
      const rclcpp::Time &, const rclcpp::Duration &) override {
    bus_.write();
    return hardware_interface::return_type::OK;
  }
  // Also implement: on_cleanup, on_shutdown, on_error,
  // export_state_interfaces, export_command_interfaces (or rely on XML auto-export).

private:
  FakeBus bus_{};
};

}  // namespace so101_hw
#endif
