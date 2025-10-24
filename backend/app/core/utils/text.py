"""Text normalization utilities for ticker and name parsing."""

from __future__ import annotations

import difflib
import re
from datetime import datetime
from typing import Iterable

RANGE_RE = re.compile(r"\$?([\d,]+)(?:\s*[\-–]\s*\$?([\d,]+))?", re.UNICODE)
TICKER_RE = re.compile(r"\b([A-Z]{1,5})(?:\s*\)|\b)")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def guess_ticker(text: str) -> str | None:
    match = TICKER_RE.search(text or "")
    return match.group(1) if match else None


def parse_amount_range(raw: str) -> tuple[float | None, float | None]:
    if not raw:
        return (None, None)
    match = RANGE_RE.search(raw.replace(",", ""))
    if not match:
        return (None, None)
    lo = float(match.group(1)) if match.group(1) else None
    hi = float(match.group(2)) if match.group(2) else None
    return (lo, hi)


def normalize_date(raw: str) -> str | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_action(raw: str) -> str:
    token = (raw or "").lower()
    if "purchase" in token or token in {"p", "buy"}:
        return "buy"
    if "sale" in token or token in {"s", "sell"}:
        return "sell"
    if "gift" in token:
        return "gift"
    return "other"


def fuzzy_match(name: str, candidates: Iterable[str]) -> tuple[str | None, float]:
    sequence = difflib.SequenceMatcher()
    sequence.set_seq1(name.lower())
    best_score = 0.0
    best_candidate = None
    for candidate in candidates:
        sequence.set_seq2(candidate.lower())
        score = sequence.ratio() * 100
        if score > best_score:
            best_score = score
            best_candidate = candidate
    return best_candidate, best_score


__all__ = [
    "normalize_whitespace",
    "guess_ticker",
    "parse_amount_range",
    "normalize_date",
    "normalize_action",
    "fuzzy_match",
]
