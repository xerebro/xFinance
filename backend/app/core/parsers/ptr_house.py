"""Parsers for House PTR documents."""

from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup

from ..utils.text import guess_ticker, normalize_action, normalize_date, normalize_whitespace, parse_amount_range

AMOUNT_RANGE = re.compile(r"\$?[\d,]+\s*[\-–]\s*\$?[\d,]+")


def parse_ptr_house_html(html: str) -> list[dict[str, str | None]]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, str | None]] = []
    for row in soup.select("table tr"):
        cells = [normalize_whitespace(cell.get_text(" ")) for cell in row.find_all("td")]
        if len(cells) < 5:
            continue
        tx_date, owner, security, tx_type, amount = cells[:5]
        ticker = guess_ticker(security)
        lo, hi = parse_amount_range(amount)
        rows.append(
            {
                "tx_date": normalize_date(tx_date),
                "owner": owner,
                "security": security,
                "action": normalize_action(tx_type),
                "ticker": ticker,
                "amount": amount,
                "amount_lo": lo,
                "amount_hi": hi,
            }
        )
    return rows


def parse_ptr_house_text(text: str) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    lines = [normalize_whitespace(line) for line in text.splitlines() if line.strip()]
    buffer: list[str] = []
    for line in lines:
        if normalize_date(line):
            if buffer:
                rows.extend(_flush_buffer(buffer))
                buffer = []
        buffer.append(line)
    if buffer:
        rows.extend(_flush_buffer(buffer))
    return rows


def _flush_buffer(lines: Iterable[str]) -> list[dict[str, str | None]]:
    lines = list(lines)
    if len(lines) < 3:
        return []
    tx_date = normalize_date(lines[0])
    security_line = lines[1]
    action_line = next((line for line in lines if "purchase" in line.lower() or "sale" in line.lower()), "")
    amount_line = next((line for line in lines if AMOUNT_RANGE.search(line)), "")
    ticker = guess_ticker(security_line)
    lo, hi = parse_amount_range(amount_line)
    return [
        {
            "tx_date": tx_date,
            "owner": None,
            "security": security_line,
            "action": normalize_action(action_line),
            "ticker": ticker,
            "amount": amount_line,
            "amount_lo": lo,
            "amount_hi": hi,
        }
    ]


__all__ = ["parse_ptr_house_html", "parse_ptr_house_text"]
