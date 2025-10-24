"""Person-centric normalization utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..utils.text import normalize_whitespace


@dataclass(slots=True)
class PersonRecord:
    full_name: str
    chamber: str | None = None
    role: str | None = None
    house_id: str | None = None
    senate_id: str | None = None
    oge_id: str | None = None
    cik: str | None = None

    def slug(self) -> str:
        return normalize_whitespace(self.full_name).lower()


def dedupe_people(records: Iterable[PersonRecord]) -> list[PersonRecord]:
    seen: dict[str, PersonRecord] = {}
    for record in records:
        key = record.slug()
        if key in seen:
            existing = seen[key]
            for field in ("chamber", "role", "house_id", "senate_id", "oge_id", "cik"):
                value = getattr(record, field)
                if value and not getattr(existing, field):
                    setattr(existing, field, value)
        else:
            seen[key] = record
    return list(seen.values())


__all__ = ["PersonRecord", "dedupe_people"]
