"""LLM-based query generation for benchmark evaluation."""

from __future__ import annotations

import json

from hcr_core.llm.claude import ClaudeClient
from hcr_core.types.corpus import Chunk
from hcr_core.types.query import DifficultyTier, Query, QueryCategory

GENERATION_SYSTEM = (
    "You are a benchmark query generator. Given a text chunk, "
    "generate a question that can ONLY be answered using information "
    "in this chunk. The question must be evidence-anchored.\n\n"
    "Respond with valid JSON only:\n"
    '{"question": "...", "answer": "...", "difficulty": "easy|medium|hard"}'
)

GENERATION_PROMPT = """Generate a {category} query for this chunk:

Chunk ID: {chunk_id}
Content:
{content}

Query category: {category}
Generate a question that requires this specific chunk to answer."""


def generate_queries_for_chunk(
    client: ClaudeClient,
    chunk: Chunk,
    category: QueryCategory,
    query_id_prefix: str = "gen",
) -> Query | None:
    """Generate a benchmark query for a specific chunk using LLM."""
    prompt = GENERATION_PROMPT.format(
        category=category.value,
        chunk_id=chunk.id,
        content=chunk.content[:2000],
    )

    response = client.complete(prompt, system=GENERATION_SYSTEM, max_tokens=256)

    try:
        parsed = json.loads(response)
        difficulty_str = parsed.get("difficulty", "medium")
        difficulty = DifficultyTier(difficulty_str)

        return Query(
            id=f"{query_id_prefix}-{chunk.id}-{category.value}",
            text=parsed["question"],
            category=category,
            difficulty=difficulty,
            gold_chunk_ids=[chunk.id],
            gold_answer=parsed["answer"],
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
