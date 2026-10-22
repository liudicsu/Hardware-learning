// Validate the explanatory diagrams in src/lib/diagrams (run: node tools/check_diagrams.mjs).
//  - every spec is registered, ids are unique, and every <Diagram id> in the lessons exists;
//  - zh.mdx and en.mdx of a lesson use the same diagrams in the same order;
//  - every label exists in both languages and the Chinese label contains Chinese text;
//  - both layouts place every node and edge inside the viewBox, the narrow layout is at most
//    360 units wide (one unit is about one pixel on a 390 px phone), and labels fit their boxes;
//  - timing specs (kind "timing"): equal column counts, label widths, and the diagram fits a 390 px phone
//    at Timing.tsx's minimum text scale; "numbers" computed in a spec must match the lesson's values;
//  - every "fact" (a regular expression) is found in the repository file it names, so the
//    numbers, pins and names drawn in a diagram are tied to the lesson scripts.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const specDir = join(root, "src/lib/diagrams/specs");

const FONT = 12, SUB = 10.5, NARROW_MAX = 360;
let failed = 0, checks = 0;
const fail = (msg) => { failed++; console.log("FAIL  " + msg); };
const ok = (cond, msg) => { checks++; if (!cond) fail(msg); };

function transpile(src) {
  return ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
}
const dataUrl = (s) => "data:text/javascript;base64," + Buffer.from(s).toString("base64");

// Width estimate: CJK and full-width forms take one em, everything else 0.6 em.
function textWidth(s, size) {
  let w = 0;
  for (const ch of s) w += /[\u3000-\u9fff\uff00-\uffef]/.test(ch) ? size : 0.6 * size;
  return w;
}
const hasCjk = (s) => /[\u4e00-\u9fff]/.test(s);
const lines = (s) => s.split("\n");

function checkText(where, text, { mono = false } = {}) {
  if (text === undefined) return;
  if (typeof text === "string") {
    // A shared string must be language-neutral: identifiers, numbers, units.
    ok(mono || !/[a-z]{3,}/.test(text.replace(/\b(Hz|ms|µs)\b/g, "")), `${where}: "${text}" is English prose; give { zh, en }`);
    return;
  }
  ok(text.zh && text.en, `${where}: both zh and en are required`);
  ok(hasCjk(text.zh), `${where}: zh label "${text.zh}" has no Chinese`);
}
const variants = (t) => (t === undefined ? [] : typeof t === "string" ? [t] : [t.zh, t.en]);

// ---------- timing diagrams (drawn by TimingSvg; layout constants read from Timing.tsx) ----------
const timingSrc = readFileSync(join(root, "src/components/diagrams/Timing.tsx"), "utf8");
const tconst = (name) => Number(timingSrc.match(new RegExp(`const ${name} = ([\\d.]+)`))[1]);
const T = { LEFT: tconst("LEFT"), COL: tconst("COL"), AVG_PAD: tconst("AVG_PAD"), MIN_SCALE: tconst("MIN_SCALE") };
// inner width of a diagram box on a 390 px phone (page and figure padding), measured with Playwright
const PHONE_BOX = 332;
function checkNumbers(spec, tag) {
  for (const n of spec.numbers ?? []) {
    const hit = Math.abs(n.value - n.expect) <= n.tol;
    ok(hit, `${tag}: number ${n.note}: computed ${n.value} vs lesson ${n.expect} (tol ${n.tol})`);
    if (hit) console.log(`calc  ${spec.id}: ${n.note}: ${+n.value.toFixed(4)} ≈ ${+n.expect.toFixed(4)}`);
  }
}
function checkTiming(spec, tag) {
  const lens = [
    ...(spec.columns ? [spec.columns.length] : []),
    ...spec.signals.map((s) => (s.kind === "bus" ? s.values?.length ?? 0 : s.levels?.length ?? 0)),
    ...(spec.rows ?? []).map((r) => r.cells.length),
  ];
  const n = Math.max(1, ...lens);
  ok(lens.every((l) => l === n), `${tag}: columns, levels/values and row cells must all have ${n} entries (got ${lens.join(", ")})`);
  for (const w of spec.columns ?? []) ok(w > 0, `${tag}: column width ${w} must be > 0`);
  const hasAvg = spec.signals.some((s) => s.average);
  const width = T.LEFT + n * T.COL + 8 + (hasAvg ? T.AVG_PAD : 0);
  ok(width * T.MIN_SCALE <= PHONE_BOX, `${tag}: ${width} units need ${Math.round(width * T.MIN_SCALE)} px at the minimum text scale; only ${PHONE_BOX} px fit at 390 px (it would scroll)`);
  for (const [k, s] of spec.signals.entries()) {
    const st = `${tag} signal ${k}`;
    checkText(`${st} name`, s.name, { mono: true });
    for (const t of variants(s.name)) ok(textWidth(t, 18) <= T.LEFT - 12, `${st}: name "${t}" wider than the label column`);
    if (s.kind === "bus") for (const v of s.values ?? []) checkText(`${st} value`, v, { mono: true });
    else for (const lv of s.levels ?? []) ok(typeof lv === "number" || lv === "x" || lv === "z", `${st}: bad level ${lv}`);
    if (s.average) {
      ok(s.kind !== "bus", `${st}: average on a bus signal`);
      ok(s.average.level >= 0 && s.average.level <= 1, `${st}: average level ${s.average.level} outside 0..1`);
      checkText(`${st} average`, s.average.label, { mono: true });
      for (const t of variants(s.average.label)) ok(textWidth(t, 14) <= T.AVG_PAD - 4, `${st}: average label "${t}" wider than ${T.AVG_PAD - 4}`);
    }
  }
  for (const r of spec.rows ?? []) {
    checkText(`${tag} row name`, r.name, { mono: true });
    for (const c of r.cells) checkText(`${tag} row cell`, c, { mono: true });
  }
  for (const sp of spec.spans ?? []) {
    ok(sp.from >= 0 && sp.to < n && sp.from <= sp.to, `${tag}: span ${sp.from}..${sp.to} outside 0..${n - 1}`);
    checkText(`${tag} span`, sp.label);
    const cw = spec.columns ? spec.columns.map((w) => (w / spec.columns.reduce((a, b) => a + b, 0)) * n * T.COL) : Array(n).fill(T.COL);
    const x0 = T.LEFT + cw.slice(0, sp.from).reduce((a, b) => a + b, 0);
    const x1 = x0 + cw.slice(sp.from, sp.to + 1).reduce((a, b) => a + b, 0);
    for (const t of variants(sp.label)) {
      const w = textWidth(t, 14);
      ok((x0 + x1) / 2 - w / 2 >= 0 && (x0 + x1) / 2 + w / 2 <= width, `${tag}: span label "${t}" (${w.toFixed(0)}) runs outside the ${width}-unit diagram`);
    }
  }
  if (spec.axisLabel) {
    checkText(`${tag} axis label`, spec.axisLabel);
    for (const t of variants(spec.axisLabel)) ok(textWidth(t, 14) <= n * T.COL, `${tag}: axis label "${t}" wider than the time axis`);
  }
  for (const [k, st] of (spec.steps ?? []).entries()) {
    checkText(`${tag} step ${k + 1}`, st.label);
    if (st.column !== undefined) ok(st.column >= 0 && st.column < n, `${tag} step ${k + 1}: column ${st.column} outside 0..${n - 1}`);
    for (const i of st.signals ?? []) ok(i >= 0 && i < spec.signals.length, `${tag} step ${k + 1}: signal ${i} does not exist`);
  }
  checkNumbers(spec, tag);
}

const specs = [];
for (const f of readdirSync(specDir).filter((f) => f.endsWith(".ts"))) {
  const mod = await import(dataUrl(transpile(readFileSync(join(specDir, f), "utf8"))));
  for (const [name, v] of Object.entries(mod)) if (v && typeof v === "object" && v.kind) specs.push({ file: f, name, spec: v });
}
const index = readFileSync(join(root, "src/lib/diagrams/index.ts"), "utf8");
const ids = new Set();

for (const { file, name, spec } of specs) {
  const tag = `${spec.id} (${file}:${name})`;
  ok(!ids.has(spec.id), `${tag}: duplicate id`);
  ids.add(spec.id);
  ok(new RegExp(`\\[${name}\\.id\\]: ${name}`).test(index), `${tag}: not registered in src/lib/diagrams/index.ts`);
  checkText(`${tag} title`, spec.title);
  checkText(`${tag} caption`, spec.caption);
  for (const src of spec.sources) ok(existsSync(join(root, src)), `${tag}: source ${src} does not exist`);
  if (spec.kind === "timing") checkTiming(spec, tag);
  else {
    const nodeIds = new Set(spec.nodes.map((n) => n.id));
    const edgeIds = new Set(spec.edges.map((e) => e.id));
    for (const n of spec.nodes) { checkText(`${tag} node ${n.id}`, n.label, n); checkText(`${tag} node ${n.id} sub`, n.sub); }
    for (const e of spec.edges) checkText(`${tag} edge ${e.id}`, e.label, e);
    for (const [k, s] of (spec.steps ?? []).entries()) {
      checkText(`${tag} step ${k + 1}`, s.label);
      for (const h of s.highlight) ok(nodeIds.has(h) || edgeIds.has(h), `${tag} step ${k + 1}: unknown id "${h}"`);
    }
    if (spec.kind === "stateMachine") ok(nodeIds.has(spec.initial), `${tag}: initial state "${spec.initial}" missing`);

    for (const which of ["wide", "narrow"]) {
      const L = spec.layouts[which];
      const lt = `${tag} ${which}`;
      if (which === "narrow") ok(L.w <= NARROW_MAX, `${lt}: width ${L.w} > ${NARROW_MAX}`);
      const inside = (x, y, what) => ok(x >= 0 && y >= 0 && x <= L.w && y <= L.h, `${lt}: ${what} at (${x}, ${y}) is outside ${L.w}x${L.h}`);
      for (const n of spec.nodes) {
        const r = L.nodes[n.id];
        ok(r, `${lt}: node ${n.id} has no position`);
        if (!r) continue;
        const [x, y, w, h] = r;
        inside(x, y, `node ${n.id}`); inside(x + w, y + h, `node ${n.id}`);
        const shape = n.shape ?? (spec.kind === "stateMachine" ? "state" : "box");
        const room = shape === "state" ? w - h / 2 : shape === "text" ? w + 4 : w - 8;
        for (const t of variants(n.label)) ok(textWidth(t, FONT) <= room, `${lt}: node ${n.id} label "${t}" (${textWidth(t, FONT).toFixed(0)}) wider than ${room}`);
        for (const t of variants(n.sub)) {
          for (const line of lines(t)) ok(textWidth(line, SUB) <= room, `${lt}: node ${n.id} sub "${line}" (${textWidth(line, SUB).toFixed(0)}) wider than ${room}`);
          // same vertical placement as BlockDiagram.tsx: label baseline, then sub lines below it
          if (shape === "box" || shape === "state") {
            const extra = (lines(t).length - 1) * (SUB + 2.5);
            const ly = y + h / 2 - 2 - extra / 2;
            const lastBase = ly + SUB + 3 + extra;
            ok(ly - FONT * 0.8 >= y && lastBase + 3 <= y + h, `${lt}: node ${n.id} label + ${lines(t).length} sub line(s) do not fit height ${h}`);
          }
        }
      }
      for (const e of spec.edges) {
        const g = L.edges[e.id];
        ok(g, `${lt}: edge ${e.id} has no geometry`);
        if (!g) continue;
        for (const [x, y] of g.pts) inside(x, y, `edge ${e.id} point`);
        if (e.label) {
          ok(g.label, `${lt}: edge ${e.id} label has no position`);
          if (!g.label) continue;
          for (const t of variants(e.label)) {
            lines(t).forEach((line, k) => {
              const w = textWidth(line, SUB);
              const a = g.anchor ?? "middle";
              const x0 = a === "start" ? g.label[0] : a === "end" ? g.label[0] - w : g.label[0] - w / 2;
              const yb = g.label[1] + k * (SUB + 2.5);
              inside(Math.floor(x0), Math.floor(yb - SUB), `edge ${e.id} label "${line}"`);
              inside(Math.ceil(x0 + w), Math.ceil(yb + 3), `edge ${e.id} label "${line}"`);
            });
          }
        }
      }
    }
  }

  for (const fact of spec.facts) {
    const p = join(root, fact.file);
    if (!existsSync(p)) { fail(`${tag}: fact file ${fact.file} missing`); continue; }
    const hit = new RegExp(fact.pattern, "m").test(readFileSync(p, "utf8"));
    ok(hit, `${tag}: fact not found in ${fact.file}: /${fact.pattern}/ (${fact.note})`);
    if (hit) console.log(`same  ${spec.id}: ${fact.note}  [${fact.file}]`);
  }
}

// Lessons: every <Diagram id> exists; zh and en use the same ids in the same order.
const content = join(root, "src/content");
for (const m of readdirSync(content)) {
  for (const lesson of readdirSync(join(content, m))) {
    const get = (loc) => {
      const p = join(content, m, lesson, `${loc}.mdx`);
      return existsSync(p) ? [...readFileSync(p, "utf8").matchAll(/<Diagram id="([^"]+)" \/>/g)].map((x) => x[1]) : [];
    };
    const en = get("en"), zh = get("zh");
    ok(JSON.stringify(en) === JSON.stringify(zh), `${m}/${lesson}: zh diagrams ${JSON.stringify(zh)} differ from en ${JSON.stringify(en)}`);
    for (const id of en) ok(ids.has(id), `${m}/${lesson}: <Diagram id="${id}" /> is not registered`);
  }
}

console.log(`\n${specs.length} diagrams, ${checks} checks, ${failed} failed`);
process.exit(failed ? 1 : 0);
