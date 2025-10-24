"""Parsers for Senate PTR results."""

from __future__ import annotations

from bs4 import BeautifulSoup

from ..utils.text import guess_ticker, normalize_action, normalize_date, normalize_whitespace, parse_amount_range


def parse_ptr_senate_html(html: str) -> list[dict[str, str | None]]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, str | None]] = []
    for row in soup.select("table tbody tr"):
        cells = [normalize_whitespace(cell.get_text(" ")) for cell in row.find_all("td")]
        if len(cells) < 6:
            continue
        tx_date, senator, security, tx_type, amount, comments = cells[:6]
        ticker = guess_ticker(security)
        lo, hi = parse_amount_range(amount)
        rows.append(
            {
                "tx_date": normalize_date(tx_date),
                "senator": senator,
                "security": security,
                "action": normalize_action(tx_type),
                "ticker": ticker,
                "amount": amount,
                "amount_lo": lo,
                "amount_hi": hi,
                "comments": comments,
            }
        )
    return rows


__all__ = ["parse_ptr_senate_html"]
