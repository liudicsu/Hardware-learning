<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project conventions (Hardware Learning site)

- Stack: Next.js 16 App Router (`src/app/[locale]/...`), Tailwind CSS v4 (`src/app/globals.css`, no tailwind.config), next-intl v4 (`src/i18n/*`, `messages/{zh,en}.json`, proxy in `src/proxy.ts`), MDX via `@next/mdx` (`src/content/m<month>/<lesson>/{zh,en}.mdx`).
- Locales: `zh` (default) and `en`. Every user-visible string must exist in both `messages/zh.json` and `messages/en.json`, or come from `L10n` objects in `src/lib/*.ts`.
- Data lives in `src/lib/curriculum.ts` (months, lessons, tasks) and `src/lib/resources.ts` (resource cards). Types in `src/lib/types.ts`.
- Progress is client-only, stored in `localStorage` (see `src/lib/progress.ts`). Never read localStorage during server render; use `useSyncExternalStore`.
- Style: dark, minimal, like X / Linear. Background near-black (`#0a0a0b`), cards `#111113` with `border-white/10`, text `zinc-100`/`zinc-400`, single accent (`sky-400`). Rounded-xl, subtle hover states, no gradients-heavy decoration.
- Use `Link` from `@/i18n/navigation` for internal links (it adds the locale prefix).
- No self-built simulators. Only embed the official Falstad page via iframe; everything else (Tinkercad, The Construct, Gazebo, ...) is an external link.
- Do not copy copyrighted text from resources. Lesson text is original.
