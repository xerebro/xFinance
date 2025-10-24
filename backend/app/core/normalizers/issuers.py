"""Issuer normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..utils.text import fuzzy_match, normalize_whitespace


@dataclass(slots=True)
class IssuerRecord:
    name: str
    ticker: str | None = None
    cik: str | None = None
    cusip: str | None = None

    def key(self) -> str:
        return normalize_whitespace(self.name).lower()


def dedupe_issuers(records: Iterable[IssuerRecord]) -> list[IssuerRecord]:
    cache: dict[str, IssuerRecord] = {}
    for record in records:
        key = record.key()
        if key in cache:
            existing = cache[key]
            for field in ("ticker", "cik", "cusip"):
                value = getattr(record, field)
                if value and not getattr(existing, field):
                    setattr(existing, field, value)
        else:
            cache[key] = record
    return list(cache.values())


def match_issuer(name: str, choices: Iterable[str]) -> tuple[str | None, float]:
    return fuzzy_match(name, choices)


__all__ = ["IssuerRecord", "dedupe_issuers", "match_issuer"]
