"""FININT OMEGA — Data models for source registry, dataset registry, lineage, quality."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Types of data sources."""

    MARKET_DATA = "market_data"
    FUNDAMENTALS = "fundamentals"
    MACRO = "macro"
    NEWS = "news"
    FILING = "filing"
    DOCUMENT = "document"
    EARNINGS = "earnings"
    CUSTOM = "custom"


class SourceStatus(str, Enum):
    """Status of a data source."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ERROR = "error"


class SourceRecord(BaseModel):
    """Registry entry for a data source."""

    source_id: str = Field(description="Unique source identifier")
    source_name: str = Field(description="Human-readable name")
    source_type: SourceType
    provider: str = Field(description="Data provider name")
    license: str = Field(default="unknown", description="License terms")
    terms_url: str | None = Field(default=None, description="Terms of service URL")
    refresh_frequency: str = Field(default="unknown", description="Refresh cadence e.g. daily, hourly")
    coverage: str = Field(default="unknown", description="Coverage description")
    status: SourceStatus = SourceStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class DataStage(str, Enum):
    """Data pipeline stages."""

    RAW = "raw"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class DatasetStatus(str, Enum):
    """Dataset quality/availability status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"
    ERROR = "error"
    UNKNOWN = "unknown"


class DatasetRecord(BaseModel):
    """Registry entry for a dataset."""

    dataset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = Field(description="Reference to source")
    name: str
    description: str = ""
    stage: DataStage
    schema_version: int = 1
    data_version: int = 1
    coverage_start: datetime | None = None
    coverage_end: datetime | None = None
    row_count: int | None = None
    quality_status: DatasetStatus = DatasetStatus.UNKNOWN
    timezone: str = "UTC"
    currency: str = "USD"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class DataQualitySeverity(str, Enum):
    """Severity of data quality issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DataQualityIssue(BaseModel):
    """A single data quality issue detected."""

    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dataset_id: str
    check_name: str
    severity: DataQualitySeverity
    description: str
    affected_rows: int = 0
    affected_columns: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    metadata: dict = Field(default_factory=dict)


class DataLineageRecord(BaseModel):
    """Tracks data lineage: where data came from and how it was transformed."""

    lineage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_dataset_id: str
    source_dataset_ids: list[str] = Field(default_factory=list)
    source_records: list[str] = Field(default_factory=list, description="Source record references")
    transformation: str = Field(description="Description of transformation applied")
    pipeline_run_id: str | None = None
    input_row_count: int | None = None
    output_row_count: int | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    success: bool = True
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
