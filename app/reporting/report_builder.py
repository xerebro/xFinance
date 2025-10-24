from __future__ import annotations

from datetime import date
from typing import List, Tuple

from ..schemas import ReportBundle, SourceRef


def build_markdown_report(state) -> Tuple[str, List[SourceRef]]:
    lines: List[str] = []
    cites: List[SourceRef] = []
    hdr = f"# Reporte de empresa(s) — {date.today().isoformat()}\n"
    lines.append(hdr)
    lines.append("> Este reporte es informativo y no constituye asesoría financiera.\n")
    for company in state.get("companies", []):
        ticker = company.ticker or "(s/d)"
        lines.append(f"## {ticker}\n")
        analysis = state.get("analysis", {}).get(ticker)
        if analysis:
            lines.append(analysis + "\n")
        extracts = [
            e
            for e in state.get("extracts", [])
            if e.company.cik == company.cik and company.cik is not None
        ]
        for ex in extracts:
            lines.append(f"### {ex.form} ({ex.accession})\n")
            if ex.sections.get("risk_factors"):
                lines.append(
                    "#### Riesgos (Item 1A / 3D)\n" + ex.sections["risk_factors"][:3000] + "\n"
                )
            if ex.sections.get("mdna"):
                lines.append("#### MD&A (Item 7)\n" + ex.sections["mdna"][:3000] + "\n")
            if ex.sections.get("financials"):
                lines.append(
                    "#### Estados financieros (Item 8)\n" + ex.sections["financials"][:3000] + "\n"
                )
            cites.extend(ex.sources)
    lines.append("\n## Mercado\n")
    for ticker, snap in state.get("market", {}).items():
        lines.append(
            f"- **{ticker}** precio: {snap.price}, capitalización: {snap.market_cap}, "
            f"EV: {snap.enterprise_value}\n"
        )
        cites.extend(snap.sources)
    markdown = "\n".join(lines)
    return markdown, cites
