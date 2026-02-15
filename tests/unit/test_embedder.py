"""Tests for chunk embedding."""

from pathlib import Path

import numpy as np

from hcr_core.corpus.embedder import ChunkEmbedder, EmbeddingCache
from hcr_core.types.corpus import Chunk


def _make_chunk(chunk_id: str, content: str) -> Chunk:
    return Chunk(id=chunk_id, document_id="doc-1", content=content, token_count=10)


class TestEmbeddingCache:
    def test_save_and_load(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        embeddings = np.random.rand(5, 384).astype(np.float32)
        chunk_ids = [f"c-{i}" for i in range(5)]
        cache.save("test-corpus", chunk_ids, embeddings)

        loaded_ids, loaded_embs = cache.load("test-corpus")
        assert loaded_ids == chunk_ids
        np.testing.assert_array_almost_equal(loaded_embs, embeddings)

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        result = cache.load("nonexistent")
        assert result is None

    def test_has_cache(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        assert not cache.has("test")
        embeddings = np.random.rand(3, 384).astype(np.float32)
        cache.save("test", ["a", "b", "c"], embeddings)
        assert cache.has("test")


class TestChunkEmbedder:
    def test_embed_chunks_returns_correct_shape(self) -> None:
        embedder = ChunkEmbedder(model_name="all-MiniLM-L6-v2")
        chunks = [
            _make_chunk("c1", "Hello world"),
            _make_chunk("c2", "Another sentence"),
        ]
        chunk_ids, embeddings = embedder.embed(chunks)
        assert len(chunk_ids) == 2
        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] > 0  # embedding dimension

    def test_embed_returns_normalized_vectors(self) -> None:
        embedder = ChunkEmbedder(model_name="all-MiniLM-L6-v2")
        chunks = [_make_chunk("c1", "Test normalization")]
        _, embeddings = embedder.embed(chunks)
        norms = np.linalg.norm(embeddings, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)

    def test_embed_single_text(self) -> None:
        embedder = ChunkEmbedder(model_name="all-MiniLM-L6-v2")
        emb = embedder.embed_text("test query")
        assert emb.ndim == 1
        assert len(emb) > 0
        norm = float(np.linalg.norm(emb))
        assert abs(norm - 1.0) < 1e-5

    def test_embed_with_cache(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        embedder = ChunkEmbedder(model_name="all-MiniLM-L6-v2", cache=cache)
        chunks = [_make_chunk("c1", "Cached embedding")]
        ids1, embs1 = embedder.embed(chunks, corpus_key="test-cache")
        ids2, embs2 = embedder.embed(chunks, corpus_key="test-cache")
        assert ids1 == ids2
        np.testing.assert_array_almost_equal(embs1, embs2)
