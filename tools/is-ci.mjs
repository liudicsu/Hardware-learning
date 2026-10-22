// Shared CI / Pages base-path logic for next.config.ts and tools/postbuild.mjs, so both agree.
// Only CI=1 or CI=true counts as CI (the comparison is case-insensitive, so CI=TRUE counts too; GitHub Actions sets CI=true); unset, empty or CI=false does not.
export const PAGES_BASE_PATH = "/Hardware-learning";

/** @returns {boolean} */
export function isCI(env = process.env) {
  return ["1", "true"].includes((env.CI ?? "").toLowerCase());
}

/** PAGES_BASE_PATH wins when set (trimmed; "" opts out); otherwise the Pages path on CI, else "". */
/** @returns {string} */
export function pagesBasePath(env = process.env) {
  const raw = env.PAGES_BASE_PATH;
  if (raw !== undefined) return raw.trim();
  return isCI(env) ? PAGES_BASE_PATH : "";
}
