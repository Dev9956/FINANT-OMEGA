"""FININT OMEGA — Grid generator for filling cells from data sources."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.research.grid.models import GeneratedGrid, GridCell, GridSpec
from core.research.grid.resolver import MetricResolver


class GridGenerator:
    """Generate a filled grid from a spec and data source."""

    def __init__(self) -> None:
        self.resolver = MetricResolver()

    def generate(self, grid_spec: GridSpec, data_source: dict[str, dict[str, Any]] | None = None) -> GeneratedGrid:
        """Fill cells from data source and compute calculated columns."""
        data_source = data_source or {}
        cells: list[GridCell] = []
        evidence_summary: dict[str, Any] = {}

        for row in grid_spec.rows:
            row_data = data_source.get(row.entity_id, {})
            for column in grid_spec.columns:
                cell = self._compute_cell(row.row_id, column.column_id, row_data, grid_spec)
                cells.append(cell)
                if cell.evidence_id:
                    evidence_summary[cell.evidence_id] = {
                        "row": row.entity_id,
                        "column": column.name,
                        "confidence": cell.confidence,
                    }

        return GeneratedGrid(
            grid_id=grid_spec.grid_id,
            spec=grid_spec,
            cells=cells,
            generated_at=datetime.now(timezone.utc),
            data_versions={"data_source": "v1"},
            evidence_summary=evidence_summary,
        )

    def _compute_cell(self, row_id: str, column_id: str, row_data: dict, grid_spec: GridSpec) -> GridCell:
        """Compute a single cell value."""
        column = next((c for c in grid_spec.columns if c.column_id == column_id), None)
        if column is None:
            return GridCell(row_id=row_id, column_id=column_id, value=None)

        raw_value = self.resolver.extract_value(row_data, column.calculation, row_id)
        confidence = self._compute_confidence(raw_value, row_data)
        evidence_id = None
        if column.evidence_required and raw_value is not None:
            evidence_id = f"ev-{uuid.uuid4().hex[:12]}"

        return GridCell(
            row_id=row_id,
            column_id=column_id,
            value=raw_value,
            unit=column.description.split("|")[-1].strip() if "|" in column.description else "",
            evidence_id=evidence_id,
            confidence=confidence,
            calculation_id=column.calculation if column.calculation else None,
        )

    def _compute_confidence(self, value: Any, row_data: dict) -> float | None:
        """Compute confidence score for a cell value."""
        if value is None:
            return None
        has_source = bool(row_data.get("data_source_version"))
        if has_source:
            return 0.95
        return 0.7
