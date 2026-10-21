"use client";

import { useId } from "react";

export interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  format?: (value: number) => string;
  unit?: string;
  testId?: string;
}

/** One full-width range input with an accessible label and a live value. */
export function Slider({ label, value, min, max, step, onChange, format, unit, testId }: SliderProps) {
  const id = useId();
  const shown = format ? format(value) : String(value);
  return (
    <label htmlFor={id} className="block min-w-0">
      <span className="flex items-baseline justify-between gap-2 text-xs">
        <span className="min-w-0 text-zinc-400">{label}</span>
        <span className="shrink-0 font-mono text-zinc-200">
          {shown}
          {unit ? ` ${unit}` : ""}
        </span>
      </span>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        data-testid={testId}
        className="mt-1 h-6 w-full cursor-pointer accent-sky-400"
      />
    </label>
  );
}
