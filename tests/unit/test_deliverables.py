"""Tests for the Research Deliverables module."""

from __future__ import annotations

import json

import pytest

from core.research.deliverables.generator import DeliverableGenerator
from core.research.deliverables.models import (
    DeliverableType,
    ResearchDeliverable,
)


class TestDeliverableGenerator:
    """Tests for DeliverableGenerator."""

    def setup_method(self) -> None:
        self.generator = DeliverableGenerator()

    def test_generate_research_memo(self) -> None:
        data = {
            "title": "Test Memo",
            "thesis": "Buy AAPL",
            "metrics": {"roe": 18.5, "pe": 28.0},
            "risks": "Market risk",
            "recommendation": "Strong Buy",
        }
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        assert isinstance(result, ResearchDeliverable)
        assert result.deliverable_type == DeliverableType.RESEARCH_MEMO
        assert result.title == "Test Memo"
        assert len(result.sections) >= 3

    def test_generate_company_report(self) -> None:
        data = {
            "symbol": "AAPL",
            "overview": "Apple Inc.",
            "metrics": {"revenue": 394000000000},
        }
        result = self.generator.generate(DeliverableType.COMPANY_REPORT, data)
        assert result.deliverable_type == DeliverableType.COMPANY_REPORT
        assert "AAPL" in result.title

    def test_generate_sector_report(self) -> None:
        data = {"sector": "Technology", "overview": "Tech sector analysis"}
        result = self.generator.generate(DeliverableType.SECTOR_REPORT, data)
        assert result.deliverable_type == DeliverableType.SECTOR_REPORT

    def test_generate_comparison_report(self) -> None:
        data = {"entities": ["AAPL", "MSFT", "GOOGL"], "comparison_metrics": {}}
        result = self.generator.generate(DeliverableType.COMPARISON_REPORT, data)
        assert result.deliverable_type == DeliverableType.COMPARISON_REPORT

    def test_generate_executive_summary(self) -> None:
        data = {"summary": "Key findings here"}
        result = self.generator.generate(DeliverableType.EXECUTIVE_SUMMARY, data)
        assert result.deliverable_type == DeliverableType.EXECUTIVE_SUMMARY

    def test_generate_investment_thesis(self) -> None:
        data = {"symbol": "MSFT", "thesis": "Cloud growth driver"}
        result = self.generator.generate(DeliverableType.INVESTMENT_THESIS, data)
        assert result.deliverable_type == DeliverableType.INVESTMENT_THESIS

    def test_generate_portfolio_report(self) -> None:
        data = {"overview": "Portfolio overview"}
        result = self.generator.generate(DeliverableType.PORTFOLIO_REPORT, data)
        assert result.deliverable_type == DeliverableType.PORTFOLIO_REPORT

    def test_generate_risk_report(self) -> None:
        data = {"overview": "Risk overview"}
        result = self.generator.generate(DeliverableType.RISK_REPORT, data)
        assert result.deliverable_type == DeliverableType.RISK_REPORT

    def test_render_markdown(self) -> None:
        data = {"title": "Test", "thesis": "Buy"}
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        md = self.generator.render_markdown(result)
        assert "# Test" in md
        assert "research_memo" in md

    def test_render_text(self) -> None:
        data = {"title": "Test", "thesis": "Buy"}
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        text = self.generator.render_text(result)
        assert "Test" in text
        assert "===" in text

    def test_render_json(self) -> None:
        data = {"title": "Test", "thesis": "Buy"}
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        json_data = self.generator.render_json(result)
        assert isinstance(json_data, dict)
        assert json_data["title"] == "Test"

    def test_render_csv(self) -> None:
        data = {"title": "Test", "thesis": "Buy"}
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        csv = self.generator.render_csv(result)
        assert "section_id,title,content" in csv

    def test_metadata_assumptions(self) -> None:
        data = {
            "title": "Test",
            "assumptions": ["GDP grows at 2%"],
            "limitations": ["Data as of Q3"],
        }
        result = self.generator.generate(DeliverableType.RESEARCH_MEMO, data)
        assert "GDP grows at 2%" in result.metadata.assumptions
        assert "Data as of Q3" in result.metadata.limitations
