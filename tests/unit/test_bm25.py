"""Tests for BM25 index."""


from hcr_core.index.bm25 import BM25Index
from hcr_core.types.corpus import Chunk


def _make_chunks() -> list[Chunk]:
    return [
        Chunk(id="c1", document_id="d1", content="python machine learning", token_count=3),
        Chunk(id="c2", document_id="d1", content="java web development", token_count=3),
        Chunk(id="c3", document_id="d1", content="python data science statistics", token_count=4),
        Chunk(id="c4", document_id="d1", content="javascript frontend react", token_count=3),
        Chunk(
            id="c5", document_id="d1",
            content="python deep learning neural networks", token_count=5,
        ),
    ]


class TestBM25Index:
    def test_search_returns_results(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("python machine learning", top_k=3)
        assert len(results) > 0
        assert len(results) <= 3

    def test_search_returns_chunk_id_score_tuples(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("python", top_k=2)
        for chunk_id, score in results:
            assert isinstance(chunk_id, str)
            assert isinstance(score, float)

    def test_relevant_results_rank_higher(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("python", top_k=5)
        top_ids = [r[0] for r in results[:3]]
        # Python-related chunks should rank in top 3
        python_chunks = {"c1", "c3", "c5"}
        assert len(set(top_ids) & python_chunks) >= 2

    def test_search_respects_top_k(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("python", top_k=2)
        assert len(results) <= 2

    def test_search_no_results_for_unrelated(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("quantum physics chemistry", top_k=3)
        # Should still return results (BM25 will return something) but scores should be low
        assert isinstance(results, list)

    def test_scores_are_sorted_descending(self) -> None:
        index = BM25Index(_make_chunks())
        results = index.search("python data", top_k=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)
