"""Tests for greedy token packing."""


from hcr_core.traversal.selection import greedy_token_packing
from hcr_core.types.corpus import Chunk


def _make_chunks() -> list[Chunk]:
    return [
        Chunk(id="c1", document_id="d1", content="A" * 10, token_count=10),
        Chunk(id="c2", document_id="d1", content="B" * 20, token_count=20),
        Chunk(id="c3", document_id="d1", content="C" * 5, token_count=5),
        Chunk(id="c4", document_id="d1", content="D" * 15, token_count=15),
    ]


class TestGreedyTokenPacking:
    def test_respects_budget(self) -> None:
        chunks = _make_chunks()
        scores = [0.9, 0.8, 0.7, 0.6]
        packed = greedy_token_packing(chunks, scores, budget=25)
        total = sum(c.token_count for c in packed)
        assert total <= 25

    def test_selects_by_score(self) -> None:
        chunks = _make_chunks()
        scores = [0.9, 0.1, 0.8, 0.2]
        packed = greedy_token_packing(chunks, scores, budget=20)
        ids = [c.id for c in packed]
        # c1 (score 0.9, 10 tokens) and c3 (score 0.8, 5 tokens) should be selected
        assert "c1" in ids
        assert "c3" in ids

    def test_empty_input(self) -> None:
        packed = greedy_token_packing([], [], budget=100)
        assert packed == []

    def test_budget_zero(self) -> None:
        chunks = _make_chunks()
        scores = [0.9, 0.8, 0.7, 0.6]
        packed = greedy_token_packing(chunks, scores, budget=0)
        assert packed == []

    def test_all_fit(self) -> None:
        chunks = _make_chunks()
        scores = [0.9, 0.8, 0.7, 0.6]
        packed = greedy_token_packing(chunks, scores, budget=100)
        assert len(packed) == 4
