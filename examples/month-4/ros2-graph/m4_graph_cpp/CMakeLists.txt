cmake_minimum_required(VERSION 3.10)
project(m4_graph_cpp)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(m4_interfaces REQUIRED)

add_executable(filter_node src/filter_node.cpp)
target_compile_features(filter_node PUBLIC cxx_std_17)
ament_target_dependencies(filter_node rclcpp m4_interfaces)

# Installed here, `ros2 run m4_graph_cpp filter_node` can find it.
install(TARGETS filter_node DESTINATION lib/${PROJECT_NAME})

ament_package()
