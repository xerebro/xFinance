"""Routers exposing SEC EDGAR filings."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..core.clients.edgar import download_form4_by_accession, list_recent_filings
from ..core.parsers.sec_form4 import parse_form4_xml
from ..core.parsers.sec_13f import parse_13f_xml

router = APIRouter(prefix="/sources/edgar", tags=["edgar"])


@router.get("/form4")
async def get_form4(accession: str = Query(..., description="SEC accession number")):
    try:
        xml = await download_form4_by_accession(accession)
    except FileNotFoundError as exc:  # pragma: no cover - network dependent
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    txns = parse_form4_xml(xml)
    return {
        "accession": accession,
        "count": len(txns),
        "transactions": [txn.model_dump() for txn in txns],
    }


@router.get("/recent")
async def get_recent_filings(
    cik: str = Query(..., description="CIK of the filer"),
    form: list[str] = Query(["4"], description="Form types to include"),
    limit: int = Query(10, le=100),
):
    filings = await list_recent_filings(cik, form, limit)
    return {"cik": cik, "filings": filings}


@router.post("/13f/parse")
async def parse_13f(xml: str):
    tables = parse_13f_xml(xml)
    return {"count": len(tables), "positions": [row.model_dump() for row in tables]}
