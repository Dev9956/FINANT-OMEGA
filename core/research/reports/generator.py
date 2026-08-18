"""FININT OMEGA — Report generator for research outputs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ReportFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class ReportSection(BaseModel):
    """A section of a research report."""

    title: str
    content: str
    order: int = 0
    subsections: list["ReportSection"] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """A complete research report."""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    subject: str = ""
    sections: list[ReportSection] = Field(default_factory=list)
    summary: str = ""
    sources: list[str] = Field(default_factory=list)
    format: ReportFormat = ReportFormat.MARKDOWN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class ReportGenerator:
    """Generate structured research reports from collected data."""

    def __init__(self) -> None:
        self._templates: dict[str, list[str]] = {}

    def register_template(self, name: str, section_titles: list[str]) -> None:
        self._templates[name] = section_titles

    def create_report(self, title: str, sections: list[dict], subject: str = "", sources: list[str] | None = None, **metadata) -> ResearchReport:
        report_sections = [
            ReportSection(
                title=s.get("title", f"Section {i+1}"),
                content=s.get("content", ""),
                order=i,
            )
            for i, s in enumerate(sections)
        ]
        summary = report_sections[0].content[:200] + "..." if report_sections else ""
        return ResearchReport(
            title=title, subject=subject, sections=report_sections,
            summary=summary, sources=sources or [], metadata=metadata,
        )

    def generate_from_template(self, template_name: str, title: str, content_map: dict[str, str], subject: str = "") -> ResearchReport:
        section_titles = self._templates.get(template_name, [])
        sections = [{"title": t, "content": content_map.get(t, "")} for t in section_titles]
        return self.create_report(title=title, sections=sections, subject=subject)

    def render_markdown(self, report: ResearchReport) -> str:
        parts = [f"# {report.title}\n"]
        if report.summary:
            parts.append(f"**Summary:** {report.summary}\n")
        for section in sorted(report.sections, key=lambda s: s.order):
            parts.append(f"## {section.title}\n")
            parts.append(f"{section.content}\n")
        if report.sources:
            parts.append("## Sources\n")
            for src in report.sources:
                parts.append(f"- {src}")
        return "\n".join(parts)

    def render_text(self, report: ResearchReport) -> str:
        parts = [report.title, "=" * len(report.title), ""]
        if report.summary:
            parts.append(f"Summary: {report.summary}")
            parts.append("")
        for section in sorted(report.sections, key=lambda s: s.order):
            parts.append(f"--- {section.title} ---")
            parts.append(section.content)
            parts.append("")
        return "\n".join(parts)
