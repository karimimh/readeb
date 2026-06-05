"use client";

import { useState } from "react";
import type { Flashcard } from "@/lib/api";

function Card({ card }: { card: Flashcard }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <button
      onClick={() => setFlipped((f) => !f)}
      className="flex min-h-32 w-full flex-col justify-center rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-indigo-300"
    >
      <span className="mb-1 text-xs font-medium uppercase tracking-wide text-indigo-500">
        {flipped ? "Answer" : "Question"}
      </span>
      <span className="text-sm text-slate-800">
        {flipped ? card.answer : card.question}
      </span>
      <span className="mt-3 text-xs text-slate-400">Click to flip</span>
    </button>
  );
}

export default function FlashcardDeck({ cards }: { cards: Flashcard[] }) {
  if (cards.length === 0) {
    return <p className="text-sm text-slate-500">No flashcards generated.</p>;
  }
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {cards.map((card) => (
        <Card key={card.id} card={card} />
      ))}
    </div>
  );
}
