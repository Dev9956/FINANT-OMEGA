"""FININT OMEGA — Evidence verifier for claim verification."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from core.evidence.claims.store import Claim, ClaimStatus, ClaimStore


class VerificationResult(BaseModel):
    """Result of verifying a claim."""

    claim_id: str
    verified: bool = False
    confidence: float = 0.0
    supporting_sources: list[str] = Field(default_factory=list)
    contradicting_sources: list[str] = Field(default_factory=list)
    notes: str = ""
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceVerifier:
    """Verify claims against available evidence sources."""

    def __init__(self, claim_store: ClaimStore | None = None) -> None:
        self._claim_store = claim_store or ClaimStore()
        self._evidence_sources: dict[str, callable] = {}

    def register_source(self, source_id: str, checker: callable) -> None:
        self._evidence_sources[source_id] = checker

    def _check_against_source(self, claim: Claim, source_id: str, checker: callable) -> dict:
        try:
            result = checker(claim.text)
            return {
                "source_id": source_id,
                "supports": result.get("supports", False),
                "confidence": result.get("confidence", 0.0),
            }
        except Exception:
            return {"source_id": source_id, "supports": False, "confidence": 0.0}

    def verify(self, claim_id: str) -> VerificationResult:
        claim = self._claim_store.get(claim_id)
        if claim is None:
            return VerificationResult(claim_id=claim_id, notes="Claim not found")

        supporting: list[str] = []
        contradicting: list[str] = []
        total_confidence = 0.0
        source_count = 0

        for source_id, checker in self._evidence_sources.items():
            result = self._check_against_source(claim, source_id, checker)
            if result["supports"]:
                supporting.append(source_id)
                total_confidence += result["confidence"]
            else:
                contradicting.append(source_id)
            source_count += 1

        avg_confidence = total_confidence / max(source_count, 1)
        verified = len(supporting) > len(contradicting) and avg_confidence > 0.5

        status = ClaimStatus.VERIFIED if verified else ClaimStatus.DISPUTED
        self._claim_store.update(claim_id, status=status, confidence=avg_confidence, evidence_ids=supporting)

        return VerificationResult(
            claim_id=claim_id,
            verified=verified,
            confidence=avg_confidence,
            supporting_sources=supporting,
            contradicting_sources=contradicting,
        )

    def verify_text(self, text: str) -> VerificationResult:
        claim = self._claim_store.create(text=text)
        return self.verify(claim.claim_id)
