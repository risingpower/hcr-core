"""LLM-based routing summary generation with contrastive prompts."""

from __future__ import annotations

import json

from hcr_core.llm.claude import ClaudeClient
from hcr_core.types.tree import RoutingSummary

SUMMARIZE_SYSTEM = (
    "You are a routing summary generator for a hierarchical retrieval system. "
    "Generate a structured routing summary that helps distinguish this cluster "
    "from its siblings. Be concise and precise.\n\n"
    "Respond with valid JSON only:\n"
    "{"
    '"theme": "...", '
    '"includes": ["topic1", "topic2"], '
    '"excludes": ["topic_not_here1"], '
    '"key_entities": ["entity1"], '
    '"key_terms": ["term1", "term2"]'
    "}"
)

SUMMARIZE_PROMPT = """Generate a routing summary for this cluster of text chunks.

CLUSTER CONTENT (sample):
{content_sample}

SIBLING SUMMARIES (what other clusters cover — use for contrastive "excludes"):
{sibling_context}

Generate a routing summary that INCLUDES what this cluster covers \
and EXCLUDES what siblings cover."""


def generate_routing_summary(
    client: ClaudeClient,
    cluster_texts: list[str],
    sibling_summaries: list[RoutingSummary] | None = None,
    max_sample_chars: int = 3000,
) -> RoutingSummary:
    """Generate a contrastive routing summary for a cluster.

    Uses LLM to create structured routing summaries with
    contrastive includes/excludes based on sibling clusters.
    """
    # Sample cluster content
    content_sample = "\n---\n".join(cluster_texts)
    if len(content_sample) > max_sample_chars:
        content_sample = content_sample[:max_sample_chars] + "\n[truncated]"

    # Build sibling context
    if sibling_summaries:
        sibling_context = "\n".join(
            f"- {s.theme}: {', '.join(s.includes)}" for s in sibling_summaries
        )
    else:
        sibling_context = "(none — this is the first cluster)"

    prompt = SUMMARIZE_PROMPT.format(
        content_sample=content_sample,
        sibling_context=sibling_context,
    )

    response = client.complete(prompt, system=SUMMARIZE_SYSTEM, max_tokens=512)

    try:
        parsed = json.loads(response)
        return RoutingSummary(
            theme=parsed["theme"],
            includes=parsed["includes"],
            excludes=parsed.get("excludes", []),
            key_entities=parsed.get("key_entities", []),
            key_terms=parsed.get("key_terms", []),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(
            f"LLM returned invalid routing summary: {e}. "
            f"Raw response: {response[:200]}"
        ) from e
