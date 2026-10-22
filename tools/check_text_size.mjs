// Rendered minimum-text-size check: every page, zh and en, at 390 px and 1280 px. Fails on any visible text
// under 12 px (HTML: computed font-size; SVG <text>: font-size x screen scale) and on horizontal page overflow.
// Not part of CI (it needs a browser). Run by hand against a build:
//   npm run build && npx next start -p 3177 &
//   npm i --no-save playwright-core && node tools/check_text_size.mjs http://localhost:3177
// Environment: CHROME = path of a Chrome/Chromium binary (default /usr/bin/google-chrome);
// WIDTHS = comma-separated viewport widths (default 390,1280).
// For the deployed site pass its base URL and "slash" (trailing slashes):
//   node tools/check_text_size.mjs https://liudicsu.github.io/Hardware-learning slash
import { readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MIN_PX = 12;
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const base = (process.argv[2] ?? "http://localhost:3177").replace(/\/$/, "");
const slash = process.argv[3] === "slash" ? "/" : "";
const widths = (process.env.WIDTHS ?? "390,1280").split(",").map(Number);
let chromium;
try {
  ({ chromium } = await import("playwright-core"));
} catch {
  console.error("playwright-core is not installed: npm i --no-save playwright-core");
  process.exit(2);
}

const paths = ["", "resources", "glossary", "math", "about"];
const content = join(root, "src/content");
for (const m of readdirSync(content).filter((d) => /^m\d+$/.test(d)))
  for (const l of readdirSync(join(content, m))) paths.push(`month/month-${m.slice(1)}/${l}`);

// runs in the page
function scan(limit) {
  const out = [];
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const where = (el) =>
    el.closest("[data-diagram]")?.getAttribute("data-diagram") ??
    el.closest("[data-widget]")?.getAttribute("data-widget") ??
    el.closest("figure,section,header,footer,nav,main,aside")?.tagName.toLowerCase() ?? "";
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || !visible(el)) continue;
    let px;
    if (el.closest("svg")) {
      const t = el.closest("text") ?? el;
      const m = t.getScreenCTM();
      if (!m) continue;
      px = parseFloat(getComputedStyle(t).fontSize) * Math.hypot(m.a, m.b);
    } else px = parseFloat(getComputedStyle(el).fontSize);
    if (px < limit - 0.05) out.push(`${px.toFixed(1)} px  ${where(el)}  "${n.textContent.trim().slice(0, 40)}"`);
  }
  return { small: out, overflow: document.documentElement.scrollWidth > window.innerWidth };
}

const browser = await chromium.launch({ executablePath: process.env.CHROME ?? "/usr/bin/google-chrome", args: ["--no-sandbox"] });
let bad = 0, pages = 0;
for (const loc of ["zh", "en"]) {
  for (const width of widths) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 } });
    for (const p of paths) {
      const page = await ctx.newPage();
      const url = `${base}/${loc}${p ? "/" + p : ""}${slash}`;
      const res = await page.goto(url, { waitUntil: "networkidle" });
      pages++;
      if (!res || !res.ok()) { bad++; console.log(`FAIL  ${url}: HTTP ${res?.status()}`); await page.close(); continue; }
      const { small, overflow } = await page.evaluate(scan, MIN_PX);
      for (const s of small) { bad++; console.log(`FAIL  ${loc} ${width}px /${p}: ${s}`); }
      if (overflow) { bad++; console.log(`FAIL  ${loc} ${width}px /${p}: page wider than the viewport`); }
      await page.close();
    }
    await ctx.close();
  }
}
await browser.close();
console.log(`\n${pages} pages, ${bad} problems`);
process.exit(bad ? 1 : 0);
