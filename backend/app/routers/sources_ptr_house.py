"""Router exposing House PTR scraping utilities."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from ..core.clients.house import download_ptr_document, list_ptr_house
from ..core.parsers.ptr_house import parse_ptr_house_html

router = APIRouter(prefix="/sources/ptr", tags=["ptr"])


@router.get("/house")
async def get_ptr_house(
    start: date = Query(..., description="Start date for filings"),
    end: date = Query(..., description="End date for filings"),
):
    listings = await list_ptr_house(start, end)
    parsed_rows: list[dict[str, str | None]] = []
    for item in listings:
        url = item.get("doc_url")
        if not url:
            continue
        content = await download_ptr_document(url)
        parsed_rows.extend(parse_ptr_house_html(content.decode("utf-8", errors="ignore")))
    return {"count": len(parsed_rows), "rows": parsed_rows}
