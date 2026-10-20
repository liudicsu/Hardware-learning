# Deployment proposal (not deployed)

**Status (2026-10-20, UTC+8): option B was chosen and implemented on branch opencode/pages-deploy.** The static export is enabled only when `PAGES_BASE_PATH` is set (`next.config.ts`), so `npm run dev` / `npm start` and the proxy are unchanged; `public/index.html` redirects to `zh/`; Markdown images get the base path through the `img` entry in the lesson page MDX components (`src/lib/basePath.ts`); the 404 page is now styled and bilingual via `src/app/global-not-found.tsx` (`experimental.globalNotFound`), which also replaces the default 404 for unknown URLs in dev/start; `.github/workflows/pages.yml` deploys `main` to <https://liudicsu.github.io/Hardware-learning/> after merge; the rest of this note is the original proposal, kept for the record.

Written 2026-10-20 (UTC+8) on branch `opencode/month-6`. Nothing has been deployed and no deployment config is
committed; this note is for the reviewer to decide.

## What the site needs from a host

`npm run build` already prerenders every page as static HTML: 2 locales × (home, about, resources, 6 month pages,
34 lessons) = 86 pages, all `●` (SSG via `generateStaticParams`, `dynamicParams = false`). There are no API routes,
no server actions, no `next/image`, no cookies/headers reads. The only server-side piece is the next-intl proxy
(`src/proxy.ts`, Next 16's name for middleware), which redirects `/` (and any path without a locale) to `/zh/...`.

## Option A (recommended): Vercel

- **Code changes:** none. Vercel builds Next.js 16 with zero config and runs the proxy, so `/` → `/zh` works as it
  does locally.
- **Preview deploys:** every push to a PR branch gets its own preview URL, posted on the PR by the Vercel GitHub app.
  That fits how this repo is reviewed (one PR per month): the reviewer can click through the new lessons in both
  locales before merging, without running anything locally. `main` becomes the production URL.
- **What the user has to do:** sign in to Vercel with GitHub, "Add New → Project", import
  `liudicsu/Hardware-learning` (framework preset Next.js, defaults are fine), and allow the Vercel GitHub app on this
  repo. Build command `npm run build`, Node 20+ (set in Project Settings if needed).
- **Cost/limits:** the Hobby plan is free for personal, non-commercial projects; check the current terms on
  vercel.com/pricing when signing up.
- **Caveat:** the default `*.vercel.app` domain may be slow or unreachable for some readers in mainland China; a custom
  domain can help. Not tested from here.

## Option B (tested, works with small changes): GitHub Pages via static export

Tested in a throwaway git worktree (`/tmp/hl-export`, nothing committed) with `output: "export"`,
`basePath: "/Hardware-learning"`, `trailingSlash: true`, `images: { unoptimized: true }`.

Result of the first, unchanged attempt: **the export builds** (`next build` writes `out/`, 89 HTML files, 32 MB);
next-intl, the App Router `[locale]` segment, MDX lessons and every dynamic route work, because every page already has
`generateStaticParams` and calls `setRequestLocale`. Next only warns that the proxy is disabled. Serving `out/` under
`/Hardware-learning/` and loading pages in headless Chrome found three problems:

1. **No page at `/Hardware-learning/`.** The proxy's redirect to `/zh` does not exist in a static export, so the
   site root is a 404 on Pages.
2. **Lesson images are broken.** Markdown images in Months 3 and 4 use root paths (`/m3/servo_bracket.png`,
   `/m4/gz_world.png`, …). `basePath` is applied to `Link` and `_next` assets but not to plain `<img src>` from MDX,
   so they request `/m3/...` instead of `/Hardware-learning/m3/...` (8 images across 5 lessons ×2 locales).
3. **Unstyled 404.** `out/404.html` is Next's default page, not the site's localized one (the localized
   `not-found.tsx` lives under `[locale]`, and there is no root layout).

With these changes the export passed: `/Hardware-learning/` redirects to `/zh/`, 10 sampled pages in both locales
(home, about, resources, month 1 and 6, lessons with images and quizzes) load with no console errors and no broken
images, client-side navigation and the zh → en switch keep the base path:

| File | Change |
|---|---|
| `next.config.ts` | `output: "export"`, `basePath` from `PAGES_BASE_PATH` (empty locally), `trailingSlash: true`, `images: { unoptimized: true }`, `env: { NEXT_PUBLIC_BASE_PATH: basePath }` |
| `src/app/[locale]/month/[month]/[lesson]/page.tsx` | an `img` entry in the MDX components that prefixes root-relative `src` with `NEXT_PUBLIC_BASE_PATH` |
| `public/index.html` | a static page with `<meta http-equiv="refresh" content="0; url=./zh/">` and links to `./zh/` and `./en/` |
| `public/.nojekyll` | stops Jekyll dropping `_next/` (not needed when deploying with `actions/deploy-pages`, harmless otherwise) |
| `src/proxy.ts` | removed (ignored by the export anyway). Alternatively keep it and switch `output: "export"` on only when `PAGES_BASE_PATH` is set, so `npm run dev` / `npm start` behave as today |
| `.github/workflows/pages.yml` | new: on push to `main`, `npm ci`, `PAGES_BASE_PATH=/Hardware-learning npm run build`, `actions/upload-pages-artifact` with `out/`, `actions/deploy-pages`; Settings → Pages → Source: GitHub Actions |

Not solved by these changes: the 404 page stays unstyled (would need a root layout, or a hand-written
`public/404.html`). There are **no preview deploys per PR** on GitHub Pages; only `main` is published.
Free for public repositories, no third-party account. `*.github.io` access from mainland China also varies.

## Other alternatives

- **Cloudflare Pages / Netlify:** both build Next.js; with the static export from option B they are pure static
  hosting and both offer preview deploys per PR. Each needs its own account, like Vercel.
- **Any static host or object storage (OSS/COS with a CDN):** upload `out/` from option B (with `PAGES_BASE_PATH`
  empty for a root domain). Useful if readers in mainland China are the main audience; needs a domain and, for a
  mainland CDN, an ICP filing.

## Recommendation

**Vercel (option A)** if the reviewer is happy to connect the repo to a Vercel account: no code changes, and a
preview link on every month's PR makes review easier. **GitHub Pages (option B)** if everything should stay on
GitHub with no extra account: the static export is tested and needs the five small changes above plus a workflow,
which would go in a separate PR. Either way, the decision is the reviewer's; nothing here is deployed.
