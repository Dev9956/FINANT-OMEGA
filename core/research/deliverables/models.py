"""FININT OMEGA — Research deliverables models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class DeliverableType(str, Enum):
    RESEARCH_MEMO = "research_memo"
    INVESTMENT_THESIS = "investment_thesis"
    COMPANY_REPORT = "company_report"
    SECTOR_REPORT = "sector_report"
    PORTFOLIO_REPORT = "portfolio_report"
    RISK_REPORT = "risk_report"
    COMPARISON_REPORT = "comparison_report"
    EXECUTIVE_SUMMARY = "executive_summary"
    CSV_EXPORT = "csv_export"
    JSON_PACKAGE = "json_package"
    MARKDOWN_REPORT = "markdown_report"


class ReportSection(BaseModel):
    """A section of a research deliverable."""

    section_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    charts_config: dict = Field(default_factory=dict)


class DeliverableMetadata(BaseModel):
    """Metadata for a research deliverable."""

    research_id: str = ""
    data_versions: dict[str, str] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    model_metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchDeliverable(BaseModel):
    """A complete research deliverable."""

    deliverable_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deliverable_type: DeliverableType
    title: str
    sections: list[ReportSection] = Field(default_factory=list)
    metadata: DeliverableMetadata = Field(default_factory=DeliverableMetadata)
    content_format: str = "markdown"
