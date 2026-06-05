# readeb Frontend — Next.js

Web UI for the AI PDF Study Assistant. Upload a textbook PDF and browse the
generated summaries, flashcards, quizzes, concepts, mind map, audio lesson
script and study notes.

## Stack

- Next.js (App Router) + React + TypeScript
- Tailwind CSS
- Talks to the Django REST API in `../backend`

## Quick start

Make sure the backend is running on http://localhost:8000 first.

```bash
cd frontend
npm install
cp .env.example .env.local     # adjust NEXT_PUBLIC_API_BASE if needed
npm run dev
```

Open http://localhost:3000.

## Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | Base URL of the Django backend |

## Pages

- `/` — Upload form + list of your documents (auto-refreshes while processing).
- `/documents/[id]` — Tabbed view of all generated study materials, with live
  status polling, reprocess and delete actions.

## Project layout

```
frontend/src/
├── app/
│   ├── page.tsx                 # Home: upload + document list
│   └── documents/[id]/page.tsx  # Document detail route
├── components/
│   ├── UploadForm.tsx
│   ├── DocumentCard.tsx
│   ├── DocumentView.tsx         # Tabbed asset viewer
│   ├── FlashcardDeck.tsx
│   ├── Quiz.tsx
│   ├── MindMapView.tsx
│   └── StatusBadge.tsx
└── lib/api.ts                   # Typed API client
```

## Build

```bash
npm run build && npm start
```
