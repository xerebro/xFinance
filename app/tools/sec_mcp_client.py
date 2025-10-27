from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client


class SECTools:
    """Cliente asíncrono para el servidor MCP de la SEC."""

    def __init__(self) -> None:
        self._session_cm: Optional[Any] = None
        self._client_session_cm: Optional[Any] = None
        self.session: Optional[ClientSession] = None

    async def _ensure(self) -> None:
        """Inicializa una sesión MCP por stdio hacia el server 'sec_edgar'."""
        if self.session is not None:
            return

        # Ajusta la ruta si tu server MCP vive en otra carpeta
        repo_root = Path(__file__).resolve().parents[2]
        server_path = repo_root / "mcp_servers" / "sec_edgar" / "main.py"

        server = StdioServerParameters(
            command="python",
            args=[str(server_path)],
            cwd=str(server_path.parent),
            env={
                **get_default_environment(),
                "SEC_USER_AGENT": os.getenv(
                    "SEC_USER_AGENT",
                    "xFinance/0.1 (contacto@example.com)",
                ),
            },
        )

        # Correcto: pasar StdioServerParameters a stdio_client
        self._session_cm = stdio_client(server)
        stdio, write = await self._session_cm.__aenter__()
        self._client_session_cm = ClientSession(stdio, write)
        self.session = await self._client_session_cm.__aenter__()
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
        if self._client_session_cm is not None:
            await self._client_session_cm.__aexit__(None, None, None)
            self._client_session_cm = None
        if self._session_cm is not None:
            await self._session_cm.__aexit__(None, None, None)
            self._session_cm = None
        self.session = None
