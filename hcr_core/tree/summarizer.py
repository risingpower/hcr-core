"""LLM-based routing summary generation with contrastive prompts."""

from __future__ import annotations

import json
import logging
import re

from hcr_core.llm.claude import ClaudeClient
from hcr_core.types.tree import RoutingSummary

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = (
    "You are a routing summary generator for a hierarchical retrieval system. "
    "Your job: help a search system decide whether a user's query should be "
    "routed to THIS cluster or a sibling cluster.\n\n"
    "Rules:\n"
    "- 'includes': specific topics covered. Use terms a user would search for, "
    "not abstract categories. 5-8 items.\n"
    "- 'excludes': topics NOT here but in siblings. Be specific. 3-5 items.\n"
    "- 'key_entities': proper nouns, product names, system names from the content. "
    "5-10 items.\n"
    "- 'key_terms': searchable keywords and phrases a user would type. "
    "Include abbreviations, synonyms, and specific terms. 8-15 items.\n\n"
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

SIBLING SUMMARIES (what other clusters cover — use to write specific "excludes"):
{sibling_context}

Generate a routing summary. Be SPECIFIC, not abstract:
- BAD includes: ["Billing Structures", "Pricing Configuration"]
- GOOD includes: ["rate plan charges", "invoice line items", "tiered pricing setup"]
- BAD key_terms: ["billing", "pricing"]
- GOOD key_terms: ["rate plan", "charge model", "tiered pricing", "per unit", \
"invoice item", "subscription charge", "overage"]

Use the ACTUAL terms and entities from the content, not paraphrased categories."""


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

    last_error: Exception | None = None
    for attempt in range(3):
        response = client.complete(prompt, system=SUMMARIZE_SYSTEM, max_tokens=512)
        try:
            parsed = json.loads(_extract_json(response))
            return RoutingSummary(
                theme=parsed["theme"],
                includes=parsed["includes"],
                excludes=parsed.get("excludes", []),
                key_entities=parsed.get("key_entities", []),
                key_terms=parsed.get("key_terms", []),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e
            logger.warning(
                "Routing summary parse failed (attempt %d/3): %s. "
                "Response: %s",
                attempt + 1,
                e,
                response[:150],
            )

    # All retries exhausted — build a minimal fallback from raw text
    logger.warning(
        "All 3 summary attempts failed. Using fallback summary. Last error: %s",
        last_error,
    )
    words = " ".join(cluster_texts)[:500].split()
    return RoutingSummary(
        theme="(auto-fallback: unparseable cluster)",
        includes=list(dict.fromkeys(w for w in words if len(w) > 4))[:8],
        excludes=[],
        key_entities=[],
        key_terms=list(dict.fromkeys(w for w in words if len(w) > 3))[:10],
    )


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response that may contain preamble or code fences."""
    text = text.strip()

    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Find the first { and last } to extract the JSON object
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]

    return text
