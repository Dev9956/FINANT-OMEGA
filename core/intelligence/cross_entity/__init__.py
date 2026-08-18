"""FININT OMEGA — Large-Scale Cross-Entity Intelligence."""

from core.intelligence.cross_entity.models import (
    CrossEntityRequest,
    CrossEntityResult,
    EntityMetrics,
    RankingResult,
)
from core.intelligence.cross_entity.engine import CrossEntityEngine

__all__ = [
    "CrossEntityEngine",
    "CrossEntityRequest",
    "CrossEntityResult",
    "EntityMetrics",
    "RankingResult",
]
