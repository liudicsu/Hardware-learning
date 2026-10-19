export function StatusPill({ ready, label }: { ready: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        ready
          ? "border-sky-400/30 bg-sky-400/10 text-sky-300"
          : "border-white/10 text-zinc-500"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ready ? "bg-sky-400" : "bg-zinc-600"}`} />
      {label}
    </span>
  );
}
