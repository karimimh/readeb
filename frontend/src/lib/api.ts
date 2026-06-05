// Typed client for the readeb Django REST API.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

export const API_URL = `${API_BASE}/api`;

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface Statistics {
  pages?: number;
  chunks?: number;
  flashcards?: number;
  quiz_questions?: number;
  concepts?: number;
  definitions?: number;
  mode?: "offline" | "llm";
}

export interface Summary {
  id: number;
  chunk_id: number;
  summary_short: string;
  summary_long: string;
  takeaways: string[];
}

export interface Flashcard {
  id: number;
  chunk_id: number;
  question: string;
  answer: string;
}

export type QuizType = "mcq" | "true_false" | "short_answer";

export interface QuizQuestion {
  id: number;
  chunk_id: number;
  question: string;
  type: QuizType;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface Concept {
  id: number;
  name: string;
  description: string;
}

export interface Definition {
  id: number;
  term: string;
  definition: string;
}

export interface MindMapNode {
  root: string;
  children: MindMapNode[];
}

export interface Notes {
  id: number;
  topic: string;
  content: string;
}

export interface DocumentSummary {
  id: number;
  title: string;
  status: DocumentStatus;
  error: string;
  statistics: Statistics;
  file_url: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface DocumentDetail extends DocumentSummary {
  summaries: Summary[];
  flashcards: Flashcard[];
  quiz_questions: QuizQuestion[];
  concepts: Concept[];
  definitions: Definition[];
  notes: Notes[];
  mindmap: MindMapNode | null;
  audio_script: string | null;
}

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail =
        body.detail ||
        body.file?.[0] ||
        JSON.stringify(body) ||
        detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const res = await fetch(`${API_URL}/documents/`, { cache: "no-store" });
  const data = await handle<Paginated<DocumentSummary> | DocumentSummary[]>(res);
  return Array.isArray(data) ? data : data.results;
}

export async function getDocument(id: number | string): Promise<DocumentDetail> {
  const res = await fetch(`${API_URL}/documents/${id}/`, { cache: "no-store" });
  return handle<DocumentDetail>(res);
}

export async function getStatus(
  id: number | string
): Promise<{ id: number; status: DocumentStatus; error: string; statistics: Statistics }> {
  const res = await fetch(`${API_URL}/documents/${id}/status/`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function uploadDocument(
  file: File,
  title?: string
): Promise<DocumentDetail> {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);
  const res = await fetch(`${API_URL}/documents/`, {
    method: "POST",
    body: form,
  });
  return handle<DocumentDetail>(res);
}

export async function reprocessDocument(
  id: number | string
): Promise<{ status: DocumentStatus }> {
  const res = await fetch(`${API_URL}/documents/${id}/process/`, {
    method: "POST",
  });
  return handle(res);
}

export async function deleteDocument(id: number | string): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${id}/`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete document (${res.status})`);
  }
}
