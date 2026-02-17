"""Wikipedia article loader via HuggingFace datasets library.

Streams Wikipedia articles, filters by business/tech/org topic keywords,
and returns Document objects for corpus preparation.
"""

from __future__ import annotations

import logging
import re

from hcr_core.types.corpus import Document

logger = logging.getLogger(__name__)

# Keywords for filtering — business, technology, organizational topics
# matching the GitLab handbook's domain
TOPIC_KEYWORDS: list[str] = [
    "company",
    "organization",
    "management",
    "software",
    "technology",
    "engineering",
    "devops",
    "policy",
    "compliance",
    "human resources",
    "leadership",
    "remote work",
    "open source",
    "saas",
    "cloud computing",
    "security",
    "governance",
    "agile",
    "project management",
    "startup",
    "enterprise",
    "data science",
    "machine learning",
    "artificial intelligence",
    "infrastructure",
    "automation",
    "continuous integration",
    "continuous delivery",
    "version control",
    "software development",
    "information technology",
    "cybersecurity",
    "networking",
    "database",
    "api",
    "microservices",
    "kubernetes",
    "docker",
    "linux",
    "programming",
    "computer science",
]

# Word count bounds for filtering articles
MIN_WORDS = 500
MAX_WORDS = 10000


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the topic keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _word_count(text: str) -> int:
    """Rough word count via whitespace splitting."""
    return len(text.split())


def _clean_wiki_text(text: str) -> str:
    """Light cleanup of Wikipedia article text.

    Removes excessive whitespace and common wiki artifacts.
    """
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove section-only lines like "== References ==" at the end
    text = re.sub(r"\n==\s*(?:References|External links|See also|Notes|Further reading)\s*==.*",
                  "", text, flags=re.DOTALL)
    return text.strip()


def load_wikipedia_articles(
    target_count: int = 2500,
    topic_keywords: list[str] | None = None,
    seed: int = 42,
) -> list[Document]:
    """Load Wikipedia articles filtered by topic keywords.

    Streams from HuggingFace datasets library ('wikipedia', '20220301.en'),
    filters by keyword match on title + first 500 chars, and by article length.

    Args:
        target_count: Target number of articles to collect.
        topic_keywords: Keywords to filter on. Defaults to TOPIC_KEYWORDS.
        seed: Random seed for shuffling the dataset stream.

    Returns:
        List of Document objects with source="wikipedia".
    """
    from datasets import load_dataset

    keywords = topic_keywords or TOPIC_KEYWORDS

    logger.info(
        "Loading Wikipedia articles (target=%d, keywords=%d)...",
        target_count,
        len(keywords),
    )

    # Stream to avoid downloading the full 20GB dataset
    ds = load_dataset(
        "wikipedia",
        "20220301.en",
        split="train",
        streaming=True,
        trust_remote_code=True,
    )
    # Shuffle with a buffer for diversity
    ds = ds.shuffle(seed=seed, buffer_size=10000)

    documents: list[Document] = []
    scanned = 0
    skipped_length = 0
    skipped_keyword = 0

    for article in ds:
        scanned += 1

        title: str = article["title"]
        text: str = article["text"]

        # Filter by length
        wc = _word_count(text)
        if wc < MIN_WORDS or wc > MAX_WORDS:
            skipped_length += 1
            if scanned % 50000 == 0:
                logger.info(
                    "  Scanned %d articles, collected %d/%d...",
                    scanned,
                    len(documents),
                    target_count,
                )
            continue

        # Filter by keyword match on title + first 500 chars
        match_text = f"{title} {text[:500]}"
        if not _matches_keywords(match_text, keywords):
            skipped_keyword += 1
            if scanned % 50000 == 0:
                logger.info(
                    "  Scanned %d articles, collected %d/%d...",
                    scanned,
                    len(documents),
                    target_count,
                )
            continue

        # Clean and create document
        cleaned = _clean_wiki_text(text)
        doc_id = f"wikipedia-{len(documents):05d}"
        documents.append(
            Document(
                id=doc_id,
                source="wikipedia",
                content=cleaned,
                metadata={"title": title, "url": f"https://en.wikipedia.org/wiki/{title}"},
            )
        )

        if len(documents) % 100 == 0:
            logger.info(
                "  Collected %d/%d articles (scanned %d)",
                len(documents),
                target_count,
                scanned,
            )

        if len(documents) >= target_count:
            break

    logger.info(
        "Wikipedia loading complete: %d articles from %d scanned "
        "(skipped: %d length, %d keyword)",
        len(documents),
        scanned,
        skipped_length,
        skipped_keyword,
    )

    return documents
