import { getResource, resourceUrl } from "@/lib/resources";

export interface ResourceCardProps {
  id: string;
  locale: "zh" | "en";
  labels: {
    open: string;
    supplement: string;
    kind: string;
  };
}

function ExternalArrowIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="h-3.5 w-3.5 shrink-0 text-zinc-500 transition-colors group-hover:text-sky-400"
    >
      <path d="M7 17 17 7" />
      <path d="M9 7h8v8" />
    </svg>
  );
}

function hostnameOf(url: string): string {
  return new URL(url).hostname.replace(/^www\./, "");
}

export function ResourceCard({ id, locale, labels }: ResourceCardProps) {
  const resource = getResource(id);
  const url = resourceUrl(resource, locale);
  const license = resource.license[locale];

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${labels.open}: ${resource.title[locale]}`}
      className="group block rounded-xl border border-white/10 bg-[#111113] p-5 transition-colors hover:border-white/20 hover:bg-white/[0.02]"
    >
      <div className="flex items-center gap-2">
        <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-zinc-400">
          {labels.kind}
        </span>
        {resource.extra && (
          <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-amber-300/80">
            {labels.supplement}
          </span>
        )}
        <span className="ml-auto shrink-0 text-xs text-zinc-500">
          {resource.cost[locale]}
        </span>
      </div>

      <h3 className="mt-3 flex items-start gap-1 text-base font-medium text-zinc-100">
        <span>{resource.title[locale]}</span>
        <ExternalArrowIcon />
      </h3>
      <p className="mt-0.5 text-xs text-zinc-500">{resource.author}</p>
      <p className="mt-2 text-sm text-zinc-400">{resource.summary[locale]}</p>

      <p className="mt-3 text-[11px] text-zinc-600">
        {license.includes("©") ? license : `© ${license}`}
      </p>
      <p className="mt-1 text-xs text-sky-400/80">{hostnameOf(url)}</p>
    </a>
  );
}
