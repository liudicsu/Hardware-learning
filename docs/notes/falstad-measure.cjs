/* eslint-disable @typescript-eslint/no-require-imports -- plain Node script, run outside the app */
// Measure the course's Falstad circuits in the real CircuitJS (falstad.com).
// Usage (needs playwright-core and a Chrome binary; not a repo dependency):
//   NODE_PATH=/path/to/node_modules node docs/notes/falstad-measure.cjs
// For each circuit/variant it loads circuitjs.html?cct=<text>, lets the
// simulation run, then reads values through window.CircuitJS1 (the documented
// JS interface: getElements(), elm.getType(), getCurrent(), getVoltageDiff(),
// getInfo(), getNodeVoltage(<labeled node>), getTime()).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const src = fs.readFileSync(path.join(__dirname, "../../src/lib/circuits.ts"), "utf8");
function cct(name) {
  const m = src.match(new RegExp(`\\b${name}: \\{\\s*cct: \`([^\`]*)\``));
  if (!m) throw new Error("no cct for " + name);
  return m[1];
}
// Set the positions of the SPST switches ("s" lines), in file order.
// pos 0 = closed, 1 = open.
function withSwitches(text, positions) {
  let i = 0;
  return text
    .split("\n")
    .map((line) => {
      const f = line.split(" ");
      if (f[0] !== "s") return line;
      const p = positions[i++];
      if (p !== undefined) f[6] = String(p);
      return f.join(" ");
    })
    .join("\n");
}

const CASES = [
  // loadedDivider: switches = [S]
  ["loadedDivider", "S open (no load)", [1], ["vout"]],
  ["loadedDivider", "S closed (10 kΩ load)", [0], ["vout"]],
  ["ledLimit", "as drawn", [], ["vled"]],
  // pullupButton: switches = [button]
  ["pullupButton", "button released", [1], ["pin"]],
  ["pullupButton", "button pressed", [0], ["pin"]],
  // ammeterSeriesParallel: switches = [Sser, Spar]
  ["ammeterSeriesParallel", "meter in series (Sser closed, Spar open)", [0, 1], []],
  ["ammeterSeriesParallel", "meter across battery (Sser open, Spar closed)", [1, 0], []],
  // hBridge: switches in file order = [S1, S2, S3, S4]
  ["hBridge", "forward S1+S4", [0, 1, 1, 0], []],
  ["hBridge", "reverse S2+S3", [1, 0, 0, 1], []],
  ["hBridge", "brake S2+S4", [1, 0, 1, 0], []],
  ["hBridge", "coast (all open)", [1, 1, 1, 1], []],
  ["hBridge", "shoot-through S1+S2 (left leg)", [0, 0, 1, 1], []],
  ["hBridge", "shoot-through S3+S4 (right leg)", [1, 1, 0, 0], []],
];

if (!process.env.DYNAMIC) (async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME || "/usr/bin/google-chrome",
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const out = [];
  for (const [name, label, sw, nodes] of CASES) {
    const text = withSwitches(cct(name), sw);
    const url =
      "https://www.falstad.com/circuit/circuitjs.html?running=false&cct=" + encodeURIComponent(text);
    await page.goto(url, { waitUntil: "load" });
    await page.waitForFunction(() => window.CircuitJS1 && window.CircuitJS1.getElements, null, {
      timeout: 60000,
    });
    // Track peak |current| of every element on every timestep (catches the fuse transient).
    await page.evaluate(() => {
      window.__peak = {};
      const sim = window.CircuitJS1;
      sim.ontimestep = (s) => {
        s.getElements().forEach((e, i) => {
          const c = Math.abs(e.getCurrent());
          if (!(window.__peak[i] >= c)) window.__peak[i] = c;
          if (e.getType() === "FuseElm" && window.__blownAt === undefined &&
              (e.getInfo() || []).join(" ").includes("blown"))
            window.__blownAt = s.getTime();
        });
      };
    });
    // start only after the hook is installed, so transients from t = 0 are seen
    await page.evaluate(() => window.CircuitJS1.setSimRunning(true));
    // let it settle: wait for at least 50 ms of simulated time
    await page.waitForFunction(() => window.CircuitJS1.getTime() > 0.05, null, { timeout: 120000 });
    const r = await page.evaluate((nodes) => {
      const sim = window.CircuitJS1;
      const elms = sim.getElements().map((e, i) => ({
        i,
        type: e.getType(),
        current: e.getCurrent(),
        vdiff: e.getVoltageDiff(),
        peak: window.__peak[i],
        info: (e.getInfo() || []).join(" | "),
      }));
      const v = {};
      for (const n of nodes) v[n] = sim.getNodeVoltage(n);
      return { t: sim.getTime(), elms, v, blownAt: window.__blownAt, exported: sim.exportCircuit() };
    }, nodes);
    out.push({ name, label, switches: sw, ...r });
    console.log(`\n### ${name}: ${label}  (sim t = ${(r.t * 1000).toFixed(1)} ms)`);
    if (r.blownAt !== undefined) console.log(`fuse blown at sim t = ${(r.blownAt * 1000).toFixed(3)} ms`);
    for (const [k, val] of Object.entries(r.v)) console.log(`V(${k}) = ${val.toFixed(4)} V`);
    for (const e of r.elms) {
      if (["WireElm", "GroundElm", "TextElm", "LabeledNodeElm", "OutputElm"].includes(e.type)) continue;
      console.log(
        `${e.i} ${e.type}: I = ${(e.current * 1000).toFixed(3)} mA, Vdiff = ${e.vdiff.toFixed(4)} V, peak|I| = ${(e.peak * 1000).toFixed(3)} mA :: ${e.info}`,
      );
    }
  }
  if (errors.length) console.log("\npage errors:", errors);
  fs.writeFileSync(process.env.OUT_JSON || "falstad-measure.json", JSON.stringify(out, null, 2));
  await browser.close();
})();

// ---------------------------------------------------------------------------
// Dynamic case: H-bridge brake after running forward. CircuitJS has no API to
// flip a switch, so we click the switches on the canvas (circuit coordinates
// are mapped to screen pixels from two known posts), with the simulation
// paused while both clicks happen, then sample the motor current.
// Run with: DYNAMIC=1 NODE_PATH=... node docs/notes/falstad-measure.cjs
if (process.env.DYNAMIC) (async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME || "/usr/bin/google-chrome",
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({ viewport: { width: 1000, height: 700 } });
  const url = "https://www.falstad.com/circuit/circuitjs.html?running=true&cct=" + encodeURIComponent(cct("hBridge"));
  await page.goto(url, { waitUntil: "load" });
  await page.waitForFunction(() => window.CircuitJS1 && window.CircuitJS1.getTime() > 0.03, null, { timeout: 60000 });
  // Screen mapping measured from a screenshot at this viewport: circuit (96,64) -> (142,101), (480,400) -> (690,581).
  const sx = (690 - 142) / (480 - 96), sy = (581 - 101) / (400 - 64);
  const scr = (x, y) => [142 + (x - 96) * sx, 101 + (y - 64) * sy];
  const ammeter = () => page.evaluate(() => {
    const a = window.CircuitJS1.getElements().find((e) => e.getType() === "AmmeterElm");
    return a.getCurrent();
  });
  const switches = () => page.evaluate(() => (window.CircuitJS1.exportCircuit().match(/<s [^>]*>/g) || []).map((l) => (/ p="1"/.test(l) ? "1" : "0")).join(""));
  console.log("\n### hBridge dynamic: forward, then brake (S1 open, S2 closed; S4 stays closed)");
  console.log("switch positions S1S2S3S4 before (0 = closed):", await switches(), " motor I =", ((await ammeter()) * 1000).toFixed(1), "mA");
  await page.evaluate(() => window.CircuitJS1.setSimRunning(false));
  // CircuitJS only toggles a switch it is hovering over, so move there in steps first.
  const clickAt = async (x, y) => {
    const [px, py] = scr(x, y);
    await page.mouse.move(px + 2, py, { steps: 10 });
    await page.waitForTimeout(300);
    await page.mouse.click(px + 2, py, { delay: 80 });
    await page.waitForTimeout(300);
  };
  await clickAt(288, 144); // S1 -> open
  await clickAt(288, 312); // S2 -> closed
  console.log("switch positions after clicks:", await switches());
  await page.evaluate(() => {
    const sim = window.CircuitJS1;
    window.__t0 = sim.getTime();
    window.__samples = [];
    sim.ontimestep = (s) => {
      const a = s.getElements().find((e) => e.getType() === "AmmeterElm");
      window.__samples.push([s.getTime() - window.__t0, a.getCurrent()]);
    };
    sim.setSimRunning(true);
  });
  await page.waitForFunction(() => window.CircuitJS1.getTime() - window.__t0 > 0.006, null, { timeout: 60000 });
  const samples = await page.evaluate(() => window.__samples);
  for (const ms of [0, 0.5, 1, 2, 3, 5]) {
    const s = samples.find(([dt]) => dt >= ms / 1000 - 1e-9);
    if (s) console.log(`t+${ms} ms: motor I = ${(s[1] * 1000).toFixed(1)} mA`);
  }
  await browser.close();
})();
