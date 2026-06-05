"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import FlashcardDeck from "@/components/FlashcardDeck";
import MindMapView from "@/components/MindMapView";
import Quiz from "@/components/Quiz";
import StatusBadge from "@/components/StatusBadge";
import {
  deleteDocument,
  getDocument,
  reprocessDocument,
  type DocumentDetail,
} from "@/lib/api";
import { useRouter } from "next/navigation";

type Tab =
  | "summaries"
  | "flashcards"
  | "quiz"
  | "concepts"
  | "mindmap"
  | "audio"
  | "notes";

const TABS: { key: Tab; label: string }[] = [
  { key: "summaries", label: "Summaries" },
  { key: "flashcards", label: "Flashcards" },
  { key: "quiz", label: "Quiz" },
  { key: "concepts", label: "Concepts" },
  { key: "mindmap", label: "Mind map" },
  { key: "audio", label: "Audio lesson" },
  { key: "notes", label: "Notes" },
];

export default function DocumentView({ id }: { id: string }) {
  const router = useRouter();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("summaries");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getDocument(id);
      setDoc(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document.");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while processing.
  useEffect(() => {
    if (!doc) return;
    if (doc.status !== "processing" && doc.status !== "pending") return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [doc, load]);

  async function handleReprocess() {
    setBusy(true);
    try {
      await reprocessDocument(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this document and all generated materials?")) return;
    setBusy(true);
    try {
      await deleteDocument(id);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
      setBusy(false);
    }
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link href="/" className="text-sm text-indigo-600">
          ← Back
        </Link>
        <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </p>
      </div>
    );
  }

  if (!doc) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  const processing = doc.status === "processing" || doc.status === "pending";
  const s = doc.statistics || {};

  return (
    <div className="space-y-6">
      <div>
        <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-800">
          ← All documents
        </Link>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{doc.title}</h1>
            <StatusBadge status={doc.status} />
          </div>
          {doc.status === "completed" && (
            <p className="mt-1 text-sm text-slate-500">
              {s.pages} pages · {s.chunks} chunks · {s.flashcards} flashcards ·{" "}
              {s.quiz_questions} quiz questions · {s.concepts} concepts
              {s.mode ? ` · ${s.mode} mode` : ""}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {doc.file_url && (
            <a
              href={doc.file_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
            >
              View PDF
            </a>
          )}
          <button
            onClick={handleReprocess}
            disabled={busy || processing}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
          >
            Reprocess
          </button>
          <button
            onClick={handleDelete}
            disabled={busy}
            className="rounded-lg border border-rose-300 px-3 py-1.5 text-sm text-rose-600 hover:bg-rose-50 disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>

      {processing && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-6 text-center">
          <p className="font-medium text-blue-800">Generating study materials…</p>
          <p className="mt-1 text-sm text-blue-600">
            This page updates automatically when processing completes.
          </p>
        </div>
      )}

      {doc.status === "failed" && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p className="font-medium">Processing failed</p>
          <p className="mt-1 break-words">{doc.error}</p>
        </div>
      )}

      {doc.status === "completed" && (
        <>
          <div className="flex flex-wrap gap-1 border-b border-slate-200">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`rounded-t-lg px-3 py-2 text-sm font-medium transition ${
                  tab === t.key
                    ? "border-b-2 border-indigo-600 text-indigo-700"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="pt-2">
            {tab === "summaries" && <Summaries doc={doc} />}
            {tab === "flashcards" && <FlashcardDeck cards={doc.flashcards} />}
            {tab === "quiz" && <Quiz questions={doc.quiz_questions} />}
            {tab === "concepts" && <Concepts doc={doc} />}
            {tab === "mindmap" && <MindMapView data={doc.mindmap} />}
            {tab === "audio" && <AudioScript content={doc.audio_script} />}
            {tab === "notes" && <Notes doc={doc} />}
          </div>
        </>
      )}
    </div>
  );
}

function Summaries({ doc }: { doc: DocumentDetail }) {
  if (doc.summaries.length === 0)
    return <p className="text-sm text-slate-500">No summaries generated.</p>;
  return (
    <div className="space-y-4">
      {doc.summaries.map((s) => (
        <div
          key={s.id}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h3 className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Chunk {s.chunk_id}
          </h3>
          {s.summary_short && (
            <p className="mt-1 font-medium text-slate-800">{s.summary_short}</p>
          )}
          {s.summary_long && (
            <p className="mt-2 text-sm text-slate-600">{s.summary_long}</p>
          )}
          {s.takeaways.length > 0 && (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {s.takeaways.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function Concepts({ doc }: { doc: DocumentDetail }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div>
        <h3 className="mb-3 font-semibold">Key concepts</h3>
        {doc.concepts.length === 0 ? (
          <p className="text-sm text-slate-500">None found.</p>
        ) : (
          <ul className="space-y-2">
            {doc.concepts.map((c) => (
              <li
                key={c.id}
                className="rounded-lg border border-slate-200 bg-white p-3 text-sm"
              >
                <span className="font-medium text-slate-800">{c.name}</span>
                {c.description && (
                  <span className="text-slate-500"> — {c.description}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <h3 className="mb-3 font-semibold">Definitions</h3>
        {doc.definitions.length === 0 ? (
          <p className="text-sm text-slate-500">None found.</p>
        ) : (
          <ul className="space-y-2">
            {doc.definitions.map((d) => (
              <li
                key={d.id}
                className="rounded-lg border border-slate-200 bg-white p-3 text-sm"
              >
                <span className="font-medium text-slate-800">{d.term}</span> —{" "}
                <span className="text-slate-500">{d.definition}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function AudioScript({ content }: { content: string | null }) {
  if (!content)
    return <p className="text-sm text-slate-500">No audio script generated.</p>;
  return (
    <div className="prose-pre rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-700">
      {content}
    </div>
  );
}

function Notes({ doc }: { doc: DocumentDetail }) {
  if (doc.notes.length === 0)
    return <p className="text-sm text-slate-500">No notes generated.</p>;
  return (
    <div className="space-y-4">
      {doc.notes.map((n) => (
        <div
          key={n.id}
          className="prose-pre rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-700"
        >
          {n.content}
        </div>
      ))}
    </div>
  );
}
