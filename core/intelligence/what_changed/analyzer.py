"""FININT OMEGA — What-changed analyzer: detect changes in fundamentals, estimates, sentiment."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChangeItem(BaseModel):
    """A single detected change."""

    field_name: str
    old_value: float | str | None = None
    new_value: float | str | None = None
    change_pct: float | None = None
    significance: str = "low"
    description: str = ""


class WhatChangedReport(BaseModel):
    """Report of what changed between two snapshots."""

    symbol: str
    changes: list[ChangeItem] = Field(default_factory=list)
    summary: str = ""
    overall_significance: str = "low"


class WhatChangedAnalyzer:
    """Detect meaningful changes between two data snapshots."""

    SIGNIFICANCE_THRESHOLDS = {
        "revenue": 0.05,
        "eps": 0.05,
        "pe_ratio": 0.10,
        "margin": 0.02,
        "debt_equity": 0.05,
    }

    def compare_snapshots(self, symbol: str, old: dict, new: dict) -> WhatChangedReport:
        changes: list[ChangeItem] = []
        all_keys = set(old.keys()) | set(new.keys())

        for key in sorted(all_keys):
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val == new_val:
                continue
            if old_val is None and new_val is not None:
                changes.append(ChangeItem(
                    field_name=key, old_value=None, new_value=new_val,
                    significance="low", description=f"{key} added: {new_val}",
                ))
                continue
            if old_val is not None and new_val is None:
                changes.append(ChangeItem(
                    field_name=key, old_value=old_val, new_value=None,
                    significance="low", description=f"{key} removed",
                ))
                continue
            try:
                old_f = float(old_val)
                new_f = float(new_val)
                pct = (new_f - old_f) / abs(old_f) if old_f != 0 else 0.0
                threshold = self.SIGNIFICANCE_THRESHOLDS.get(key, 0.05)
                sig = "high" if abs(pct) > threshold * 3 else "medium" if abs(pct) > threshold else "low"
                changes.append(ChangeItem(
                    field_name=key, old_value=old_val, new_value=new_val,
                    change_pct=pct, significance=sig,
                    description=f"{key}: {old_val} → {new_val} ({pct:+.1%})",
                ))
            except (ValueError, TypeError):
                if str(old_val) != str(new_val):
                    changes.append(ChangeItem(
                        field_name=key, old_value=old_val, new_value=new_val,
                        significance="low", description=f"{key} changed",
                    ))

        high_count = sum(1 for c in changes if c.significance == "high")
        overall = "high" if high_count > 0 else "medium" if len(changes) > 3 else "low"
        summary_parts = [c.description for c in changes if c.significance in ("high", "medium")]

        return WhatChangedReport(
            symbol=symbol,
            changes=changes,
            summary="; ".join(summary_parts[:5]) if summary_parts else "No significant changes",
            overall_significance=overall,
        )
