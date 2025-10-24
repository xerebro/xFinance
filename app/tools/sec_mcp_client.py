from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client
except Exception as exc:  # noqa: BLE001
    ClientSession = Any  # type: ignore[assignment]
    stdio_client = None  # type: ignore[assignment]


class SECTools:
    """Cliente asíncrono para el servidor MCP de la SEC."""

    def __init__(self) -> None:
        self.proc: Optional[subprocess.Popen[bytes]] = None
        self.session: Optional[ClientSession] = None
        self._lock = asyncio.Lock()

    async def _ensure(self) -> None:
        if self.session is not None:
            return
        async with self._lock:
            if self.session is not None:
                return
            server_path = Path(__file__).resolve().parents[2] / "mcp_servers" / "sec_edgar" / "main.py"
            env = os.environ.copy()
            env.setdefault("PYTHONUNBUFFERED", "1")
            self.proc = subprocess.Popen(
                ["python", str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            if stdio_client is None:
                raise RuntimeError("La librería MCP no está disponible")
            self.session = await stdio_client(self.proc.stdin, self.proc.stdout)  # type: ignore[arg-type]
            await self.session.initialize()

    async def _call(self, tool_name: str, **kwargs: Any) -> Any:
        await self._ensure()
        if not self.session:
            raise RuntimeError("Sesión MCP no inicializada")
        tools = await self.session.list_tools()
        if tool_name not in [t.name for t in tools.tools]:
            raise RuntimeError(f"Tool {tool_name} no expuesto por MCP")
        result = await self.session.call_tool(tool_name, kwargs)
        if not result.content:
            return None
        payload = result.content[0].text
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

    async def get_cik(self, ticker: str) -> str:
        data = await self._call("get_cik", ticker=ticker)
        if isinstance(data, dict):
            return data.get("cik") or ""
        return str(data)

    async def ticker_from_cik(self, cik: str) -> str:
        data = await self._call("ticker_from_cik", cik=cik)
        if isinstance(data, dict):
            return data.get("ticker") or ""
        return str(data)

    async def list_filings(self, cik: str, forms: List[str], years: List[int]) -> List[Dict[str, Any]]:
        data = await self._call("list_filings", cik=cik, forms=forms, years=years)
        return data or []

    async def get_filing_docs(self, cik: str, accession: str, prefer_html: bool = True) -> List[str]:
        data = await self._call(
            "get_filing_docs",
            cik=cik,
            accession=accession,
            prefer_html=prefer_html,
        )
        return data or []

    async def extract_sections(
        self, urls: List[str], form: str, accession: str, cik: str
    ) -> Dict[str, Any]:
        return await self._call(
            "extract_sections",
            urls=urls,
            form=form,
            accession=accession,
            cik=cik,
        )

    async def get_companyfacts(self, cik: str) -> Dict[str, Any]:
        return await self._call("get_companyfacts", cik=cik)

    async def shutdown(self) -> None:
        if self.session:
            await self.session.close()
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.session = None
        self.proc = None
