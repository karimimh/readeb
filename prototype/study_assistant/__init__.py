"""Reusable services for the AI PDF Study Assistant prototype.

Designed so each module can later be lifted into a Django service
(`backend/study_assistant/services/*.py`) with minimal changes.
"""

from .models import (
    Page,
    ExtractedPDF,
    Chunk,
    ChunkSummary,
    Flashcard,
    FlashcardSet,
    QuizQuestion,
    QuizSet,
    Concept,
    Definition,
    ConceptSet,
    MindMapNode,
    Statistics,
)

__all__ = [
    "Page",
    "ExtractedPDF",
    "Chunk",
    "ChunkSummary",
    "Flashcard",
    "FlashcardSet",
    "QuizQuestion",
    "QuizSet",
    "Concept",
    "Definition",
    "ConceptSet",
    "MindMapNode",
    "Statistics",
]
