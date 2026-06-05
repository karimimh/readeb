"""Quiz generation (MCQ / true-false / short answer)."""

from __future__ import annotations

from typing import List

from .llm_client import LLMClient, load_prompt
from .models import Chunk, QuizQuestion, QuizSet

SYSTEM = "You are an exam writer producing fair, exam-quality questions in valid JSON."

_VALID_TYPES = {"mcq", "true_false", "short_answer"}


def generate_quiz(client: LLMClient, chunk: Chunk) -> QuizSet:
    template = load_prompt("quiz")
    user = template.replace("{chunk}", chunk.text)
    data = client.complete_json(SYSTEM, user, cache_key_extra=f"quiz:{chunk.chunk_id}")

    questions: List[QuizQuestion] = []
    for q in data.get("questions", []):
        qtype = str(q.get("type", "")).lower().strip()
        if qtype not in _VALID_TYPES:
            continue
        questions.append(
            QuizQuestion(
                question=str(q.get("question", "")).strip(),
                type=qtype,  # type: ignore[arg-type]
                options=[str(o) for o in q.get("options", [])],
                correct_answer=str(q.get("correct_answer", "")).strip(),
                explanation=str(q.get("explanation", "")).strip(),
            )
        )
    return QuizSet(chunk_id=chunk.chunk_id, questions=questions)


def generate_quizzes_for_chunks(client: LLMClient, chunks: List[Chunk]) -> List[QuizSet]:
    return [generate_quiz(client, c) for c in chunks]
