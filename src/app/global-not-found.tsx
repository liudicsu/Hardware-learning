import type { Metadata } from "next";
import { BASE_PATH } from "@/lib/basePath";
import "./globals.css";

export const metadata: Metadata = {
  title: "404 · 页面不存在 / Page not found",
};

export default function GlobalNotFound() {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-[#0a0a0b] text-zinc-100 antialiased">
        <main className="flex min-h-screen items-center justify-center px-6 py-16">
          <div className="w-full max-w-lg rounded-xl border border-white/10 bg-[#111113] p-8 text-center">
            <p className="font-mono text-sm text-sky-400">404</p>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-100">页面不存在</h1>
            <p className="mt-1 text-lg text-zinc-400">Page not found</p>
            <p className="mt-5 text-sm text-zinc-400">这个页面可能已被移动或删除。</p>
            <p className="mt-1 text-sm text-zinc-500">The page may have been moved or deleted.</p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a
                href={`${BASE_PATH}/zh/`}
                className="rounded-lg border border-sky-400/40 bg-sky-400/[0.06] px-4 py-2 text-sm text-sky-300 transition-colors hover:border-sky-400/70"
              >
                返回中文首页
              </a>
              <a
                href={`${BASE_PATH}/en/`}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-zinc-300 transition-colors hover:border-white/20 hover:text-zinc-100"
              >
                English home
              </a>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
