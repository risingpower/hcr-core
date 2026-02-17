"""Chunk embedding with sentence-transformers and caching."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from hcr_core.types.corpus import Chunk

logger = logging.getLogger(__name__)


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
        model_name: str = "all-mpnet-base-v2",
        cache: EmbeddingCache | None = None,
    ) -> None:
        self._model: SentenceTransformer = SentenceTransformer(model_name)
        self._cache = cache

    def embed(
        self,
        chunks: list[Chunk],
        corpus_key: str | None = None,
        batch_size: int = 256,
        show_progress: bool = False,
    ) -> tuple[list[str], NDArray[np.float32]]:
        """Embed chunks, returning (chunk_ids, embeddings) with L2 normalization.

        Args:
            chunks: Chunks to embed.
            corpus_key: Cache key. If set and cached, returns cached result.
            batch_size: Batch size for encoding. Larger = faster but more memory.
            show_progress: Show tqdm progress bar (useful for large corpora).
        """
        if corpus_key and self._cache and self._cache.has(corpus_key):
            result = self._cache.load(corpus_key)
            if result is not None:
                return result

        chunk_ids = [c.id for c in chunks]
        texts = [c.content for c in chunks]

        if show_progress and len(chunks) > batch_size:
            embeddings = self._embed_batched(texts, batch_size)
        else:
            raw: NDArray[np.float32] = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            embeddings = np.asarray(raw, dtype=np.float32)

        if corpus_key and self._cache:
            self._cache.save(corpus_key, chunk_ids, embeddings)

        return chunk_ids, embeddings

    def _embed_batched(
        self,
        texts: list[str],
        batch_size: int,
    ) -> NDArray[np.float32]:
        """Embed texts in batches with tqdm progress bar."""
        from tqdm import tqdm

        all_embeddings: list[NDArray[np.float32]] = []
        total = len(texts)

        with tqdm(total=total, desc="Embedding chunks", unit="chunk") as pbar:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                batch = texts[start:end]
                raw: NDArray[np.float32] = self._model.encode(
                    batch, normalize_embeddings=True, show_progress_bar=False
                )
                all_embeddings.append(np.asarray(raw, dtype=np.float32))
                pbar.update(len(batch))

        return np.vstack(all_embeddings)

    def embed_text(self, text: str) -> NDArray[np.float32]:
        """Embed a single text string (e.g., a query), returning a 1D normalized vector."""
        raw: NDArray[np.float32] = self._model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(raw[0], dtype=np.float32)
