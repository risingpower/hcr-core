"""LLM-as-judge sufficiency evaluation."""

from __future__ import annotations

import json
import logging

from hcr_core.llm.claude import ClaudeClient
from hcr_core.types.corpus import Chunk
from hcr_core.types.metrics import SufficiencyResult
from hcr_core.types.query import Query
from tests.benchmark.cache.manager import JudgeCache

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = (
    "You are an evaluation judge. Given a question, a gold-standard answer, "
    "and retrieved context chunks, determine if the context is SUFFICIENT "
    "to answer the question correctly.\n\n"
    "Respond with valid JSON only:\n"
    '{"is_sufficient": true/false, "reasoning": "brief explanation"}'
)

JUDGE_PROMPT = """Question: {query_text}

Gold Answer: {gold_answer}

Retrieved Context ({token_count} tokens):
{context}

Is the retrieved context sufficient to correctly answer the question?"""


class SufficiencyJudge:
    """Evaluates whether retrieved chunks sufficiently answer a query."""

    def __init__(
        self,
        client: ClaudeClient,
        cache: JudgeCache | None = None,
    ) -> None:
        self._client = client
        self._cache = cache

    def evaluate(
        self,
        query: Query,
        chunks: list[Chunk],
        token_budget: int,
    ) -> SufficiencyResult:
        """Evaluate sufficiency synchronously."""
        chunk_ids = [c.id for c in chunks]

        # Check cache
        if self._cache is not None:
            cached = self._cache.load(query.id, chunk_ids)
            if cached is not None:
                return SufficiencyResult(
                    query_id=query.id,
                    token_budget=token_budget,
                    is_sufficient=cached["is_sufficient"],
                    judge_reasoning=cached["reasoning"],
                )

        context = "\n\n---\n\n".join(c.content for c in chunks)
        total_tokens = sum(c.token_count for c in chunks)

        prompt = JUDGE_PROMPT.format(
            query_text=query.text,
            gold_answer=query.gold_answer,
            token_count=total_tokens,
            context=context,
        )

        response = self._client.complete(prompt, system=JUDGE_SYSTEM, max_tokens=256)

        try:
            parsed = json.loads(response)
            is_sufficient = bool(parsed["is_sufficient"])
            reasoning = str(parsed["reasoning"])
        except (json.JSONDecodeError, KeyError) as e:
            logging.warning(
                "Failed to parse judge response for query %s: %s. "
                "Raw response: %s",
                query.id,
                e,
                response[:500],
            )
            is_sufficient = False
            reasoning = f"Failed to parse judge response: {e}"

        # Cache result
        if self._cache is not None:
            self._cache.save(
                query.id,
                chunk_ids,
                {"is_sufficient": is_sufficient, "reasoning": reasoning},
            )

        return SufficiencyResult(
            query_id=query.id,
            token_budget=token_budget,
            is_sufficient=is_sufficient,
            judge_reasoning=reasoning,
        )

    async def aevaluate(
        self,
        query: Query,
        chunks: list[Chunk],
        token_budget: int,
    ) -> SufficiencyResult:
        """Evaluate sufficiency asynchronously."""
        chunk_ids = [c.id for c in chunks]

        if self._cache is not None:
            cached = self._cache.load(query.id, chunk_ids)
            if cached is not None:
                return SufficiencyResult(
                    query_id=query.id,
                    token_budget=token_budget,
                    is_sufficient=cached["is_sufficient"],
                    judge_reasoning=cached["reasoning"],
                )

        context = "\n\n---\n\n".join(c.content for c in chunks)
        total_tokens = sum(c.token_count for c in chunks)

        prompt = JUDGE_PROMPT.format(
            query_text=query.text,
            gold_answer=query.gold_answer,
            token_count=total_tokens,
            context=context,
        )

        response = await self._client.acomplete(
            prompt, system=JUDGE_SYSTEM, max_tokens=256
        )

        try:
            parsed = json.loads(response)
            is_sufficient = bool(parsed["is_sufficient"])
            reasoning = str(parsed["reasoning"])
        except (json.JSONDecodeError, KeyError) as e:
            logging.warning(
                "Failed to parse judge response for query %s: %s. "
                "Raw response: %s",
                query.id,
                e,
                response[:500],
            )
            is_sufficient = False
            reasoning = f"Failed to parse judge response: {e}"

        if self._cache is not None:
            self._cache.save(
                query.id,
                chunk_ids,
                {"is_sufficient": is_sufficient, "reasoning": reasoning},
            )

        return SufficiencyResult(
            query_id=query.id,
            token_budget=token_budget,
            is_sufficient=is_sufficient,
            judge_reasoning=reasoning,
        )
