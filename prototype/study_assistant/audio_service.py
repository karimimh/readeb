"""Audio lesson script generation and optional TTS synthesis."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .llm_client import LLMClient, load_prompt

SYSTEM = "You are an engaging university lecturer writing audio scripts in clear Markdown."


def generate_audio_script(client: LLMClient, material: str, cache_tag: str = "audio") -> str:
    template = load_prompt("audio_lesson")
    user = template.replace("{material}", material)
    return client.complete(SYSTEM, user, cache_key_extra=cache_tag)


def script_to_speech_openai(
    script: str,
    output_path: str | Path,
    model: Optional[str] = None,
    voice: Optional[str] = None,
) -> Path:
    """Synthesize the script to an mp3 using the OpenAI TTS API."""
    from openai import OpenAI

    model = model or os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = voice or os.getenv("OPENAI_TTS_VOICE", "alloy")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=script,
    ) as response:
        response.stream_to_file(str(output_path))
    return output_path
