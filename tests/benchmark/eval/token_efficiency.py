"""Token efficiency curve computation."""

from __future__ import annotations

from dataclasses import dataclass, field

from hcr_core.types.query import Query
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.eval.sufficiency import SufficiencyJudge


@dataclass
class TokenEfficiencyPoint:
    """A single point on the token efficiency curve."""

    budget: int
    sufficiency_rate: float
    mean_tokens_used: float
    queries_evaluated: int


@dataclass
class TokenEfficiencyCurve:
    """Full token efficiency curve for a retrieval system."""

    system_name: str
    points: list[TokenEfficiencyPoint] = field(default_factory=list)


def compute_efficiency_curve(
    baseline: RetrievalBaseline,
    queries: list[Query],
    judge: SufficiencyJudge,
    budgets: list[int] | None = None,
) -> TokenEfficiencyCurve:
    """Compute token efficiency curve across multiple budgets.

    For each budget, retrieve chunks and evaluate sufficiency.
    """
    if budgets is None:
        budgets = [200, 400, 600, 800, 1200, 10000]

    curve = TokenEfficiencyCurve(system_name=baseline.name)

    for budget in budgets:
        sufficient_count = 0
        total_tokens = 0.0

        for query in queries:
            chunks = baseline.retrieve(query.text, token_budget=budget)
            result = judge.evaluate(query, chunks, token_budget=budget)
            if result.is_sufficient:
                sufficient_count += 1
            total_tokens += sum(c.token_count for c in chunks)

        n = len(queries)
        curve.points.append(
            TokenEfficiencyPoint(
                budget=budget,
                sufficiency_rate=sufficient_count / n if n > 0 else 0.0,
                mean_tokens_used=total_tokens / n if n > 0 else 0.0,
                queries_evaluated=n,
            )
        )

    return curve
