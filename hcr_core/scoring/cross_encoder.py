"""Cross-encoder scoring for per-level reranking."""

from __future__ import annotations

from sentence_transformers import CrossEncoder

from tests.benchmark.cache.manager import CrossEncoderCache


class CrossEncoderScorer:
    """Scores (query, text) pairs using a cross-encoder model."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        cache: CrossEncoderCache | None = None,
    ) -> None:
        self._model = CrossEncoder(model_name)
        self._cache = cache

    def score(self, query: str, text: str, chunk_id: str | None = None) -> float:
        """Score a single (query, text) pair."""
        if self._cache is not None and chunk_id is not None:
            cached = self._cache.load(query, chunk_id)
            if cached is not None:
                return cached

        score: float = float(self._model.predict([(query, text)])[0])

        if self._cache is not None and chunk_id is not None:
            self._cache.save(query, chunk_id, score)

        return score

    def score_batch(
        self,
        query: str,
        texts: list[str],
        chunk_ids: list[str] | None = None,
    ) -> list[float]:
        """Score multiple (query, text) pairs."""
        if chunk_ids is not None and self._cache is not None:
            # Check cache for each
            scores: list[float] = []
            uncached_indices: list[int] = []
            uncached_pairs: list[tuple[str, str]] = []

            for i, (text, cid) in enumerate(zip(texts, chunk_ids, strict=True)):
                cached = self._cache.load(query, cid)
                if cached is not None:
                    scores.append(cached)
                else:
                    scores.append(0.0)  # placeholder
                    uncached_indices.append(i)
                    uncached_pairs.append((query, text))

            if uncached_pairs:
                new_scores: list[float] = self._model.predict(uncached_pairs).tolist()
                for idx, new_score in zip(uncached_indices, new_scores, strict=True):
                    scores[idx] = new_score
                    if chunk_ids is not None:
                        self._cache.save(query, chunk_ids[idx], new_score)

            return scores

        pairs = [(query, text) for text in texts]
        result: list[float] = self._model.predict(pairs).tolist()
        return result
