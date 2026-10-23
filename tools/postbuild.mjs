// These checks ride on npm's postbuild hook only: `npx next build` or
// `npm run build --ignore-scripts` silently skip them. Once the token has
// workflow scope, move them into their own steps in .github/workflows/ci.yml.
// Usage: npm run build
//   PAGES_BASE_PATH=/Hardware-learning npm run build   (check that export)
//   CI=1 npm run build                                 (build and check the Pages export)
import { spawnSync } from "node:child_process";
import { isCI, pagesBasePath } from "./is-ci.mjs";

const CHECKER = "tools/check_basepath_links.mjs";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "inherit", ...options });
  if (result.error) {
    if (result.error.code === "ENOENT") return { status: 127, notFound: true };
    console.error(result.error.message);
    return { status: 1, notFound: false };
  }
  return { status: result.status ?? 1, notFound: false };
}

const quotes = run("python3", ["tools/check_quotes.py"]);
if (quotes.notFound) {
  if (isCI()) {
    console.error("python3 not found; tools/check_quotes.py is required on CI.");
    process.exit(127);
  }
  console.warn("Warning: python3 not found; skipping tools/check_quotes.py.");
} else if (quotes.status !== 0) {
  process.exit(quotes.status);
}

const basePath = pagesBasePath();

// rendered percent check (tools/check_visible_pct.mjs): the export in out/ when there is a base path, else the prerendered pages
const visible = run(process.execPath, ["tools/check_visible_pct.mjs", basePath !== "" ? "out" : ".next/server/app"]);
if (visible.status !== 0) process.exit(visible.status);

// rendered Markdown leak check (tools/check_visible_markdown.mjs): no literal "**" in the visible text of the same pages
const markdown = run(process.execPath, ["tools/check_visible_markdown.mjs", basePath !== "" ? "out" : ".next/server/app"]);
if (markdown.status !== 0) process.exit(markdown.status);

if (basePath !== "") {
  const check = run(process.execPath, [CHECKER, "out", basePath]);
  process.exit(check.status);
}

console.log(
  "Base-path link check skipped (no base path). Run it with `PAGES_BASE_PATH=/Hardware-learning npm run build` " +
    "or `CI=1 npm run build`.",
);
process.exit(0);
