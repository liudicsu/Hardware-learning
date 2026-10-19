"use client";

import type { ComponentProps } from "react";
import { Link, usePathname } from "@/i18n/navigation";

type Props = ComponentProps<typeof Link> & { match?: string };

export function NavLink({ match, className = "", ...props }: Props) {
  const pathname = usePathname();
  const target = match ?? (typeof props.href === "string" ? props.href : "");
  const active = target === "/" ? pathname === "/" : pathname.startsWith(target);
  return (
    <Link
      {...props}
      aria-current={active ? "page" : undefined}
      className={`rounded-md px-2.5 py-1.5 text-sm transition-colors ${
        active ? "text-white" : "text-zinc-400 hover:text-zinc-100"
      } ${className}`}
    />
  );
}
