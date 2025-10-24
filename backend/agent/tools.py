"""LangChain tool definitions for the xFinance data sources."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from langchain.tools import StructuredTool

from ..app.core.clients.edgar import download_form4_by_accession, list_recent_filings
from ..app.core.clients.house import list_ptr_house
from ..app.core.clients.senate import list_ptr_senate
from ..app.core.clients.oge import search_filings
from ..app.core.parsers.sec_form4 import parse_form4_xml


async def _fetch_form4(accession: str) -> dict[str, Any]:
    xml = await download_form4_by_accession(accession)
    txns = parse_form4_xml(xml)
    return {"accession": accession, "transactions": [txn.model_dump() for txn in txns]}


async def _fetch_recent_form4(cik: str, days: int = 30) -> dict[str, Any]:
    filings = await list_recent_filings(cik, ["4"], limit=50)
    return {"cik": cik, "filings": filings}


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


async def _search_oge(person: str | None = None, year: int | None = None) -> dict[str, Any]:
    results = await search_filings(person=person, year=year)
    return {"results": results}


tools = [
    StructuredTool.from_function(_fetch_form4, name="fetch_edgar_form4", description="Download and parse Form 4 by accession"),
    StructuredTool.from_function(_fetch_recent_form4, name="list_edgar_form4", description="List recent Form 4 filings for a CIK"),
    StructuredTool.from_function(_fetch_ptr_house, name="fetch_ptr_house", description="List House PTR filings in the past N days"),
    StructuredTool.from_function(_fetch_ptr_senate, name="fetch_ptr_senate", description="List Senate PTR filings in the past N days"),
    StructuredTool.from_function(_search_oge, name="fetch_oge_278", description="Search OGE 278 filings"),
]


__all__ = ["tools"]
