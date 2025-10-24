"""HTTP client helpers for the SEC EDGAR system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...config import get_settings
from ..utils.rate_limit import RateLimiter

_SETTINGS = get_settings()
_BASE_ARCHIVES = "https://www.sec.gov/Archives/"
_SUBMISSIONS_BASE = "https://data.sec.gov/submissions/"
_RATE_LIMITER = RateLimiter(rate=10, per=1.0)


@dataclass(slots=True)
class FilingDocument:
    url: str
    name: str
    type: str


async def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", _SETTINGS.sec_user_agent)
    async with _RATE_LIMITER.limit():
        async with httpx.AsyncClient(timeout=kwargs.pop("timeout", 30.0), headers=headers, follow_redirects=True) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response


async def fetch_json(url: str) -> Any:
    response = await _request("GET", url)
    return response.json()


async def fetch_text(url: str) -> str:
    response = await _request("GET", url)
    return response.text


async def fetch_bytes(url: str) -> bytes:
    response = await _request("GET", url)
    return response.content


def accession_to_cik(accession: str) -> str:
    return accession.split("-", 1)[0].lstrip("0") or "0"


async def get_filing_index(accession: str) -> dict[str, Any]:
    cik = accession_to_cik(accession)
    acc_no = accession.replace("-", "")
    url = f"{_BASE_ARCHIVES}edgar/data/{cik}/{acc_no}/index.json"

    retry = AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )

    async for attempt in retry:
        with attempt:
            return await fetch_json(url)
    raise RuntimeError("Unable to fetch index")


async def download_document(accession: str, filename: str) -> bytes:
    cik = accession_to_cik(accession)
    acc_no = accession.replace("-", "")
    url = f"{_BASE_ARCHIVES}edgar/data/{cik}/{acc_no}/{filename}"
    return await fetch_bytes(url)


async def download_form4_by_accession(accession: str) -> str:
    index = await get_filing_index(accession)
    documents = index.get("directory", {}).get("item", [])
    candidates = [doc for doc in documents if doc["type"].endswith("xml") and "form4" in doc["name"].lower()]
    if not candidates:
        raise FileNotFoundError(f"No Form 4 XML found for accession {accession}")
    filename = candidates[0]["name"]
    content = await download_document(accession, filename)
    return content.decode("utf-8", errors="replace")


async def list_recent_filings(cik: str, form_types: Iterable[str], limit: int = 10) -> list[dict[str, Any]]:
    norm_cik = cik.zfill(10)
    url = f"{_SUBMISSIONS_BASE}CIK{norm_cik}.json"
    data = await fetch_json(url)
    recent = data.get("filings", {}).get("recent", {})
    out: list[dict[str, Any]] = []
    for idx, form in enumerate(recent.get("form", [])):
        if form not in form_types:
            continue
        entry = {
            "accession": recent["accessionNumber"][idx],
            "filed": recent["filingDate"][idx],
            "primary_doc": recent["primaryDocument"][idx],
        }
        out.append(entry)
        if len(out) >= limit:
            break
    return out


__all__ = [
    "fetch_json",
    "fetch_text",
    "fetch_bytes",
    "download_form4_by_accession",
    "list_recent_filings",
    "get_filing_index",
    "FilingDocument",
]
