"""Tests for agent prompt planning and entity resolution."""

from __future__ import annotations

from backend.agent.prompt import parse_user_query
from backend.app.core.utils.entities import resolve_companies


def test_resolve_companies_multiple_matches():
    text = "Necesito comparar Apple con Microsoft y también revisar a Tesla"
    companies = resolve_companies(text)
    tickers = sorted([company.ticker for company in companies if company.ticker])
    assert tickers == ["AAPL", "MSFT", "TSLA"]


def test_parse_user_query_builds_requests():
    query = "Analiza los 10-K, 13F y la data de Yahoo Finance para Apple y Microsoft"
    plan = parse_user_query(query)
    assert {company.ticker for company in plan.companies} == {"AAPL", "MSFT"}
    assert "10-k" in plan.info_types
    assert "form 13F" in plan.info_types
    assert "yahoo" in plan.info_types
    tool_names = {request.tool for request in plan.requests}
    assert {"fetch_edgar_filings", "fetch_edgar_13f", "fetch_yahoo_quote"}.issubset(tool_names)
