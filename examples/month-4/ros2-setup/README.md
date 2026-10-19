# Lesson 1: Which ROS 2, and your first workspace / 第 1 课：选哪个 ROS 2，搭好第一个工作空间

**`m4_hello/`**: the lesson's first package (`ament_python`), generated with `ros2 pkg create` and then edited: `hello_node` publishes `hello #N` on `/hello` every 0.5 s. The generated tests and the licence file were removed; the licence is left as the `TODO` placeholder on purpose, so pick your own.
本课的第一个包（`ament_python`）：先用 `ros2 pkg create` 生成，再修改。`hello_node` 每 0.5 秒在 `/hello` 上发布 `hello #N`。生成的测试和许可证文件已删除；许可证故意保留 `TODO` 占位符，请自己选择。

```bash
mkdir -p ~/ros2_ws/src
cp -r m4_hello ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 run m4_hello hello_node
```

Needs ROS 2 Jazzy (see [`../README.md`](../README.md)). These are real runs on a computer, no robot and no simulator; `../check.sh` repeats every command quoted in the lesson.
需要 ROS 2 Jazzy（见 [`../README.md`](../README.md)）。这些都是电脑上的真实运行，不需要机器人，也不涉及仿真；`../check.sh` 会重复课程里引用的每一条命令。
