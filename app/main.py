from __future__ import annotations
import json
import uuid
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import PlainTextResponse, StreamingResponse

from .agent_graph import AgentState, graph
from .schemas import CompanySpec, ReportBundle, RetrievalSpec

app = FastAPI(title="xFinance Agent")

REPORT_STORE: Dict[str, ReportBundle] = {}


@app.get("/health")
async def health() -> Dict[str, bool]:
    return {"ok": True}


async def _serialize_state(state: AgentState) -> str:
    payload = jsonable_encoder(state)
    return json.dumps(payload, ensure_ascii=False)


@app.post("/api/agent/run")
async def run_agent(request: Request) -> StreamingResponse:
    body = await request.json()
    job_id = str(uuid.uuid4())

    async def event_stream() -> AsyncGenerator[str, None]:
        retrieval_payload = body.get("retrieval") or {"years": []}
        if not retrieval_payload.get("years"):
            from datetime import datetime

            current_year = datetime.utcnow().year
            retrieval_payload["years"] = [current_year]
        state: AgentState = {
            "job_id": job_id,
            "query": body.get("query", ""),
            "companies": [CompanySpec(**c) for c in body.get("companies", [])],
            "retrieval": RetrievalSpec(**retrieval_payload),
            "extracts": [],
            "market": {},
            "analysis": {},
            "citations": [],
            "messages": [],
        }
        yield f"event: job\ndata: {json.dumps({'jobId': job_id})}\n\n"
        last_state: AgentState | None = None
        async for updated_state in graph.astream(state):
            last_state = updated_state
            chunk = await _serialize_state(updated_state)
            yield f"data: {chunk}\n\n"
        if last_state is not None:
            bundle = ReportBundle(
                companies=last_state.get("companies", []),
                retrieval=last_state.get("retrieval"),
                extracts=last_state.get("extracts", []),
                market=last_state.get("market", {}),
                analysis=last_state.get("analysis", {}),
                combined_summary=last_state.get("combined_summary", ""),
                citations=last_state.get("citations", []),
                markdown=last_state.get("markdown", ""),
            )
            REPORT_STORE[job_id] = bundle
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/report/{job_id}")
async def get_report(job_id: str, format: str = "json") -> Any:
    bundle = REPORT_STORE.get(job_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if format == "markdown":
        return PlainTextResponse(bundle.markdown, media_type="text/markdown")
    return bundle
