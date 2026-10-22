import type { BlockDiagramSpec, Layout } from "../types";

/*
 * m4/gazebo-sim "Launch and bridge" (D086): which way each topic crosses ros_gz_bridge. The topic lists are those of
 * m4_gazebo/config/bridge.yaml: check_diagrams runs tools/diagrams/bridge_topics.py (the spec's script), which reads
 * that file and prints the topics per direction in file order, and requires the lines built from GZ_TO_ROS and
 * ROS_TO_GZ below. Bindings tie the drawn boxes to the same lists, and `flows` checks that the arrows run
 * Gazebo -> GZ_TO_ROS -> ROS 2 and ROS 2 -> ROS_TO_GZ -> Gazebo in both layouts.
 */

const BRIDGE = "examples/month-4/gazebo-sim/m4_gazebo/config/bridge.yaml";
const SCRIPT = "tools/diagrams/bridge_topics.py";
const EN = "src/content/m4/gazebo-sim/en.mdx";
const ZH = "src/content/m4/gazebo-sim/zh.mdx";

const GZ_TO_ROS = ["clock", "scan", "camera/image_raw", "camera/camera_info", "joint_states", "odom", "tf"];
const ROS_TO_GZ = ["cmd_vel", "pan_cmd", "tilt_cmd"];
/** bridge.yaml entries whose ROS and Gazebo message types have different names. */
const TYPE_PAIRS: [string, string, "<-" | "->", string][] = [
  ["joint_states", "sensor_msgs/msg/JointState", "<-", "gz.msgs.Model"],
  ["tf", "tf2_msgs/msg/TFMessage", "<-", "gz.msgs.Pose_V"],
  ["pan_cmd", "std_msgs/msg/Float64", "->", "gz.msgs.Double"],
  ["tilt_cmd", "std_msgs/msg/Float64", "->", "gz.msgs.Double"],
];
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
const line = (t: string) => `(^|\\n)${esc(t)}(\\n|$)`;
const short = (t: string) => t.split(/[/.]/).pop();
/** Identifier lists read the same in both languages. */
const both = (t: string) => ({ zh: t, en: t });

const wide: Layout = {
  w: 750,
  h: 220,
  nodes: {
    gz: [10, 40, 180, 52],
    out: [300, 0, 190, 126],
    in: [300, 150, 190, 66],
    ros: [560, 40, 180, 52],
  },
  edges: {
    gzOut: { pts: [[190, 60], [300, 60]], label: [245, 53] },
    outRos: { pts: [[490, 60], [560, 60]] },
    rosIn: { pts: [[650, 92], [650, 183], [490, 183]], label: [570, 176] },
    inGz: { pts: [[300, 183], [100, 183], [100, 92]] },
  },
};

const narrow: Layout = {
  w: 340,
  h: 302,
  nodes: {
    gz: [10, 0, 320, 52],
    out: [10, 88, 170, 126],
    in: [196, 88, 134, 66],
    ros: [10, 250, 320, 52],
  },
  edges: {
    gzOut: { pts: [[95, 52], [95, 88]], label: [102, 75], anchor: "start" },
    outRos: { pts: [[95, 214], [95, 250]] },
    rosIn: { pts: [[263, 250], [263, 154]], label: [256, 207], anchor: "end" },
    inGz: { pts: [[263, 88], [263, 52]] },
  },
};

export const gzBridge: BlockDiagramSpec = {
  kind: "block",
  id: "gz-bridge",
  title: { zh: "ros_gz_bridge：传感器出来，命令进去", en: "ros_gz_bridge: sensor data out, commands in" },
  caption: {
    zh: `bridge.yaml 列出的 ${GZ_TO_ROS.length + ROS_TO_GZ.length} 个话题，两边同名，方向由 direction 字段决定。类型在桥上转换，多数两边同名（如 LaserScan），名字不同的有：${TYPE_PAIRS.map(([t, , d, g]) => `${t} ${d === "<-" ? "←" : "→"} ${g}`).join("、")}（ROS 侧为 ${[...new Set(TYPE_PAIRS.map((p) => short(p[1])))].join("、")}）。列表之外的话题都不过桥。`,
    en: `The ${GZ_TO_ROS.length + ROS_TO_GZ.length} topics in bridge.yaml, with the same name on both sides; the direction field decides which way each crosses. Types are converted on the bridge; most have the same name on both sides (LaserScan), and the ones that differ are ${TYPE_PAIRS.map(([t, , d, g]) => `${t} ${d === "<-" ? "←" : "→"} ${g}`).join(", ")} (${[...new Set(TYPE_PAIRS.map((p) => short(p[1])))].join(", ")} on the ROS side). Nothing outside the list crosses.`,
  },
  sources: [BRIDGE, SCRIPT],
  nodes: [
    { id: "gz", label: { zh: "Gazebo（gz-sim）", en: "Gazebo (gz-sim)" }, sub: { zh: "传感器 · DiffDrive\n关节插件", en: "sensors · DiffDrive\njoint plugins" } },
    { id: "out", label: { zh: "桥接：GZ_TO_ROS", en: "bridge: GZ_TO_ROS" }, sub: both(GZ_TO_ROS.join("\n")), tone: "a", mono: true },
    { id: "in", label: { zh: "桥接：ROS_TO_GZ", en: "bridge: ROS_TO_GZ" }, sub: both(ROS_TO_GZ.join("\n")), tone: "c", mono: true },
    { id: "ros", label: "ROS 2", sub: both("rviz2 · teleop\nrobot_state_publisher") },
  ],
  edges: [
    { id: "gzOut", label: { zh: "传感器、状态", en: "sensors, state" }, tone: "a" },
    { id: "outRos", tone: "a" },
    { id: "rosIn", label: { zh: "命令", en: "commands" }, tone: "c" },
    { id: "inGz", tone: "c" },
  ],
  layouts: { wide, narrow },
  script: {
    run: SCRIPT,
    lines: [
      `${GZ_TO_ROS.length + ROS_TO_GZ.length} bridged topics`,
      `GZ_TO_ROS: ${GZ_TO_ROS.join(", ")}`,
      `ROS_TO_GZ: ${ROS_TO_GZ.join(", ")}`,
      "same name on both sides: yes",
      ...TYPE_PAIRS.map(([t, r, d, g]) => `type differs: ${t} ${r} ${d} ${g}`),
    ],
  },
  bindings: [
    { node: "out", has: [...GZ_TO_ROS.map(line), "GZ_TO_ROS"], lacks: ROS_TO_GZ.map(line), note: "GZ_TO_ROS box lists exactly bridge.yaml's GZ_TO_ROS topics" },
    { node: "in", has: [...ROS_TO_GZ.map(line), "ROS_TO_GZ"], lacks: GZ_TO_ROS.map(line), note: "ROS_TO_GZ box lists exactly bridge.yaml's ROS_TO_GZ topics" },
  ],
  flows: [
    { edge: "gzOut", from: "gz", to: "out", note: "sensor data leaves Gazebo" },
    { edge: "outRos", from: "out", to: "ros", note: "and arrives in ROS 2" },
    { edge: "rosIn", from: "ros", to: "in", note: "commands leave ROS 2" },
    { edge: "inGz", from: "in", to: "gz", note: "and arrive in Gazebo" },
  ],
  facts: [
    ...[...GZ_TO_ROS.map((t) => [t, "GZ_TO_ROS"]), ...ROS_TO_GZ.map((t) => [t, "ROS_TO_GZ"])].map(([t, d]) => ({
      file: BRIDGE,
      pattern: `^- ros_topic_name: ${esc(t)}\\n  gz_topic_name: ${esc(t)}\\n.*\\n.*\\n  direction: ${d}$`,
      note: `${t}: ${d}`,
    })),
    ...TYPE_PAIRS.map(([t, r, , g]) => ({ file: BRIDGE, pattern: `^- ros_topic_name: ${esc(t)}\\n.*\\n  ros_type_name: ${esc(r)}\\n  gz_type_name: ${esc(g)}$`, note: `${t}: ${short(r)} / ${g}` })),
    { file: BRIDGE, pattern: "^# GZ_TO_ROS = sensor data and state coming out of the simulator; ROS_TO_GZ = commands going in\\.$", note: "bridge.yaml's own summary of the two directions" },
    ...[...GZ_TO_ROS, ...ROS_TO_GZ].flatMap((t) => [EN, ZH].map((file) => ({ file, pattern: `^/${esc(t)}$`, note: `/${t} in the lesson's ros2 topic list` }))),
    { file: EN, pattern: "you list each topic, its type on both sides and the direction, and nothing else crosses", note: "en: explicit list (caption)" },
    { file: ZH, pattern: "你列出每个话题、它在两边的类型以及方向，除此之外什么也不过来", note: "zh: explicit list (caption)" },
    { file: EN, pattern: "DiffDrive listens on `cmd_vel` and publishes odometry plus the `odom → base_footprint` transform", note: "en: DiffDrive in the Gazebo box" },
    { file: EN, pattern: "^<Diagram id=\"gz-bridge\" />$", note: "placed in the en lesson" },
    { file: ZH, pattern: "^<Diagram id=\"gz-bridge\" />$", note: "placed in the zh lesson" },
  ],
};
