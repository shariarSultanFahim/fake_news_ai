"""Preprocessing utilities matching training pipeline exactly as specified in AGENT.md section 2."""

from typing import Tuple
import unicodedata
from normalizer import normalize


def is_bangla_char(char: str) -> bool:
    """Check if character is within Bangla Unicode block (U+0980 to U+09FF)."""
    return '\u0980' <= char <= '\u09FF'


def is_letter_or_bangla(char: str) -> bool:
    """
    Check if a character is considered a letter/character.
    Includes characters in the Bangla Unicode block (U+0980 to U+09FF excluding punctuation/symbols)
    and general alphabetic letters (category starting with 'L').
    """
    if is_bangla_char(char):
        # Exclude Bangla punctuation (Po), symbols (So/Sc), unassigned (Cn)
        cat = unicodedata.category(char)
        return cat not in ('Po', 'So', 'Sc', 'Cn')
    return unicodedata.category(char).startswith('L')


def bangla_ratio(text: str) -> float:
    """
    Calculate the ratio of Bangla letters to all letters.
    Section 3 Rule 1: 'fewer than 50% of the letters in headline + content are Bangla (Unicode block U+0980 to U+09FF).'
    Returns 0.0 if there are no letters.
    """
    letters = [ch for ch in text if is_letter_or_bangla(ch)]
    if not letters:
        return 0.0
    bangla_count = sum(1 for ch in letters if is_bangla_char(ch))
    return bangla_count / len(letters)


def count_words(text: str) -> int:
    """Count words split by whitespace."""
    return len(text.strip().split())


def preprocess_inputs(
    headline: str,
    content: str,
    uses_normalizer: bool = True
) -> Tuple[str, str, bool]:
    """
    Apply preprocessing to headline and content.
    1. Strip whitespace.
    2. Normalize if uses_normalizer is true using csebuetnlp normalizer with default arguments.
    3. Truncation logic: if headline has > 100 words, cap at 100 words (mark truncated=True).
    """
    headline = (headline or "").strip()
    content = (content or "").strip()

    truncated = False

    if uses_normalizer:
        if headline:
            headline = normalize(headline)
        if content:
            content = normalize(content)

    words = headline.split()
    if len(words) > 100:
        headline = " ".join(words[:100])
        truncated = True

    return headline, content, truncated
