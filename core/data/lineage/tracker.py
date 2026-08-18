"""FININT OMEGA — Data lineage tracking."""

from __future__ import annotations

from datetime import datetime, timezone

from core.data.models import DataLineageRecord, DatasetRecord


class LineageTracker:
    """Tracks data lineage: source → transformation → target."""

    def __init__(self) -> None:
        self._records: list[DataLineageRecord] = []

    def record(
        self,
        target_dataset: DatasetRecord,
        source_datasets: list[DatasetRecord],
        transformation: str,
        input_row_count: int | None = None,
        output_row_count: int | None = None,
        pipeline_run_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> DataLineageRecord:
        """Record a lineage entry."""
        entry = DataLineageRecord(
            target_dataset_id=target_dataset.dataset_id,
            source_dataset_ids=[ds.dataset_id for ds in source_datasets],
            transformation=transformation,
            input_row_count=input_row_count,
            output_row_count=output_row_count,
            pipeline_run_id=pipeline_run_id,
            success=success,
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
        )
        self._records.append(entry)
        return entry

    def get_lineage(self, dataset_id: str) -> list[DataLineageRecord]:
        """Get all lineage records for a dataset."""
        return [r for r in self._records if r.target_dataset_id == dataset_id]

    def get_upstream(self, dataset_id: str) -> list[DataLineageRecord]:
        """Get all upstream lineage for a dataset."""
        result = []
        visited = set()
        queue = [dataset_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for record in self._records:
                if record.target_dataset_id == current:
                    result.append(record)
                    queue.extend(record.source_dataset_ids)
        return result

    def get_downstream(self, dataset_id: str) -> list[DataLineageRecord]:
        """Get all downstream lineage for a dataset."""
        result = []
        visited = set()
        queue = [dataset_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for record in self._records:
                if current in record.source_dataset_ids:
                    result.append(record)
                    queue.append(record.target_dataset_id)
        return result

    def clear(self) -> None:
        """Clear all lineage records."""
        self._records.clear()
