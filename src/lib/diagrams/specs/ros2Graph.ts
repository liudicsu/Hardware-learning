import type { BlockDiagramSpec } from "../types";

/*
 * m4/ros2-graph: the four-node system of the lesson (plus the action client in collect_client.py).
 * Topics: sensor_node -> /raw -> filter_node -> /filtered -> aggregator_node (subscribes "input",
 * remapped to filtered in graph.launch.py) -> /summary.
 * Service: /set_alpha on config_node, which calls /filter_node/set_parameters.
 * Action: /collect on aggregator_node.
 */

const PKG = "examples/month-4/ros2-graph";

export const ros2GraphSystem: BlockDiagramSpec = {
  kind: "block",
  id: "ros2-graph-system",
  title: { zh: "本课的 ROS 2 计算图：话题、服务、参数、动作", en: "The lesson's ROS 2 graph: topics, a service, a parameter, an action" },
  caption: {
    zh: "实线箭头：话题（蓝）；服务调用（琥珀色）；虚线：参数服务；绿色：动作。",
    en: "Solid arrows: topics (blue) and service calls (amber); dashed: the parameter service; green: the action.",
  },
  sources: [
    `${PKG}/m4_graph/launch/graph.launch.py`,
    `${PKG}/m4_graph/m4_graph/sensor_node.py`,
    `${PKG}/m4_graph_cpp/src/filter_node.cpp`,
    `${PKG}/m4_graph/m4_graph/aggregator_node.py`,
    `${PKG}/m4_graph/m4_graph/config_node.py`,
    `${PKG}/m4_graph/m4_graph/collect_client.py`,
  ],
  nodes: [
    { id: "sensor", label: "sensor_node", sub: { zh: "Python 节点", en: "Python node" }, mono: true, tone: "a" },
    { id: "filter", label: "filter_node", sub: { zh: "C++ 节点", en: "C++ node" }, mono: true, tone: "a" },
    { id: "aggregator", label: "aggregator_node", sub: { zh: "Python 节点", en: "Python node" }, mono: true, tone: "a" },
    { id: "you", label: { zh: "你", en: "you" }, sub: { zh: "命令行", en: "terminal" } },
    { id: "config", label: "config_node", sub: { zh: "Python 节点", en: "Python node" }, mono: true, tone: "b" },
    { id: "client", label: "collect_client", sub: { zh: "动作客户端", en: "action client" }, mono: true, tone: "ok" },
  ],
  edges: [
    { id: "raw", label: "/raw", mono: true, tone: "a" },
    { id: "filtered", label: "/filtered", mono: true, tone: "a" },
    { id: "summary", label: "/summary", mono: true, tone: "a" },
    { id: "setAlpha", label: { zh: "/set_alpha\n服务", en: "/set_alpha\nservice" }, tone: "b" },
    { id: "setParams", label: { zh: "set_parameters\n（参数服务）", en: "set_parameters\n(parameter service)" }, tone: "b", dashed: true },
    { id: "collect", label: { zh: "/collect\n动作", en: "/collect\naction" }, tone: "ok" },
  ],
  layouts: {
    wide: {
      w: 720,
      h: 200,
      nodes: {
        sensor: [0, 20, 140, 46],
        filter: [200, 20, 140, 46],
        aggregator: [400, 20, 160, 46],
        you: [0, 150, 140, 46],
        config: [200, 150, 140, 46],
        client: [400, 150, 160, 46],
      },
      edges: {
        raw: { pts: [[140, 43], [198, 43]], label: [169, 36] },
        filtered: { pts: [[340, 43], [398, 43]], label: [369, 36] },
        summary: { pts: [[560, 43], [712, 43]], label: [636, 36] },
        setAlpha: { pts: [[140, 173], [198, 173]], label: [169, 150] },
        setParams: { pts: [[270, 150], [270, 68]], label: [278, 104], anchor: "start" },
        collect: { pts: [[480, 150], [480, 68]], label: [488, 104], anchor: "start" },
      },
    },
    narrow: {
      w: 340,
      h: 312,
      nodes: {
        sensor: [10, 8, 150, 40],
        filter: [10, 88, 150, 40],
        aggregator: [10, 168, 150, 40],
        client: [10, 268, 150, 40],
        you: [190, 8, 140, 40],
        config: [190, 88, 140, 40],
      },
      edges: {
        raw: { pts: [[85, 48], [85, 86]], label: [91, 71], anchor: "start" },
        filtered: { pts: [[85, 128], [85, 166]], label: [91, 151], anchor: "start" },
        summary: { pts: [[160, 188], [332, 188]], label: [246, 181] },
        setAlpha: { pts: [[260, 48], [260, 86]], label: [266, 63], anchor: "start" },
        setParams: { pts: [[190, 108], [162, 108]], label: [168, 146], anchor: "start" },
        collect: { pts: [[85, 266], [85, 210]], label: [91, 236], anchor: "start" },
      },
    },
  },
  steps: [
    {
      label: {
        zh: "话题：sensor_node 在 /raw 上发布原始读数，filter_node 平滑后发布到 /filtered，aggregator_node 订阅它并在 /summary 上发布统计。",
        en: "Topics: sensor_node publishes raw readings on /raw, filter_node smooths them onto /filtered, and aggregator_node subscribes and publishes statistics on /summary.",
      },
      highlight: ["sensor", "filter", "aggregator", "raw", "filtered", "summary"],
    },
    {
      label: {
        zh: "服务与参数：你调用 config_node 的 /set_alpha 服务；它检查新值，再通过 filter_node 自己的 set_parameters 参数服务写入 alpha。",
        en: "Service and parameter: you call config_node's /set_alpha service; it validates the value and writes alpha through filter_node's own set_parameters service.",
      },
      highlight: ["you", "setAlpha", "config", "setParams", "filter"],
    },
    {
      label: {
        zh: "动作：客户端向 aggregator_node 的 /collect 动作发送目标，收集若干读数，期间接收反馈，也可以取消。",
        en: "Action: a client sends a goal to aggregator_node's /collect action to gather a number of readings, receives feedback, and can cancel.",
      },
      highlight: ["client", "collect", "aggregator"],
    },
  ],
  facts: [
    { file: `${PKG}/m4_graph/m4_graph/sensor_node.py`, pattern: "create_publisher\\(Reading, 'raw', 10\\)", note: "sensor_node publishes raw" },
    { file: `${PKG}/m4_graph_cpp/src/filter_node.cpp`, pattern: 'create_publisher<Reading>\\("filtered", 10\\)', note: "filter_node publishes filtered" },
    { file: `${PKG}/m4_graph_cpp/src/filter_node.cpp`, pattern: '"raw", 10,', note: "filter_node subscribes raw" },
    { file: `${PKG}/m4_graph/launch/graph.launch.py`, pattern: "remappings=\\[\\('input', 'filtered'\\), \\('summary', summary_topic\\)\\]", note: "aggregator input is remapped to filtered" },
    { file: `${PKG}/m4_graph/launch/graph.launch.py`, pattern: "'summary_topic', default_value='summary'", note: "summary topic defaults to /summary" },
    { file: `${PKG}/m4_graph/m4_graph/aggregator_node.py`, pattern: "ActionServer\\(self, Collect, 'collect'", note: "aggregator serves the collect action" },
    { file: `${PKG}/m4_graph/m4_graph/config_node.py`, pattern: "create_service\\(SetAlpha, 'set_alpha'", note: "config_node offers set_alpha" },
    { file: `${PKG}/m4_graph/m4_graph/config_node.py`, pattern: "'target_node', 'filter_node'", note: "config_node targets filter_node" },
    { file: `${PKG}/m4_graph/m4_graph/config_node.py`, pattern: "f'/\\{self\\.target\\}/set_parameters'", note: "config_node calls <target>/set_parameters" },
    { file: `${PKG}/m4_graph/m4_graph/collect_client.py`, pattern: "ActionClient\\(node, Collect, 'collect'\\)", note: "collect_client is the action client" },
  ],
};
