from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import yfinance as yf

from ..schemas import MarketSnapshot, SectionExtract, SourceRef


class YahooClient:
    async def snapshot(self, ticker: str) -> MarketSnapshot:
        t = yf.Ticker(ticker)
        info = getattr(t, "fast_info", {}) or {}
        basics = getattr(t, "info", {}) or {}
        metrics = {}
        pe = basics.get("trailingPE") or basics.get("forwardPE")
        if pe is not None:
            metrics["pe"] = float(pe)
        ps = basics.get("priceToSalesTrailing12Months")
        if ps is not None:
            metrics["ps"] = float(ps)
        ebitda = basics.get("ebitda")
        if ebitda is not None:
            metrics["ebitda"] = float(ebitda)
        ev = basics.get("enterpriseValue") or info.get("enterprise_value")
        market_cap = basics.get("marketCap") or info.get("market_cap")
        price = info.get("last_price") or basics.get("currentPrice")
        return MarketSnapshot(
            ticker=ticker,
            as_of=datetime.now(timezone.utc).isoformat(),
            price=float(price) if price is not None else None,
            market_cap=float(market_cap) if market_cap is not None else None,
            enterprise_value=float(ev) if ev is not None else None,
            metrics=metrics,
            sources=[
                SourceRef(
                    kind="yahoo",
                    title=f"Yahoo Finance {ticker}",
                    url=f"https://finance.yahoo.com/quote/{ticker}",
                )
            ],
        )

    async def simple_scorecard(
        self, ticker: str, snapshot: MarketSnapshot, extracts: List[SectionExtract]
    ) -> str:
        bullets = []
        pe = snapshot.metrics.get("pe")
        if pe is not None and pe < 15:
            bullets.append("Valoración P/E por debajo de 15 (aparente infravaloración relativa).")
        has_risks = any(
            ex.sections.get("risk_factors") for ex in extracts if ex.company.ticker == ticker
        )
        if has_risks:
            bullets.append("Riesgos materiales identificados en 10-K/20-F recientes.")
        if not bullets:
            bullets.append("Sin señales destacadas.")
        return "\n".join(f"- {b}" for b in bullets)
