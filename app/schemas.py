from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CompanySpec(BaseModel):
    ticker: Optional[str] = None
    cik: Optional[str] = None


class RetrievalSpec(BaseModel):
    forms: List[str] = Field(
        default_factory=lambda: ["10-K", "10-Q", "20-F"], description="SEC form types"
    )
    years: List[int]

    def model_post_init(self, __context: Dict[str, object] | None) -> None:  # type: ignore[override]
        # Normalise forms to uppercase and trim whitespace
        self.forms = [f.strip().upper() for f in self.forms if f.strip()]


class SourceRef(BaseModel):
    kind: str  # "sec" | "yahoo"
    title: str
    url: str
    meta: Dict[str, str] = Field(default_factory=dict)


class SectionExtract(BaseModel):
    accession: str
    form: str
    filing_date: str
    company: CompanySpec
    sections: Dict[str, str]
    sources: List[SourceRef] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    ticker: str
    as_of: str
    price: Optional[float]
    market_cap: Optional[float]
    enterprise_value: Optional[float]
    metrics: Dict[str, float] = Field(default_factory=dict)
    sources: List[SourceRef] = Field(default_factory=list)


class ReportBundle(BaseModel):
    companies: List[CompanySpec]
    retrieval: RetrievalSpec
    extracts: List[SectionExtract] = Field(default_factory=list)
    market: Dict[str, MarketSnapshot] = Field(default_factory=dict)
    analysis: Dict[str, str] = Field(default_factory=dict)
    combined_summary: str = ""
    citations: List[SourceRef] = Field(default_factory=list)
    markdown: str = ""
