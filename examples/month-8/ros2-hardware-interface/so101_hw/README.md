# so101_hw — skeleton only (本页未运行 / not run on this page)

Minimal ros2_control **System** hardware-component sketch for an SO-101-class arm.
Copy this folder into **your** Jazzy workspace package, fill serial I/O, and build with `colcon`.
This site's CI does **not** compile or load the plugin.

Lifecycle methods to implement (control.ros.org Jazzy *Writing a Hardware Component*):
`on_init`, `on_configure` / `on_cleanup` / `on_shutdown`, `on_activate` / `on_deactivate`,
`on_error`, `export_state_interfaces`, `export_command_interfaces`, `read`, `write`
(optional `prepare_command_mode_switch` / `perform_command_mode_switch`).

`fake_bus.hpp` is an in-memory stand-in for the Feetech bus so you can unit-test
`read`/`write` without hardware. Pair with lesson 8.6 Dev Container + `action-ros-ci`
in **your** package repo.
