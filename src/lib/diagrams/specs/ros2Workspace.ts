import type { BlockDiagramSpec, Layout } from "../types";

// Tree rows top to bottom: [node id, depth, sub lines]. Rows are 30 units tall with no sub line, 34 with one and
// 48 with two (label 12.3 + sub lines 12.3, BlockDiagram.tsx); each row is indented 18 units per level and hangs
// from its parent's trunk (parent x + 9), which ends at the middle of the row's label.
const ROWS: [string, number, number][] = [
  ["root", 0, 0],
  ["src", 1, 0],
  ["pkg", 2, 0],
  ["packageXml", 3, 1],
  ["setupPy", 3, 2],
  ["setupCfg", 3, 0],
  ["resourceMarker", 3, 2],
  ["module", 3, 0],
  ["initPy", 4, 0],
  ["helloNode", 4, 1],
  ["build", 1, 1],
  ["install", 1, 2],
  ["log", 1, 0],
];
const PARENT: Record<string, string> = {
  src: "root", pkg: "src", packageXml: "pkg", setupPy: "pkg", setupCfg: "pkg", resourceMarker: "pkg", module: "pkg",
  initPy: "module", helloNode: "module", build: "root", install: "root", log: "root",
};
const EDGE: Record<string, string> = {
  src: "t-src", pkg: "t-pkg", packageXml: "t-package-xml", setupPy: "t-setup-py", setupCfg: "t-setup-cfg",
  resourceMarker: "t-resource", module: "t-module", initPy: "t-init", helloNode: "t-hello", build: "t-build",
  install: "t-install", log: "t-log",
};
const ROW_H = [30, 34, 48];
const FONT = 12.3;

function tree(widths: Record<string, number>, w: number): Layout {
  const nodes: Layout["nodes"] = {};
  const mid: Record<string, number> = {};
  let y = 4;
  for (const [id, depth, subs] of ROWS) {
    const h = ROW_H[subs];
    nodes[id] = [depth * 18, y, widths[id], h];
    // middle of the label line (see the label baseline in BlockDiagram.tsx)
    mid[id] = Math.round(subs ? y + h / 2 - 2 - ((subs - 1) * (FONT + 2.5)) / 2 - FONT * 0.36 : y + h / 2);
    y += h;
  }
  const edges: Layout["edges"] = {};
  for (const [id, parent] of Object.entries(PARENT)) {
    const [px, py, , ph] = nodes[parent];
    const x = px + 9;
    edges[EDGE[id]] = { pts: [[x, py + ph], [x, mid[id]], [nodes[id][0], mid[id]]] };
  }
  return { w, h: y + 4, nodes, edges };
}

const NARROW_W: Record<string, number> = {
  root: 72, src: 60, pkg: 90, packageXml: 212, setupPy: 196, setupCfg: 90, resourceMarker: 196,
  module: 90, initPy: 100, helloNode: 112, build: 184, install: 280, log: 60,
};
const WIDE_W = Object.fromEntries(Object.entries(NARROW_W).map(([id, v]) => [id, v + 40]));

export const ros2WorkspaceTree: BlockDiagramSpec = {
  kind: "block",
  id: "ros2-workspace-tree",
  title: { zh: "colcon 工作区的目录结构", en: "Layout of a colcon workspace" },
  sources: [
    "examples/month-4/ros2-setup/m4_hello/setup.py",
    "examples/month-4/ros2-setup/m4_hello/package.xml",
  ],
  nodes: [
    { id: "root", label: "ros2_ws/", shape: "file", mono: true, tone: "a" },
    { id: "src", label: "src/", shape: "file", mono: true, tone: "a" },
    { id: "pkg", label: "m4_hello/", shape: "file", mono: true, tone: "a" },
    {
      id: "packageXml",
      label: "package.xml",
      sub: { zh: "名称、版本、依赖", en: "name, version, dependencies" },
      shape: "file",
      mono: true,
    },
    {
      id: "setupPy",
      label: "setup.py",
      sub: { zh: "安装规则和它提供的命令", en: "install rules and\nthe commands it provides" },
      shape: "file",
      mono: true,
    },
    { id: "setupCfg", label: "setup.cfg", shape: "file", mono: true },
    {
      id: "resourceMarker",
      label: "resource/m4_hello",
      sub: { zh: "让 ROS 找到包的标记文件", en: "marker file so ROS\ncan find the package" },
      shape: "file",
      mono: true,
    },
    { id: "module", label: "m4_hello/", shape: "file", mono: true, tone: "a" },
    { id: "initPy", label: "__init__.py", shape: "file", mono: true },
    {
      id: "helloNode",
      label: "hello_node.py",
      sub: { zh: "节点", en: "the node" },
      shape: "file",
      mono: true,
    },
    {
      id: "build",
      label: "build/",
      sub: { zh: "由 colcon build 创建", en: "created by colcon build" },
      shape: "file",
      mono: true,
      tone: "muted",
    },
    {
      id: "install",
      label: "install/",
      sub: { zh: "由 colcon build 创建：要 source 的目录", en: "created by colcon build:\nwhat you source" },
      shape: "file",
      mono: true,
      tone: "muted",
    },
    { id: "log", label: "log/", shape: "file", mono: true, tone: "muted" },
  ],
  edges: [
    { id: "t-src", tone: "muted", arrow: false },
    { id: "t-pkg", tone: "muted", arrow: false },
    { id: "t-package-xml", tone: "muted", arrow: false },
    { id: "t-setup-py", tone: "muted", arrow: false },
    { id: "t-setup-cfg", tone: "muted", arrow: false },
    { id: "t-resource", tone: "muted", arrow: false },
    { id: "t-module", tone: "muted", arrow: false },
    { id: "t-init", tone: "muted", arrow: false },
    { id: "t-hello", tone: "muted", arrow: false },
    { id: "t-build", tone: "muted", arrow: false },
    { id: "t-install", tone: "muted", arrow: false },
    { id: "t-log", tone: "muted", arrow: false },
  ],
  layouts: { narrow: tree(NARROW_W, 340), wide: tree(WIDE_W, 480) },
  facts: [
    {
      file: "examples/month-4/ros2-setup/m4_hello/setup.py",
      pattern: "hello_node",
      note: "setup.py defines the hello_node entry point",
    },
    {
      file: "examples/month-4/ros2-setup/m4_hello/package.xml",
      pattern: "<name>m4_hello</name>",
      note: "package.xml names the package m4_hello",
    },
    {
      file: "examples/month-4/ros2-setup/m4_hello/setup.py",
      pattern: "resource/' \\+ package_name",
      note: "setup.py installs the resource/m4_hello marker",
    },
  ],
};
