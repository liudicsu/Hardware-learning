cmake_minimum_required(VERSION 3.10)
project(m4_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

# Generate C++ and Python code for every interface listed here.
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Reading.msg"
  "msg/Summary.msg"
  "srv/SetAlpha.srv"
  "action/Collect.action"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
