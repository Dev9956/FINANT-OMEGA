"""FININT OMEGA — Private document store with tenant isolation."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import structlog

from core.data.private_rag.models import (
    AccessLevel,
    PrivateDocument,
    SearchResult,
)

logger = structlog.get_logger()


class PrivateDocumentStore:
    """In-memory document store with tenant isolation."""

    def __init__(self) -> None:
        self._documents: dict[str, PrivateDocument] = {}

    def ingest_document(self, doc: PrivateDocument, owner_id: str) -> PrivateDocument:
        """Ingest a new document, enforcing owner assignment."""
        try:
            if not doc.doc_id:
                doc.doc_id = str(uuid.uuid4())
            if doc.owner_id and doc.owner_id != owner_id:
                raise ValueError("Document owner mismatch: cannot ingest another user's document")
            doc.owner_id = owner_id
            if not doc.content_hash:
                doc.content_hash = hashlib.sha256(doc.content.encode("utf-8")).hexdigest()
            doc.ingested_at = datetime.now(timezone.utc)
            self._documents[doc.doc_id] = doc
            logger.info("document_ingested", doc_id=doc.doc_id, owner_id=owner_id)
            return doc
        except Exception as e:
            logger.error("ingest_document_failed", error=str(e))
            raise

    def get_document(self, doc_id: str, owner_id: str) -> PrivateDocument | None:
        """Get a document by ID, enforcing owner access."""
        try:
            doc = self._documents.get(doc_id)
            if doc is None:
                return None
            if doc.owner_id != owner_id:
                logger.warning("access_denied", doc_id=doc_id, owner_id=owner_id)
                return None
            return doc
        except Exception as e:
            logger.error("get_document_failed", error=str(e))
            return None

    def list_documents(
        self, owner_id: str, filters: dict | None = None
    ) -> list[PrivateDocument]:
        """List documents belonging to an owner with optional filters."""
        try:
            results = [
                doc for doc in self._documents.values() if doc.owner_id == owner_id
            ]
            if filters:
                if "file_type" in filters:
                    results = [d for d in results if d.file_type == filters["file_type"]]
                if "access_level" in filters:
                    results = [
                        d for d in results if d.access_level.value == filters["access_level"]
                    ]
                if "source_classification" in filters:
                    results = [
                        d
                        for d in results
                        if d.source_classification.value == filters["source_classification"]
                    ]
            return results
        except Exception as e:
            logger.error("list_documents_failed", error=str(e))
            return []

    def delete_document(self, doc_id: str, owner_id: str) -> bool:
        """Delete a document, enforcing owner access."""
        try:
            doc = self._documents.get(doc_id)
            if doc is None:
                return False
            if doc.owner_id != owner_id:
                logger.warning("delete_denied", doc_id=doc_id, owner_id=owner_id)
                return False
            del self._documents[doc_id]
            logger.info("document_deleted", doc_id=doc_id, owner_id=owner_id)
            return True
        except Exception as e:
            logger.error("delete_document_failed", error=str(e))
            return False

    def search(self, query: str, owner_id: str, top_k: int = 5) -> list[SearchResult]:
        """Search documents by keyword, returning only owner's documents."""
        try:
            query_lower = query.lower()
            scored: list[tuple[float, PrivateDocument]] = []
            for doc in self._documents.values():
                if doc.owner_id != owner_id:
                    continue
                title_match = 1.0 if query_lower in doc.title.lower() else 0.0
                content_match = 1.0 if query_lower in doc.content.lower() else 0.0
                score = title_match * 2.0 + content_match
                if score > 0:
                    scored.append((score, doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for score, doc in scored[:top_k]:
                results.append(
                    SearchResult(
                        doc_id=doc.doc_id,
                        title=doc.title,
                        content=doc.content[:500],
                        score=score,
                        metadata=doc.metadata,
                    )
                )
            return results
        except Exception as e:
            logger.error("search_failed", error=str(e))
            return []

    def verify_access(self, doc_id: str, owner_id: str) -> bool:
        """Verify that a user has access to a document."""
        doc = self._documents.get(doc_id)
        if doc is None:
            return False
        return doc.owner_id == owner_id

    def get_document_hash(self, doc_id: str) -> str | None:
        """Get the content hash of a document."""
        doc = self._documents.get(doc_id)
        if doc is None:
            return None
        return doc.content_hash
