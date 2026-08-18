"""Tests for the Generative Research Grid module."""

from __future__ import annotations

import pytest

from core.research.grid.generator import GridGenerator
from core.research.grid.models import ColumnSpec, GridSpec, MetricType, RowSpec
from core.research.grid.planner import GridPlanner
from core.research.grid.resolver import MetricResolver


class TestGridPlanner:
    """Tests for GridPlanner."""

    def setup_method(self) -> None:
        self.planner = GridPlanner()

    def test_plan_grid_basic(self) -> None:
        spec = self.planner.plan_grid("Compare AAPL MSFT GOOGL on revenue growth and PE ratio")
        assert isinstance(spec, GridSpec)
        assert len(spec.rows) == 3
        assert len(spec.columns) >= 2

    def test_resolve_sector_entities(self) -> None:
        spec = self.planner.plan_grid("Show me tech sector metrics")
        assert len(spec.rows) == 7
        entity_ids = [r.entity_id for r in spec.rows]
        assert "AAPL" in entity_ids

    def test_resolve_financial_metrics(self) -> None:
        spec = self.planner.plan_grid("ROE and debt-to-equity for JPM")
        metric_ids = [c.column_id for c in spec.columns]
        assert "roe" in metric_ids
        assert "debt_equity" in metric_ids

    def test_default_metrics_when_none_found(self) -> None:
        spec = self.planner.plan_grid("Analyze AAPL")
        assert len(spec.columns) >= 3

    def test_grid_spec_has_title(self) -> None:
        spec = self.planner.plan_grid("Compare AAPL and MSFT")
        assert spec.title != ""


class TestMetricResolver:
    """Tests for MetricResolver."""

    def setup_method(self) -> None:
        self.resolver = MetricResolver()

    def test_resolve_standard_metric(self) -> None:
        col = self.resolver.resolve_metric("revenue_growth")
        assert col.name == "Revenue Growth (YoY)"
        assert col.metric_type == MetricType.NUMERIC
        assert col.source == "financial_statements"

    def test_resolve_all_standard_metrics(self) -> None:
        for metric_key in MetricResolver.STANDARD_METRICS:
            col = self.resolver.resolve_metric(metric_key)
            assert col.column_id == metric_key
            assert col.name != ""

    def test_resolve_unknown_metric(self) -> None:
        col = self.resolver.resolve_metric("custom_metric_xyz")
        assert col.source == "unknown"
        assert col.evidence_required is False

    def test_resolve_entity(self) -> None:
        row = self.resolver.resolve_entity("AAPL")
        assert row.entity_id == "AAPL"
        assert row.entity_type == "company"

    def test_resolve_calculation_revenue_growth(self) -> None:
        calc = self.resolver.resolve_calculation("revenue_growth_yoy", [])
        data = {"revenue_current": 100, "revenue_prior": 80}
        result = calc(data, "test")
        assert result == 25.0

    def test_resolve_calculation_debt_equity(self) -> None:
        calc = self.resolver.resolve_calculation("debt_equity_ratio", [])
        data = {"total_debt": 100, "total_equity": 50}
        result = calc(data, "test")
        assert result == 2.0

    def test_extract_value(self) -> None:
        data = {"roe": 15.5, "revenue": 1000000}
        assert self.resolver.extract_value(data, "roe", "AAPL") == 15.5
        assert self.resolver.extract_value(data, "revenue", "AAPL") == 1000000


class TestGridGenerator:
    """Tests for GridGenerator."""

    def setup_method(self) -> None:
        self.generator = GridGenerator()
        self.planner = GridPlanner()

    def test_generate_empty_data(self) -> None:
        spec = self.planner.plan_grid("Compare AAPL MSFT on ROE")
        grid = self.generator.generate(spec)
        assert len(grid.cells) == len(spec.rows) * len(spec.columns)
        assert grid.generated_at is not None

    def test_generate_with_data(self) -> None:
        spec = GridSpec(
            title="Test",
            rows=[RowSpec(entity_id="AAPL", entity_name="Apple")],
            columns=[ColumnSpec(column_id="roe", name="ROE", calculation="roe")],
        )
        data = {"AAPL": {"roe": 18.5}}
        grid = self.generator.generate(spec, data)
        assert len(grid.cells) == 1
        cell = grid.cells[0]
        assert cell.value == 18.5
        assert cell.row_id == spec.rows[0].row_id

    def test_generate_missing_data(self) -> None:
        spec = GridSpec(
            title="Test",
            rows=[RowSpec(entity_id="AAPL", entity_name="Apple")],
            columns=[ColumnSpec(column_id="roe", name="ROE", calculation="roe")],
        )
        grid = self.generator.generate(spec, {})
        cell = grid.cells[0]
        assert cell.value is None

    def test_evidence_attached(self) -> None:
        spec = GridSpec(
            title="Test",
            rows=[RowSpec(entity_id="AAPL", entity_name="Apple")],
            columns=[ColumnSpec(column_id="roe", name="ROE", calculation="roe", evidence_required=True)],
        )
        data = {"AAPL": {"roe": 18.5}}
        grid = self.generator.generate(spec, data)
        cell = grid.cells[0]
        assert cell.evidence_id is not None
