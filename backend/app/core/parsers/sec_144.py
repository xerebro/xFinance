"""Parser for Form 144 text filings."""

from __future__ import annotations

import re

from ..utils.text import normalize_whitespace

ISSUER_RE = re.compile(r"Name of Issuer\s*:\s*(.+)", re.IGNORECASE)
AFFILIATE_RE = re.compile(r"Relationship to Issuer\s*:\s*(.+)", re.IGNORECASE)
SECURITY_RE = re.compile(r"Title of the Securities\s*:\s*(.+)", re.IGNORECASE)
SHARES_RE = re.compile(r"Number of Shares\s*:\s*([\d,]+)", re.IGNORECASE)
PRICE_RE = re.compile(r"Proposed Sale Price\s*:\s*\$?([\d\.]+)", re.IGNORECASE)


def parse_form144_text(text: str) -> dict[str, str | None]:
    clean = normalize_whitespace(text)
    return {
        "issuer": _search(ISSUER_RE, clean),
        "relationship": _search(AFFILIATE_RE, clean),
        "security": _search(SECURITY_RE, clean),
        "shares": _search(SHARES_RE, clean),
        "price": _search(PRICE_RE, clean),
    }


def _search(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1).strip() if match else None


__all__ = ["parse_form144_text"]
