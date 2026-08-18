"""FININT OMEGA — Deliverable generator for research outputs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from core.research.deliverables.models import (
    DeliverableMetadata,
    DeliverableType,
    ReportSection,
    ResearchDeliverable,
)


class DeliverableGenerator:
    """Generate structured research deliverables."""

    def generate(self, deliverable_type: DeliverableType, research_data: dict[str, Any]) -> ResearchDeliverable:
        """Route to the appropriate generator based on deliverable type."""
        generators = {
            DeliverableType.RESEARCH_MEMO: self.generate_research_memo,
            DeliverableType.COMPANY_REPORT: self.generate_company_report,
            DeliverableType.SECTOR_REPORT: self.generate_sector_report,
            DeliverableType.COMPARISON_REPORT: self.generate_comparison_report,
            DeliverableType.EXECUTIVE_SUMMARY: self.generate_executive_summary,
            DeliverableType.INVESTMENT_THESIS: self._generate_investment_thesis,
            DeliverableType.PORTFOLIO_REPORT: self._generate_portfolio_report,
            DeliverableType.RISK_REPORT: self._generate_risk_report,
        }
        generator = generators.get(deliverable_type, self.generate_research_memo)
        return generator(research_data)

    def generate_research_memo(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a research memo."""
        title = data.get("title", "Research Memo")
        sections = [
            ReportSection(
                title="Investment Thesis",
                content=data.get("thesis", "No thesis provided."),
                evidence_ids=data.get("evidence_ids", []),
            ),
            ReportSection(
                title="Key Metrics",
                content=self._format_metrics(data.get("metrics", {})),
            ),
            ReportSection(
                title="Risks",
                content=data.get("risks", "No risks identified."),
            ),
            ReportSection(
                title="Recommendation",
                content=data.get("recommendation", "No recommendation provided."),
            ),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.RESEARCH_MEMO,
            title=title,
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def generate_company_report(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a company report."""
        symbol = data.get("symbol", "UNKNOWN")
        title = data.get("title", f"{symbol} Company Report")
        sections = [
            ReportSection(
                title="Company Overview",
                content=data.get("overview", f"Analysis of {symbol}."),
            ),
            ReportSection(
                title="Financial Summary",
                content=self._format_metrics(data.get("metrics", {})),
                evidence_ids=data.get("evidence_ids", []),
            ),
            ReportSection(
                title="Valuation",
                content=data.get("valuation", "Valuation analysis pending."),
            ),
            ReportSection(
                title="Competitive Position",
                content=data.get("competitive", "Competitive analysis pending."),
            ),
            ReportSection(
                title="Risks & Catalysts",
                content=data.get("risks", "Risk assessment pending."),
            ),
            ReportSection(
                title="Recommendation",
                content=data.get("recommendation", "No recommendation."),
            ),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.COMPANY_REPORT,
            title=title,
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def generate_sector_report(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a sector report."""
        sector = data.get("sector", "Unknown Sector")
        title = data.get("title", f"{sector} Sector Report")
        sections = [
            ReportSection(
                title="Sector Overview",
                content=data.get("overview", f"Analysis of the {sector} sector."),
            ),
            ReportSection(
                title="Key Players",
                content=data.get("key_players", "Key players analysis pending."),
            ),
            ReportSection(
                title="Sector Metrics",
                content=self._format_metrics(data.get("metrics", {})),
                evidence_ids=data.get("evidence_ids", []),
            ),
            ReportSection(
                title="Trends & Outlook",
                content=data.get("trends", "Trend analysis pending."),
            ),
            ReportSection(
                title="Risks",
                content=data.get("risks", "Sector risks pending."),
            ),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.SECTOR_REPORT,
            title=title,
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def generate_comparison_report(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a comparison report."""
        entities = data.get("entities", [])
        title = data.get("title", f"Comparison: {', '.join(entities)}")
        sections = [
            ReportSection(
                title="Entities Compared",
                content=", ".join(entities) if entities else "No entities specified.",
            ),
            ReportSection(
                title="Comparative Metrics",
                content=self._format_comparison_metrics(data.get("comparison_metrics", {})),
                evidence_ids=data.get("evidence_ids", []),
            ),
            ReportSection(
                title="Ranking",
                content=data.get("ranking", "Ranking pending."),
            ),
            ReportSection(
                title="Conclusion",
                content=data.get("conclusion", "Conclusion pending."),
            ),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.COMPARISON_REPORT,
            title=title,
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def generate_executive_summary(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate an executive summary."""
        title = data.get("title", "Executive Summary")
        sections = [
            ReportSection(
                title="Summary",
                content=data.get("summary", "Executive summary pending."),
            ),
            ReportSection(
                title="Key Findings",
                content=data.get("findings", "Key findings pending."),
            ),
            ReportSection(
                title="Action Items",
                content=data.get("action_items", "No action items."),
            ),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.EXECUTIVE_SUMMARY,
            title=title,
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def _generate_investment_thesis(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate an investment thesis."""
        symbol = data.get("symbol", "UNKNOWN")
        sections = [
            ReportSection(title="Thesis", content=data.get("thesis", "Thesis pending.")),
            ReportSection(title="Valuation Framework", content=data.get("valuation", "Valuation pending.")),
            ReportSection(title="Key Drivers", content=data.get("drivers", "Drivers pending.")),
            ReportSection(title="Risks", content=data.get("risks", "Risks pending.")),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.INVESTMENT_THESIS,
            title=data.get("title", f"{symbol} Investment Thesis"),
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def _generate_portfolio_report(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a portfolio report."""
        sections = [
            ReportSection(title="Portfolio Overview", content=data.get("overview", "Portfolio overview pending.")),
            ReportSection(title="Holdings", content=data.get("holdings", "Holdings pending.")),
            ReportSection(title="Performance", content=data.get("performance", "Performance pending.")),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.PORTFOLIO_REPORT,
            title=data.get("title", "Portfolio Report"),
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def _generate_risk_report(self, data: dict[str, Any]) -> ResearchDeliverable:
        """Generate a risk report."""
        sections = [
            ReportSection(title="Risk Overview", content=data.get("overview", "Risk overview pending.")),
            ReportSection(title="Risk Metrics", content=self._format_metrics(data.get("metrics", {}))),
            ReportSection(title="Mitigation", content=data.get("mitigation", "Mitigation pending.")),
        ]
        return ResearchDeliverable(
            deliverable_type=DeliverableType.RISK_REPORT,
            title=data.get("title", "Risk Report"),
            sections=sections,
            metadata=self._build_metadata(data),
        )

    def render_markdown(self, deliverable: ResearchDeliverable) -> str:
        """Render a deliverable as Markdown."""
        parts = [f"# {deliverable.title}\n"]
        parts.append(f"**Type:** {deliverable.deliverable_type.value}\n")
        parts.append(f"**Generated:** {deliverable.metadata.created_at.isoformat()}\n\n")
        for section in deliverable.sections:
            parts.append(f"## {section.title}\n")
            parts.append(f"{section.content}\n")
            if section.evidence_ids:
                parts.append(f"*Evidence: {', '.join(section.evidence_ids)}*\n")
        if deliverable.metadata.assumptions:
            parts.append("## Assumptions\n")
            for a in deliverable.metadata.assumptions:
                parts.append(f"- {a}")
        if deliverable.metadata.limitations:
            parts.append("## Limitations\n")
            for l in deliverable.metadata.limitations:
                parts.append(f"- {l}")
        return "\n".join(parts)

    def render_text(self, deliverable: ResearchDeliverable) -> str:
        """Render a deliverable as plain text."""
        parts = [deliverable.title, "=" * len(deliverable.title), ""]
        parts.append(f"Type: {deliverable.deliverable_type.value}")
        parts.append(f"Generated: {deliverable.metadata.created_at.isoformat()}")
        parts.append("")
        for section in deliverable.sections:
            parts.append(f"--- {section.title} ---")
            parts.append(section.content)
            parts.append("")
        return "\n".join(parts)

    def render_json(self, deliverable: ResearchDeliverable) -> dict:
        """Render a deliverable as a JSON-serializable dict."""
        return deliverable.model_dump(mode="json")

    def render_csv(self, deliverable: ResearchDeliverable) -> str:
        """Render a deliverable as CSV (sections as rows)."""
        lines = ["section_id,title,content"]
        for section in deliverable.sections:
            content = section.content.replace('"', '""')
            lines.append(f'"{section.section_id}","{section.title}","{content}"')
        return "\n".join(lines)

    def _format_metrics(self, metrics: dict[str, Any]) -> str:
        if not metrics:
            return "No metrics available."
        lines = []
        for key, value in metrics.items():
            lines.append(f"- **{key}:** {value}")
        return "\n".join(lines)

    def _format_comparison_metrics(self, comparison: dict[str, dict[str, Any]]) -> str:
        if not comparison:
            return "No comparison data available."
        lines = []
        for metric, values in comparison.items():
            lines.append(f"### {metric}")
            for entity, value in values.items():
                lines.append(f"  - {entity}: {value}")
        return "\n".join(lines)

    def _build_metadata(self, data: dict[str, Any]) -> DeliverableMetadata:
        return DeliverableMetadata(
            research_id=data.get("research_id", str(uuid.uuid4())),
            data_versions=data.get("data_versions", {}),
            sources=data.get("sources", []),
            evidence_ids=data.get("evidence_ids", []),
            calculation_ids=data.get("calculation_ids", []),
            assumptions=data.get("assumptions", []),
            limitations=data.get("limitations", []),
        )
