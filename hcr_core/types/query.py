"""Query data models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class QueryCategory(StrEnum):
    """Query type classification from RB-006."""

    SINGLE_BRANCH = "single_branch"
    ENTITY_SPANNING = "entity_spanning"
    DPI = "dpi"
    MULTI_HOP = "multi_hop"
    COMPARATIVE = "comparative"
    AGGREGATION = "aggregation"
    TEMPORAL = "temporal"
    AMBIGUOUS = "ambiguous"
    OOD = "ood"


class DifficultyTier(StrEnum):
    """Query difficulty for stratified evaluation."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Query(BaseModel):
    """A benchmark query with gold-standard annotations."""

    id: str
    text: str
    category: QueryCategory
    difficulty: DifficultyTier
    budget_feasible_400: bool = True
    gold_chunk_ids: list[str] = Field(min_length=1)
    gold_answer: str
