# AI PDF Study Assistant - Research & Prototype Notebook

## Goal

Build a Jupyter Notebook prototype that can take a university textbook PDF as input and generate learning materials automatically.

This notebook is intended as the first validation phase before building the production backend with Django REST Framework and a React frontend.

The notebook should focus entirely on content extraction, chunking, AI processing, and educational content generation.

---

# Main Features

Given a PDF textbook, generate:

1. Chapter Summaries
2. Section Summaries
3. Flashcards (Q&A)
4. Multiple Choice Quizzes
5. Audio Lesson Scripts
6. Mind Maps
7. Key Concepts
8. Important Definitions
9. Study Notes

---

# High-Level Pipeline

PDF
↓
Text Extraction
↓
Cleaning
↓
Chunking
↓
AI Processing
↓
Generate Learning Assets
↓
Export Results

---

# Tech Stack

Python 3.12+

Recommended Libraries:

PDF Processing:
- pymupdf (fitz)
- pdfplumber

AI:
- OpenAI API
- Anthropic API
- Gemini API

Data Models:
- pydantic

Notebook:
- jupyter

Visualization:
- graphviz
- networkx
- matplotlib

Audio:
- OpenAI TTS
or
- ElevenLabs

Exports:
- markdown
- json
- html

---

# Notebook Objectives

The notebook should answer:

Can we reliably convert textbook PDFs into engaging study materials?

The notebook should be designed so that every generation step can be inspected individually.

---

# Folder Structure

prototype/

├── notebooks/
│   └── pdf_study_assistant.ipynb
│
├── sample_pdfs/
│   └── textbook.pdf
│
├── outputs/
│   ├── summaries/
│   ├── flashcards/
│   ├── quizzes/
│   ├── mindmaps/
│   ├── audio_scripts/
│   └── json/
│
├── prompts/
│   ├── summary.txt
│   ├── flashcards.txt
│   ├── quiz.txt
│   ├── mindmap.txt
│   └── audio_lesson.txt
│
└── requirements.txt

---

# Phase 1: PDF Extraction

Requirements:

Create a reusable function:

extract_pdf_text(pdf_path)

Output:

{
  "pages": [
    {
      "page_number": 1,
      "text": "..."
    }
  ]
}

Requirements:

- Preserve page numbers
- Remove headers
- Remove footers
- Remove duplicate whitespace
- Preserve section titles when possible

---

# Phase 2: Chunking

Create:

chunk_text(text)

Goals:

- Chunks between 1000 and 2000 words
- Overlap between chunks
- Preserve semantic boundaries

Output:

[
  {
    "chunk_id": 1,
    "text": "..."
  }
]

---

# Phase 3: Generate Summary

For each chunk:

Generate:

- concise summary
- detailed summary
- key takeaways

Output Schema:

{
  "chunk_id": 1,
  "summary_short": "",
  "summary_long": "",
  "takeaways": []
}

Prompt Requirements:

- Educational tone
- Preserve factual accuracy
- Avoid hallucinations
- Focus on exam-relevant information

---

# Phase 4: Generate Flashcards

For each chunk:

Generate:

10-20 flashcards

Output Schema:

{
  "question": "",
  "answer": ""
}

Requirements:

- Focus on concepts
- Focus on definitions
- Focus on formulas
- Avoid trivial facts

---

# Phase 5: Generate Quiz Questions

Generate:

- Multiple Choice Questions
- True/False Questions
- Short Answer Questions

Output Schema:

{
  "question": "",
  "type": "mcq",
  "options": [],
  "correct_answer": "",
  "explanation": ""
}

Requirements:

- Exam-oriented
- Medium difficulty
- Include explanations

---

# Phase 6: Key Concepts Extraction

Generate:

{
  "concepts": [
    {
      "name": "",
      "description": ""
    }
  ]
}

Requirements:

- Extract major topics
- Remove duplicates
- Merge similar concepts

---

# Phase 7: Mind Map Generation

Generate hierarchical structure:

{
  "root": "",
  "children": []
}

Example:

Machine Learning
├── Supervised Learning
├── Unsupervised Learning
└── Reinforcement Learning

Requirements:

- Produce JSON
- Visualize using graphviz
- Save PNG output

---

# Phase 8: Audio Lesson Script

Generate:

10-15 minute spoken lesson

Requirements:

- Conversational style
- Explain concepts simply
- Include examples
- Include recap section

Output:

audio_script.md

Optional:

Convert script to speech using TTS.

---

# Phase 9: Chapter Notes

Generate condensed study notes:

Output:

# Topic

## Important Concepts

## Definitions

## Examples

## Common Exam Questions

## Quick Revision Sheet

---

# Data Models

Use Pydantic models for all outputs.

Example:

class Flashcard(BaseModel):
    question: str
    answer: str

class QuizQuestion(BaseModel):
    question: str
    type: str
    options: list[str]
    correct_answer: str
    explanation: str

---

# Caching

Implement local caching.

Store all LLM responses:

cache/

Purpose:

- Reduce API costs
- Avoid reprocessing

Cache key:

hash(prompt + chunk)

---

# Evaluation Metrics

For every PDF processed, generate:

statistics.json

{
  "pages": 0,
  "chunks": 0,
  "flashcards": 0,
  "quiz_questions": 0,
  "concepts": 0
}

---

# Notebook Sections

1. Setup
2. Load PDF
3. Extract Text
4. Chunk Text
5. Generate Summaries
6. Generate Flashcards
7. Generate Quizzes
8. Extract Concepts
9. Generate Mind Map
10. Generate Audio Script
11. Export Results
12. Evaluation

---

# Future Django Backend Design

The notebook code should be written in a modular way so it can later be moved into Django services.

Target structure:

backend/

study_assistant/

services/

- pdf_extractor.py
- chunker.py
- summary_service.py
- flashcard_service.py
- quiz_service.py
- concept_service.py
- mindmap_service.py
- audio_service.py

The notebook should avoid notebook-specific logic where possible and instead implement reusable classes and functions.

---

# Stretch Goals

If time permits:

1. Generate Anki decks (.apkg)
2. Generate spaced repetition schedules
3. Generate chapter timelines
4. Generate infographic content
5. Generate "teach me like I'm 12" explanations
6. Generate professor-style lecture notes
7. Generate podcast-style discussion scripts
8. Generate interactive learning paths

---

# Success Criteria

The notebook is considered successful if:

- A 100+ page textbook can be processed.
- Summaries are coherent.
- Flashcards are useful for revision.
- Quiz questions are answerable from the text.
- Mind maps correctly represent topic relationships.
- Audio scripts sound like mini lectures.
- All outputs can later be integrated into a Django REST API backend.