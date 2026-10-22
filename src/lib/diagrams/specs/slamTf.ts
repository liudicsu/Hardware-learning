import type { BlockDiagramSpec } from "../types";

/*
 * m4/slam-nav: the TF chain map -> odom -> base_footprint -> base_link -> lidar_link and who publishes
 * each transform. slam.yaml (map_frame/odom_frame/base_frame), controllers.yaml (odom_frame_id,
 * base_frame_id, enable_odom_tf) and the URDF joints are checked by check_diagrams.
 * The lesson's ASCII said "laser_link"; the URDF and the Gazebo lidar use lidar_link, so the diagram
 * (and the lesson) use lidar_link.
 */

const SLAM_YAML = "examples/month-4/slam-nav/m4_nav/config/slam.yaml";
const CONTROLLERS = "examples/month-4/ros2-control/m4_control/config/controllers.yaml";
const URDF = "examples/month-4/urdf-tf/m4_description/urdf/robot.urdf.xacro";

export const slamTfChain: BlockDiagramSpec = {
  kind: "block",
  id: "slam-tf-chain",
  title: { zh: "建图时的 TF 链，以及每一段由谁发布", en: "The TF chain while mapping, and who publishes each link" },
  caption: {
    zh: "SLAM Toolbox 纠正漂移时，只有 map → odom 这一段会动；odom → base_footprint 保持平滑。",
    en: "When SLAM Toolbox corrects drift, only map → odom moves; odom → base_footprint stays smooth.",
  },
  sources: [SLAM_YAML, CONTROLLERS, URDF],
  nodes: [
    { id: "map", label: "map", mono: true, tone: "a" },
    { id: "odom", label: "odom", mono: true, tone: "a" },
    { id: "footprint", label: "base_footprint", mono: true, tone: "a" },
    { id: "base", label: "base_link", mono: true, tone: "a" },
    { id: "lidar", label: "lidar_link", mono: true, tone: "a" },
    {
      id: "slam",
      label: "SLAM Toolbox",
      mono: true,
      sub: { zh: "每当扫描匹配纠正漂移时，\n就会轻微跳一下", en: "jumps a little whenever\na scan match corrects\nthe drift" },
      tone: "b",
    },
    {
      id: "diff",
      label: "diff_drive_controller",
      mono: true,
      sub: { zh: "轮式里程计，第 5 课：\n平滑，但缓慢漂移", en: "wheel odometry, Lesson 5:\nsmooth, drifts slowly" },
      tone: "b",
    },
    { id: "rsp", label: "robot_state_publisher", mono: true, sub: { zh: "URDF，第 3 课", en: "URDF, Lesson 3" }, tone: "b" },
  ],
  edges: [
    { id: "tf1", tone: "a" },
    { id: "tf2", tone: "a" },
    { id: "tf3", tone: "a" },
    { id: "tf4", tone: "a" },
    { id: "bySlam", tone: "b", dashed: true },
    { id: "byDiff", tone: "b", dashed: true },
    { id: "byRsp3", tone: "b", dashed: true },
    { id: "byRsp4", tone: "b", dashed: true },
  ],
  layouts: {
    wide: {
      w: 720,
      h: 150,
      nodes: {
        map: [0, 10, 90, 34],
        odom: [130, 10, 90, 34],
        footprint: [260, 10, 150, 34],
        base: [450, 10, 110, 34],
        lidar: [600, 10, 120, 34],
        slam: [0, 80, 200, 64],
        diff: [216, 80, 196, 48],
        rsp: [428, 80, 292, 40],
      },
      edges: {
        tf1: { pts: [[90, 27], [128, 27]] },
        tf2: { pts: [[220, 27], [258, 27]] },
        tf3: { pts: [[410, 27], [448, 27]] },
        tf4: { pts: [[560, 27], [598, 27]] },
        bySlam: { pts: [[109, 80], [109, 31]] },
        byDiff: { pts: [[239, 80], [239, 31]] },
        byRsp3: { pts: [[440, 80], [440, 31]] },
        byRsp4: { pts: [[579, 80], [579, 31]] },
      },
    },
    narrow: {
      w: 340,
      h: 320,
      nodes: {
        map: [10, 4, 120, 30],
        odom: [10, 74, 120, 30],
        footprint: [10, 144, 120, 30],
        base: [10, 214, 120, 30],
        lidar: [10, 284, 120, 30],
        slam: [150, 20, 185, 64],
        diff: [144, 99, 196, 48],
        rsp: [150, 208, 185, 40],
      },
      edges: {
        tf1: { pts: [[70, 34], [70, 72]] },
        tf2: { pts: [[70, 104], [70, 142]] },
        tf3: { pts: [[70, 174], [70, 212]] },
        tf4: { pts: [[70, 244], [70, 282]] },
        bySlam: { pts: [[150, 53], [74, 53]] },
        byDiff: { pts: [[144, 123], [74, 123]] },
        byRsp3: { pts: [[150, 222], [140, 222], [140, 193], [74, 193]] },
        byRsp4: { pts: [[150, 234], [140, 234], [140, 263], [74, 263]] },
      },
    },
  },
  steps: [
    {
      label: {
        zh: "map → odom：SLAM Toolbox 发布。它是对里程计漂移的修正，扫描匹配成功时会跳一下。",
        en: "map → odom: published by SLAM Toolbox. It is the correction for odometry drift and jumps when a scan match succeeds.",
      },
      highlight: ["map", "odom", "tf1", "slam", "bySlam"],
    },
    {
      label: {
        zh: "odom → base_footprint：diff_drive_controller 根据轮子转动积分得到，连续平滑，但误差会一直累积。",
        en: "odom → base_footprint: diff_drive_controller integrates wheel rotations; it is smooth, but its error keeps adding up.",
      },
      highlight: ["odom", "footprint", "tf2", "diff", "byDiff"],
    },
    {
      label: {
        zh: "base_footprint → base_link → lidar_link：robot_state_publisher 根据 URDF 发布机器人自身的各连杆（固定关节走 /tf_static）。",
        en: "base_footprint → base_link → lidar_link: robot_state_publisher publishes the robot's own links from the URDF (fixed joints on /tf_static).",
      },
      highlight: ["footprint", "base", "lidar", "tf3", "tf4", "rsp", "byRsp3", "byRsp4"],
    },
  ],
  facts: [
    { file: SLAM_YAML, pattern: "odom_frame: odom", note: "SLAM Toolbox's odom frame is odom" },
    { file: SLAM_YAML, pattern: "map_frame: map\\s+# SLAM Toolbox publishes map -> odom", note: "SLAM Toolbox publishes map -> odom" },
    { file: SLAM_YAML, pattern: "base_frame: base_footprint", note: "SLAM Toolbox's base frame is base_footprint" },
    { file: CONTROLLERS, pattern: "base_frame_id: base_footprint", note: "diff_drive_controller: odom -> base_footprint" },
    { file: CONTROLLERS, pattern: "odom_frame_id: odom", note: "diff_drive_controller odom frame" },
    { file: CONTROLLERS, pattern: "enable_odom_tf: true", note: "diff_drive_controller publishes the odom TF" },
    { file: URDF, pattern: '<parent link="base_footprint"/>\\s*<child link="base_link"/>', note: "URDF joint base_footprint -> base_link" },
    { file: URDF, pattern: '<parent link="base_link"/>\\s*<child link="lidar_link"/>', note: "URDF joint base_link -> lidar_link (not laser_link)" },
    { file: "src/content/m4/slam-nav/en.mdx", pattern: "only `map → odom` moves", note: "lesson text: only map -> odom moves" },
  ],
};
