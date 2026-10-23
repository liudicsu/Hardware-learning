// Reader-visible Markdown leak check on the built HTML: every page's text (scripts, styles, <pre> and <code>
// blocks, comments and tag attributes removed; tags dropped so adjacent spans run together the way textContent
// reads them) must not contain a literal "**" or a leaked "__". MDX leaves "**" / "__" as text when the closing
// delimiter cannot close, e.g. `**<Term>回抽</Term>**是` (a closing "**" after punctuation or a tag and before a
// CJK letter), so the reader sees asterisks/underscores instead of bold. Code is excluded because "**" is Python's
// power operator and "__" appears in dunder names. Fill-in blanks ("___") and Python dunders left in tables
// ("__init__.py") are stripped before the "__" scan so they do not false-positive; "__" that remains is treated
// as an unrendered emphasis delimiter.
// Usage: node tools/check_visible_markdown.mjs [dir]   (default: out/ when it exists, else .next/server/app)
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2] ?? (existsSync("out") ? "out" : ".next/server/app");
if (!existsSync(dir)) {
  console.error(`check_visible_markdown: ${dir} does not exist; run npm run build first.`);
  process.exit(1);
}
const walk = (d) => readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(d, e.name)) : [join(d, e.name)]));
const pages = walk(dir).filter((f) => f.endsWith(".html"));
const named = { nbsp: " ", amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", ast: "*", midast: "*", lowbar: "_" };
const decode = (s) =>
  s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) =>
    e[0] === "#" ? String.fromCodePoint(e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : Number(e.slice(1))) : (named[e.toLowerCase()] ?? m));
const bad = [];
for (const f of pages) {
  const html = readFileSync(f, "utf8")
    .replace(/<(script|style|pre|code|template)\b[\s\S]*?<\/\1>/gi, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<[^>]*>/g, "");
  const text = decode(html);
  for (const m of text.matchAll(/\*\*/g)) {
    bad.push(`${f}: leaked "**" …${text.slice(Math.max(0, m.index - 30), m.index + 32).replace(/\s+/g, " ")}…`);
  }
  // Drop fill-in blanks (___) and Python-style dunders (__init__) before scanning for leaked "__".
  const forUnderscore = text.replace(/_{3,}/g, " ").replace(/__([A-Za-z][A-Za-z0-9]*)__/g, "$1");
  for (const m of forUnderscore.matchAll(/__/g)) {
    bad.push(`${f}: leaked "__" …${forUnderscore.slice(Math.max(0, m.index - 30), m.index + 32).replace(/\s+/g, " ")}…`);
  }
}
if (pages.length === 0) {
  console.error(`check_visible_markdown: no HTML pages under ${dir}`);
  process.exit(1);
}
if (bad.length) {
  console.error(`check_visible_markdown: ${bad.length} literal "**" or "__" in visible text in ${dir} (unrendered bold/strong; move the delimiters inside the tag or before the punctuation):`);
  for (const b of bad.slice(0, 40)) console.error(`  ${b}`);
  if (bad.length > 40) console.error(`  … and ${bad.length - 40} more`);
  process.exit(1);
}
console.log(`check_visible_markdown: ${pages.length} pages in ${dir}, no literal "**" or "__" in visible text`);
