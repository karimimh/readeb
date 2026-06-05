"""Key-concept and definition extraction with simple cross-chunk merging."""

from __future__ import annotations

import re
from typing import Iterable, List

from .llm_client import LLMClient, load_prompt
from .models import Chunk, Concept, ConceptSet, Definition

SYSTEM = "You are a meticulous concept extractor. Always respond in valid JSON."


def extract_concepts(client: LLMClient, chunk: Chunk) -> ConceptSet:
    template = load_prompt("concepts")
    user = template.replace("{chunk}", chunk.text)
    data = client.complete_json(SYSTEM, user, cache_key_extra=f"concepts:{chunk.chunk_id}")
    concepts = [
        Concept(name=str(c.get("name", "")).strip(), description=str(c.get("description", "")).strip())
        for c in data.get("concepts", [])
        if c.get("name")
    ]
    definitions = [
        Definition(term=str(d.get("term", "")).strip(), definition=str(d.get("definition", "")).strip())
        for d in data.get("definitions", [])
        if d.get("term") and d.get("definition")
    ]
    return ConceptSet(chunk_id=chunk.chunk_id, concepts=concepts, definitions=definitions)


def extract_concepts_for_chunks(client: LLMClient, chunks: List[Chunk]) -> List[ConceptSet]:
    return [extract_concepts(client, c) for c in chunks]


# --- Merging across chunks --------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip().rstrip(".,;:"))


def merge_concepts(sets: Iterable[ConceptSet]) -> ConceptSet:
    seen_concepts: dict[str, Concept] = {}
    seen_defs: dict[str, Definition] = {}

    for s in sets:
        for c in s.concepts:
            key = _norm(c.name)
            if not key:
                continue
            if key not in seen_concepts:
                seen_concepts[key] = c
            elif len(c.description) > len(seen_concepts[key].description):
                seen_concepts[key] = c
        for d in s.definitions:
            key = _norm(d.term)
            if not key:
                continue
            if key not in seen_defs:
                seen_defs[key] = d
            elif len(d.definition) > len(seen_defs[key].definition):
                seen_defs[key] = d

    return ConceptSet(
        chunk_id=None,
        concepts=sorted(seen_concepts.values(), key=lambda c: c.name.lower()),
        definitions=sorted(seen_defs.values(), key=lambda d: d.term.lower()),
    )
