export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function withBasePath(src: string): string {
  if (!src.startsWith("/") || src.startsWith("//")) return src;
  if (/^https?:\/\//.test(src)) return src;
  if (BASE_PATH && src.startsWith(BASE_PATH) && (src.length === BASE_PATH.length || "/#?".includes(src[BASE_PATH.length]))) return src;
  return `${BASE_PATH}${src}`;
}

// The export uses trailingSlash: true, so this avoids a GitHub Pages redirect.
export function withPageSlash(href: string): string {
  if (!BASE_PATH || !href.startsWith("/") || href.startsWith("//")) return href;
  const index = href.search(/[#?]/);
  const path = index === -1 ? href : href.slice(0, index);
  const suffix = index === -1 ? "" : href.slice(index);
  if (path.endsWith("/")) return href;
  const lastSegment = path.slice(path.lastIndexOf("/") + 1);
  if (lastSegment.includes(".")) return href;
  return `${path}/${suffix}`;
}
