"""LangChain tool definitions for the xFinance data sources."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable

import httpx
from langchain.tools import StructuredTool

from ..app.core.clients.edgar import download_form4_by_accession, list_recent_filings
from ..app.core.clients.house import list_ptr_house
from ..app.core.clients.senate import list_ptr_senate
from ..app.core.clients.oge import search_filings
from ..app.core.parsers.sec_form4 import parse_form4_xml
from ..app.core.utils.rate_limit import RateLimiter

_YAHOO_LIMITER = RateLimiter(rate=5, per=1.0)


async def _fetch_form4(accession: str) -> dict[str, Any]:
    xml = await download_form4_by_accession(accession)
    txns = parse_form4_xml(xml)
    return {"accession": accession, "transactions": [txn.model_dump() for txn in txns]}


async def _fetch_form_list(cik: str, forms: Iterable[str], limit: int = 25) -> dict[str, Any]:
    filings = await list_recent_filings(cik, forms, limit=limit)
    return {"cik": cik, "forms": list(forms), "filings": filings}


async def _fetch_form4_list(cik: str, limit: int = 25) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["4"], limit)


async def _fetch_form3_list(cik: str, limit: int = 10) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["3"], limit)


async def _fetch_form5_list(cik: str, limit: int = 10) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["5"], limit)


async def _fetch_13d_g_list(cik: str, limit: int = 10) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["SC 13D", "SC 13G"], limit)


async def _fetch_13f_list(cik: str, limit: int = 10) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["13F-HR", "13F-NT"], limit)


async def _fetch_144_list(cik: str, limit: int = 10) -> dict[str, Any]:
    return await _fetch_form_list(cik, ["144"], limit)


async def _fetch_ptr_house(days: int = 30) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=days)
    listings = await list_ptr_house(start, end)
    return {"start": start.isoformat(), "end": end.isoformat(), "results": listings}


async def _fetch_ptr_senate(days: int = 30) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=days)
    listings = await list_ptr_senate(start, end)
    return {"start": start.isoformat(), "end": end.isoformat(), "results": listings}


async def _search_oge(person: str | None = None, year: int | None = None, form_type: str | None = None) -> dict[str, Any]:
    results = await search_filings(person=person, year=year, form_type=form_type)
    return {"results": results, "form_type": form_type or "278"}


async def _fetch_yahoo_quote(ticker: str) -> dict[str, Any]:
    symbol = ticker.upper()
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": symbol}
    async with _YAHOO_LIMITER.limit():
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    results = payload.get("quoteResponse", {}).get("result", [])
    quote = results[0] if results else {}
    return {"ticker": symbol, "quote": quote}


tools = [
    StructuredTool.from_function(
        _fetch_form4,
        name="fetch_edgar_form4",
        description="Download and parse Form 4 by accession",
    ),
    StructuredTool.from_function(
        _fetch_form_list,
        name="fetch_edgar_filings",
        description="List recent EDGAR filings for specified form types",
    ),
    StructuredTool.from_function(
        _fetch_form4_list,
        name="fetch_edgar_form4_list",
        description="List recent Form 4 filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_form3_list,
        name="fetch_edgar_form3",
        description="List recent Form 3 filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_form5_list,
        name="fetch_edgar_form5",
        description="List recent Form 5 filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_13d_g_list,
        name="fetch_edgar_13d_g",
        description="List Schedule 13D/13G filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_13f_list,
        name="fetch_edgar_13f",
        description="List recent Form 13F filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_144_list,
        name="fetch_edgar_144",
        description="List Form 144 filings for a CIK",
    ),
    StructuredTool.from_function(
        _fetch_ptr_house,
        name="fetch_ptr_house",
        description="List House PTR filings in the past N days",
    ),
    StructuredTool.from_function(
        _fetch_ptr_senate,
        name="fetch_ptr_senate",
        description="List Senate PTR filings in the past N days",
    ),
    StructuredTool.from_function(
        _search_oge,
        name="fetch_oge_278",
        description="Search OGE Form 278 filings",
    ),
    StructuredTool.from_function(
        lambda form_type="278-T", person=None, year=None, days=30: _search_oge(
            person=person, year=year, form_type=form_type
        ),
        name="fetch_oge_278_t",
        description="Search OGE Form 278-T (periodic transaction) filings",
    ),
    StructuredTool.from_function(
        _fetch_yahoo_quote,
        name="fetch_yahoo_quote",
        description="Fetch latest market snapshot from Yahoo Finance",
    ),
]


__all__ = ["tools"]
