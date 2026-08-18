"""FININT OMEGA — Claim store with CRUD operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REFUTED = "refuted"


class Claim(BaseModel):
    """A factual claim that can be verified."""

    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    subject: str = ""
    source_id: str = ""
    status: ClaimStatus = ClaimStatus.PENDING
    confidence: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class ClaimStore:
    """CRUD store for factual claims."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    def create(self, text: str, **kwargs) -> Claim:
        claim = Claim(text=text, **kwargs)
        self._claims[claim.claim_id] = claim
        return claim

    def get(self, claim_id: str) -> Claim | None:
        return self._claims.get(claim_id)

    def update(self, claim_id: str, **kwargs) -> Claim | None:
        claim = self._claims.get(claim_id)
        if claim is None:
            return None
        update_data = kwargs.copy()
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = claim.model_copy(update=update_data)
        self._claims[claim_id] = updated
        return updated

    def delete(self, claim_id: str) -> bool:
        return self._claims.pop(claim_id, None) is not None

    def list_all(self) -> list[Claim]:
        return list(self._claims.values())

    def list_by_status(self, status: ClaimStatus) -> list[Claim]:
        return [c for c in self._claims.values() if c.status == status]

    def search(self, query: str) -> list[Claim]:
        q = query.lower()
        return [c for c in self._claims.values() if q in c.text.lower() or q in c.subject.lower()]

    def count(self) -> int:
        return len(self._claims)
