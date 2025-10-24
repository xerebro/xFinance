"""Router exposing OGE filings."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..core.clients.oge import download_filing, search_filings
from ..core.parsers.oge_278 import parse_oge_text

router = APIRouter(prefix="/sources/oge", tags=["oge"])


@router.get("/")
async def search(
    person: str | None = Query(None, description="Person name"),
    year: int | None = Query(None, description="Filing year"),
    form_type: str | None = Query(None, description="Form type, e.g. 278e or 278-t"),
):
    results = await search_filings(person=person, year=year, form_type=form_type)
    return {"count": len(results), "results": results}


@router.post("/parse")
async def parse(document_url: str):
    raw = await download_filing(document_url)
    text = raw.decode("utf-8", errors="ignore")
    parsed = parse_oge_text(text)
    return {"count": len(parsed), "rows": parsed}
