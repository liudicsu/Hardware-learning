import { readFile } from "node:fs/promises";
import path from "node:path";
import { isValidElement, type ReactNode } from "react";

export type TocItem = { id: string; text: string };

/** Slug shared by the TOC (from MDX source) and the rendered <h2> (from React children). */
export function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .trim()
      .replace(/[^\p{L}\p{N}\s-]/gu, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "") || "section"
  );
}

/** Plain text of inline markdown: drops `code` ticks, **bold**, *em*, <strong>, [links](url). */
function stripInline(md: string): string {
  return md
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/<\/?[a-zA-Z][^>]*>/g, "")
    .replace(/[`*_]/g, "")
    .trim();
}

export function nodeText(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(nodeText).join("");
  if (isValidElement<{ children?: ReactNode }>(node)) return nodeText(node.props.children);
  return "";
}

/** Reads `## ` headings (outside code fences) from a lesson's MDX source at build time. */
export async function lessonToc(monthId: number, slug: string, locale: string): Promise<TocItem[]> {
  const file = path.join(process.cwd(), "src", "content", `m${monthId}`, slug, `${locale}.mdx`);
  const src = await readFile(file, "utf8").catch(() => "");
  const items: TocItem[] = [];
  let fence = false;
  for (const line of src.split("\n")) {
    if (line.trimStart().startsWith("```")) fence = !fence;
    if (fence) continue;
    const m = /^##\s+(.+?)\s*#*\s*$/.exec(line);
    if (m) {
      const text = stripInline(m[1]);
      items.push({ id: slugify(text), text });
    }
  }
  return items;
}
