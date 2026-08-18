"""FININT OMEGA — AI Investment Debate Engine."""

from core.intelligence.debate.models import (
    AnalystRole,
    DebateConfig,
    DebateResult,
    EvidenceVerification,
    SynthesisResult,
)
from core.intelligence.debate.engine import DebateEngine

__all__ = [
    "AnalystRole",
    "DebateConfig",
    "DebateEngine",
    "DebateResult",
    "EvidenceVerification",
    "SynthesisResult",
]
