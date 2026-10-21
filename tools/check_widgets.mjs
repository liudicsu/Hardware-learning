// Check that the TypeScript models behind the formula widgets reproduce the Python outputs.
// Run with: node tools/check_widgets.mjs
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ts = require("typescript");

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const models = join(root, "src/lib/models");
const expectedDir = join(root, "tools/sim/expected");

function transpile(source) {
  return ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
}

function dataUrl(source) {
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const formatUrl = dataUrl(transpile(readFileSync(join(models, "format.ts"), "utf8")));

async function loadModel(name) {
  let source = transpile(readFileSync(join(models, name + ".ts"), "utf8"));
  source = source.replace(/from\s+["']\.\/format["']/g, "from " + JSON.stringify(formatUrl));
  return import(dataUrl(source));
}

const format = await import(formatUrl);
const fixed = format.fixed;

let checks = 0;
let failed = 0;

function compare(name, label, want, got) {
  checks++;
  const same = want === got;
  if (!same) {
    failed++;
  }
  console.log((same ? "same  " : "DIFF  ") + name + " " + label);
  console.log("  expected " + JSON.stringify(want));
  console.log("  got      " + JSON.stringify(got));
}

const pid = await loadModel("pid");
{
  const want = readFileSync(join(expectedDir, "m3-pid_sim.txt"), "utf8");
  const got = pid.report().join("\n") + "\n";
  compare("pid", "report", want, got);
}

const kinematics = await loadModel("kinematics");
{
  const want = readFileSync(join(expectedDir, "m5-kinematics.txt"), "utf8");
  const got = kinematics.report().join("\n") + "\n";
  compare("kinematics", "report", want, got);
}

const camera = await loadModel("camera");
{
  const lines = readFileSync(join(expectedDir, "m5-cam_pixel.txt"), "utf8")
    .split("\n")
    .filter((line) => line.startsWith("  ("));

  // Data-line layout from pixel_to_table.py:
  //   "  (u:4.0f, v:4.0f)   (3D point)   (exact mm)   error   ignoring distortion"
  // The pixel column is characters [0, 14), the 3D-point column [17, 41), and the
  // exact (mm) column [44, 68). Keep the pixel and exact columns, separated by 3 spaces.
  const pixelCol = (line) => line.slice(0, 14);
  const exactCol = (line) => line.slice(44, 68);

  const gotPixels = camera.pixelReport();
  const projectExpected = [
    ["(320.0, 240.0)", "(320.0, 240.0)"],
    ["(420.0, 300.0)", "(420.6, 300.4)"],
    ["(600.0, 440.0)", "(616.3, 451.7)"],
  ];

  lines.forEach((line, i) => {
    const want = pixelCol(line) + "   " + exactCol(line);
    compare("camera", "pixel " + (i + 1), want, gotPixels[i]);

    const mm = exactCol(line).match(/-?\d+\.\d+/g).map(Number);
    const point = [mm[0] / 1000, mm[1] / 1000, mm[2] / 1000];
    const show = ([u, v]) => "(" + fixed(u, 1) + ", " + fixed(v, 1) + ")";
    compare(
      "camera",
      "project pixel " + (i + 1),
      projectExpected[i][0],
      show(camera.project(point)),
    );
    compare(
      "camera",
      "project ignoreDistortion pixel " + (i + 1),
      projectExpected[i][1],
      show(camera.project(point, camera.TRUE_CAMERA, true)),
    );
  });
}

console.log(`widgets: ${checks} checks, ${failed} failed`);
process.exitCode = failed === 0 ? 0 : 1;
