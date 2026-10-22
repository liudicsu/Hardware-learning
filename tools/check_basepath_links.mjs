// Base-path link check for the static export that GitHub Pages deploys.
//   PAGES_BASE_PATH=/Hardware-learning npm run build
//   node tools/check_basepath_links.mjs [exportDir] [basePath]
// Walks every .html file under exportDir and checks each href="..." / src="..." value. Any in-site absolute
// path (a leading "/", but not "//") must be exactly basePath or start with basePath + "/", and it must not
// repeat basePath (e.g. /Hardware-learning/Hardware-learning/...). External URLs, anchors, data: URIs and
// relative paths are ignored. exportDir defaults to "out"; basePath defaults to $PAGES_BASE_PATH or
// "/Hardware-learning".
// Usage: node tools/check_basepath_links.mjs [exportDir] [basePath]
// Exits 1 if the directory is missing or any link fails, otherwise prints OK and exits 0.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const dir = resolve(process.argv[2] ?? "out");
let basePath = (process.argv[3] ?? process.env.PAGES_BASE_PATH ?? "/Hardware-learning").trim();
if (!basePath.startsWith("/")) basePath = "/" + basePath;
basePath = basePath.replace(/\/+$/, "");

if (!existsSync(dir) || !statSync(dir).isDirectory()) {
  console.error(`Export directory not found: ${dir}`);
  console.error("Build the static export first, e.g. PAGES_BASE_PATH=/Hardware-learning npm run build");
  process.exit(1);
}

function walk(current, files) {
  for (const entry of readdirSync(current, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = join(current, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) files.push(full);
  }
  return files;
}

const attrRe = /(?:^|[\s"'<>])(href|src)\s*=\s*(["'])([\s\S]*?)\2/gi;
const failures = [];
const files = walk(dir, []);

for (const file of files) {
  const text = readFileSync(file, "utf8");
  const shown = relative(dir, file).split("\\").join("/");
  for (const match of text.matchAll(attrRe)) {
    const attr = match[1].toLowerCase();
    const value = match[3];
    if (!value.startsWith("/") || value.startsWith("//")) continue;
    if (basePath && value.startsWith(basePath + basePath)) {
      failures.push({ file: shown, attr, value });
      continue;
    }
    if (value === basePath || value.startsWith(basePath + "/")) continue;
    failures.push({ file: shown, attr, value });
  }
}

console.log(`Scanned ${files.length} HTML file${files.length === 1 ? "" : "s"} (base path ${basePath || "/"}).`);
const limit = 50;
for (const failure of failures.slice(0, limit))
  console.log(`FAIL  ${failure.file}: ${failure.attr}="${failure.value}"`);
if (failures.length > limit) console.log(`... ${failures.length - limit} more failure(s) not shown.`);

if (failures.length > 0) {
  console.error(`${failures.length} link${failures.length === 1 ? "" : "s"} outside the base path.`);
  process.exit(1);
}

console.log("OK: every in-site absolute link starts with the base path.");
