"""Chunk embedding with sentence-transformers and caching."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from hcr_core.types.corpus import Chunk


class EmbeddingCache:
    """File-based cache for embeddings, keyed by corpus identifier."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def has(self, corpus_key: str) -> bool:
        return (self._cache_dir / f"{corpus_key}.npy").exists()

    def save(
        self,
        corpus_key: str,
        chunk_ids: list[str],
        embeddings: NDArray[np.float32],
    ) -> None:
        np.save(self._cache_dir / f"{corpus_key}.npy", embeddings)
        ids_path = self._cache_dir / f"{corpus_key}_ids.json"
        ids_path.write_text(json.dumps(chunk_ids))

    def load(
        self, corpus_key: str
    ) -> tuple[list[str], NDArray[np.float32]] | None:
        emb_path = self._cache_dir / f"{corpus_key}.npy"
        ids_path = self._cache_dir / f"{corpus_key}_ids.json"
        if not emb_path.exists() or not ids_path.exists():
            return None
        embeddings: NDArray[np.float32] = np.load(emb_path)
        chunk_ids: list[str] = json.loads(ids_path.read_text())
        return chunk_ids, embeddings


class ChunkEmbedder:
    """Embeds chunks using sentence-transformers with optional caching."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache: EmbeddingCache | None = None,
    ) -> None:
        self._model: SentenceTransformer = SentenceTransformer(model_name)
        self._cache = cache

    def embed(
        self,
        chunks: list[Chunk],
        corpus_key: str | None = None,
    ) -> tuple[list[str], NDArray[np.float32]]:
        """Embed chunks, returning (chunk_ids, embeddings) with L2 normalization."""
        if corpus_key and self._cache and self._cache.has(corpus_key):
            result = self._cache.load(corpus_key)
            if result is not None:
                return result

        chunk_ids = [c.id for c in chunks]
        texts = [c.content for c in chunks]
        raw: NDArray[np.float32] = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        embeddings = np.asarray(raw, dtype=np.float32)

        if corpus_key and self._cache:
            self._cache.save(corpus_key, chunk_ids, embeddings)

        return chunk_ids, embeddings

    def embed_text(self, text: str) -> NDArray[np.float32]:
        """Embed a single text string (e.g., a query), returning a 1D normalized vector."""
        raw: NDArray[np.float32] = self._model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(raw[0], dtype=np.float32)
