"""Client helpers for the Clerk of the House PTR portal."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...config import get_settings
from ..utils.rate_limit import RateLimiter
from ..utils.text import normalize_whitespace

_SETTINGS = get_settings()
_SEARCH_URL = "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/ViewMemberSearchResult"
_RATE_LIMITER = RateLimiter(rate=2, per=1.0)


async def _client() -> httpx.AsyncClient:
    headers = {"User-Agent": _SETTINGS.sec_user_agent, "Referer": _SEARCH_URL}
    return httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True)


async def list_ptr_house(start: date, end: date) -> list[dict[str, Any]]:
    """List Periodic Transaction Reports published by the House Clerk."""

    form_data = {
        "startDate": start.strftime("%m/%d/%Y"),
        "endDate": end.strftime("%m/%d/%Y"),
        "searchType": "ptr",
    }

    retry = AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )

    async for attempt in retry:
        with attempt:
            async with _RATE_LIMITER.limit():
                async with await _client() as client:
                    response = await client.post(_SEARCH_URL, data=form_data)
                    response.raise_for_status()
                    return _parse_search_results(response.text)
    return []


def _parse_search_results(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, Any]] = []
    for tr in soup.select("table tbody tr"):
        cells = [normalize_whitespace(td.get_text(" ")) for td in tr.find_all("td")]
        if len(cells) < 5:
            continue
        link = tr.find("a")
        href = link.get("href") if link else None
        rows.append(
            {
                "filed_date": cells[0],
                "member": cells[1],
                "description": cells[2],
                "ptr_type": cells[3],
                "doc_url": href,
            }
        )
    return rows


async def download_ptr_document(url: str) -> bytes:
    async with await _client() as client:
        async with _RATE_LIMITER.limit():
            response = await client.get(url)
            response.raise_for_status()
            return response.content


__all__ = ["list_ptr_house", "download_ptr_document"]
