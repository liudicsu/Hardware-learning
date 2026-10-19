"use client";

import { months } from "@/lib/curriculum";
import {
  monthStats,
  useHydrated,
  useProgress,
} from "@/lib/progress";
import { ProgressBar } from "./ProgressBar";

export interface MonthProgressProps {
  monthId: number;
  label: string;
}

export function MonthProgress({ monthId, label }: MonthProgressProps) {
  const progress = useProgress();
  const hydrated = useHydrated();
  const month = months.find((entry) => entry.id === monthId);
  const percent =
    hydrated && month ? monthStats(progress, month).percent : 0;

  return <ProgressBar value={percent} label={label} />;
}
