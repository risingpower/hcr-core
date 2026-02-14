"""Metric data models for benchmark evaluation."""

from pydantic import BaseModel, Field


class EpsilonMeasurement(BaseModel):
    """Per-level routing accuracy measurement (novel metric)."""

    level: int = Field(ge=0)
    queries_evaluated: int = Field(gt=0)
    correct_branch_in_beam: int = Field(ge=0)
    epsilon: float = Field(ge=0.0, le=1.0)


class SufficiencyResult(BaseModel):
    """LLM-as-judge sufficiency evaluation for a single query."""

    query_id: str
    token_budget: int = Field(gt=0)
    is_sufficient: bool
    judge_reasoning: str


class BenchmarkResult(BaseModel):
    """Aggregate benchmark results for a retrieval system."""

    system_name: str
    corpus_size: int = Field(gt=0)
    query_count: int = Field(gt=0)
    epsilon_per_level: list[EpsilonMeasurement]
    sufficiency_at_400: float = Field(ge=0.0, le=1.0)
    ndcg_at_10: float = Field(ge=0.0, le=1.0)
    recall_at_10: float = Field(ge=0.0, le=1.0)
    mrr: float = Field(ge=0.0, le=1.0)
    mean_tokens_used: float = Field(ge=0.0)
