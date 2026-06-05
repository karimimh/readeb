"""Deterministic, offline study-material generator.

Used when no LLM provider is configured (``USE_REAL_LLM=False``). It produces
useful, fully-offline learning assets straight from the extracted text so the
website is demoable without spending API tokens. The shapes returned here match
exactly what the real LLM services in ``study_assistant`` return.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")

_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
    "which", "their", "they", "have", "has", "had", "but", "not", "you", "your",
    "can", "may", "will", "would", "could", "should", "these", "those", "such",
    "into", "than", "then", "them", "its", "his", "her", "our", "out", "use",
    "used", "using", "also", "each", "any", "all", "one", "two", "between",
    "when", "where", "what", "who", "how", "why", "because", "however",
    "therefore", "while", "about", "above", "below", "more", "most", "some",
    "other", "must", "very", "over", "under", "within",
}


def _sentences(text: str) -> List[str]:
    raw = _SENTENCE_RE.split(text.replace("\n", " "))
    return [s.strip() for s in raw if len(s.strip()) > 20]


def _keywords(text: str, limit: int = 12) -> List[str]:
    counts: Counter[str] = Counter()
    for token in _WORD_RE.findall(text):
        low = token.lower()
        if len(low) < 4 or low in _STOPWORDS:
            continue
        counts[low] += 1
    return [w for w, _ in counts.most_common(limit)]


def _proper_nouns(text: str, limit: int = 12) -> List[str]:
    """Pick capitalised multi-word phrases as candidate concept names."""
    candidates: Counter[str] = Counter()
    for match in re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text):
        phrase = match.strip()
        if phrase.lower() in _STOPWORDS or len(phrase) < 4:
            continue
        candidates[phrase] += 1
    ranked = [p for p, _ in candidates.most_common(limit * 2)]
    if len(ranked) < limit:
        ranked += [k.title() for k in _keywords(text, limit)]
    # De-duplicate preserving order.
    seen: set[str] = set()
    out: List[str] = []
    for p in ranked:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
        if len(out) >= limit:
            break
    return out


# --- Public generation functions -------------------------------------------

def summarise(chunk_id: int, text: str) -> Dict[str, Any]:
    sents = _sentences(text)
    short = " ".join(sents[:2]) if sents else text[:200]
    long_sents = sents[: min(8, len(sents))]
    long = " ".join(long_sents)
    takeaways = [s for s in sents[:5]] if sents else []
    return {
        "chunk_id": chunk_id,
        "summary_short": short[:400],
        "summary_long": long,
        "takeaways": takeaways,
    }


def flashcards(chunk_id: int, text: str) -> Dict[str, Any]:
    cards: List[Dict[str, str]] = []
    keys = _proper_nouns(text, 6)
    sents = _sentences(text)
    for key in keys:
        # Find a sentence that mentions the key term to act as the answer.
        answer = next((s for s in sents if key.lower() in s.lower()), "")
        if not answer:
            continue
        cards.append(
            {
                "question": f"What is the significance of \u201c{key}\u201d in this material?",
                "answer": answer,
            }
        )
        if len(cards) >= 5:
            break
    if not cards and sents:
        for s in sents[:3]:
            cards.append({"question": f"Explain: {s[:60]}...", "answer": s})
    return {"chunk_id": chunk_id, "flashcards": cards}


def quiz(chunk_id: int, text: str) -> Dict[str, Any]:
    sents = _sentences(text)
    keys = _proper_nouns(text, 8)
    questions: List[Dict[str, Any]] = []

    # True/false from a factual sentence.
    if sents:
        questions.append(
            {
                "question": f"True or False: {sents[0]}",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "This statement is taken directly from the material.",
            }
        )

    # MCQ asking which key term is covered.
    if len(keys) >= 4:
        correct = keys[0]
        distractors = keys[1:4]
        options = [correct, *distractors]
        questions.append(
            {
                "question": "Which of the following key terms is discussed in this section?",
                "type": "mcq",
                "options": options,
                "correct_answer": correct,
                "explanation": f"\u201c{correct}\u201d appears in the material.",
            }
        )

    # Short answer.
    if len(sents) > 1:
        questions.append(
            {
                "question": "In one sentence, summarise the main idea of this section.",
                "type": "short_answer",
                "options": [],
                "correct_answer": sents[0],
                "explanation": "Any answer capturing this idea is acceptable.",
            }
        )
    return {"chunk_id": chunk_id, "questions": questions}


def concepts(chunk_id: int, text: str) -> Dict[str, Any]:
    sents = _sentences(text)
    names = _proper_nouns(text, 8)
    concept_list: List[Dict[str, str]] = []
    for name in names:
        desc = next((s for s in sents if name.lower() in s.lower()), "")
        concept_list.append({"name": name, "description": desc})

    definitions: List[Dict[str, str]] = []
    for s in sents:
        m = re.match(r"^([A-Z][\w\s\-]{2,40}?)\s+(?:is|are|refers to|means)\s+(.+)", s)
        if m:
            definitions.append({"term": m.group(1).strip(), "definition": s})
        if len(definitions) >= 8:
            break
    return {"chunk_id": chunk_id, "concepts": concept_list, "definitions": definitions}


def mindmap(title: str, chunk_topics: List[str], material: str) -> Dict[str, Any]:
    keys = _proper_nouns(material, 9)
    # Distribute key terms under a few grouped branches.
    branches: List[Dict[str, Any]] = []
    group_size = 3
    for i, topic in enumerate(chunk_topics[:4] or ["Key Topics"]):
        children = [
            {"root": k, "children": []}
            for k in keys[i * group_size : (i + 1) * group_size]
        ]
        branches.append({"root": topic, "children": children})
    return {"root": title or "Study Map", "children": branches}


def audio_script(title: str, sections: List[str]) -> str:
    parts = [f"# Audio Lesson: {title}\n", "Welcome to this study session. "]
    for i, section in enumerate(sections, 1):
        sents = _sentences(section)
        intro = " ".join(sents[:3])
        parts.append(f"\n## Part {i}\n\n{intro}\n")
    parts.append("\nThat concludes this lesson. Review the key terms and try the quiz.\n")
    return "\n".join(parts)


def notes(topic: str, material: str) -> str:
    sents = _sentences(material)
    keys = _proper_nouns(material, 8)
    lines = [f"# {topic}", "", "## Important Concepts"]
    lines += [f"- {s}" for s in sents[:5]] or ["- (no content extracted)"]
    lines += ["", "## Definitions"]
    for k in keys[:6]:
        desc = next((s for s in sents if k.lower() in s.lower()), "")
        lines.append(f"- **{k}** \u2014 {desc}")
    lines += ["", "## Quick Revision Sheet"]
    lines += [f"- {k}" for k in keys[:8]]
    return "\n".join(lines)
