from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.constants import END
from langgraph.graph import StateGraph

from .reporting.report_builder import build_markdown_report
from .schemas import (
    CompanySpec,
    MarketSnapshot,
    RetrievalSpec,
    SectionExtract,
    SourceRef,
)
from .tools.sec_mcp_client import SECTools
from .tools.yahoo_client import YahooClient

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    query: str
    companies: List[CompanySpec]
    retrieval: RetrievalSpec
    extracts: List[SectionExtract]
    market: Dict[str, MarketSnapshot]
    analysis: Dict[str, str]
    combined_summary: str
    citations: List[SourceRef]
    markdown: str
    messages: List[Dict[str, Any]]
    job_id: str


_sec_client = SECTools()
_yahoo_client = YahooClient()


def _get_llm() -> Optional[AzureChatOpenAI]:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat-gpt-5-nano")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    if not (endpoint and key and deployment):
        logger.warning("Azure OpenAI environment variables missing. Falling back to heuristic analysis.")
        return None
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        deployment_name=deployment,
        api_version=api_version,
        temperature=0.2,
    )


async def _llm_plan(query: str, companies: List[CompanySpec]) -> str:
    llm = _get_llm()
    if not llm:
        companies_str = ", ".join(filter(None, [c.ticker or c.cik for c in companies])) or "empresas"
        return (
            "Plan inicial: resolver identificadores de las compañías (tickers/CIK), "
            "descargar filings relevantes de la SEC, obtener métricas de mercado y sintetizar el reporte "
            f"para {companies_str}."
        )
    result = await llm.ainvoke(
        [
            SystemMessage(
                content="Eres un analista financiero que planifica una investigación multi-compañía"
            ),
            HumanMessage(
                content=(
                    "Construye un plan conciso (3-4 pasos) para analizar las compañías siguientes: "
                    f"{companies}. Consulta 10-K/10-Q/20-F recientes y métricas de mercado."
                )
            ),
        ]
    )
    return result.content if hasattr(result, "content") else str(result)


async def plan_node(state: AgentState) -> AgentState:
    plan = await _llm_plan(state.get("query", ""), state.get("companies", []))
    messages = list(state.get("messages", []))
    messages.append({"role": "system", "content": plan})
    state["messages"] = messages
    return state


async def resolve_entities(state: AgentState) -> AgentState:
    companies: List[CompanySpec] = []
    for comp in state.get("companies", []):
        if comp.cik and comp.ticker:
            companies.append(comp)
            continue
        try:
            if not comp.cik and comp.ticker:
                cik = await _sec_client.get_cik(comp.ticker)
                comp = CompanySpec(ticker=comp.ticker, cik=cik)
            elif not comp.ticker and comp.cik:
                ticker = await _sec_client.ticker_from_cik(comp.cik)
                comp = CompanySpec(ticker=ticker, cik=comp.cik)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to resolve entity", exc_info=exc)
        companies.append(comp)
    state["companies"] = companies
    messages = list(state.get("messages", []))
    messages.append({
        "role": "status",
        "content": "Identidades de compañías resueltas.",
    })
    state["messages"] = messages
    return state


async def fetch_edgar(state: AgentState) -> AgentState:
    retrieval = state.get("retrieval")
    if not retrieval:
        return state
    extracts: List[SectionExtract] = list(state.get("extracts", []))
    for company in state.get("companies", []):
        if not company.cik:
            continue
        try:
            filings = await _sec_client.list_filings(
                cik=company.cik,
                forms=retrieval.forms,
                years=retrieval.years,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unable to list filings", exc_info=exc)
            continue
        for filing in filings or []:
            accession = filing.get("accession") or filing.get("adsh")
            if not accession:
                continue
            try:
                docs = await _sec_client.get_filing_docs(
                    cik=company.cik,
                    accession=accession,
                    prefer_html=True,
                )
                section_data = await _sec_client.extract_sections(
                    urls=docs,
                    form=filing.get("form", ""),
                    accession=accession,
                    cik=company.cik,
                )
                section = SectionExtract(**section_data)
                if not section.company.ticker and company.ticker:
                    section.company = CompanySpec(ticker=company.ticker, cik=company.cik)
                extracts.append(section)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to process filing", exc_info=exc)
    state["extracts"] = extracts
    messages = list(state.get("messages", []))
    messages.append({
        "role": "status",
        "content": f"Descarga de filings completada ({len(extracts)} extractos).",
    })
    state["messages"] = messages
    return state


async def fetch_yahoo(state: AgentState) -> AgentState:
    market: Dict[str, MarketSnapshot] = dict(state.get("market", {}))
    for company in state.get("companies", []):
        ticker = company.ticker
        if not ticker:
            continue
        if ticker in market:
            continue
        try:
            snapshot = await _yahoo_client.snapshot(ticker)
            market[ticker] = snapshot
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch Yahoo snapshot", exc_info=exc)
    state["market"] = market
    messages = list(state.get("messages", []))
    messages.append({
        "role": "status",
        "content": "Métricas de mercado recuperadas de Yahoo Finance.",
    })
    state["messages"] = messages
    return state


async def analyze(state: AgentState) -> AgentState:
    analysis = dict(state.get("analysis", {}))
    llm = _get_llm()
    for company in state.get("companies", []):
        ticker = company.ticker or company.cik or "Empresa"
        if ticker in analysis:
            continue
        extracts = [e for e in state.get("extracts", []) if e.company.cik == company.cik]
        market = state.get("market", {}).get(company.ticker or "", None)
        if llm:
            summary_prompt = (
                "Genera un resumen ejecutivo (3-4 viñetas) usando los siguientes datos. "
                "Incluye riesgos y señales cuantitativas cuando existan.\n"
            )
            context: Dict[str, Any] = {
                "extracts": [e.model_dump() for e in extracts],
                "market": market.model_dump() if market else {},
            }
            try:
                result = await llm.ainvoke(
                    [
                        SystemMessage(
                            content="Eres un analista financiero prudente. Usa un tono neutral y cita hechos."
                        ),
                        HumanMessage(content=f"{summary_prompt}\nDatos: {json.dumps(context)[:6000]}")
                    ]
                )
                analysis_text = result.content if hasattr(result, "content") else str(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("LLM analysis failed", exc_info=exc)
                analysis_text = _heuristic_analysis(extracts, market)
        else:
            analysis_text = _heuristic_analysis(extracts, market)
        analysis[ticker] = analysis_text
    state["analysis"] = analysis
    messages = list(state.get("messages", []))
    messages.append({
        "role": "status",
        "content": "Análisis sintetizado.",
    })
    state["messages"] = messages
    return state


async def write_report(state: AgentState) -> AgentState:
    markdown, cites = build_markdown_report(state)
    state["markdown"] = markdown
    state.setdefault("citations", [])
    state["citations"].extend(cites)
    state.setdefault("combined_summary", "")
    if not state["combined_summary"]:
        combined = []
        for ticker, summary in state.get("analysis", {}).items():
            combined.append(f"### {ticker}\n{summary}")
        state["combined_summary"] = "\n\n".join(combined)
    messages = list(state.get("messages", []))
    messages.append({
        "role": "final",
        "content": "Reporte generado.",
    })
    state["messages"] = messages
    return state


def _heuristic_analysis(extracts: List[SectionExtract], market: Optional[MarketSnapshot]) -> str:
    bullets: List[str] = []
    if market and market.price is not None:
        bullets.append(f"Precio actual: {market.price:.2f} USD")
    if market and market.market_cap is not None:
        bullets.append(f"Capitalización: {market.market_cap:,.0f} USD")
    if extracts:
        latest = extracts[0]
        for key, label in {
            "risk_factors": "Riesgos",
            "mdna": "MD&A",
        }.items():
            text = latest.sections.get(key)
            if text:
                bullets.append(f"{label}: {text[:200]}...")
    bullets.append("Nota: análisis heurístico sin LLM.")
    return "\n".join(f"- {b}" for b in bullets)


# Build the graph
builder = StateGraph(AgentState)

builder.add_node("Plan", plan_node)
builder.add_node("ResolveEntities", resolve_entities)
builder.add_node("FetchEDGAR", fetch_edgar)
builder.add_node("FetchYahoo", fetch_yahoo)
builder.add_node("Analyze", analyze)
builder.add_node("WriteReport", write_report)

builder.set_entry_point("Plan")

builder.add_edge("Plan", "ResolveEntities")
builder.add_edge("ResolveEntities", "FetchEDGAR")
builder.add_edge("ResolveEntities", "FetchYahoo")
builder.add_edge("FetchEDGAR", "Analyze")
builder.add_edge("FetchYahoo", "Analyze")
builder.add_edge("Analyze", "WriteReport")
builder.add_edge("WriteReport", END)


graph = builder.compile()
