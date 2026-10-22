import type { NextConfig } from "next";
import createMDX from "@next/mdx";
import createNextIntlPlugin from "next-intl/plugin";

// GitHub Actions sets CI=true. CI is used as the export switch only because this repo's token cannot edit
// .github/workflows; a dedicated variable (e.g. PAGES_EXPORT=1 set in ci.yml) would be clearer and should
// replace this once workflow scope exists. With CI set, `npm run build` produces the Pages export once and
// the postbuild check scans out/ without a second build; set PAGES_BASE_PATH="" to opt out.
const basePath = process.env.PAGES_BASE_PATH ?? (process.env.CI ? "/Hardware-learning" : "");
const isPages = basePath !== "";

const nextConfig: NextConfig = {
  pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"],
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  experimental: { globalNotFound: true },
  ...(isPages
    ? {
        output: "export" as const,
        basePath,
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

const withMDX = createMDX({
  options: {
    // Plugins are passed by name so they stay serializable for Turbopack.
    remarkPlugins: [["remark-gfm", {}]],
  },
});

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

export default withNextIntl(withMDX(nextConfig));
