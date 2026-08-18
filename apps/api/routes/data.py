"""FININT OMEGA — Data management API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException

from apps.api.schemas import ErrorResponse
from core.data.connectors import MockFundamentalsConnector, MockMacroConnector, MockMarketConnector
from core.data.lineage import LineageTracker
from core.data.models import (
    DatasetRecord,
    DatasetStatus,
    DataStage,
    SourceRecord,
    SourceStatus,
    SourceType,
)
from core.data.pipeline import DataPipeline
from core.data.quality import DataQualityChecker
from core.data.schemas import CompanyIdentifier, FinancialStatement, MacroIndicator, MarketOHLCV

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/data", tags=["data"])

# In-memory stores for M1 (will be replaced with DB in later milestones)
_source_registry: dict[str, SourceRecord] = {}
_dataset_registry: dict[str, DatasetRecord] = {}
_lineage_tracker = LineageTracker()
_quality_checker = DataQualityChecker()


@router.get("/sources")
async def list_sources() -> list[dict]:
    """List all registered data sources."""
    return [s.model_dump() for s in _source_registry.values()]


@router.post("/sources")
async def register_source(source: SourceRecord) -> dict:
    """Register a new data source."""
    _source_registry[source.source_id] = source
    logger.info("source_registered", source_id=source.source_id)
    return source.model_dump()


@router.get("/sources/{source_id}")
async def get_source(source_id: str) -> dict:
    """Get a specific data source."""
    if source_id not in _source_registry:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")
    return _source_registry[source_id].model_dump()


@router.get("/datasets")
async def list_datasets() -> list[dict]:
    """List all registered datasets."""
    return [d.model_dump() for d in _dataset_registry.values()]


@router.post("/datasets")
async def register_dataset(dataset: DatasetRecord) -> dict:
    """Register a new dataset."""
    _dataset_registry[dataset.dataset_id] = dataset
    logger.info("dataset_registered", dataset_id=dataset.dataset_id)
    return dataset.model_dump()


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str) -> dict:
    """Get a specific dataset."""
    if dataset_id not in _dataset_registry:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    return _dataset_registry[dataset_id].model_dump()


@router.get("/datasets/{dataset_id}/lineage")
async def get_dataset_lineage(dataset_id: str) -> list[dict]:
    """Get lineage for a dataset."""
    records = _lineage_tracker.get_lineage(dataset_id)
    return [r.model_dump() for r in records]


@router.get("/datasets/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str) -> list[dict]:
    """Get quality issues for a dataset."""
    if dataset_id not in _dataset_registry:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    # Run checks on available stats
    dataset = _dataset_registry[dataset_id]
    stats = dataset.metadata.get("quality_stats", {})
    if not stats:
        return []
    issues = _quality_checker.run_all_checks(dataset, stats)
    return [i.model_dump() for i in issues]


@router.post("/pipeline/run")
async def run_pipeline(pipeline_name: str, data: list[dict]) -> dict:
    """Run a data pipeline by name."""
    pipeline = _get_pipeline(pipeline_name)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_name}")
    run = pipeline.run(data)
    return run.model_dump()


@router.get("/pipelines")
async def list_pipelines() -> list[str]:
    """List available pipelines."""
    return ["market_ohlcv", "financial_statements", "macro_indicators"]


@router.get("/mock/{domain}")
async def get_mock_data(domain: str, symbol: str = "MOCK") -> list[dict]:
    """Get mock data for development/testing."""
    if domain == "market":
        connector = MockMarketConnector()
        records = connector.fetch(symbol=symbol, days=30)
        return [r.data for r in records]
    elif domain == "fundamentals":
        connector = MockFundamentalsConnector()
        records = connector.fetch(symbol=symbol)
        return [r.data for r in records]
    elif domain == "macro":
        connector = MockMacroConnector()
        records = connector.fetch()
        return [r.data for r in records]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}")


def _get_pipeline(name: str) -> DataPipeline | None:
    """Get a pipeline by name."""
    if name == "market_ohlcv":
        pipeline = DataPipeline(name="market_ohlcv")
        pipeline.add_step("validate_raw", "Validate raw OHLCV", 0)
        pipeline.add_step("bronze", "Clean and type OHLCV", 1)
        pipeline.add_step("silver", "Normalize and join", 2)
        pipeline.add_step("gold", "Compute derived fields", 3)
        return pipeline
    elif name == "financial_statements":
        pipeline = DataPipeline(name="financial_statements")
        pipeline.add_step("validate_raw", "Validate raw statements", 0)
        pipeline.add_step("bronze", "Parse and type statements", 1)
        pipeline.add_step("silver", "Normalize and validate", 2)
        pipeline.add_step("gold", "Compute ratios", 3)
        return pipeline
    elif name == "macro_indicators":
        pipeline = DataPipeline(name="macro_indicators")
        pipeline.add_step("validate_raw", "Validate raw indicators", 0)
        pipeline.add_step("bronze", "Parse and type indicators", 1)
        pipeline.add_step("silver", "Normalize units", 2)
        pipeline.add_step("gold", "Aggregate", 3)
        return pipeline
    return None
