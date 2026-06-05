"use client";

import { useCallback, useEffect, useState } from "react";
import DocumentCard from "@/components/DocumentCard";
import UploadForm from "@/components/UploadForm";
import { listDocuments, type DocumentSummary } from "@/lib/api";

export default function Home() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await listDocuments();
      setDocs(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message}. Is the backend running on :8000?`
          : "Failed to load documents."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    // Poll while any document is still processing.
    const id = setInterval(() => {
      setDocs((current) => {
        if (
          current.some((d) => d.status === "processing" || d.status === "pending")
        ) {
          refresh();
        }
        return current;
      });
    }, 4000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div className="space-y-10">
      <section className="text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Turn textbooks into study materials
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-slate-500">
          Upload a PDF and readeb generates summaries, flashcards, quizzes, key
          concepts, a mind map, an audio lesson script and exam-ready notes.
        </p>
      </section>

      <UploadForm onUploaded={refresh} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Your documents</h2>
          <button
            onClick={refresh}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            Refresh
          </button>
        </div>

        {error && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : docs.length === 0 && !error ? (
          <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
            No documents yet. Upload your first PDF above to get started.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {docs.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
