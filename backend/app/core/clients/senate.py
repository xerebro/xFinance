"""Client helpers for U.S. Senate eFD portal."""

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
_BASE_URL = "https://efdsearch.senate.gov/search"
_RATE_LIMITER = RateLimiter(rate=1, per=1.0)


async def _client() -> httpx.AsyncClient:
    headers = {"User-Agent": _SETTINGS.sec_user_agent, "Referer": _BASE_URL}
    cookies = {"efd_consent": "true"}
    return httpx.AsyncClient(timeout=45.0, headers=headers, follow_redirects=True, cookies=cookies)


async def list_ptr_senate(start: date, end: date) -> list[dict[str, Any]]:
    params = {
        "startDate": start.strftime("%m/%d/%Y"),
        "endDate": end.strftime("%m/%d/%Y"),
        "include": "PTR",
        "reportType": "transaction",
    }

    retry = AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )

    async for attempt in retry:
        with attempt:
            async with await _client() as client:
                async with _RATE_LIMITER.limit():
                    response = await client.get(f"{_BASE_URL}/report/results/", params=params)
                    response.raise_for_status()
                    return _parse_results(response.text)
    return []


def _parse_results(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, Any]] = []
    for row in soup.select("table tbody tr"):
        cells = [normalize_whitespace(cell.get_text(" ")) for cell in row.find_all("td")]
        if len(cells) < 6:
            continue
        link = row.find("a")
        href = link.get("href") if link else None
        out.append(
            {
                "filed_date": cells[0],
                "senator": cells[1],
                "ptr_type": cells[2],
                "doc_url": href,
                "description": cells[3],
                "amount": cells[4],
            }
        )
    return out


async def download_ptr_senate(url: str) -> bytes:
    async with await _client() as client:
        async with _RATE_LIMITER.limit():
            response = await client.get(url)
            response.raise_for_status()
            return response.content


__all__ = ["list_ptr_senate", "download_ptr_senate"]
