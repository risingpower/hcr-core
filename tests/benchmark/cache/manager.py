"""Caching for benchmark evaluation: judge results and cross-encoder scores."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any


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


class CrossEncoderCache:
    """Pickle-based cache for cross-encoder scores, keyed by (query_hash, chunk_id)."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir) / "cross_encoder"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, float] = {}
        self._cache_file = self._cache_dir / "scores.pkl"
        if self._cache_file.exists():
            with open(self._cache_file, "rb") as f:
                self._cache = pickle.load(f)  # noqa: S301

    def _key(self, query_text: str, chunk_id: str) -> str:
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
        return f"{query_hash}_{chunk_id}"

    def _persist(self) -> None:
        with open(self._cache_file, "wb") as f:
            pickle.dump(self._cache, f)

    def save(self, query_text: str, chunk_id: str, score: float) -> None:
        self._cache[self._key(query_text, chunk_id)] = score
        self._persist()

    def save_batch(self, query_text: str, scores: dict[str, float]) -> None:
        for chunk_id, score in scores.items():
            self._cache[self._key(query_text, chunk_id)] = score
        self._persist()

    def load(self, query_text: str, chunk_id: str) -> float | None:
        return self._cache.get(self._key(query_text, chunk_id))
