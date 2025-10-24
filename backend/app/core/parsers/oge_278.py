"""Parser utilities for OGE Form 278 filings."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.text import normalize_action, normalize_date, normalize_whitespace, parse_amount_range

SECTION_HEADER = re.compile(r"^Part\s+(?:1|2|3)", re.IGNORECASE)


def parse_oge_text(text: str) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    current_section: str | None = None
    for line in text.splitlines():
        clean = normalize_whitespace(line)
        if not clean:
            continue
        if SECTION_HEADER.match(clean):
            current_section = clean
            continue
        if "transaction" in clean.lower() or "purchase" in clean.lower() or "sale" in clean.lower():
            parsed = _parse_transaction_line(clean, current_section)
            if parsed:
                rows.append(parsed)
    return rows


def _parse_transaction_line(line: str, section: str | None) -> dict[str, str | None] | None:
    tokens = line.split(" ")
    date_token = next((token for token in tokens if normalize_date(token)), None)
    amount_lo, amount_hi = parse_amount_range(line)
    if not date_token and amount_lo is None and amount_hi is None:
        return None
    return {
        "section": section,
        "tx_date": normalize_date(date_token or ""),
        "description": line,
        "amount": line,
        "amount_lo": amount_lo,
        "amount_hi": amount_hi,
        "action": normalize_action(line),
    }


__all__ = ["parse_oge_text"]
