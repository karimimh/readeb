import Link from "next/link";
import type { DocumentSummary } from "@/lib/api";
import StatusBadge from "./StatusBadge";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function DocumentCard({ doc }: { doc: DocumentSummary }) {
  const s = doc.statistics || {};
  return (
    <Link
      href={`/documents/${doc.id}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-indigo-300 hover:shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-900 line-clamp-2">{doc.title}</h3>
        <StatusBadge status={doc.status} />
      </div>
      <p className="mt-1 text-xs text-slate-400">{formatDate(doc.created_at)}</p>

      {doc.status === "completed" && (
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
          {s.pages != null && <span>{s.pages} pages</span>}
          {s.flashcards != null && <span>{s.flashcards} flashcards</span>}
          {s.quiz_questions != null && <span>{s.quiz_questions} quiz Qs</span>}
          {s.concepts != null && <span>{s.concepts} concepts</span>}
        </div>
      )}

      {doc.status === "failed" && doc.error && (
        <p className="mt-2 line-clamp-2 text-xs text-rose-600">{doc.error}</p>
      )}
    </Link>
  );
}
