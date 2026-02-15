"""Caching for benchmark evaluation: judge results and cross-encoder scores."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from hcr_core.cache import CrossEncoderCache

__all__ = ["CrossEncoderCache", "JudgeCache"]


class JudgeCache:
    """JSON-based cache for LLM judge results, keyed by (query_id, chunk_ids)."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir) / "judge"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, query_id: str, chunk_ids: list[str]) -> str:
        ids_hash = hashlib.sha256(",".join(sorted(chunk_ids)).encode()).hexdigest()[:16]
        return f"{query_id}_{ids_hash}"

    def _path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def has(self, query_id: str, chunk_ids: list[str]) -> bool:
        return self._path(self._key(query_id, chunk_ids)).exists()

    def save(self, query_id: str, chunk_ids: list[str], result: dict[str, Any]) -> None:
        key = self._key(query_id, chunk_ids)
        self._path(key).write_text(json.dumps(result, indent=2))

    def load(self, query_id: str, chunk_ids: list[str]) -> dict[str, Any] | None:
        key = self._key(query_id, chunk_ids)
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text())  # type: ignore[no-any-return]
