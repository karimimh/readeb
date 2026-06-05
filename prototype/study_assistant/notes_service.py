"""Condensed chapter / topic notes generation."""

from __future__ import annotations

from .llm_client import LLMClient, load_prompt

SYSTEM = "You write dense, exam-ready study notes in clean Markdown."


def generate_notes(client: LLMClient, topic: str, material: str, cache_tag: str = "notes") -> str:
    template = load_prompt("notes")
    user = template.replace("{topic}", topic).replace("{material}", material)
    return client.complete(SYSTEM, user, cache_key_extra=f"{cache_tag}:{topic}")
