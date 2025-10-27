"""Entity resolution helpers for companies and identifiers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .text import normalize_whitespace


@dataclass(slots=True)
class CompanyProfile:
    """Small record capturing identifier data for an issuer/company."""

    name: str
    ticker: str | None = None
    cik: str | None = None
    cusip: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "ticker": self.ticker,
            "cik": self.cik,
            "cusip": self.cusip,
        }


_COMPANY_DATA: dict[str, dict[str, str | None]] = {
    "apple": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "cik": "0000320193",
        "cusip": "037833100",
    },
    "microsoft": {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "cik": "0000789019",
        "cusip": "594918104",
    },
    "google": {
        "name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "cik": "0001652044",
        "cusip": "02079K305",
    },
    "tesla": {
        "name": "Tesla, Inc.",
        "ticker": "TSLA",
        "cik": "0001318605",
        "cusip": "88160R101",
    },
    "amazon": {
        "name": "Amazon.com, Inc.",
        "ticker": "AMZN",
        "cik": "0001018724",
        "cusip": "023135106",
    },
    "nvidia": {
        "name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "cik": "0001045810",
        "cusip": "67066G104",
    },
}

_ALIASES: dict[str, str] = {
    "apple": "apple",
    "apple inc": "apple",
    "aapl": "apple",
    "microsoft": "microsoft",
    "msft": "microsoft",
    "google": "google",
    "alphabet": "google",
    "alphabet inc": "google",
    "googl": "google",
    "tesla": "tesla",
    "tesla inc": "tesla",
    "tsla": "tesla",
    "amazon": "amazon",
    "amazon.com": "amazon",
    "amzn": "amazon",
    "nvidia": "nvidia",
    "nvidia corporation": "nvidia",
    "nvda": "nvidia",
}

_UPPER_STOPWORDS = {"SEC", "PTR", "OGE", "FORM", "EDGAR", "USA", "NYSE", "NASDAQ"}


def _company_from_key(key: str) -> CompanyProfile:
    payload = _COMPANY_DATA[key]
    return CompanyProfile(
        name=payload["name"] or key.title(),
        ticker=payload.get("ticker"),
        cik=payload.get("cik"),
        cusip=payload.get("cusip"),
    )


def _dedupe(companies: Iterable[CompanyProfile]) -> list[CompanyProfile]:
    seen: dict[str, CompanyProfile] = {}
    for company in companies:
        key = company.ticker or company.cik or company.name.lower()
        if key in seen:
            existing = seen[key]
            if not existing.cik and company.cik:
                existing.cik = company.cik
            if not existing.ticker and company.ticker:
                existing.ticker = company.ticker
            if not existing.cusip and company.cusip:
                existing.cusip = company.cusip
        else:
            seen[key] = company
    return list(seen.values())


def resolve_companies(text: str) -> list[CompanyProfile]:
    """Resolve company mentions within free text into structured profiles."""

    lowered = normalize_whitespace(text.lower())
    matches: list[CompanyProfile] = []
    for alias, key in _ALIASES.items():
        if alias in lowered:
            matches.append(_company_from_key(key))

    # Detect uppercase tickers directly mentioned in the prompt
    uppercase_tokens = set(re.findall(r"\b[A-Z]{1,5}\b", text or ""))
    for token in uppercase_tokens:
        if token in _UPPER_STOPWORDS:
            continue
        key = _ALIASES.get(token.lower()) or _ALIASES.get(token)
        if key:
            matches.append(_company_from_key(key))

    return _dedupe(matches)


__all__ = ["CompanyProfile", "resolve_companies"]
