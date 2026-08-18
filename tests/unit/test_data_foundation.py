"""FININT OMEGA — M1 tests for data foundation."""

import pytest
from datetime import date, datetime, timezone

from core.data.connectors import MockMarketConnector, MockFundamentalsConnector, MockMacroConnector
from core.data.lineage import LineageTracker
from core.data.models import (
    DatasetRecord,
    DatasetStatus,
    DataQualityIssue,
    DataQualitySeverity,
    DataStage,
    SourceRecord,
    SourceStatus,
    SourceType,
)
from core.data.normalization import normalize_string, normalize_symbol, parse_date, safe_float, safe_int
from core.data.pipeline import DataPipeline, PipelineRun, PipelineStatus
from core.data.quality import DataQualityChecker
from core.data.schemas import (
    CompanyIdentifier,
    Currency,
    Exchange,
    FinancialRatios,
    FinancialStatement,
    MacroIndicator,
    MarketOHLCV,
)
from core.data.validation import validate_ohlcv, validate_financial_statement, validate_date_range


# ── Source Registry ──

class TestSourceRecord:
    def test_create_source(self):
        src = SourceRecord(
            source_id="test_source",
            source_name="Test Source",
            source_type=SourceType.MARKET_DATA,
            provider="Test Provider",
        )
        assert src.source_id == "test_source"
        assert src.status == SourceStatus.ACTIVE

    def test_source_types(self):
        for st in SourceType:
            src = SourceRecord(
                source_id=f"test_{st.value}",
                source_name=f"Test {st.value}",
                source_type=st,
                provider="Test",
            )
            assert src.source_type == st


# ── Dataset Registry ──

class TestDatasetRecord:
    def test_create_dataset(self):
        ds = DatasetRecord(
            source_id="test_source",
            name="Test Dataset",
            stage=DataStage.RAW,
        )
        assert ds.dataset_id
        assert ds.stage == DataStage.RAW
        assert ds.quality_status == DatasetStatus.UNKNOWN


# ── Domain Schemas ──

class TestMarketOHLCV:
    def test_create_ohlcv(self):
        rec = MarketOHLCV(
            symbol="TCS",
            date=date(2025, 6, 15),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=500000,
        )
        assert rec.symbol == "TCS"
        assert rec.high >= rec.low

    def test_exchange_enum(self):
        for ex in Exchange:
            assert ex.value


class TestFinancialStatement:
    def test_income_statement(self):
        fs = FinancialStatement(
            symbol="RELIANCE",
            period_end=date(2025, 3, 31),
            statement_type="income_statement",
            revenue=500000000.0,
            net_income=75000000.0,
        )
        assert fs.revenue == 500000000.0


class TestMacroIndicator:
    def test_macro(self):
        m = MacroIndicator(
            indicator_id="us_gdp",
            indicator_name="US GDP",
            country="US",
            date=date(2025, 12, 31),
            value=2.5,
        )
        assert m.value == 2.5


# ── Normalization ──

class TestNormalization:
    def test_parse_date_string(self):
        d = parse_date("2025-06-15")
        assert d == date(2025, 6, 15)

    def test_parse_date_object(self):
        d = parse_date(date(2025, 6, 15))
        assert d == date(2025, 6, 15)

    def test_parse_date_invalid(self):
        with pytest.raises(ValueError):
            parse_date("not-a-date")

    def test_normalize_string(self):
        assert normalize_string("  Hello   World  ") == "HELLO WORLD"

    def test_normalize_symbol(self):
        assert normalize_symbol(" tcs ") == "TCS"

    def test_safe_float_valid(self):
        assert safe_float("123.45") == 123.45

    def test_safe_float_none(self):
        assert safe_float(None) == 0.0

    def test_safe_float_invalid(self):
        assert safe_float("abc", default=-1.0) == -1.0

    def test_safe_int_valid(self):
        assert safe_int("42") == 42

    def test_safe_int_none(self):
        assert safe_int(None) == 0


# ── Validation ──

class TestValidation:
    def test_validate_ohlcv_valid(self):
        valid, errors = validate_ohlcv({
            "symbol": "TCS",
            "date": "2025-06-15",
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 103,
            "volume": 500000,
        })
        assert valid is True
        assert errors == []

    def test_validate_ohlcv_missing_field(self):
        valid, errors = validate_ohlcv({"symbol": "TCS"})
        assert valid is False
        assert any("symbol" in e or "Missing" in e for e in errors)

    def test_validate_ohlcv_high_less_than_low(self):
        valid, errors = validate_ohlcv({
            "symbol": "TCS",
            "date": "2025-06-15",
            "open": 100,
            "high": 90,
            "low": 95,
            "close": 100,
        })
        assert valid is False
        assert any("High" in e for e in errors)

    def test_validate_financial_statement(self):
        valid, errors = validate_financial_statement({
            "symbol": "TCS",
            "period_end": "2025-03-31",
            "statement_type": "income_statement",
        })
        assert valid is True

    def test_validate_financial_statement_invalid_type(self):
        valid, errors = validate_financial_statement({
            "symbol": "TCS",
            "period_end": "2025-03-31",
            "statement_type": "invalid",
        })
        assert valid is False

    def test_validate_date_range(self):
        valid, errors = validate_date_range(date(2025, 1, 1), date(2025, 12, 31))
        assert valid is True

    def test_validate_date_range_invalid(self):
        valid, errors = validate_date_range(date(2025, 12, 31), date(2025, 1, 1))
        assert valid is False


# ── Data Quality ──

class TestDataQuality:
    def test_missing_values_check(self):
        checker = DataQualityChecker()
        ds = DatasetRecord(source_id="test", name="test", stage=DataStage.BRONZE)
        issues = checker.check_missing_values(
            ds,
            columns=["close", "volume"],
            null_counts={"close": 50, "volume": 5},
            total_rows=100,
        )
        assert len(issues) == 1
        assert issues[0].check_name == "missing_values"
        assert issues[0].severity == DataQualitySeverity.HIGH

    def test_duplicates_check(self):
        checker = DataQualityChecker()
        ds = DatasetRecord(source_id="test", name="test", stage=DataStage.BRONZE)
        issues = checker.check_duplicates(ds, duplicate_count=10, total_rows=1000)
        assert len(issues) == 1

    def test_staleness_check(self):
        checker = DataQualityChecker()
        ds = DatasetRecord(source_id="test", name="test", stage=DataStage.BRONZE)
        from datetime import timedelta
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        issues = checker.check_staleness(ds, last_updated=old_time, max_age_hours=24)
        assert len(issues) == 1

    def test_run_all_checks(self):
        checker = DataQualityChecker()
        ds = DatasetRecord(source_id="test", name="test", stage=DataStage.BRONZE)
        from datetime import timedelta
        issues = checker.run_all_checks(ds, {
            "null_counts": {"close": 50},
            "total_rows": 100,
            "duplicate_count": 5,
            "last_updated": datetime.now(timezone.utc) - timedelta(hours=1),
        })
        # Should find missing values and duplicates, but not stale data
        assert len(issues) >= 1


# ── Pipeline ──

class TestPipeline:
    def test_pipeline_creation(self):
        p = DataPipeline(name="test_pipeline")
        p.add_step("step1", "First step", 0)
        p.add_step("step2", "Second step", 1)
        assert len(p.steps) == 2
        assert p.steps[0].name == "step1"

    def test_pipeline_run(self):
        p = DataPipeline(name="test")
        p.add_step("validate", "Validate", 0)
        p.add_step("transform", "Transform", 1)
        run = p.run([{"a": 1}, {"a": 2}])
        assert run.status == PipelineStatus.COMPLETED
        assert run.output_rows == 2

    def test_pipeline_error(self):
        class FailingPipeline(DataPipeline):
            def bronze_transform(self, data):
                raise ValueError("Test error")

        p = FailingPipeline(name="failing")
        run = p.run([{"a": 1}])
        assert run.status == PipelineStatus.FAILED
        assert "Test error" in run.error_message


# ── Lineage ──

class TestLineage:
    def test_record_lineage(self):
        tracker = LineageTracker()
        src = DatasetRecord(source_id="s", name="src", stage=DataStage.RAW)
        tgt = DatasetRecord(source_id="s", name="tgt", stage=DataStage.BRONZE)
        record = tracker.record(tgt, [src], "raw_to_bronze")
        assert record.success is True
        assert record.target_dataset_id == tgt.dataset_id

    def test_get_lineage(self):
        tracker = LineageTracker()
        src = DatasetRecord(source_id="s", name="src", stage=DataStage.RAW)
        tgt = DatasetRecord(source_id="s", name="tgt", stage=DataStage.BRONZE)
        tracker.record(tgt, [src], "raw_to_bronze")
        records = tracker.get_lineage(tgt.dataset_id)
        assert len(records) == 1


# ── Connectors ──

class TestConnectors:
    def test_mock_market(self):
        conn = MockMarketConnector()
        assert conn.health_check() is True
        data = conn.fetch(symbol="TCS", days=5)
        assert len(data) == 5
        assert data[0]["symbol"] == "TCS"

    def test_mock_fundamentals(self):
        conn = MockFundamentalsConnector()
        data = conn.fetch(symbol="RELIANCE")
        assert len(data) == 1
        assert data[0]["statement_type"] == "income_statement"

    def test_mock_macro(self):
        conn = MockMacroConnector()
        data = conn.fetch()
        assert len(data) == 1
        assert data[0]["indicator_id"] == "us_gdp_growth"


# ── Data Stage Enum ──

class TestDataStage:
    def test_all_stages(self):
        stages = [DataStage.RAW, DataStage.BRONZE, DataStage.SILVER, DataStage.GOLD]
        assert len(stages) == 4
