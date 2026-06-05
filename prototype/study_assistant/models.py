"""Pydantic data models shared across services."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# --- PDF extraction ---------------------------------------------------------

class Page(BaseModel):
    page_number: int
    text: str


class ExtractedPDF(BaseModel):
    source_path: str
    pages: List[Page] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


# --- Chunking ---------------------------------------------------------------

class Chunk(BaseModel):
    chunk_id: int
    text: str
    word_count: int = 0
    start_page: Optional[int] = None
    end_page: Optional[int] = None


# --- Summaries --------------------------------------------------------------

class ChunkSummary(BaseModel):
    chunk_id: int
    summary_short: str = ""
    summary_long: str = ""
    takeaways: List[str] = Field(default_factory=list)


# --- Flashcards -------------------------------------------------------------

class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardSet(BaseModel):
    chunk_id: int
    flashcards: List[Flashcard] = Field(default_factory=list)


# --- Quiz -------------------------------------------------------------------

QuestionType = Literal["mcq", "true_false", "short_answer"]


class QuizQuestion(BaseModel):
    question: str
    type: QuestionType
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str = ""


class QuizSet(BaseModel):
    chunk_id: int
    questions: List[QuizQuestion] = Field(default_factory=list)


# --- Concepts ---------------------------------------------------------------

class Concept(BaseModel):
    name: str
    description: str = ""


class Definition(BaseModel):
    term: str
    definition: str


class ConceptSet(BaseModel):
    chunk_id: Optional[int] = None
    concepts: List[Concept] = Field(default_factory=list)
    definitions: List[Definition] = Field(default_factory=list)


# --- Mind map ---------------------------------------------------------------

class MindMapNode(BaseModel):
    root: str
    children: List["MindMapNode"] = Field(default_factory=list)


MindMapNode.model_rebuild()


# --- Stats ------------------------------------------------------------------

class Statistics(BaseModel):
    pages: int = 0
    chunks: int = 0
    flashcards: int = 0
    quiz_questions: int = 0
    concepts: int = 0
    definitions: int = 0
