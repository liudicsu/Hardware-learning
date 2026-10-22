import type { BlockDiagramSpec, Layout } from "../types";

/*
 * m4/slam-nav "What Nav2 runs" (D093): how one NavigateToPose goal becomes a velocity command.
 * Parameters are checked against nav2.yaml by check_diagrams (facts). The controller's output topic name
 * cmd_vel_nav is not in our files: nav2_bringup's navigation_launch.py (1.3.13, Jazzy) remaps cmd_vel to
 * cmd_vel_nav for controller_server (L137) and as the input of velocity_smoother (L215); the smoother publishes
 * cmd_vel_smoothed, which collision_monitor reads (cmd_vel_in_topic in nav2.yaml).
 * https://github.com/ros-navigation/navigation2/blob/1.3.13/nav2_bringup/launch/navigation_launch.py
 */

const NAV2 = "examples/month-4/slam-nav/m4_nav/config/nav2.yaml";
const LAUNCH = "examples/month-4/slam-nav/m4_nav/launch/nav.launch.py";

// Left column: goal, bt_navigator, planner, controller. The velocity chain continues in a second column
// (wide) or below (narrow). Chain edges run at x 60 with their labels to the right.
const left: Layout["nodes"] = {
  goal: [80, 0, 200, 20],
  bt: [30, 30, 300, 48],
  planner: [30, 104, 300, 48],
  controller: [30, 178, 300, 48],
};
const leftEdges: Layout["edges"] = {
  goalIn: { pts: [[180, 20], [180, 28]] },
  plan: { pts: [[60, 78], [60, 102]], label: [66, 95], anchor: "start" },
  follow: { pts: [[30, 54], [12, 54], [12, 202], [28, 202]], label: [20, 170], anchor: "start" },
};

const wide: Layout = {
  w: 740,
  h: 380,
  nodes: {
    ...left,
    smoother: [430, 185, 300, 34],
    collision: [430, 259, 300, 34],
    ddc: [430, 339, 300, 34],
  },
  edges: {
    ...leftEdges,
    cmdNav: { pts: [[330, 202], [428, 202]], label: [379, 195] },
    smoothed: { pts: [[470, 219], [470, 257]], label: [476, 243], anchor: "start" },
    out: { pts: [[470, 293], [470, 337]], label: [476, 320], anchor: "start" },
  },
};

const narrow: Layout = {
  w: 340,
  h: 424,
  nodes: {
    ...left,
    smoother: [30, 252, 300, 34],
    collision: [30, 312, 300, 34],
    ddc: [30, 386, 300, 34],
  },
  edges: {
    ...leftEdges,
    cmdNav: { pts: [[60, 226], [60, 250]], label: [66, 243], anchor: "start" },
    smoothed: { pts: [[60, 286], [60, 310]], label: [66, 303], anchor: "start" },
    out: { pts: [[60, 346], [60, 384]], label: [66, 370], anchor: "start" },
  },
};

export const nav2Pipeline: BlockDiagramSpec = {
  kind: "block",
  id: "nav2-pipeline",
  title: { zh: "Nav2 如何把一个目标变成速度指令", en: "How Nav2 turns a goal into a velocity command" },
  caption: {
    zh: "参数取自 nav2.yaml。cmd_vel_nav 这个话题名来自 nav2_bringup 的 navigation_launch.py（1.3.13）里的重映射；恢复动作（原地转、后退、等待）由 behavior_server 执行，图中略去。",
    en: "Parameters from nav2.yaml. The topic name cmd_vel_nav comes from a remapping in nav2_bringup's navigation_launch.py (1.3.13); the recoveries (spin, back up, wait) run in behavior_server, left out here.",
  },
  sources: [NAV2, LAUNCH],
  nodes: [
    { id: "goal", label: { zh: "NavigateToPose 目标", en: "NavigateToPose goal" }, shape: "text", tone: "ink" },
    {
      id: "bt",
      label: "bt_navigator",
      mono: true,
      sub: { zh: "行为树：先规划，再跟随；\n失败时执行恢复动作", en: "behaviour tree: plan, then follow;\nrecoveries on failure" },
      tone: "b",
    },
    {
      id: "planner",
      label: "planner_server",
      mono: true,
      sub: { zh: "NavFn，在全局代价地图上规划：\n静态层 + 障碍层 + 膨胀层", en: "NavFn on the global costmap:\nstatic + obstacle + inflation layers" },
      tone: "a",
    },
    {
      id: "controller",
      label: "controller_server",
      mono: true,
      sub: { zh: "Regulated Pure Pursuit，≤ 0.25 m/s；\n局部代价地图 3 m × 3 m", en: "Regulated Pure Pursuit, ≤ 0.25 m/s;\nlocal costmap 3 m × 3 m" },
      tone: "a",
    },
    { id: "smoother", label: "velocity_smoother", mono: true, sub: { zh: "限制加速度", en: "limits acceleration" }, tone: "ok" },
    { id: "collision", label: "collision_monitor", mono: true, sub: { zh: "快撞上时减速或停下", en: "slows or stops before a hit" }, tone: "ok" },
    { id: "ddc", label: "diff_drive_controller", mono: true, sub: { zh: "第 5 课，要求 TwistStamped", en: "Lesson 5, expects TwistStamped" } },
  ],
  edges: [
    { id: "goalIn", tone: "ink" },
    { id: "plan", label: { zh: "规划路径", en: "plan a path" }, tone: "b" },
    { id: "follow", label: { zh: "跟随路径", en: "follow it" }, tone: "b" },
    { id: "cmdNav", label: "cmd_vel_nav", mono: true, tone: "ok" },
    { id: "smoothed", label: "cmd_vel_smoothed", mono: true, tone: "ok" },
    { id: "out", label: "/diff_drive_controller/cmd_vel", mono: true, tone: "ok" },
  ],
  layouts: { wide, narrow },
  steps: [
    {
      label: {
        zh: "bt_navigator 接收 NavigateToPose 目标，运行行为树：先规划，再跟随，失败时尝试恢复动作。",
        en: "bt_navigator receives the NavigateToPose goal and runs the behaviour tree: plan, follow, and try recoveries on failure.",
      },
      highlight: ["goal", "goalIn", "bt"],
    },
    {
      label: {
        zh: "planner_server 用 NavFn 在全局代价地图上规划：保存的地图（静态层）+ 激光雷达看到的障碍物 + 膨胀层。",
        en: "planner_server plans with NavFn on the global costmap: the saved map (static layer) + obstacles the lidar sees + inflation.",
      },
      highlight: ["bt", "plan", "planner"],
    },
    {
      label: {
        zh: "controller_server 用 Regulated Pure Pursuit 跟随路径，最高 0.25 m/s，依据 3 m × 3 m 的局部代价地图；路径与朝向相差超过 0.785 rad（45°）时先原地转。",
        en: "controller_server follows the path with Regulated Pure Pursuit at up to 0.25 m/s on the 3 m × 3 m local costmap; it turns on the spot first when the path is more than 0.785 rad (45°) off.",
      },
      highlight: ["bt", "follow", "controller"],
    },
    {
      label: {
        zh: "速度经 velocity_smoother（限制加速度）和 collision_monitor（快撞上时减速或停下），最后发到 /diff_drive_controller/cmd_vel，类型是 TwistStamped。",
        en: "The velocity passes velocity_smoother (limits acceleration) and collision_monitor (slows or stops before a hit) and reaches /diff_drive_controller/cmd_vel as a TwistStamped.",
      },
      highlight: ["controller", "cmdNav", "smoother", "smoothed", "collision", "out", "ddc"],
    },
  ],
  facts: [
    { file: NAV2, pattern: 'plugin: "nav2_navfn_planner::NavfnPlanner"', note: "planner is NavFn" },
    { file: NAV2, pattern: 'plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"\\s*\\n\\s*desired_linear_vel: 0\\.25', note: "Regulated Pure Pursuit at 0.25 m/s" },
    { file: NAV2, pattern: "rotate_to_heading_min_angle: 0\\.785", note: "turns on the spot beyond 0.785 rad" },
    { file: NAV2, pattern: "rolling_window: true\\s*\\n\\s*width: 3\\s*\\n\\s*height: 3", note: "local costmap is a 3 m x 3 m rolling window" },
    { file: NAV2, pattern: 'local_costmap:[\\s\\S]*?plugins: \\["obstacle_layer", "inflation_layer"\\]', note: "local costmap: obstacle + inflation" },
    { file: NAV2, pattern: 'global_costmap:[\\s\\S]*?plugins: \\["static_layer", "obstacle_layer", "inflation_layer"\\]', note: "global costmap: static + obstacle + inflation" },
    { file: NAV2, pattern: 'cmd_vel_in_topic: "cmd_vel_smoothed"', note: "collision_monitor reads the smoother's output" },
    { file: NAV2, pattern: 'cmd_vel_out_topic: "/diff_drive_controller/cmd_vel"', note: "collision_monitor feeds Lesson 5's controller" },
    { file: NAV2, pattern: "velocity_smoother:\\s*\\n\\s*ros__parameters:\\s*\\n\\s*enable_stamped_cmd_vel: true", note: "TwistStamped through the chain" },
    { file: LAUNCH, pattern: "include\\('nav2_bringup', 'navigation_launch\\.py'", note: "Nav2 started from nav2_bringup's navigation_launch.py" },
    { file: "src/content/m4/slam-nav/en.mdx", pattern: "more than 0\\.785 rad \\(45°\\)", note: "lesson text matches" },
  ],
};
