// Rendered minimum-text-size check: every page, zh and en, at 390 px and 1280 px. Fails on any visible text
// under 12 px (HTML: computed font-size; SVG <text>: font-size x screen scale) and on horizontal page overflow.
// It also fails when a page throws (pageerror), when a request fails or a same-origin request returns 4xx/5xx
// (a missing JS chunk means the page never hydrates), and when the chart/wilson measurement has not completed
// within 15 s (with JS disabled, blocked scripts are not failures). Sizes are read once every [data-widget="chart"]
// and [data-widget="wilson-bar"] has its measured viewBox; that is a wait for those widgets, not a general
// hydration check.
// CI does not run it: it needs a browser, and CI lives in .github/workflows, which cannot be edited from this
// repository's token. Run it by hand before merging a layout change, once plain and once with NOJS=1, against a build:
//   npm run build && npx next start -p 3177 &
//   npm i --no-save playwright-core && node tools/check_text_size.mjs http://localhost:3177
// Environment: CHROME = path of a Chrome/Chromium binary (default /usr/bin/google-chrome);
// WIDTHS = comma-separated viewport widths (default 390,1280);
// NOJS=1 adds a second pass with JavaScript disabled, which checks the first paint (server HTML before hydration).
// For the deployed site pass its base URL and "slash" (trailing slashes):
//   node tools/check_text_size.mjs https://liudicsu.github.io/Hardware-learning slash
import { readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MIN_PX = 12;
const HYDRATE_MS = 15000;
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const base = (process.argv[2] ?? "http://localhost:3177").replace(/\/$/, "");
const origin = new URL(base).origin;
const slash = process.argv[3] === "slash" ? "/" : "";
const widths = (process.env.WIDTHS ?? "390,1280").split(",").map(Number);
const passes = process.env.NOJS ? [true, false] : [true]; // javaScriptEnabled
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

// runs in the page: true once every visible width-following SVG has replaced its pre-measurement viewBox.
// Widths are clamp(box width, min, max) as in src/components/widgets/Chart.tsx (280..600) and WilsonWidget.tsx (240..600).
function chartsMeasured() {
  const clamp = { chart: [280, 600], "wilson-bar": [240, 600] };
  return Object.entries(clamp).every(([name, [lo, hi]]) =>
    [...document.querySelectorAll(`[data-widget="${name}"]`)].every((box) => {
      const svg = box.querySelector("svg");
      const w = box.getBoundingClientRect().width;
      if (!svg || !w) return true;
      return svg.viewBox.baseVal.width === Math.max(lo, Math.min(hi, Math.round(w)));
    }),
  );
}

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
for (const js of passes) {
  const tag = js ? "" : "nojs ";
  for (const loc of ["zh", "en"]) {
    for (const width of widths) {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled: js });
      for (const p of paths) {
        const page = await ctx.newPage();
        const url = `${base}/${loc}${p ? "/" + p : ""}${slash}`;
        const where = `${tag}${loc} ${width}px /${p}`;
        const errors = [];
        page.on("pageerror", (e) => errors.push(`page error: ${String(e.message).split("\n")[0]}`));
        // ERR_ABORTED is a request the page itself cancelled (link prefetch); with JS disabled every script is blocked by design
        page.on("requestfailed", (r) => {
          const why = r.failure()?.errorText ?? "?";
          if (js && why !== "net::ERR_ABORTED") errors.push(`request failed: ${r.url()} (${why})`);
        });
        page.on("response", (r) => { if (r.status() >= 400 && r.url().startsWith(origin) && r.url() !== url) errors.push(`HTTP ${r.status()}: ${r.url()}`); });
        const res = await page.goto(url, { waitUntil: "networkidle" });
        pages++;
        if (!res || !res.ok()) { bad++; console.log(`FAIL  ${url}: HTTP ${res?.status()}`); await page.close(); continue; }
        if (js) {
          const ok = await page.waitForFunction(chartsMeasured, null, { timeout: HYDRATE_MS }).then(() => true, () => false);
          if (!ok) { bad++; console.log(`FAIL  ${where}: a chart was not measured within ${HYDRATE_MS / 1000} s (page not hydrated?)`); }
        }
        const { small, overflow } = await page.evaluate(scan, MIN_PX);
        for (const e of errors) { bad++; console.log(`FAIL  ${where}: ${e}`); }
        for (const s of small) { bad++; console.log(`FAIL  ${where}: ${s}`); }
        if (overflow) { bad++; console.log(`FAIL  ${where}: page wider than the viewport`); }
        await page.close();
      }
      await ctx.close();
    }
  }
}
await browser.close();
console.log(`\n${pages} pages, ${bad} problems`);
process.exit(bad ? 1 : 0);
