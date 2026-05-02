"""Keyword extraction from free-text partner expectations."""
from __future__ import annotations

import re
import string

_STOPWORDS: frozenset[str] = frozenset(
    [
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "should",
        "could", "may", "might", "must", "shall", "can", "of", "in", "on",
        "at", "to", "for", "with", "by", "from", "up", "about", "into",
        "through", "during", "before", "after", "above", "below", "between",
        "under", "over", "only", "just", "so", "than", "too", "very", "also",
        "my", "our", "your", "their", "his", "her", "its", "this", "that",
        "these", "those", "i", "we", "you", "they", "he", "she", "it", "me",
        "us", "them", "am", "looking", "want", "need", "prefer", "like",
        "partner", "person", "someone", "anyone", "who", "whom", "whose",
        "what", "which", "where", "when", "why", "how", "and", "or", "but",
        "if", "then", "else", "not", "no", "yes", "well", "even", "less",
        "more", "much", "many", "few", "some", "any", "all", "every", "each",
    ]
)

_MAX_KEYWORDS = 50
_MIN_TOKEN_LEN = 3


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from free-text partner expectations.

    Steps:
    1. Lowercase and strip punctuation.
    2. Split on whitespace.
    3. Filter: drop tokens shorter than 3 chars, drop English stopwords.
    4. Deduplicate, return sorted list, max 50 keywords.
    """
    if not text or not text.strip():
        return []

    # Lowercase
    lowered = text.lower()

    # Strip punctuation (replace with space to avoid merging words)
    cleaned = lowered.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))

    # Split on whitespace
    tokens = cleaned.split()

    # Filter: length >= 3, not a stopword
    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        if len(token) < _MIN_TOKEN_LEN:
            continue
        if token in _STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= _MAX_KEYWORDS:
            break

    return sorted(keywords)
