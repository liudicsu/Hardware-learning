"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { setQuizCorrect, useHydrated, useProgress } from "@/lib/progress";

export interface QuizProps {
  id: string;
  lessonKey: string;
  question: string;
  options?: string[];
  answer: number;
  tolerance?: number;
  unit?: string;
  explanation?: string;
}

type Phase = "idle" | "correct" | "incorrect";

function QuestionMarkIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="h-4 w-4 shrink-0 text-sky-400"
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M9.6 9.2a2.5 2.5 0 1 1 3.7 2.2c-.8.5-1.3 1-1.3 1.9v.4" />
      <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function Quiz({
  id,
  lessonKey,
  question,
  options,
  answer,
  tolerance = 0.03,
  unit,
  explanation,
}: QuizProps) {
  const t = useTranslations("quiz");
  const progress = useProgress();
  const hydrated = useHydrated();
  const quizKey = `${lessonKey}?${id}`;
  const alreadyCorrect = hydrated && progress.quizzes[quizKey] === true;

  const [selected, setSelected] = useState<number | null>(null);
  const [value, setValue] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [revealed, setRevealed] = useState(false);

  const isNumeric = options === undefined;

  function reset() {
    setPhase("idle");
    setRevealed(false);
    setSelected(null);
    setValue("");
  }

  function check() {
    if (options) {
      const ok = selected === answer;
      setPhase(ok ? "correct" : "incorrect");
      if (ok) {
        setQuizCorrect(quizKey, true);
        setRevealed(true);
      }
      return;
    }
    const normalized = value.trim().replace(",", ".");
    const num = normalized === "" ? NaN : Number(normalized);
    if (!Number.isFinite(num)) {
      setPhase("incorrect");
      return;
    }
    const limit = answer === 0 ? 0.01 : Math.abs(answer) * tolerance;
    const ok = Math.abs(num - answer) <= limit;
    setPhase(ok ? "correct" : "incorrect");
    if (ok) {
      setQuizCorrect(quizKey, true);
      setRevealed(true);
    }
  }

  const answerText =
    options !== undefined
      ? options[answer]
      : `${answer}${unit ? ` ${unit}` : ""}`;
  const showReveal = phase === "correct" || (phase === "incorrect" && revealed);

  return (
    <section className="not-prose my-8 rounded-xl border border-white/10 bg-[#111113] p-5">
      <header className="flex items-center gap-2">
        <QuestionMarkIcon />
        <p className="flex-1 text-sm font-medium text-zinc-100">{question}</p>
        {alreadyCorrect && (
          <span
            aria-label={t("correct")}
            className="shrink-0 text-emerald-400"
          >
            ✓
          </span>
        )}
      </header>

      {options ? (
        <ul className="mt-4 space-y-2">
          {options.map((option, index) => {
            const checked = selected === index;
            const showCorrect = showReveal && index === answer;
            return (
              <li key={index}>
                <label
                  className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm transition-colors ${
                    checked
                      ? "border-white/20 bg-white/[0.05] text-zinc-100"
                      : "border-white/10 text-zinc-300 hover:bg-white/[0.02]"
                  } ${showCorrect ? "!border-emerald-400/50 bg-emerald-400/5" : ""}`}
                >
                  <input
                    type="radio"
                    name={`quiz-${quizKey}`}
                    checked={checked}
                    onChange={() => {
                      setSelected(index);
                      setPhase("idle");
                      setRevealed(false);
                    }}
                    className="h-4 w-4 shrink-0 cursor-pointer accent-sky-400"
                  />
                  <span>{option}</span>
                </label>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="mt-4 flex items-center gap-2">
          <input
            type="text"
            inputMode="decimal"
            value={value}
            placeholder={t("yourAnswer")}
            onChange={(event) => {
              setValue(event.target.value);
              setPhase("idle");
              setRevealed(false);
            }}
            className="w-40 rounded-lg border border-white/10 bg-transparent px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 outline-none transition-colors focus:border-sky-400/60"
          />
          {unit !== undefined && <span className="text-sm text-zinc-400">{unit}</span>}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        {phase !== "correct" && (
          <button
            type="button"
            onClick={check}
            disabled={isNumeric ? value.trim() === "" : selected === null}
            className="rounded-lg disabled:cursor-not-allowed disabled:opacity-40 bg-sky-400/10 px-3 py-1.5 text-xs font-medium text-sky-400 transition-colors hover:bg-sky-400/20"
          >
            {phase === "incorrect" ? t("retry") : t("check")}
          </button>
        )}
        {phase === "correct" && (
          <button
            type="button"
            onClick={reset}
            className="text-xs text-zinc-500 transition-colors hover:text-zinc-300"
          >
            {t("retry")}
          </button>
        )}
        {phase === "incorrect" && !revealed && (
          <button
            type="button"
            onClick={() => setRevealed(true)}
            className="text-xs text-zinc-500 transition-colors hover:text-zinc-300"
          >
            {t("showAnswer")}
          </button>
        )}
        {phase === "correct" && (
          <span className="text-xs font-medium text-emerald-400">
            {t("correct")}
          </span>
        )}
        {phase === "incorrect" && (
          <span className="text-xs font-medium text-rose-400">
            {t("incorrect")}
          </span>
        )}
      </div>

      {showReveal && (
        <div className="mt-3 rounded-lg bg-white/[0.03] p-3">
          <p className="text-xs">
            <span className="text-zinc-500">{t("answer")}</span>
            <span className="text-zinc-200">{answerText}</span>
            {phase === "incorrect" && isNumeric && value.trim() !== "" && (
              <span className="ml-3 text-zinc-600">
                {t("yourAnswer")}:{" "}
                <span className="text-zinc-400">{value.trim()}</span>
              </span>
            )}
          </p>
          {explanation !== undefined && (
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">{explanation}</p>
          )}
        </div>
      )}
    </section>
  );
}
