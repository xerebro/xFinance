"""LangGraph agent wiring for orchestrating source fetch, normalization and storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from ..app.core.normalizers.transactions import normalize_form4_transaction
from .tools import tools


@dataclass
class AgentState:
    query: str
    source: Literal["ptr_house", "ptr_senate", "oge", "edgar_form4"] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    normalized: list[dict[str, Any]] = field(default_factory=list)


async def source_select(state: AgentState) -> Literal["fetch_form4", "fetch_ptr", "fetch_oge"]:
    if "form4" in (state.query or "").lower():
        state.source = "edgar_form4"
        return "fetch_form4"
    if "senate" in state.query.lower():
        state.source = "ptr_senate"
        return "fetch_ptr"
    if "oge" in state.query.lower():
        state.source = "oge"
        return "fetch_oge"
    state.source = "ptr_house"
    return "fetch_ptr"


async def fetch_form4(state: AgentState) -> AgentState:
    tool = next(tool for tool in tools if tool.name == "fetch_edgar_form4")
    result = await tool.ainvoke({"accession": state.payload.get("accession")})
    state.payload = result
    state.normalized = [normalize_form4_transaction(txn) for txn in result["transactions"]]
    return state


async def fetch_ptr(state: AgentState) -> AgentState:
    tool_name = "fetch_ptr_senate" if state.source == "ptr_senate" else "fetch_ptr_house"
    tool = next(tool for tool in tools if tool.name == tool_name)
    result = await tool.ainvoke({"days": state.payload.get("days", 30)})
    state.payload = result
    state.normalized = result.get("results", [])
    return state


async def fetch_oge(state: AgentState) -> AgentState:
    tool = next(tool for tool in tools if tool.name == "fetch_oge_278")
    result = await tool.ainvoke({
        "person": state.payload.get("person"),
        "year": state.payload.get("year"),
    })
    state.payload = result
    state.normalized = result.get("results", [])
    return state


async def finalize(state: AgentState) -> AgentState:
    return state


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("SourceSelect", source_select)
    graph.add_node("FetchForm4", fetch_form4)
    graph.add_node("FetchPTR", fetch_ptr)
    graph.add_node("FetchOGE", fetch_oge)
    graph.add_node("Answer", finalize)

    graph.set_entry_point("SourceSelect")
    graph.add_conditional_edges(
        "SourceSelect",
        source_select,
        {
            "fetch_form4": "FetchForm4",
            "fetch_ptr": "FetchPTR",
            "fetch_oge": "FetchOGE",
        },
    )
    graph.add_edge("FetchForm4", "Answer")
    graph.add_edge("FetchPTR", "Answer")
    graph.add_edge("FetchOGE", "Answer")
    graph.add_edge("Answer", END)
    return graph


__all__ = ["build_graph", "AgentState"]
