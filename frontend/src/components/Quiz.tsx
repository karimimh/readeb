"use client";

import { useState } from "react";
import type { QuizQuestion } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  mcq: "Multiple choice",
  true_false: "True / False",
  short_answer: "Short answer",
};

function Question({ q, index }: { q: QuizQuestion; index: number }) {
  const [revealed, setRevealed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const options =
    q.type === "true_false" && q.options.length === 0
      ? ["True", "False"]
      : q.options;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <p className="font-medium text-slate-800">
          {index + 1}. {q.question}
        </p>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          {TYPE_LABELS[q.type] ?? q.type}
        </span>
      </div>

      {options.length > 0 && (
        <ul className="mt-3 space-y-2">
          {options.map((opt) => {
            const isCorrect = revealed && opt === q.correct_answer;
            const isWrongPick =
              revealed && selected === opt && opt !== q.correct_answer;
            return (
              <li key={opt}>
                <button
                  onClick={() => {
                    setSelected(opt);
                    setRevealed(true);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                    isCorrect
                      ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                      : isWrongPick
                        ? "border-rose-300 bg-rose-50 text-rose-700"
                        : "border-slate-200 hover:border-indigo-300"
                  }`}
                >
                  {opt}
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <button
        onClick={() => setRevealed((r) => !r)}
        className="mt-3 text-sm text-indigo-600 hover:text-indigo-800"
      >
        {revealed ? "Hide answer" : "Show answer"}
      </button>

      {revealed && (
        <div className="mt-2 rounded-lg bg-slate-50 p-3 text-sm">
          <p>
            <span className="font-medium text-slate-700">Answer:</span>{" "}
            {q.correct_answer}
          </p>
          {q.explanation && (
            <p className="mt-1 text-slate-500">{q.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function Quiz({ questions }: { questions: QuizQuestion[] }) {
  if (questions.length === 0) {
    return <p className="text-sm text-slate-500">No quiz questions generated.</p>;
  }
  return (
    <div className="space-y-4">
      {questions.map((q, i) => (
        <Question key={q.id} q={q} index={i} />
      ))}
    </div>
  );
}
