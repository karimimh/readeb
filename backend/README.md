# readeb Backend — Django REST API

Production backend for the AI PDF Study Assistant. It reuses the validated
processing pipeline from `../prototype/study_assistant` (PDF extraction +
chunking + multi-provider LLM generation) and exposes it as a REST API.

## Stack

- Django 5 + Django REST Framework
- PostgreSQL (connection configured via `DB_*` variables)
- Reuses `prototype/study_assistant` for extraction, chunking and LLM calls
- Background processing via a daemon thread (no extra broker needed for dev)

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then edit as needed (DB_* must point at a running PostgreSQL)

python manage.py migrate
python manage.py runserver 8000
```

The API is now at http://localhost:8000/api/.

### Optional: create an admin user

```bash
python manage.py createsuperuser   # browse the DB at /admin/
```

## Generation modes

By default `USE_REAL_LLM=False`, so the backend uses a built-in **offline
generator** that derives study materials directly from the extracted text. This
makes the whole site work end-to-end with **no API keys and no token cost** —
ideal for demos and development.

To use real LLM generation (matching the prototype output quality):

```env
USE_REAL_LLM=True
LLM_PROVIDER=openai          # openai | anthropic | gemini
OPENAI_API_KEY=your-key
```

LLM responses are cached on disk (shared with the prototype's `cache/`), so
re-processing identical content costs nothing.

## API

Base URL: `/api`

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/health/` | Service health check |
| `GET`  | `/documents/` | List documents (paginated) |
| `POST` | `/documents/` | Upload a PDF (`multipart`: `file`, optional `title`). Processing starts automatically. |
| `GET`  | `/documents/{id}/` | Full detail incl. every generated asset |
| `DELETE` | `/documents/{id}/` | Delete a document and its assets |
| `POST` | `/documents/{id}/process/` | Re-run the pipeline |
| `GET`  | `/documents/{id}/status/` | Lightweight status poll |
| `GET`  | `/documents/{id}/summaries/` | Chunk summaries |
| `GET`  | `/documents/{id}/flashcards/` | Flashcards |
| `GET`  | `/documents/{id}/quiz/` | Quiz questions |
| `GET`  | `/documents/{id}/concepts/` | Concepts + definitions |
| `GET`  | `/documents/{id}/mindmap/` | Mind map tree |
| `GET`  | `/documents/{id}/audio/` | Audio lesson script |
| `GET`  | `/documents/{id}/notes/` | Study notes |

### Example

```bash
curl -F "file=@textbook.pdf" -F "title=Biology Ch.3" \
     http://localhost:8000/api/documents/

curl http://localhost:8000/api/documents/1/status/
```

## Project layout

```
backend/
├── config/            # Django project (settings, urls, wsgi/asgi)
├── study/
│   ├── models.py      # Document + generated-asset models
│   ├── serializers.py # DRF serializers
│   ├── views.py       # DocumentViewSet (upload, process, asset endpoints)
│   ├── pipeline.py    # Orchestrates extract → chunk → generate → persist
│   └── offline.py     # Deterministic offline generator (no API keys)
├── requirements.txt
└── .env.example
```

## Tests

```bash
python manage.py test study
```

Django creates a temporary test database, so the PostgreSQL user needs the
`CREATEDB` privilege.

## Production notes

- Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, and proper
  `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS`.
- Replace the threaded background processing with Celery + Redis for
  concurrency and durability.
- Serve uploaded media from object storage (e.g. S3).
