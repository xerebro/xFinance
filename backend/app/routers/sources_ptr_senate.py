"""Router exposing Senate PTR fetching."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from ..core.clients.senate import download_ptr_senate, list_ptr_senate
from ..core.parsers.ptr_senate import parse_ptr_senate_html

router = APIRouter(prefix="/sources/ptr", tags=["ptr"])


@router.get("/senate")
async def get_ptr_senate(
    start: date = Query(..., description="Start date"),
    end: date = Query(..., description="End date"),
):
    listings = await list_ptr_senate(start, end)
    parsed_rows: list[dict[str, str | None]] = []
    for item in listings:
        url = item.get("doc_url")
        if not url:
            continue
        content = await download_ptr_senate(url)
        parsed_rows.extend(parse_ptr_senate_html(content.decode("utf-8", errors="ignore")))
    return {"count": len(parsed_rows), "rows": parsed_rows}
