"""Tests for benchmark evaluation metrics."""

import numpy as np

from hcr_core.types.query import DifficultyTier, Query, QueryCategory
from hcr_core.types.tree import HCRTree, RoutingSummary, TreeNode
from tests.benchmark.eval.epsilon import compute_epsilon
from tests.benchmark.eval.tree_quality import sibling_distinctiveness


def _make_routing_summary(theme: str) -> RoutingSummary:
    return RoutingSummary(
        theme=theme, includes=[theme], excludes=[], key_entities=[], key_terms=[]
    )


def _make_simple_tree() -> HCRTree:
    """Tree: root -> [branch-a, branch-b], each with 2 leaves."""
    root = TreeNode(
        id="root",
        level=0,
        parent_ids=[],
        child_ids=["branch-a", "branch-b"],
        is_leaf=False,
        summary=_make_routing_summary("All"),
    )
    branch_a = TreeNode(
        id="branch-a",
        level=1,
        parent_ids=["root"],
        child_ids=["leaf-a1", "leaf-a2"],
        is_leaf=False,
        summary=_make_routing_summary("Topic A"),
    )
    branch_b = TreeNode(
        id="branch-b",
        level=1,
        parent_ids=["root"],
        child_ids=["leaf-b1", "leaf-b2"],
        is_leaf=False,
        summary=_make_routing_summary("Topic B"),
    )
    leaf_a1 = TreeNode(
        id="leaf-a1", level=2, parent_ids=["branch-a"], child_ids=[],
        is_leaf=True, chunk_id="c-a1",
    )
    leaf_a2 = TreeNode(
        id="leaf-a2", level=2, parent_ids=["branch-a"], child_ids=[],
        is_leaf=True, chunk_id="c-a2",
    )
    leaf_b1 = TreeNode(
        id="leaf-b1", level=2, parent_ids=["branch-b"], child_ids=[],
        is_leaf=True, chunk_id="c-b1",
    )
    leaf_b2 = TreeNode(
        id="leaf-b2", level=2, parent_ids=["branch-b"], child_ids=[],
        is_leaf=True, chunk_id="c-b2",
    )
    return HCRTree(
        root_id="root",
        nodes={
            "root": root,
            "branch-a": branch_a,
            "branch-b": branch_b,
            "leaf-a1": leaf_a1,
            "leaf-a2": leaf_a2,
            "leaf-b1": leaf_b1,
            "leaf-b2": leaf_b2,
        },
        depth=2,
    )


def _make_query(qid: str, gold_chunks: list[str]) -> Query:
    return Query(
        id=qid,
        text="test query",
        category=QueryCategory.SINGLE_BRANCH,
        difficulty=DifficultyTier.EASY,
        gold_chunk_ids=gold_chunks,
        gold_answer="test answer",
    )


class TestComputeEpsilon:
    def test_perfect_routing(self) -> None:
        tree = _make_simple_tree()
        queries = [_make_query("q1", ["c-a1"])]
        # Beam results: level 1 beam contains branch-a (correct)
        beam_results = {"q1": {1: ["branch-a", "branch-b"]}}
        measurements = compute_epsilon(tree, queries, beam_results)
        assert len(measurements) >= 1
        level1 = next(m for m in measurements if m.level == 1)
        assert level1.epsilon == 0.0  # Perfect routing

    def test_wrong_routing(self) -> None:
        tree = _make_simple_tree()
        queries = [_make_query("q1", ["c-a1"])]
        # Beam at level 1 only contains branch-b (wrong)
        beam_results = {"q1": {1: ["branch-b"]}}
        measurements = compute_epsilon(tree, queries, beam_results)
        level1 = next(m for m in measurements if m.level == 1)
        assert level1.epsilon == 1.0  # Complete miss

    def test_multiple_queries(self) -> None:
        tree = _make_simple_tree()
        queries = [
            _make_query("q1", ["c-a1"]),
            _make_query("q2", ["c-b1"]),
        ]
        beam_results = {
            "q1": {1: ["branch-a"]},  # Correct
            "q2": {1: ["branch-a"]},  # Wrong — should be branch-b
        }
        measurements = compute_epsilon(tree, queries, beam_results)
        level1 = next(m for m in measurements if m.level == 1)
        assert level1.epsilon == 0.5  # 1 out of 2 wrong


class TestSiblingDistinctiveness:
    def test_orthogonal_siblings(self) -> None:
        # Orthogonal embeddings = maximum distinctiveness
        # Keys must match child_ids of root node: "branch-a", "branch-b"
        embeddings = {
            "branch-a": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "branch-b": np.array([0.0, 1.0, 0.0], dtype=np.float32),
        }
        tree = _make_simple_tree()
        sd = sibling_distinctiveness(tree, embeddings)
        # Cosine distance of orthogonal vectors is 1.0
        assert sd > 0.9

    def test_identical_siblings(self) -> None:
        # Same embedding = zero distinctiveness
        embeddings = {
            "branch-a": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "branch-b": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        }
        tree = _make_simple_tree()
        sd = sibling_distinctiveness(tree, embeddings)
        assert sd < 0.01

    def test_kill_criterion(self) -> None:
        # SD < 0.15 is the kill criterion
        embeddings = {
            "branch-a": np.array([1.0, 0.01, 0.0], dtype=np.float32),
            "branch-b": np.array([1.0, 0.02, 0.0], dtype=np.float32),
        }
        tree = _make_simple_tree()
        sd = sibling_distinctiveness(tree, embeddings)
        assert sd < 0.15  # This would trigger the kill criterion
