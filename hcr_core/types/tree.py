"""Tree data models: nodes, routing summaries, and the HCR tree."""

from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class RoutingSummary(BaseModel):
    """Structured routing summary for tree nodes (RB-004 design)."""

    theme: str
    includes: list[str]
    excludes: list[str]
    key_entities: list[str]
    key_terms: list[str]
    content_snippet: str = ""

    @field_validator("theme")
    @classmethod
    def theme_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("theme must not be empty")
        return v


class TreeNode(BaseModel):
    """A node in the HCR tree. Leaf nodes point to chunks; internal nodes have summaries."""

    id: str
    level: int = Field(ge=0)
    parent_ids: list[str]
    child_ids: list[str]
    is_leaf: bool
    summary: RoutingSummary | None = None
    summary_embedding: list[float] | None = None
    chunk_id: str | None = None

    @model_validator(mode="after")
    def validate_node_invariants(self) -> Self:
        if self.is_leaf and self.chunk_id is None:
            raise ValueError("Leaf nodes must have a chunk_id")
        if not self.is_leaf and not self.child_ids:
            raise ValueError("Internal nodes must have children")
        return self


class HCRTree(BaseModel):
    """The complete HCR tree structure."""

    root_id: str
    nodes: dict[str, TreeNode]
    depth: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_root_exists(self) -> Self:
        if self.root_id not in self.nodes:
            raise ValueError(f"root_id '{self.root_id}' not found in nodes")
        return self
