import type { ComponentProps } from "react";
import { nodeText, slugify } from "@/lib/toc";

export function H2({ children, ...rest }: ComponentProps<"h2">) {
  const id = slugify(nodeText(children));
  return (
    <h2 id={id} className="group scroll-mt-20" {...rest}>
      {children}
      <a href={`#${id}`} aria-hidden="true" tabIndex={-1} className="ml-2 text-zinc-600 opacity-0 transition-opacity group-hover:opacity-100">
        #
      </a>
    </h2>
  );
}
