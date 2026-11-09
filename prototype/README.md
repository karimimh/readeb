# Prototype — AI PDF Study Assistant

End-to-end notebook prototype that turns a university textbook PDF into
summaries, flashcards, quizzes, concept lists, mind maps, audio scripts,
and study notes.

## Quick start

```bash
cd prototype
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set LLM_PROVIDER and at least one *_API_KEY

# Drop a textbook PDF into sample_pdfs/, then:
jupyter lab notebooks/pdf_study_assistant.ipynb
```

Open the notebook and run the cells top-to-bottom. The first cell installs
the dependencies into the kernel (restart the kernel afterwards). Set
`PDF_NAME` in the "Load PDF" cell to the file you placed in `sample_pdfs/`.

## Layout

```
prototype/
├── notebooks/pdf_study_assistant.ipynb   # Main interactive pipeline
├── study_assistant/                      # Reusable services (future Django backend)
│   ├── pdf_extractor.py
│   ├── chunker.py
│   ├── llm_client.py
│   ├── summary_service.py
│   ├── flashcard_service.py
│   ├── quiz_service.py
│   ├── concept_service.py
│   ├── mindmap_service.py
│   ├── audio_service.py
│   ├── notes_service.py
│   ├── exporter.py
│   ├── cache.py
│   └── models.py
├── prompts/                              # Editable prompt templates
├── sample_pdfs/                          # Drop test PDFs here (git-ignored)
├── outputs/                              # Generated assets per run (git-ignored)
└── requirements.txt
```

## Notes

- **Caching:** every LLM call is cached on disk at `cache/<sha256>.json`,
  keyed by provider, model, temperature, and prompt content. Re-running a
  cell costs nothing if inputs are unchanged.
- **Providers:** `LLM_PROVIDER=openai|anthropic|gemini`. Only the SDK
  for the chosen provider needs valid credentials.
- **Graphviz:** the mind map renderer requires the `graphviz` system
  binary (`brew install graphviz` on macOS).
- **TTS:** audio synthesis is optional. Set `SYNTHESIZE_AUDIO = True` in the
  audio cell to render the lesson to MP3 with OpenAI's `audio.speech`
  endpoint (`OPENAI_TTS_MODEL` / `OPENAI_TTS_VOICE`).
