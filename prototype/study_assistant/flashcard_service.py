"""Flashcard generation."""

from __future__ import annotations

from typing import List

from .llm_client import LLMClient, load_prompt
from .models import Chunk, Flashcard, FlashcardSet

SYSTEM = "You are an expert tutor producing high-quality flashcards in valid JSON."


def generate_flashcards(client: LLMClient, chunk: Chunk) -> FlashcardSet:
    template = load_prompt("flashcards")
    user = template.replace("{chunk}", chunk.text)
    data = client.complete_json(SYSTEM, user, cache_key_extra=f"flashcards:{chunk.chunk_id}")
    cards = [
        Flashcard(question=str(c.get("question", "")).strip(), answer=str(c.get("answer", "")).strip())
        for c in data.get("flashcards", [])
        if c.get("question") and c.get("answer")
    ]
    return FlashcardSet(chunk_id=chunk.chunk_id, flashcards=cards)


def generate_flashcards_for_chunks(client: LLMClient, chunks: List[Chunk]) -> List[FlashcardSet]:
    return [generate_flashcards(client, c) for c in chunks]
