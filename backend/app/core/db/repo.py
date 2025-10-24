"""Repository helpers for persistence operations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


class Repository:
    """High level persistence operations for normalized filings."""

    def __init__(self, session: Session):
        self.session = session

    # --- Person helpers -------------------------------------------------
    def get_person_by_source_id(self, *, house_id: str | None = None, senate_id: str | None = None, oge_id: str | None = None) -> models.Person | None:
        stmt = select(models.Person)
        if house_id:
            stmt = stmt.where(models.Person.house_id == house_id)
        if senate_id:
            stmt = stmt.where(models.Person.senate_id == senate_id)
        if oge_id:
            stmt = stmt.where(models.Person.oge_id == oge_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert_person(self, payload: dict[str, Any]) -> models.Person:
        person = self.get_person_by_source_id(
            house_id=payload.get("house_id"),
            senate_id=payload.get("senate_id"),
            oge_id=payload.get("oge_id"),
        )
        if person is None:
            person = models.Person(**payload)
            self.session.add(person)
        else:
            for key, value in payload.items():
                setattr(person, key, value)
        return person

    # --- Filing helpers -------------------------------------------------
    def get_filing(self, source: str, source_key: str) -> models.FilingRaw | None:
        stmt = select(models.FilingRaw).where(
            models.FilingRaw.source == source,
            models.FilingRaw.source_key == source_key,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def add_filing(
        self,
        *,
        source: str,
        source_key: str,
        doc: str | None = None,
        json_payload: dict[str, Any] | None = None,
        person: models.Person | None = None,
    ) -> models.FilingRaw:
        filing = self.get_filing(source, source_key)
        if filing is None:
            filing = models.FilingRaw(source=source, source_key=source_key, doc=doc, json=json_payload)
            if person:
                filing.person = person
            self.session.add(filing)
        else:
            filing.doc = doc or filing.doc
            filing.json = json_payload or filing.json
        return filing

    # --- Transaction helpers -------------------------------------------
    def add_transactions(
        self,
        filing: models.FilingRaw,
        records: Iterable[dict[str, Any]],
    ) -> list[models.Transaction]:
        txs: list[models.Transaction] = []
        for record in records:
            tx = models.Transaction(**record)
            tx.filing = filing
            self.session.add(tx)
            txs.append(tx)
        return txs

    # --- Positions (13F) helpers ---------------------------------------
    def add_positions(
        self,
        filing: models.FilingRaw,
        positions: Iterable[dict[str, Any]],
    ) -> list[models.Position13F]:
        pos_rows: list[models.Position13F] = []
        for payload in positions:
            pos = models.Position13F(**payload)
            pos.filing = filing
            self.session.add(pos)
            pos_rows.append(pos)
        return pos_rows


__all__ = ["Repository"]
