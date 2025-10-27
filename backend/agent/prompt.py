"""Prompt planning utilities for the LangGraph agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..app.core.utils.entities import CompanyProfile, resolve_companies


@dataclass(slots=True)
class SourceRequest:
    """Represents a single tool invocation required by the plan."""

    request_id: str
    tool: str
    params: dict[str, object]
    company: CompanyProfile | None
    info_type: str


@dataclass(slots=True)
class ParsedPlan:
    """Structured information extracted from the user query."""

    companies: list[CompanyProfile]
    info_types: list[str]
    requests: list[SourceRequest]


_FORM_KEYWORDS: dict[str, tuple[list[str], str]] = {
    "10-k": (['10-k', '10k', '10 k'], "10-k"),
    "10-q": (['10-q', '10q', '10 q', '10-1', '10 1'], "10-q"),
    "20-f": (['20-f', '20f'], "20-f"),
    "ptr": (['ptr', 'periodic transaction', 'house ptr', 'senate ptr'], "ptr"),
    "oge": (['oge', '278e', '278-t', 'oge form'], "oge"),
    "form3": (['form 3', 'form3', 'section 16', 'insider form 3'], "form 3"),
    "form4": (['form 4', 'form4', 'insider form 4'], "form 4"),
    "form5": (['form 5', 'form5', 'insider form 5'], "form 5"),
    "form144": (['form 144', '144 filing'], "form 144"),
    "schedule13": (['schedule 13d', 'schedule 13g', '13d', '13g'], "schedule 13D/G"),
    "form13f": (['13f', 'form 13f'], "form 13F"),
    "yahoo": (['yahoo', 'yahoo finance'], "yahoo"),
}


def _detect_info_types(query: str) -> list[str]:
    lowered = query.lower()
    found: list[str] = []
    for key, (aliases, label) in _FORM_KEYWORDS.items():
        if any(alias in lowered for alias in aliases):
            found.append(label)
    # If no explicit SEC forms mentioned assume general insider focus
    if not found:
        found.extend(["10-k", "10-q", "form 4", "form 13F"])
    return list(dict.fromkeys(found))


def _plan_requests(companies: Iterable[CompanyProfile], info_types: Iterable[str]) -> list[SourceRequest]:
    plan: list[SourceRequest] = []

    def add_request(tool: str, params: dict[str, object], company: CompanyProfile | None, info: str) -> None:
        request_id = f"{tool}:{info}:{len(plan)}"
        plan.append(SourceRequest(request_id=request_id, tool=tool, params=params, company=company, info_type=info))

    info_set = list(info_types)
    companies_list = list(companies)

    for info in info_set:
        if info in {"10-k", "10-q", "20-f"}:
            form_types = {
                "10-k": ["10-K", "10-K/A"],
                "10-q": ["10-Q", "10-Q/A"],
                "20-f": ["20-F", "20-F/A"],
            }[info]
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_filings",
                    {"cik": company.cik, "forms": form_types, "limit": 5},
                    company,
                    info,
                )
        elif info == "form 4":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_form4_list",
                    {"cik": company.cik, "limit": 25},
                    company,
                    info,
                )
        elif info == "form 3":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_form3",
                    {"cik": company.cik, "limit": 10},
                    company,
                    info,
                )
        elif info == "form 5":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_form5",
                    {"cik": company.cik, "limit": 10},
                    company,
                    info,
                )
        elif info == "schedule 13D/G":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_13d_g",
                    {"cik": company.cik, "limit": 10},
                    company,
                    info,
                )
        elif info == "form 13F":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_13f",
                    {"cik": company.cik, "limit": 10},
                    company,
                    info,
                )
        elif info == "form 144":
            for company in companies_list:
                if not company.cik:
                    continue
                add_request(
                    "fetch_edgar_144",
                    {"cik": company.cik, "limit": 10},
                    company,
                    info,
                )
        elif info == "ptr":
            add_request("fetch_ptr_house", {"days": 30}, None, info)
            add_request("fetch_ptr_senate", {"days": 30}, None, info)
        elif info == "oge":
            add_request("fetch_oge_278", {"form_type": "278"}, None, info)
            add_request("fetch_oge_278_t", {"form_type": "278-T", "days": 30}, None, info)
        elif info == "yahoo":
            for company in companies_list:
                if not company.ticker:
                    continue
                add_request(
                    "fetch_yahoo_quote",
                    {"ticker": company.ticker},
                    company,
                    info,
                )

    return plan


def parse_user_query(query: str) -> ParsedPlan:
    """Parse the user request and build a plan of tool invocations."""

    companies = resolve_companies(query)
    info_types = _detect_info_types(query)
    requests = _plan_requests(companies, info_types)
    return ParsedPlan(companies=companies, info_types=info_types, requests=requests)


__all__ = ["ParsedPlan", "SourceRequest", "parse_user_query"]
