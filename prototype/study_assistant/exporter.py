"""Export helpers: JSON, Markdown, HTML, and statistics."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Iterable, List

from pydantic import BaseModel

from .models import (
    ChunkSummary,
    ConceptSet,
    FlashcardSet,
    QuizSet,
    Statistics,
)


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


# --- Generic JSON dump ------------------------------------------------------

def dump_json(obj: BaseModel | list | dict, path: str | Path) -> Path:
    path = Path(path)
    _ensure_dir(path.parent)
    if isinstance(obj, BaseModel):
        data = obj.model_dump()
    elif isinstance(obj, list) and obj and isinstance(obj[0], BaseModel):
        data = [o.model_dump() for o in obj]
    else:
        data = obj
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --- Markdown views ---------------------------------------------------------

def summaries_to_markdown(summaries: Iterable[ChunkSummary]) -> str:
    parts: List[str] = ["# Summaries\n"]
    for s in summaries:
        parts.append(f"## Chunk {s.chunk_id}\n")
        if s.summary_short:
            parts.append(f"**Short:** {s.summary_short}\n")
        if s.summary_long:
            parts.append(f"\n{s.summary_long}\n")
        if s.takeaways:
            parts.append("\n**Key takeaways**\n")
            parts.extend(f"- {t}" for t in s.takeaways)
            parts.append("")
    return "\n".join(parts).strip() + "\n"


def flashcards_to_markdown(sets: Iterable[FlashcardSet]) -> str:
    parts: List[str] = ["# Flashcards\n"]
    for fs in sets:
        parts.append(f"## Chunk {fs.chunk_id}\n")
        for i, card in enumerate(fs.flashcards, 1):
            parts.append(f"**Q{i}.** {card.question}\n\n*A.* {card.answer}\n")
    return "\n".join(parts).strip() + "\n"


def quizzes_to_markdown(sets: Iterable[QuizSet]) -> str:
    parts: List[str] = ["# Quizzes\n"]
    for qs in sets:
        parts.append(f"## Chunk {qs.chunk_id}\n")
        for i, q in enumerate(qs.questions, 1):
            parts.append(f"**{i}. ({q.type})** {q.question}")
            if q.options:
                parts.extend(f"  - {o}" for o in q.options)
            parts.append(f"  - _Answer:_ {q.correct_answer}")
            if q.explanation:
                parts.append(f"  - _Why:_ {q.explanation}")
            parts.append("")
    return "\n".join(parts).strip() + "\n"


def concepts_to_markdown(cs: ConceptSet) -> str:
    parts: List[str] = ["# Concepts & Definitions\n", "## Concepts\n"]
    for c in cs.concepts:
        parts.append(f"- **{c.name}** — {c.description}")
    parts.append("\n## Definitions\n")
    for d in cs.definitions:
        parts.append(f"- **{d.term}** — {d.definition}")
    return "\n".join(parts).strip() + "\n"


def write_text(text: str, path: str | Path) -> Path:
    path = Path(path)
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")
    return path


# --- HTML view --------------------------------------------------------------

_HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><title>{title}</title>
<style>
 body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#222}}
 h1,h2,h3{{color:#1a3a8a}} code{{background:#f3f3f3;padding:.1em .3em;border-radius:3px}}
 .card{{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:.75rem 0;background:#fafbff}}
 .q{{font-weight:600}}
</style></head><body>
{body}
</body></html>
"""


def html_report(title: str, sections: dict[str, str]) -> str:
    body_parts = [f"<h1>{escape(title)}</h1>"]
    for heading, html in sections.items():
        body_parts.append(f"<h2>{escape(heading)}</h2>")
        body_parts.append(html)
    return _HTML_TEMPLATE.format(title=escape(title), body="\n".join(body_parts))


# --- Stats ------------------------------------------------------------------

def build_statistics(
    n_pages: int,
    n_chunks: int,
    flashcard_sets: List[FlashcardSet],
    quiz_sets: List[QuizSet],
    merged_concepts: ConceptSet,
) -> Statistics:
    return Statistics(
        pages=n_pages,
        chunks=n_chunks,
        flashcards=sum(len(fs.flashcards) for fs in flashcard_sets),
        quiz_questions=sum(len(qs.questions) for qs in quiz_sets),
        concepts=len(merged_concepts.concepts),
        definitions=len(merged_concepts.definitions),
    )
