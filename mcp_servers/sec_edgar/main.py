from __future__ import annotations

import asyncio
import json
import os
import re
import time
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import mcp
except ImportError as exc:  # noqa: BLE001
    raise RuntimeError("La librería MCP es obligatoria para ejecutar el servidor SEC") from exc

SEC_BASE = "https://data.sec.gov"
UA = os.getenv("SEC_USER_AGENT", "xFinance/1.0 (contact: you@example.com)")
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.timestamp = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self.lock:
                now = time.monotonic()
                elapsed = now - self.timestamp
                if elapsed > 0:
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                    self.timestamp = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
            await asyncio.sleep(0.05)


bucket = TokenBucket(capacity=8, refill_rate=8)
_client: Optional[httpx.AsyncClient] = None
_company_cache: Optional[Dict[str, Dict[str, str]]] = None


async def _client_factory() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60)
    return _client


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(4))
async def _get_json(client: httpx.AsyncClient, url: str) -> Dict:
    await bucket.acquire()
    resp = await client.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    resp.raise_for_status()
    return resp.json()


async def _get_text(client: httpx.AsyncClient, url: str) -> str:
    await bucket.acquire()
    resp = await client.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    resp.raise_for_status()
    return resp.text


async def _load_company_map() -> Dict[str, Dict[str, str]]:
    global _company_cache
    if _company_cache is not None:
        return _company_cache
    client = await _client_factory()
    data = await _get_json(client, COMPANY_TICKERS_URL)
    cache: Dict[str, Dict[str, str]] = {}
    for entry in data.values():
        ticker = (entry.get("ticker") or "").upper()
        if not ticker:
            continue
        cache[ticker] = {
            "cik": str(entry.get("cik_str")),
            "title": entry.get("title", ""),
        }
    _company_cache = cache
    return cache


@mcp.tool()
async def get_cik(ticker: str) -> Dict[str, str]:
    mapping = await _load_company_map()
    info = mapping.get(ticker.upper())
    if not info:
        raise ValueError(f"Ticker {ticker} no encontrado en el índice SEC")
    return {"ticker": ticker.upper(), "cik": str(info["cik"]).zfill(10)}


@mcp.tool()
async def ticker_from_cik(cik: str) -> Dict[str, str]:
    mapping = await _load_company_map()
    target = str(int(cik)).zfill(10)
    for ticker, info in mapping.items():
        if str(info["cik"]).zfill(10) == target:
            return {"ticker": ticker, "cik": target}
    raise ValueError(f"CIK {cik} no encontrado")


@mcp.tool()
async def list_filings(cik: str, forms: List[str], years: List[int]) -> List[Dict]:
    cik10 = str(int(cik)).zfill(10)
    client = await _client_factory()
    submissions = await _get_json(client, f"{SEC_BASE}/submissions/CIK{cik10}.json")
    result: List[Dict] = []
    filings = submissions.get("filings", {}).get("recent", {})
    forms_recent = filings.get("form", [])
    accession = filings.get("accessionNumber", [])
    filing_date = filings.get("filingDate", [])
    if not forms_recent:
        return result
    forms_set = {f.upper() for f in forms}
    years_set = {int(y) for y in years}
    for idx, form in enumerate(forms_recent):
        if form.upper() not in forms_set:
            continue
        acc = accession[idx]
        date = filing_date[idx]
        if years_set and int(date.split("-")[0]) not in years_set:
            continue
        result.append({"form": form, "accession": acc, "filing_date": date})
        if len(result) >= 20:
            break
    return result


@mcp.tool()
async def get_filing_docs(cik: str, accession: str, prefer_html: bool = True) -> List[str]:
    client = await _client_factory()
    cik_trim = str(int(cik))
    acc_nodash = accession.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_trim}/{acc_nodash}/index.json"
    idx = await _get_json(client, index_url)
    docs: List[str] = []
    for item in idx.get("directory", {}).get("item", []):
        name = item.get("name", "")
        if prefer_html:
            if name.lower().endswith((".htm", ".html")):
                docs.append(index_url.replace("index.json", name))
        else:
            if name.lower().endswith((".pdf", ".htm", ".html")):
                docs.append(index_url.replace("index.json", name))
    return docs[:5]


ITEM_PATTERNS = {
    "risk_factors": [r"item\s*1a\.?\s*risk\s*factors", r"item\s*3d\.?\s*risk\s*factors"],
    "mdna": [r"item\s*7\.?\s*management's\s*discussion", r"operating\s*and\s*financial\s*review"],
    "financials": [r"item\s*8\.?\s*financial\s*statements", r"consolidated\s*financial\s*statements"],
}


@mcp.tool()
async def extract_sections(urls: List[str], form: str, accession: str, cik: str) -> Dict:
    text_by_section: Dict[str, str] = {k: "" for k in ITEM_PATTERNS}
    sources: List[Dict] = []
    client = await _client_factory()
    for url in urls:
        if not url.lower().endswith((".htm", ".html")):
            continue
        try:
            html = await _get_text(client, url)
        except httpx.HTTPStatusError:
            continue
        sources.append({"kind": "sec", "title": form, "url": url})
        soup = BeautifulSoup(html, "lxml")
        body = soup.get_text("\n", strip=True)
        lower = body.lower()
        for key, patterns in ITEM_PATTERNS.items():
            if text_by_section[key]:
                continue
            for pattern in patterns:
                match = re.search(pattern, lower)
                if match:
                    start = match.start()
                    next_match = re.search(r"\nitem\s+\d+[a-z]?\.", lower[start + 10 :])
                    end = start + 10 + (next_match.start() if next_match else len(lower))
                    text_by_section[key] = body[start:end][:20000]
                    break
    return {
        "accession": accession,
        "form": form,
        "filing_date": "",
        "company": {"ticker": "", "cik": str(int(cik)).zfill(10)},
        "sections": text_by_section,
        "sources": sources,
    }


@mcp.tool()
async def get_companyfacts(cik: str) -> Dict:
    client = await _client_factory()
    cik10 = str(int(cik)).zfill(10)
    return await _get_json(client, f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik10}.json")


if __name__ == "__main__":
    mcp.run()
