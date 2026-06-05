"""Chunk-level summary generation."""

from __future__ import annotations

from typing import List

from .llm_client import LLMClient, load_prompt
from .models import Chunk, ChunkSummary

SYSTEM = "You are a precise, factual academic assistant. Always reply with valid JSON when asked."


def summarise_chunk(client: LLMClient, chunk: Chunk) -> ChunkSummary:
    template = load_prompt("summary")
    user = template.replace("{chunk}", chunk.text)
    data = client.complete_json(SYSTEM, user, cache_key_extra=f"summary:{chunk.chunk_id}")
    return ChunkSummary(
        chunk_id=chunk.chunk_id,
        summary_short=data.get("summary_short", ""),
        summary_long=data.get("summary_long", ""),
        takeaways=list(data.get("takeaways", [])),
    )


def summarise_chunks(client: LLMClient, chunks: List[Chunk]) -> List[ChunkSummary]:
    return [summarise_chunk(client, c) for c in chunks]
