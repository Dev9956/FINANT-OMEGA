"""FININT OMEGA — Data quality validation framework."""

from __future__ import annotations

from datetime import datetime, timezone

from core.data.models import DataQualityIssue, DataQualitySeverity, DatasetRecord


class DataQualityChecker:
    """Runs validation checks on datasets and returns issues."""

    def check_missing_values(
        self,
        dataset: DatasetRecord,
        columns: list[str],
        null_counts: dict[str, int],
        total_rows: int,
    ) -> list[DataQualityIssue]:
        """Check for missing values exceeding threshold."""
        issues = []
        threshold = 0.1  # 10% threshold
        for col in columns:
            null_count = null_counts.get(col, 0)
            if total_rows > 0 and (null_count / total_rows) > threshold:
                severity = (
                    DataQualitySeverity.CRITICAL
                    if null_count / total_rows > 0.5
                    else DataQualitySeverity.HIGH
                )
                issues.append(
                    DataQualityIssue(
                        dataset_id=dataset.dataset_id,
                        check_name="missing_values",
                        severity=severity,
                        description=f"Column '{col}' has {null_count}/{total_rows} missing values ({null_count/total_rows:.1%})",
                        affected_rows=null_count,
                        affected_columns=[col],
                    )
                )
        return issues

    def check_duplicates(
        self,
        dataset: DatasetRecord,
        duplicate_count: int,
        total_rows: int,
        key_columns: list[str] | None = None,
    ) -> list[DataQualityIssue]:
        """Check for duplicate records."""
        issues = []
        if duplicate_count > 0:
            severity = (
                DataQualitySeverity.CRITICAL
                if total_rows > 0 and duplicate_count / total_rows > 0.05
                else DataQualitySeverity.MEDIUM
            )
            issues.append(
                DataQualityIssue(
                    dataset_id=dataset.dataset_id,
                    check_name="duplicates",
                    severity=severity,
                    description=f"Found {duplicate_count} duplicate rows out of {total_rows} total",
                    affected_rows=duplicate_count,
                    affected_columns=key_columns or [],
                )
            )
        return issues

    def check_date_validity(
        self,
        dataset: DatasetRecord,
        date_column: str,
        invalid_count: int,
        min_date: datetime | None = None,
        max_date: datetime | None = None,
    ) -> list[DataQualityIssue]:
        """Check for invalid dates."""
        issues = []
        if invalid_count > 0:
            issues.append(
                DataQualityIssue(
                    dataset_id=dataset.dataset_id,
                    check_name="invalid_dates",
                    severity=DataQualitySeverity.HIGH,
                    description=f"Column '{date_column}' has {invalid_count} invalid dates",
                    affected_rows=invalid_count,
                    affected_columns=[date_column],
                )
            )
        if min_date and min_date.year < 1900:
            issues.append(
                DataQualityIssue(
                    dataset_id=dataset.dataset_id,
                    check_name="suspicious_date_range",
                    severity=DataQualitySeverity.MEDIUM,
                    description=f"Date column '{date_column}' starts before 1900: {min_date}",
                    affected_columns=[date_column],
                )
            )
        return issues

    def check_numeric_ranges(
        self,
        dataset: DatasetRecord,
        column: str,
        out_of_range_count: int,
        min_value: float | None = None,
        max_value: float | None = None,
        total_rows: int = 0,
    ) -> list[DataQualityIssue]:
        """Check for impossible numeric values (e.g., negative prices)."""
        issues = []
        if out_of_range_count > 0:
            issues.append(
                DataQualityIssue(
                    dataset_id=dataset.dataset_id,
                    check_name="numeric_range_violation",
                    severity=DataQualitySeverity.HIGH,
                    description=(
                        f"Column '{column}' has {out_of_range_count} values outside "
                        f"range [{min_value}, {max_value}]"
                    ),
                    affected_rows=out_of_range_count,
                    affected_columns=[column],
                )
            )
        return issues

    def check_staleness(
        self,
        dataset: DatasetRecord,
        last_updated: datetime,
        max_age_hours: float = 24.0,
    ) -> list[DataQualityIssue]:
        """Check if dataset is stale."""
        issues = []
        now = datetime.now(timezone.utc)
        age_hours = (now - last_updated).total_seconds() / 3600
        if age_hours > max_age_hours:
            severity = (
                DataQualitySeverity.CRITICAL
                if age_hours > max_age_hours * 7
                else DataQualitySeverity.MEDIUM
            )
            issues.append(
                DataQualityIssue(
                    dataset_id=dataset.dataset_id,
                    check_name="stale_data",
                    severity=severity,
                    description=f"Dataset last updated {age_hours:.1f}h ago (threshold: {max_age_hours}h)",
                )
            )
        return issues

    def run_all_checks(
        self,
        dataset: DatasetRecord,
        stats: dict,
    ) -> list[DataQualityIssue]:
        """Run all available checks on a dataset given its statistics."""
        issues = []

        if "null_counts" in stats and "total_rows" in stats:
            issues.extend(
                self.check_missing_values(
                    dataset,
                    columns=list(stats["null_counts"].keys()),
                    null_counts=stats["null_counts"],
                    total_rows=stats["total_rows"],
                )
            )

        if "duplicate_count" in stats and "total_rows" in stats:
            issues.extend(
                self.check_duplicates(
                    dataset,
                    duplicate_count=stats["duplicate_count"],
                    total_rows=stats["total_rows"],
                    key_columns=stats.get("key_columns"),
                )
            )

        if "last_updated" in stats:
            issues.extend(
                self.check_staleness(
                    dataset,
                    last_updated=stats["last_updated"],
                    max_age_hours=stats.get("max_age_hours", 24.0),
                )
            )

        return issues
