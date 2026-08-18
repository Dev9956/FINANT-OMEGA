"""FININT OMEGA — Why-moved analyzer: explain why a security moved."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MoveExplanation(BaseModel):
    """Explanation of why a security moved."""

    symbol: str
    price_change_pct: float = 0.0
    volume_change_pct: float = 0.0
    primary_driver: str = ""
    contributing_factors: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    metadata: dict = Field(default_factory=dict)


class WhyMovedAnalyzer:
    """Analyze and explain why a security's price moved."""

    def __init__(self) -> None:
        self._event_weights: dict[str, float] = {
            "earnings": 0.35,
            "analyst_upgrade": 0.20,
            "analyst_downgrade": -0.20,
            "merger_news": 0.30,
            "macro_news": 0.15,
            "sector_rotation": 0.10,
            "insider_activity": 0.15,
            "guidance_change": 0.25,
        }

    def analyze(
        self,
        symbol: str,
        price_change_pct: float,
        volume_change_pct: float,
        events: list[dict] | None = None,
    ) -> MoveExplanation:
        factors: list[str] = []
        driver_scores: dict[str, float] = {}

        for event in (events or []):
            event_type = event.get("type", "")
            weight = self._event_weights.get(event_type, 0.0)
            if weight != 0:
                driver_scores[event_type] = weight
                factors.append(f"{event_type}: {event.get('description', '')}")

        if not driver_scores:
            if abs(price_change_pct) > 5:
                factors.append("Large move with no clear catalyst — possible technical or flow-driven")
            elif abs(price_change_pct) > 2:
                factors.append("Moderate move — may be sector rotation or macro-driven")
            else:
                factors.append("Normal price fluctuation")

        primary = max(driver_scores, key=lambda k: abs(driver_scores[k])) if driver_scores else "unknown"
        confidence = min(abs(price_change_pct) / 10.0, 1.0) if price_change_pct != 0 else 0.3

        return MoveExplanation(
            symbol=symbol,
            price_change_pct=price_change_pct,
            volume_change_pct=volume_change_pct,
            primary_driver=primary,
            contributing_factors=factors,
            confidence=confidence,
        )
