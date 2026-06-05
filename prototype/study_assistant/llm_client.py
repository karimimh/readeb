"""Thin multi-provider LLM client with retry, caching, and JSON-mode helpers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from .cache import JSONCache


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from `prototype/prompts/<name>.txt`."""
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Any:
    """Best-effort: strip markdown fences and parse the first JSON object/array."""
    text = text.strip()
    m = _JSON_FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()
    # Find first {...} or [...] block.
    start = min(
        (i for i in (text.find("{"), text.find("[")) if i != -1),
        default=-1,
    )
    if start == -1:
        raise ValueError(f"No JSON found in model output:\n{text[:500]}")
    # Try to parse from start to end, then progressively trim.
    candidate = text[start:]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Try to locate matching closing brace by scanning.
        depth = 0
        opener = candidate[0]
        closer = "}" if opener == "{" else "]"
        for i, ch in enumerate(candidate):
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(candidate[: i + 1])
        raise


@dataclass
class LLMConfig:
    provider: str = "openai"           # openai | anthropic | gemini
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        model = {
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "gemini": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        }.get(provider)
        return cls(provider=provider, model=model)


class LLMClient:
    """Provider-agnostic chat client with optional response caching."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        cache: Optional[JSONCache] = None,
    ) -> None:
        self.config = config or LLMConfig.from_env()
        self.cache = cache

    # --- public API ---------------------------------------------------------

    def complete(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool = False,
        cache_key_extra: str = "",
    ) -> str:
        """Run a single-turn chat completion. Returns raw text."""
        if self.cache is not None:
            key = self.cache.make_key(
                self.config.provider,
                self.config.model or "",
                str(self.config.temperature),
                "json" if json_mode else "text",
                system,
                user,
                cache_key_extra,
            )
            cached = self.cache.get(key)
            if cached is not None and isinstance(cached, dict) and "text" in cached:
                return cached["text"]
        else:
            key = None

        text = self._call_with_retry(system, user, json_mode=json_mode)

        if self.cache is not None and key is not None:
            self.cache.set(key, {"text": text})

        return text

    def complete_json(self, system: str, user: str, *, cache_key_extra: str = "") -> Any:
        raw = self.complete(system, user, json_mode=True, cache_key_extra=cache_key_extra)
        return extract_json(raw)

    # --- internals ----------------------------------------------------------

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=20))
    def _call_with_retry(self, system: str, user: str, *, json_mode: bool) -> str:
        provider = self.config.provider
        if provider == "openai":
            return self._call_openai(system, user, json_mode=json_mode)
        if provider == "anthropic":
            return self._call_anthropic(system, user)
        if provider == "gemini":
            return self._call_gemini(system, user, json_mode=json_mode)
        raise ValueError(f"Unknown LLM provider: {provider}")

    def _call_openai(self, system: str, user: str, *, json_mode: bool) -> str:
        from openai import OpenAI

        base_url = os.getenv("OPENAI_BASE_URL")  # allows Groq / OpenRouter / etc.
        client = OpenAI(base_url=base_url) if base_url else OpenAI()
        kwargs: dict[str, Any] = dict(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def _call_anthropic(self, system: str, user: str) -> str:
        import anthropic

        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Concatenate text blocks.
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "".join(parts)

    def _call_gemini(self, system: str, user: str, *, json_mode: bool) -> str:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        generation_config: dict[str, Any] = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
        model = genai.GenerativeModel(
            model_name=self.config.model,
            system_instruction=system,
            generation_config=generation_config,
        )
        resp = model.generate_content(user)
        return resp.text or ""
