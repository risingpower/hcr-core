"""Query suite management: load, save, filter, split."""

from __future__ import annotations

import json
from pathlib import Path

from hcr_core.types.query import DifficultyTier, Query, QueryCategory


class QuerySuite:
    """A collection of benchmark queries with load/save/filter/split support."""

    def __init__(self, queries: list[Query] | None = None) -> None:
        self.queries = queries or []

    def __len__(self) -> int:
        return len(self.queries)

    def save(self, path: Path) -> None:
        """Save queries to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [q.model_dump() for q in self.queries]
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> QuerySuite:
        """Load queries from a JSON file."""
        path = Path(path)
        data = json.loads(path.read_text())
        queries = [Query(**item) for item in data]
        return cls(queries)

    def filter_budget_feasible(self, feasible: bool = True) -> QuerySuite:
        """Filter queries by budget feasibility at 400 tokens."""
        filtered = [q for q in self.queries if q.budget_feasible_400 == feasible]
        return QuerySuite(filtered)

    def filter_category(self, category: QueryCategory) -> QuerySuite:
        """Filter queries by category."""
        filtered = [q for q in self.queries if q.category == category]
        return QuerySuite(filtered)

    def filter_difficulty(self, difficulty: DifficultyTier) -> QuerySuite:
        """Filter queries by difficulty."""
        filtered = [q for q in self.queries if q.difficulty == difficulty]
        return QuerySuite(filtered)

    def split(
        self,
        train: float = 0.6,
        dev: float = 0.2,
        test: float = 0.2,
    ) -> tuple[QuerySuite, QuerySuite, QuerySuite]:
        """Split queries into train/dev/test sets."""
        n = len(self.queries)
        train_end = int(n * train)
        dev_end = train_end + int(n * dev)

        return (
            QuerySuite(self.queries[:train_end]),
            QuerySuite(self.queries[train_end:dev_end]),
            QuerySuite(self.queries[dev_end:]),
        )
