# readeb — AI PDF Study Assistant

**Upload a textbook PDF and get summaries, flashcards, quizzes, key concepts, a
mind map, an audio-lesson script, and study notes.**

readeb is a full-stack project in three parts: a Python generation pipeline first
validated in a Jupyter notebook, a Django REST API that reuses that pipeline, and a
Next.js web app for uploading PDFs and studying the results. It runs end to end
with **no API keys** through a deterministic offline generator. One setting
switches it to real LLM generation with OpenAI, Anthropic, Gemini, or any
OpenAI-compatible endpoint.

## Features

Implemented:

- **PDF ingestion**: PyMuPDF extraction (pdfplumber as an alternative backend),
  removal of repeated headers and footers, whitespace cleanup, and page numbers
  preserved.
- **Chunking**: paragraph-aware chunks of about 1,500 words, with overlap and
  start/end page tags.
- **Generated study material**:
  - short and long summaries plus key takeaways for each chunk
  - question/answer flashcards
  - multiple-choice, true/false, and short-answer quiz questions with explanations
  - key concepts and definitions, de-duplicated across the whole document
  - a hierarchical mind map (JSON; the prototype also renders it to PNG with
    Graphviz)
  - an audio-lesson script, with optional MP3 output through OpenAI TTS in the
    prototype
  - Markdown study notes
- **Two generation modes**: an offline, rule-based generator (no tokens, no cost)
  and a provider-agnostic LLM client with retries, JSON-mode parsing, and a
  SHA-256-keyed on-disk response cache, so content that was already processed
  costs nothing to re-run.
- **REST API**: upload, list, detail, delete, re-process, status polling, and an
  endpoint for each asset type.
- **Web UI**: upload form, document list that refreshes while documents are
  processing, and a tabbed document view with flip-card flashcards, an interactive
  quiz, a mind-map tree, the audio script, and notes.
- **Prototype exports**: JSON, Markdown, an HTML report, and a `statistics.json`
  per run.

Not implemented yet / planned:

- User accounts. All uploaded documents are currently visible to every visitor.
- A durable job queue. Processing runs in a background thread in the API process;
  Celery with Redis is the intended replacement.
- Object storage for uploads (files are saved under `backend/media/`).
- Containerized setup and CI.
- Stretch ideas from the [original prototype brief](docs/prototype-brief.md),
  such as Anki export and spaced-repetition schedules.

## Architecture

```text
            ┌──────────────────────┐   REST/JSON   ┌───────────────────────────────┐
 Browser ──▶│ Next.js (frontend/)  │ ────────────▶ │ Django + DRF (backend/)       │
            │ upload, poll, study  │               │ DocumentViewSet               │
            └──────────────────────┘               │   │ background thread         │
                                                   │   ▼                           │
                                                   │ study/pipeline.py             │
                                                   │   extract → chunk → generate  │
                                                   │   │             │             │
                                                   │   │   offline.py (no keys) or │
                                                   │   │   study_assistant LLM     │
                                                   │   ▼   services (prototype/)   │
                                                   │ PostgreSQL: Document + assets │
                                                   └───────────────────────────────┘
```

- `prototype/study_assistant/` is the shared core: PDF extraction, chunking, the
  multi-provider `LLMClient`, one service per asset type, and Pydantic models for
  every output. Prompt templates live in `prototype/prompts/`.
- The Django backend adds `prototype/` to `sys.path` and imports those services
  directly, so the notebook and the API run the same code.
- `backend/study/pipeline.py` orchestrates a run: reset old assets, extract,
  chunk, generate per chunk, merge concepts, generate the document-level assets,
  then store statistics. The document status moves through
  `pending → processing → completed | failed`.
- `backend/study/offline.py` returns the same shapes as the LLM services. It is
  used when `USE_REAL_LLM=False` or no API key is set for the chosen provider.

## Tech stack

| Layer | Technologies |
| ----- | ------------ |
| Pipeline | Python 3.12+, PyMuPDF, pdfplumber, Pydantic v2, tenacity |
| LLM providers | OpenAI SDK (also used for Groq, OpenRouter, and other OpenAI-compatible APIs), Anthropic SDK, Google Generative AI SDK |
| Backend | Django 5, Django REST Framework, django-cors-headers, PostgreSQL (psycopg2) |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Prototype | Jupyter, Graphviz, networkx, matplotlib, OpenAI TTS (optional) |

## Repository layout

```text
prototype/
  study_assistant/   Reusable pipeline: extractor, chunker, LLM client, services, models
  prompts/           Prompt templates for each asset type
  notebooks/         pdf_study_assistant.ipynb, which runs the pipeline step by step
backend/
  config/            Django project settings and URLs
  study/             Models, serializers, viewset, pipeline, offline generator, tests
frontend/
  src/app/           Home page (upload and list) and /documents/[id]
  src/components/    Document view, flashcards, quiz, mind map, status badge
  src/lib/api.ts     Typed API client
docs/
  prototype-brief.md Original requirements brief for the notebook phase
```

Each part has its own README with more detail:
[backend](backend/README.md), [frontend](frontend/README.md),
[prototype](prototype/README.md).

## Running locally

Requirements: Python 3.12+, Node.js 20+, and a PostgreSQL server.

### 1. Database

Create a database that matches the `DB_*` values in `backend/.env`. To use the
defaults from `.env.example` with Docker, for example:

```bash
docker run -d --name readeb-postgres -p 5432:5432 \
  -e POSTGRES_DB=readeb -e POSTGRES_USER=readeb -e POSTGRES_PASSWORD=readeb \
  postgres:16
```

### 2. Backend (http://localhost:8000)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

### 3. Frontend (http://localhost:3000)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000 and upload a PDF. The generated material appears when
processing finishes.

## Configuration

Each part reads its own environment file. Every variable is listed with a
placeholder in the matching `.env.example`.

| File | Key settings |
| ---- | ------------ |
| `backend/.env` | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_*`, `CORS_ALLOWED_ORIGINS`, `USE_REAL_LLM`, `LLM_PROVIDER`, `*_API_KEY`, `*_MODEL`, `OPENAI_BASE_URL`, `MAX_PDF_UPLOAD_BYTES` |
| `frontend/.env.local` | `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`) |
| `prototype/.env` | `LLM_PROVIDER`, `*_API_KEY`, `*_MODEL`, `OPENAI_BASE_URL`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE` |

To turn on real LLM generation in the backend:

```env
USE_REAL_LLM=True
LLM_PROVIDER=openai        # openai | anthropic | gemini
OPENAI_API_KEY=your-key
```

## Testing

```bash
cd backend
python manage.py test study
```

The suite covers the offline generator (summaries, flashcards, quiz types, and
concept extraction). Django creates a temporary test database, so the configured
PostgreSQL user needs permission to create databases. The frontend has
`npm run lint`. There are no frontend or end-to-end tests yet.

## Project status

This is a working prototype and MVP, built as a personal project. Upload,
processing, and studying work end to end in both offline and LLM modes. It is not
production-ready: it has no authentication, processing is in-process, and test
coverage is limited to the offline generator. See the planned items above.
