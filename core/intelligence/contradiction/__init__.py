"""FININT OMEGA — Contradiction detection engine."""

from core.intelligence.contradiction.models import (
    ContradictionCategory,
    ContradictionItem,
    ContradictionResult,
    ContradictionSeverity,
    EvidenceConflict,
)
from core.intelligence.contradiction.detector import ContradictionDetector

__all__ = [
    "ContradictionCategory",
    "ContradictionDetector",
    "ContradictionItem",
    "ContradictionResult",
    "ContradictionSeverity",
    "EvidenceConflict",
]
