"""Unified search router for normalized data."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import models
from ..core.db.repo import Repository
from ..deps import get_db

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def unified_search(
    q: str | None = Query(None, description="Free text query"),
    person: str | None = Query(None, description="Person name filter"),
    ticker: str | None = Query(None, description="Ticker filter"),
    db: Session = Depends(get_db),
):
    repo = Repository(db)
    stmt = select(models.Transaction).join(models.FilingRaw)
    if ticker:
        stmt = stmt.where(models.Transaction.ticker == ticker.upper())
    if person:
        stmt = stmt.join(models.Person).where(models.Person.full_name.ilike(f"%{person}%"))
    results = db.execute(stmt.limit(100)).scalars().all()
    response = [
        {
            "tx_id": str(row.tx_id),
            "tx_date": row.tx_date.isoformat() if row.tx_date else None,
            "ticker": row.ticker,
            "amount": float(row.amount) if row.amount else None,
            "action": row.action,
        }
        for row in results
    ]
    return {"count": len(response), "transactions": response}
