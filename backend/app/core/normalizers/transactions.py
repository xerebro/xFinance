"""Transaction normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..utils.text import normalize_action, normalize_date, parse_amount_range


@dataclass(slots=True)
class TransactionRecord:
    filing_id: str | None
    person_id: str | None
    issuer_id: str | None
    tx_date: date | None
    action: str
    quantity: float | None
    price: float | None
    amount: float | None
    ticker: str | None
    cik: str | None
    notes: str | None = None


def normalize_ptr_record(raw: dict[str, str]) -> TransactionRecord:
    lo, hi = parse_amount_range(raw.get("amount", ""))
    amount = hi if hi is not None else lo
    tx_date = normalize_date(raw.get("tx_date", ""))
    return TransactionRecord(
        filing_id=None,
        person_id=None,
        issuer_id=None,
        tx_date=tx_date,
        action=normalize_action(raw.get("action", "")),
        quantity=None,
        price=None,
        amount=amount,
        ticker=raw.get("ticker"),
        cik=raw.get("cik"),
        notes=raw.get("security"),
    )


def compute_amount(quantity: float | None, price: float | None) -> float | None:
    if quantity is None or price is None:
        return None
    return float(quantity) * float(price)


def normalize_form4_transaction(raw: dict[str, str | float | None]) -> TransactionRecord:
    amount = compute_amount(raw.get("shares"), raw.get("price"))
    tx_date = normalize_date(str(raw.get("tx_date", "")))
    return TransactionRecord(
        filing_id=None,
        person_id=None,
        issuer_id=None,
        tx_date=tx_date,
        action=normalize_action(str(raw.get("tx_code", ""))),
        quantity=raw.get("shares"),
        price=raw.get("price"),
        amount=amount,
        ticker=raw.get("issuer_ticker"),
        cik=raw.get("issuer_cik"),
        notes=raw.get("security_title"),
    )


__all__ = [
    "TransactionRecord",
    "normalize_ptr_record",
    "normalize_form4_transaction",
    "compute_amount",
]
