"""LangGraph agent wiring for orchestrating source fetch, normalization and storage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from langgraph.graph import END, StateGraph

from ..app.core.normalizers.transactions import (
    normalize_form4_transaction,
    normalize_ptr_record,
)
from .prompt import ParsedPlan, SourceRequest, parse_user_query
from .tools import tools


@dataclass(slots=True)
class AgentState:
    """State carried between LangGraph nodes."""

    query: str
    plan: ParsedPlan | None = None
    requests: list[SourceRequest] = field(default_factory=list)
    raw_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    normalized: dict[str, dict[str, Any]] = field(default_factory=dict)
    enriched: dict[str, dict[str, Any]] = field(default_factory=dict)
    storage: dict[str, dict[str, Any]] = field(default_factory=dict)
    answer: dict[str, Any] = field(default_factory=dict)


def _get_tool(name: str):
    return next(tool for tool in tools if tool.name == name)


async def source_select(state: AgentState) -> AgentState:
    plan = parse_user_query(state.query)
    state.plan = plan
    state.requests = plan.requests
    return state


async def fetcher(state: AgentState) -> AgentState:
    results: dict[str, dict[str, Any]] = {}
    for request in state.requests:
        tool = _get_tool(request.tool)
        payload = await tool.ainvoke(request.params)
        results[request.request_id] = {"request": request, "data": payload}
    state.raw_results = results
    return state


async def normalizer(state: AgentState) -> AgentState:
    normalized: dict[str, dict[str, Any]] = {}
    for request_id, bundle in state.raw_results.items():
        request: SourceRequest = bundle["request"]
        data: dict[str, Any] = bundle["data"]
        normalized_payload: Any
        if request.tool == "fetch_edgar_form4":
            transactions = [normalize_form4_transaction(txn) for txn in data.get("transactions", [])]
            normalized_payload = [asdict(txn) for txn in transactions]
        elif request.tool in {"fetch_ptr_house", "fetch_ptr_senate"}:
            transactions = [normalize_ptr_record(row) for row in data.get("results", [])]
            normalized_payload = [asdict(txn) for txn in transactions]
        else:
            normalized_payload = data
        normalized[request_id] = {
            "info_type": request.info_type,
            "tool": request.tool,
            "company": request.company.to_dict() if request.company else None,
            "data": normalized_payload,
        }
    state.normalized = normalized
    return state


async def enricher(state: AgentState) -> AgentState:
    enriched: dict[str, dict[str, Any]] = {}
    for request_id, payload in state.normalized.items():
        company = payload.get("company") or {}
        data = payload.get("data")
        if isinstance(data, list):
            enriched_rows: list[Any] = []
            for row in data:
                if isinstance(row, dict):
                    row = dict(row)
                    row.setdefault("ticker", company.get("ticker"))
                    row.setdefault("cik", company.get("cik"))
                    enriched_rows.append(row)
                else:
                    enriched_rows.append(row)
            payload = {**payload, "data": enriched_rows}
        enriched[request_id] = payload
    state.enriched = enriched
    return state


async def store(state: AgentState) -> AgentState:
    # In lieu of a full persistence layer, keep the enriched payload for downstream usage.
    state.storage = state.enriched
    return state


async def answer(state: AgentState) -> AgentState:
    summary: list[str] = []
    for payload in state.enriched.values():
        company = payload.get("company") or {}
        label = company.get("name") or company.get("ticker") or "General"
        data = payload.get("data")
        if isinstance(data, dict):
            if "filings" in data:
                count = len(data.get("filings", []))
            elif "results" in data:
                results = data.get("results", [])
                count = len(results) if isinstance(results, list) else 1
            elif "quote" in data:
                count = 1 if data.get("quote") else 0
            else:
                count = len(data)
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 1 if data else 0
        summary.append(f"{label}: {payload.get('info_type')} → {count} registros")
    state.answer = {
        "companies": [company.to_dict() for company in (state.plan.companies if state.plan else [])],
        "info_types": state.plan.info_types if state.plan else [],
        "summary": summary,
    }
    return state


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("SourceSelect", source_select)
    graph.add_node("Fetcher", fetcher)
    graph.add_node("Normalizer", normalizer)
    graph.add_node("Enricher", enricher)
    graph.add_node("Store", store)
    graph.add_node("Answer", answer)

    graph.set_entry_point("SourceSelect")
    graph.add_edge("SourceSelect", "Fetcher")
    graph.add_edge("Fetcher", "Normalizer")
    graph.add_edge("Normalizer", "Enricher")
    graph.add_edge("Enricher", "Store")
    graph.add_edge("Store", "Answer")
    graph.add_edge("Answer", END)
    return graph


__all__ = ["build_graph", "AgentState"]
