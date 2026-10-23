// Reader-visible percent check on the built HTML: every page's text (scripts, styles, <pre> code blocks, comments
// and tag attributes removed; tags dropped so adjacent spans run together the way textContent reads them) must not
// glue a digit to "%" or "％" ("0%", "15％", "15 ％"). It is the rendered counterpart of the source rule in
// tools/check_diagrams.mjs, so a component that prints "{percent}%" fails here even though no lesson contains it.
// Usage: node tools/check_visible_pct.mjs [dir]   (default: out/ when it exists, else .next/server/app)
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2] ?? (existsSync("out") ? "out" : ".next/server/app");
if (!existsSync(dir)) {
  console.error(`check_visible_pct: ${dir} does not exist; run npm run build first.`);
  process.exit(1);
}
const walk = (d) => readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(d, e.name)) : [join(d, e.name)]));
const pages = walk(dir).filter((f) => f.endsWith(".html"));
const named = { nbsp: " ", amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", thinsp: " ", ensp: " ", emsp: " " };
const decode = (s) =>
  s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) =>
    e[0] === "#" ? String.fromCodePoint(e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : Number(e.slice(1))) : (named[e.toLowerCase()] ?? m));
const bad = [];
for (const f of pages) {
  const html = readFileSync(f, "utf8")
    .replace(/<(script|style|pre|template|noscript)\b[\s\S]*?<\/\1>/gi, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<[^>]*>/g, "");
  const text = decode(html);
  for (const m of text.matchAll(/\d%|\d\s*％/g)) bad.push(`${f}: "…${text.slice(Math.max(0, m.index - 30), m.index + m[0].length + 5).replace(/\s+/g, " ")}…"`);
}
if (pages.length === 0) {
  console.error(`check_visible_pct: no HTML pages under ${dir}`);
  process.exit(1);
}
if (bad.length) {
  console.error(`check_visible_pct: ${bad.length} visible percentages without a space ("15 %") in ${dir}:`);
  for (const b of bad.slice(0, 40)) console.error(`  ${b}`);
  if (bad.length > 40) console.error(`  … and ${bad.length - 40} more`);
  process.exit(1);
}
console.log(`check_visible_pct: ${pages.length} pages in ${dir}, every visible percentage has a space before %`);
