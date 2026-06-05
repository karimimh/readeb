"""End-to-end processing pipeline: PDF -> study assets, persisted to the DB.

Extraction and chunking always reuse the validated ``study_assistant`` package.
Generation uses the real multi-provider LLM client when ``USE_REAL_LLM`` is set
and an API key is available; otherwise it falls back to the deterministic
offline generator so the website works end-to-end without credentials.
"""

from __future__ import annotations

import logging
import threading
from typing import List

from django.conf import settings
from django.utils import timezone

from . import offline
from .models import (
    AudioScript,
    Concept,
    Definition,
    Document,
    Flashcard,
    MindMap,
    Notes,
    QuizQuestion,
    Summary,
)

logger = logging.getLogger(__name__)

# Cap how much material is sent to the whole-document generators (mindmap,
# audio, notes) to keep prompts within a reasonable size.
_MAX_OVERVIEW_WORDS = 6000


def process_document_async(document_id: int) -> None:
    """Run :func:`process_document` in a background daemon thread."""
    thread = threading.Thread(
        target=process_document, args=(document_id,), daemon=True
    )
    thread.start()


def process_document(document_id: int) -> None:
    """Process a single document: extract, chunk, generate, persist."""
    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s no longer exists; skipping.", document_id)
        return

    document.status = Document.Status.PROCESSING
    document.error = ""
    document.save(update_fields=["status", "error", "updated_at"])

    try:
        _run_pipeline(document)
        document.status = Document.Status.COMPLETED
        document.processed_at = timezone.now()
        document.error = ""
        document.save(update_fields=["status", "processed_at", "error", "updated_at"])
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        logger.exception("Processing failed for document %s", document_id)
        document.status = Document.Status.FAILED
        document.error = f"{type(exc).__name__}: {exc}"
        document.save(update_fields=["status", "error", "updated_at"])


# --- Internal helpers -------------------------------------------------------

def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _use_real_llm() -> bool:
    if not settings.USE_REAL_LLM:
        return False
    import os

    provider = settings.LLM_PROVIDER.lower()
    key_var = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider)
    return bool(key_var and os.getenv(key_var))


def _run_pipeline(document: Document) -> None:
    from study_assistant.chunker import chunk_extracted_pdf
    from study_assistant.pdf_extractor import extract_pdf_text

    # Start clean on re-runs.
    document.reset_assets()

    extracted = extract_pdf_text(document.file.path)
    chunks = chunk_extracted_pdf(extracted)

    if _use_real_llm():
        _generate_with_llm(document, chunks)
    else:
        _generate_offline(document, chunks)

    n_flashcards = document.flashcards.count()
    n_quiz = document.quiz_questions.count()
    document.statistics = {
        "pages": len(extracted.pages),
        "chunks": len(chunks),
        "flashcards": n_flashcards,
        "quiz_questions": n_quiz,
        "concepts": document.concepts.count(),
        "definitions": document.definitions.count(),
        "mode": "llm" if _use_real_llm() else "offline",
    }
    document.save(update_fields=["statistics", "updated_at"])


def _chunk_topic(text: str) -> str:
    head = offline._proper_nouns(text, 1)
    return head[0] if head else "Section"


def _generate_offline(document: Document, chunks) -> None:
    overview_parts: List[str] = []
    chunk_topics: List[str] = []

    for chunk in chunks:
        text = chunk.text
        overview_parts.append(text)
        chunk_topics.append(_chunk_topic(text))

        s = offline.summarise(chunk.chunk_id, text)
        Summary.objects.create(
            document=document,
            chunk_id=s["chunk_id"],
            summary_short=s["summary_short"],
            summary_long=s["summary_long"],
            takeaways=s["takeaways"],
        )

        fc = offline.flashcards(chunk.chunk_id, text)
        Flashcard.objects.bulk_create(
            Flashcard(
                document=document,
                chunk_id=fc["chunk_id"],
                question=c["question"],
                answer=c["answer"],
            )
            for c in fc["flashcards"]
        )

        qz = offline.quiz(chunk.chunk_id, text)
        QuizQuestion.objects.bulk_create(
            QuizQuestion(
                document=document,
                chunk_id=qz["chunk_id"],
                question=q["question"],
                type=q["type"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
            )
            for q in qz["questions"]
        )

        co = offline.concepts(chunk.chunk_id, text)
        _persist_concepts(document, co)

    overview = _truncate_words("\n\n".join(overview_parts), _MAX_OVERVIEW_WORDS)
    _dedupe_concepts(document)

    MindMap.objects.update_or_create(
        document=document,
        defaults={"data": offline.mindmap(document.title, chunk_topics, overview)},
    )
    AudioScript.objects.update_or_create(
        document=document,
        defaults={"content": offline.audio_script(document.title, overview_parts)},
    )
    Notes.objects.create(
        document=document,
        topic=document.title,
        content=offline.notes(document.title, overview),
    )


def _generate_with_llm(document: Document, chunks) -> None:
    from study_assistant.cache import JSONCache
    from study_assistant.concept_service import extract_concepts, merge_concepts
    from study_assistant.flashcard_service import generate_flashcards
    from study_assistant.llm_client import LLMClient, LLMConfig
    from study_assistant.mindmap_service import generate_mindmap
    from study_assistant.audio_service import generate_audio_script
    from study_assistant.notes_service import generate_notes
    from study_assistant.quiz_service import generate_quiz
    from study_assistant.summary_service import summarise_chunk

    # Ensure the LLM client reads prompts/cache from the configured locations.
    import study_assistant.llm_client as llm_module

    llm_module.PROMPTS_DIR = settings.PROMPTS_DIR

    cache = JSONCache(settings.LLM_CACHE_DIR)
    client = LLMClient(config=LLMConfig.from_env(), cache=cache)

    overview_parts: List[str] = []
    chunk_topics: List[str] = []
    concept_sets = []

    for chunk in chunks:
        overview_parts.append(chunk.text)
        chunk_topics.append(_chunk_topic(chunk.text))

        s = summarise_chunk(client, chunk)
        Summary.objects.create(
            document=document,
            chunk_id=s.chunk_id,
            summary_short=s.summary_short,
            summary_long=s.summary_long,
            takeaways=s.takeaways,
        )

        fc = generate_flashcards(client, chunk)
        Flashcard.objects.bulk_create(
            Flashcard(
                document=document,
                chunk_id=fc.chunk_id,
                question=card.question,
                answer=card.answer,
            )
            for card in fc.flashcards
        )

        qz = generate_quiz(client, chunk)
        QuizQuestion.objects.bulk_create(
            QuizQuestion(
                document=document,
                chunk_id=qz.chunk_id,
                question=q.question,
                type=q.type,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
            )
            for q in qz.questions
        )

        cs = extract_concepts(client, chunk)
        concept_sets.append(cs)

    merged = merge_concepts(concept_sets)
    Concept.objects.bulk_create(
        Concept(document=document, name=c.name, description=c.description)
        for c in merged.concepts
    )
    Definition.objects.bulk_create(
        Definition(document=document, term=d.term, definition=d.definition)
        for d in merged.definitions
    )

    overview = _truncate_words("\n\n".join(overview_parts), _MAX_OVERVIEW_WORDS)

    mindmap_node = generate_mindmap(client, overview)
    MindMap.objects.update_or_create(
        document=document, defaults={"data": mindmap_node.model_dump()}
    )

    script = generate_audio_script(client, overview)
    AudioScript.objects.update_or_create(
        document=document, defaults={"content": script}
    )

    note_md = generate_notes(client, document.title, overview)
    Notes.objects.create(document=document, topic=document.title, content=note_md)


def _persist_concepts(document: Document, concept_data) -> None:
    Concept.objects.bulk_create(
        Concept(document=document, name=c["name"], description=c["description"])
        for c in concept_data["concepts"]
        if c["name"]
    )
    Definition.objects.bulk_create(
        Definition(document=document, term=d["term"], definition=d["definition"])
        for d in concept_data["definitions"]
        if d["term"]
    )


def _dedupe_concepts(document: Document) -> None:
    """Collapse duplicate concept/definition rows produced per-chunk."""
    seen_concepts: set[str] = set()
    for concept in document.concepts.all():
        key = concept.name.strip().lower()
        if key in seen_concepts:
            concept.delete()
        else:
            seen_concepts.add(key)

    seen_terms: set[str] = set()
    for definition in document.definitions.all():
        key = definition.term.strip().lower()
        if key in seen_terms:
            definition.delete()
        else:
            seen_terms.add(key)
