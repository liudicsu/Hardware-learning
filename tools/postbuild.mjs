// Runs automatically after `npm run build` (npm's postbuild hook).
// CI workflows cannot be edited here, so the base-path link check for the
// GitHub Pages export rides on npm instead: with PAGES_BASE_PATH set it checks
// the existing export; on CI (which builds without env) it rebuilds the Pages
// export in a child process and checks that; locally it explains how to run it.
// Usage: npm run build
//   PAGES_BASE_PATH=/Hardware-learning npm run build   (check that export)
//   CI=1 npm run build                                 (build Pages export and check it)
import { spawnSync } from "node:child_process";

const BASE_PATH = "/Hardware-learning";
const CHECKER = "tools/check_basepath_links.mjs";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "inherit", ...options });
  if (result.error) {
    console.error(result.error.message);
    return 1;
  }
  return result.status ?? 1;
}

function runCheck(basePath) {
  return run(process.execPath, [CHECKER, "out", basePath]);
}

const basePath = (process.env.PAGES_BASE_PATH ?? "").trim();
if (basePath !== "") {
  process.exit(runCheck(basePath));
}

if (process.env.CI) {
  console.log("CI build: building the Pages export to check base-path links...");
  const buildStatus = run("npx", ["next", "build"], {
    env: { ...process.env, PAGES_BASE_PATH: BASE_PATH },
  });
  if (buildStatus !== 0) process.exit(buildStatus);
  process.exit(runCheck(BASE_PATH));
}

console.log(
  "Base-path link check skipped (no PAGES_BASE_PATH). Run it with `CI=1 npm run build` " +
    `or \`PAGES_BASE_PATH=${BASE_PATH} npm run build\`.`,
);
process.exit(0);
