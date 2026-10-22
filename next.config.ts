import type { NextConfig } from "next";
import createMDX from "@next/mdx";
import createNextIntlPlugin from "next-intl/plugin";

// CI (GitHub Actions sets CI=true) builds the Pages export once, so the postbuild check can scan out/ without a second build; set PAGES_BASE_PATH="" to opt out.
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
