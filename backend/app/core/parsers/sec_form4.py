"""Parser for SEC Form 4 XML ownership filings."""

from __future__ import annotations

from datetime import date

from lxml import etree
from pydantic import BaseModel


class Form4Txn(BaseModel):
    issuer_cik: str
    issuer_ticker: str | None
    reporting_owner: str
    is_director: bool | None
    is_officer: bool | None
    officer_title: str | None
    tx_code: str
    security_title: str
    tx_date: date
    shares: float | None
    price: float | None


TXN_XPATHS = [
    ("nonDerivativeTable", ".//nonDerivativeTransaction"),
    ("derivativeTable", ".//derivativeTransaction"),
]


def parse_form4_xml(xml_text: str) -> list[Form4Txn]:
    root = etree.fromstring(xml_text.encode())
    issuer_cik = root.findtext("issuer/issuerCik")
    ticker = root.findtext("issuer/issuerTradingSymbol")
    owner_name = root.findtext("reportingOwner/reportingOwnerId/rptOwnerName")
    director = root.findtext("reportingOwner/reportingOwnerRelationship/isDirector") == "1"
    officer = root.findtext("reportingOwner/reportingOwnerRelationship/isOfficer") == "1"
    officer_title = root.findtext("reportingOwner/reportingOwnerRelationship/officerTitle")

    out = []
    for _, xp in TXN_XPATHS:
        for tx in root.findall(xp):
            tx_date_raw = tx.findtext("transactionDate/value") or ""
            shares_raw = tx.findtext("transactionAmounts/transactionShares/value")
            price_raw = tx.findtext("transactionAmounts/transactionPricePerShare/value")
            out.append(
                Form4Txn(
                    issuer_cik=issuer_cik,
                    issuer_ticker=ticker,
                    reporting_owner=owner_name,
                    is_director=director,
                    is_officer=officer,
                    officer_title=officer_title,
                    tx_code=(tx.findtext("transactionCoding/transactionCode") or "").strip(),
                    security_title=(tx.findtext("securityTitle/value") or "").strip(),
                    tx_date=(tx_date_raw or ""),
                    shares=float(shares_raw) if shares_raw else None,
                    price=float(price_raw) if price_raw else None,
                )
            )
    return out


__all__ = ["parse_form4_xml", "Form4Txn"]
