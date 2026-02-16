"""Tests for core data models."""

import numpy as np
import pytest
from pydantic import ValidationError

from hcr_core.types.corpus import Chunk, Document
from hcr_core.types.metrics import BenchmarkResult, EpsilonMeasurement, SufficiencyResult
from hcr_core.types.query import DifficultyTier, Query, QueryCategory
from hcr_core.types.tree import HCRTree, RoutingSummary, TreeNode


class TestDocument:
    def test_create_document(self) -> None:
        doc = Document(id="doc-1", source="handbook", content="Hello world")
        assert doc.id == "doc-1"
        assert doc.source == "handbook"
        assert doc.content == "Hello world"
        assert doc.metadata == {}

    def test_document_with_metadata(self) -> None:
        doc = Document(
            id="doc-2", source="email", content="Test", metadata={"author": "alice"}
        )
        assert doc.metadata["author"] == "alice"

    def test_document_requires_content(self) -> None:
        with pytest.raises(ValidationError):
            Document(id="doc-1", source="test", content="")  # type: ignore[arg-type]


class TestChunk:
    def test_create_chunk(self) -> None:
        chunk = Chunk(
            id="chunk-1", document_id="doc-1", content="Some text", token_count=5
        )
        assert chunk.id == "chunk-1"
        assert chunk.document_id == "doc-1"
        assert chunk.token_count == 5
        assert chunk.metadata == {}

    def test_chunk_requires_positive_tokens(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(id="c1", document_id="d1", content="text", token_count=0)

    def test_chunk_requires_content(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(id="c1", document_id="d1", content="", token_count=5)  # type: ignore[arg-type]


class TestQueryCategory:
    def test_all_categories_exist(self) -> None:
        expected = [
            "single_branch",
            "entity_spanning",
            "dpi",
            "multi_hop",
            "comparative",
            "aggregation",
            "temporal",
            "ambiguous",
            "ood",
        ]
        for cat in expected:
            assert QueryCategory(cat) is not None

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValueError):
            QueryCategory("nonexistent")


class TestDifficultyTier:
    def test_all_tiers_exist(self) -> None:
        for tier in ["easy", "medium", "hard"]:
            assert DifficultyTier(tier) is not None


class TestQuery:
    def test_create_query(self) -> None:
        q = Query(
            id="q-1",
            text="What is the vacation policy?",
            category=QueryCategory.SINGLE_BRANCH,
            difficulty=DifficultyTier.EASY,
            gold_chunk_ids=["chunk-1", "chunk-2"],
            gold_answer="Two weeks paid vacation.",
        )
        assert q.id == "q-1"
        assert q.category == QueryCategory.SINGLE_BRANCH
        assert q.difficulty == DifficultyTier.EASY
        assert q.budget_feasible_400 is True
        assert len(q.gold_chunk_ids) == 2

    def test_query_budget_infeasible(self) -> None:
        q = Query(
            id="q-2",
            text="Compare all departments",
            category=QueryCategory.AGGREGATION,
            difficulty=DifficultyTier.HARD,
            budget_feasible_400=False,
            gold_chunk_ids=["c1"],
            gold_answer="answer",
        )
        assert q.budget_feasible_400 is False

    def test_query_requires_gold_chunks(self) -> None:
        with pytest.raises(ValidationError):
            Query(
                id="q-3",
                text="test",
                category=QueryCategory.SINGLE_BRANCH,
                difficulty=DifficultyTier.EASY,
                gold_chunk_ids=[],
                gold_answer="answer",
            )


class TestRoutingSummary:
    def test_create_routing_summary(self) -> None:
        rs = RoutingSummary(
            theme="HR Policies",
            includes=["vacation", "sick leave", "benefits"],
            excludes=["engineering", "product"],
            key_entities=["HR department"],
            key_terms=["PTO", "leave", "benefits"],
        )
        assert rs.theme == "HR Policies"
        assert len(rs.includes) == 3
        assert len(rs.excludes) == 2

    def test_routing_summary_requires_theme(self) -> None:
        with pytest.raises(ValidationError):
            RoutingSummary(
                theme="",  # type: ignore[arg-type]
                includes=["a"],
                excludes=["b"],
                key_entities=[],
                key_terms=[],
            )


class TestTreeNode:
    def test_create_leaf_node(self) -> None:
        node = TreeNode(
            id="node-1",
            level=2,
            parent_ids=["node-0"],
            child_ids=[],
            is_leaf=True,
            chunk_id="chunk-1",
        )
        assert node.is_leaf is True
        assert node.chunk_id == "chunk-1"
        assert node.summary is None
        assert node.summary_embedding is None

    def test_create_internal_node(self) -> None:
        summary = RoutingSummary(
            theme="Engineering",
            includes=["code", "deploys"],
            excludes=["sales"],
            key_entities=["CTO"],
            key_terms=["CI/CD"],
        )
        emb = np.zeros(768, dtype=np.float32).tolist()
        node = TreeNode(
            id="node-0",
            level=1,
            parent_ids=[],
            child_ids=["node-1", "node-2"],
            is_leaf=False,
            summary=summary,
            summary_embedding=emb,
        )
        assert node.is_leaf is False
        assert node.summary is not None
        assert node.summary_embedding is not None
        assert len(node.summary_embedding) == 768

    def test_leaf_requires_chunk_id(self) -> None:
        with pytest.raises(ValidationError):
            TreeNode(
                id="n1",
                level=2,
                parent_ids=["n0"],
                child_ids=[],
                is_leaf=True,
                chunk_id=None,
            )

    def test_internal_node_requires_children(self) -> None:
        with pytest.raises(ValidationError):
            TreeNode(
                id="n1",
                level=1,
                parent_ids=[],
                child_ids=[],
                is_leaf=False,
            )


class TestHCRTree:
    def test_create_tree(self) -> None:
        root = TreeNode(
            id="root",
            level=0,
            parent_ids=[],
            child_ids=["leaf-1"],
            is_leaf=False,
            summary=RoutingSummary(
                theme="All",
                includes=["everything"],
                excludes=[],
                key_entities=[],
                key_terms=[],
            ),
        )
        leaf = TreeNode(
            id="leaf-1",
            level=1,
            parent_ids=["root"],
            child_ids=[],
            is_leaf=True,
            chunk_id="chunk-1",
        )
        tree = HCRTree(root_id="root", nodes={"root": root, "leaf-1": leaf}, depth=1)
        assert tree.depth == 1
        assert len(tree.nodes) == 2
        assert tree.root_id == "root"

    def test_tree_requires_root_in_nodes(self) -> None:
        leaf = TreeNode(
            id="leaf-1",
            level=1,
            parent_ids=["root"],
            child_ids=[],
            is_leaf=True,
            chunk_id="chunk-1",
        )
        with pytest.raises(ValidationError):
            HCRTree(root_id="root", nodes={"leaf-1": leaf}, depth=1)

    def test_tree_requires_positive_depth(self) -> None:
        root = TreeNode(
            id="root",
            level=0,
            parent_ids=[],
            child_ids=["l1"],
            is_leaf=False,
            summary=RoutingSummary(
                theme="All",
                includes=["x"],
                excludes=[],
                key_entities=[],
                key_terms=[],
            ),
        )
        with pytest.raises(ValidationError):
            HCRTree(root_id="root", nodes={"root": root}, depth=0)


class TestEpsilonMeasurement:
    def test_create_epsilon(self) -> None:
        em = EpsilonMeasurement(
            level=1, queries_evaluated=100, correct_branch_in_beam=97, epsilon=0.03
        )
        assert em.epsilon == 0.03
        assert em.level == 1

    def test_epsilon_bounded(self) -> None:
        with pytest.raises(ValidationError):
            EpsilonMeasurement(
                level=1, queries_evaluated=10, correct_branch_in_beam=5, epsilon=1.5
            )


class TestSufficiencyResult:
    def test_create_sufficiency(self) -> None:
        sr = SufficiencyResult(
            query_id="q-1",
            token_budget=400,
            is_sufficient=True,
            judge_reasoning="Answer is complete.",
        )
        assert sr.is_sufficient is True
        assert sr.token_budget == 400


class TestBenchmarkResult:
    def test_create_benchmark_result(self) -> None:
        br = BenchmarkResult(
            system_name="bm25-baseline",
            corpus_size=10000,
            query_count=100,
            epsilon_per_level=[
                EpsilonMeasurement(
                    level=1,
                    queries_evaluated=100,
                    correct_branch_in_beam=95,
                    epsilon=0.05,
                )
            ],
            sufficiency_at_400=0.72,
            ndcg_at_10=0.65,
            recall_at_10=0.70,
            mrr=0.80,
            mean_tokens_used=380.0,
        )
        assert br.system_name == "bm25-baseline"
        assert br.corpus_size == 10000
        assert br.sufficiency_at_400 == 0.72
