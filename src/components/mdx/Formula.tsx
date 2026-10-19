import type { ReactNode } from "react";

export interface FormulaProps {
  children: ReactNode;
  label?: string;
}

export function Formula({ children, label }: FormulaProps) {
  return (
    <div className="my-4">
      <div className="rounded-lg bg-white/[0.03] py-3 text-center font-mono text-lg text-zinc-100">
        {children}
      </div>
      {label !== undefined && (
        <p className="mt-1 text-center text-xs text-zinc-500">{label}</p>
      )}
    </div>
  );
}
