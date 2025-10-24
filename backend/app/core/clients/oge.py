"""Client utilities for the OGE 278e/278-T portal."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...config import get_settings
from ..utils.rate_limit import RateLimiter

_SETTINGS = get_settings()
_SEARCH_ENDPOINT = "https://www.oge.gov/api/filing-search"
_RATE_LIMITER = RateLimiter(rate=1, per=1.0)


async def _client() -> httpx.AsyncClient:
    headers = {"User-Agent": _SETTINGS.sec_user_agent, "Accept": "application/json"}
    return httpx.AsyncClient(timeout=45.0, headers=headers, follow_redirects=True)


async def search_filings(person: str | None = None, year: int | None = None, form_type: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "format": "json",
        "formType": form_type or "278",
    }
    if person:
        params["q"] = person
    if year:
        params["year"] = year

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
                    response = await client.get(_SEARCH_ENDPOINT, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    return payload.get("results", [])
    return []


async def download_filing(document_url: str) -> bytes:
    async with await _client() as client:
        async with _RATE_LIMITER.limit():
            response = await client.get(document_url)
            response.raise_for_status()
            return response.content


__all__ = ["search_filings", "download_filing"]
