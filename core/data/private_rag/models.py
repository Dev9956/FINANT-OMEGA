"""FININT OMEGA — Private RAG models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AccessLevel(str, Enum):
    """Document access level."""

    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class SourceClassification(str, Enum):
    """How the document was obtained."""

    USER_UPLOADED = "user_uploaded"
    USER_CREATED = "user_created"
    LICENSED = "licensed"


class PrivateDocument(BaseModel):
    """A private document stored in the RAG system."""

    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str = Field(default="", description="User who owns this document")
    title: str
    content: str
    content_hash: str = Field(default="", description="SHA-256 hash of content")
    file_type: str = Field(default="text", description="Document file type")
    access_level: AccessLevel = AccessLevel.PRIVATE
    metadata: dict = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_classification: SourceClassification = SourceClassification.USER_UPLOADED


class PrivateDocumentChunk(BaseModel):
    """A chunk of a private document for embedding/search."""

    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    owner_id: str
    content: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class TenantContext(BaseModel):
    """Context for a tenant/user operation."""

    user_id: str
    tenant_id: str = ""
    access_level: AccessLevel = AccessLevel.PRIVATE


class SearchResult(BaseModel):
    """Result from a private RAG search."""

    doc_id: str
    chunk_id: str | None = None
    title: str
    content: str
    score: float = 0.0
    metadata: dict = Field(default_factory=dict)
