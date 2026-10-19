# Lesson 2: Nodes, topics, services and actions / 第 2 课：节点、话题、服务与动作

Three packages that together form the lesson's graph (and this topic's practice task):
三个包合起来就是本课的那张图（也正是本主题的实践任务）：

- **`m4_interfaces/`** (`ament_cmake`): `msg/Reading.msg`, `msg/Summary.msg`, `srv/SetAlpha.srv`, `action/Collect.action`.
  自定义接口包：两条消息、一个服务、一个动作。
- **`m4_graph_cpp/`** (`ament_cmake`, C++): `filter_node`, an exponential moving average `/raw` → `/filtered` with a validated `alpha` parameter.
  C++ 滤波节点：指数移动平均，`/raw` → `/filtered`，`alpha` 参数带校验。
- **`m4_graph/`** (`ament_python`): `sensor_node` (seeded fake readings on `/raw`), `config_node` (`/set_alpha` service that forwards to the filter's parameter service), `aggregator_node` (`/summary` statistics and the `/collect` action), `collect_client`, `config/aggregator.yaml` and `launch/graph.launch.py` (arguments `rate`, `summary_topic`).
  Python 包：传感器节点（固定随机种子的假读数）、配置节点（`/set_alpha` 服务，转发到滤波器的参数服务）、汇总节点（`/summary` 统计和 `/collect` 动作）、动作客户端、YAML 配置和带参数的 launch 文件。

```bash
cp -r m4_interfaces m4_graph_cpp m4_graph ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 launch m4_graph graph.launch.py rate:=10.0 summary_topic:=stats
# second terminal / 另开一个终端
ros2 service call /set_alpha m4_interfaces/srv/SetAlpha "{alpha: 0.5}"
ros2 run m4_graph collect_client 5
```

Needs ROS 2 Jazzy (see [`../README.md`](../README.md)). These are real runs on a computer, no robot and no simulator; `../check.sh` repeats every command quoted in the lesson. The package licences are left as the `TODO` placeholder on purpose.
需要 ROS 2 Jazzy（见 [`../README.md`](../README.md)）。这些都是电脑上的真实运行，不需要机器人，也不涉及仿真；`../check.sh` 会重复课程里引用的每一条命令。包的许可证故意保留 `TODO` 占位符。
