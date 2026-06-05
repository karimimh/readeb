"""Simple on-disk JSON cache keyed by SHA-256(prompt + payload)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


class JSONCache:
    def __init__(self, cache_dir: str | Path = "cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(*parts: str) -> str:
        h = hashlib.sha256()
        for p in parts:
            h.update(p.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any) -> None:
        self._path(key).write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def has(self, key: str) -> bool:
        return self._path(key).exists()
