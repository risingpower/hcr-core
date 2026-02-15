"""Caching for cross-encoder scores and benchmark evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class CrossEncoderCache:
    """JSON-based cache for cross-encoder scores, keyed by (query_hash, chunk_id)."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir) / "cross_encoder"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, float] = {}
        self._cache_file = self._cache_dir / "scores.json"
        if self._cache_file.exists():
            self._cache = json.loads(self._cache_file.read_text())

    def _key(self, query_text: str, chunk_id: str) -> str:
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
        return f"{query_hash}_{chunk_id}"

    def _persist(self) -> None:
        self._cache_file.write_text(json.dumps(self._cache))

    def save(self, query_text: str, chunk_id: str, score: float) -> None:
        self._cache[self._key(query_text, chunk_id)] = score
        self._persist()

    def save_batch(self, query_text: str, scores: dict[str, float]) -> None:
        for chunk_id, score in scores.items():
            self._cache[self._key(query_text, chunk_id)] = score
        self._persist()

    def load(self, query_text: str, chunk_id: str) -> float | None:
        return self._cache.get(self._key(query_text, chunk_id))
