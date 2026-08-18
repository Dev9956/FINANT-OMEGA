"""FININT OMEGA — Digital Twin Engine."""

from __future__ import annotations

from core.intelligence.digital_twin.models import (
    DigitalTwin,
    TwinScenario,
    TwinSnapshot,
)


class DigitalTwinEngine:
    """Manage digital twins for companies/assets."""

    def __init__(self) -> None:
        self._twins: dict[str, DigitalTwin] = {}

    def create_twin(self, entity: str, name: str = "") -> DigitalTwin:
        twin = DigitalTwin(entity=entity, name=name or entity)
        self._twins[twin.twin_id] = twin
        return twin

    def get_twin(self, twin_id: str) -> DigitalTwin | None:
        return self._twins.get(twin_id)

    def get_twin_by_entity(self, entity: str) -> DigitalTwin | None:
        for twin in self._twins.values():
            if twin.entity == entity:
                return twin
        return None

    def update_snapshot(self, twin_id: str, snapshot: TwinSnapshot) -> bool:
        twin = self._twins.get(twin_id)
        if twin is None:
            return False
        twin.snapshots.append(snapshot)
        twin.updated_at = snapshot.timestamp
        return True

    def apply_scenario(self, twin_id: str, scenario: TwinScenario) -> dict | None:
        twin = self._twins.get(twin_id)
        if twin is None:
            return None

        latest = twin.snapshots[-1] if twin.snapshots else TwinSnapshot()
        affected = {}

        for metric, change in scenario.changes.items():
            current = latest.market.get(metric) or latest.financials.get(metric) or latest.valuation.get(metric) or 0
            affected[metric] = current * (1 + change / 100)

        scenario.affected_metrics = affected
        twin.scenarios.append(scenario)
        return affected

    def get_latest_snapshot(self, twin_id: str) -> TwinSnapshot | None:
        twin = self._twins.get(twin_id)
        if twin is None or not twin.snapshots:
            return None
        return twin.snapshots[-1]

    def list_twins(self) -> list[DigitalTwin]:
        return list(self._twins.values())
