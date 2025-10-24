"""Parser for Schedule 13D/G text and HTML filings."""

from __future__ import annotations

import re
from typing import Iterable

from selectolax.parser import HTMLParser

from ..utils.text import normalize_whitespace

ITEM_RE = re.compile(r"Item\s+(\d+)\.\s*(.*)", re.IGNORECASE)
PERCENT_RE = re.compile(r"([\d\.]+)%")


def parse_13d_html(html: str) -> list[dict[str, str | None]]:
    tree = HTMLParser(html)
    sections: list[dict[str, str | None]] = []
    for node in tree.css("body *"):
        text = normalize_whitespace(node.text())
        if not text:
            continue
        match = ITEM_RE.match(text)
        if match:
            sections.append({"item": match.group(1), "title": match.group(2), "content": text})
    return sections


def parse_13d_text(text: str) -> list[dict[str, str | None]]:
    sections: list[dict[str, str | None]] = []
    current: dict[str, str | None] | None = None
    for line in text.splitlines():
        clean = normalize_whitespace(line)
        if not clean:
            continue
        match = ITEM_RE.match(clean)
        if match:
            if current:
                sections.append(current)
            current = {"item": match.group(1), "title": match.group(2), "content": clean}
        elif current:
            current["content"] += " " + clean
    if current:
        sections.append(current)
    return sections


def extract_percentages(sections: Iterable[dict[str, str | None]]) -> list[float]:
    values: list[float] = []
    for section in sections:
        text = section.get("content") or ""
        for match in PERCENT_RE.finditer(text):
            try:
                values.append(float(match.group(1)))
            except ValueError:  # pragma: no cover - defensive
                continue
    return values


__all__ = ["parse_13d_html", "parse_13d_text", "extract_percentages"]
