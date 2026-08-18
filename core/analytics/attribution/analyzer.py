"""FININT OMEGA — Attribution analytics: asset, sector, factor attribution."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AttributionResult(BaseModel):
    """Result of an attribution analysis."""

    total_return: float = 0.0
    asset_contribution: dict[str, float] = Field(default_factory=dict)
    sector_contribution: dict[str, float] = Field(default_factory=dict)
    factor_contribution: dict[str, float] = Field(default_factory=dict)
    residual: float = 0.0


class AttributionAnalyzer:
    """Decompose portfolio returns by asset, sector, and factor contributions."""

    def asset_attribution(self, holdings: list[dict]) -> dict[str, float]:
        """Compute return contribution by individual asset.

        Each holding should have 'symbol', 'weight', and 'return_pct'.
        """
        contributions: dict[str, float] = {}
        for h in holdings:
            symbol = h.get("symbol", "unknown")
            weight = h.get("weight", 0.0)
            ret = h.get("return_pct", 0.0)
            contributions[symbol] = weight * ret
        return contributions

    def sector_attribution(self, holdings: list[dict]) -> dict[str, float]:
        """Compute return contribution grouped by sector.

        Each holding should have 'sector', 'weight', and 'return_pct'.
        """
        sector_totals: dict[str, float] = {}
        sector_weights: dict[str, float] = {}
        for h in holdings:
            sector = h.get("sector", "Unknown")
            weight = h.get("weight", 0.0)
            ret = h.get("return_pct", 0.0)
            sector_totals[sector] = sector_totals.get(sector, 0.0) + weight * ret
            sector_weights[sector] = sector_weights.get(sector, 0.0) + weight
        return sector_totals

    def factor_attribution(self, holdings: list[dict], factor_exposures: dict[str, dict[str, float]]) -> dict[str, float]:
        """Compute return contribution by risk factors.

        factor_exposures maps factor_name -> {symbol: exposure}.
        Each holding should have 'symbol', 'weight', and 'return_pct'.
        """
        factor_returns: dict[str, float] = {}
        for factor_name, exposures in factor_exposures.items():
            contribution = 0.0
            for h in holdings:
                symbol = h.get("symbol", "unknown")
                weight = h.get("weight", 0.0)
                exposure = exposures.get(symbol, 0.0)
                contribution += weight * exposure
            factor_returns[factor_name] = contribution
        return factor_returns

    def full_attribution(
        self,
        holdings: list[dict],
        factor_exposures: dict[str, dict[str, float]] | None = None,
    ) -> AttributionResult:
        """Run complete attribution analysis."""
        asset_attr = self.asset_attribution(holdings)
        sector_attr = self.sector_attribution(holdings)
        factor_attr = self.factor_attribution(holdings, factor_exposures) if factor_exposures else {}
        total = sum(asset_attr.values())
        explained = sum(sector_attr.values())
        return AttributionResult(
            total_return=total,
            asset_contribution=asset_attr,
            sector_contribution=sector_attr,
            factor_contribution=factor_attr,
            residual=total - explained,
        )
