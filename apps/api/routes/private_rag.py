"""FININT OMEGA — Private RAG API routes."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from core.data.private_rag.models import (
    AccessLevel,
    PrivateDocument,
    SourceClassification,
)
from core.data.private_rag.search import PrivateSearchEngine
from core.data.private_rag.store import PrivateDocumentStore

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/private", tags=["private-rag"])

_store = PrivateDocumentStore()
_engine = PrivateSearchEngine(_store)


class DocumentUploadRequest(BaseModel):
    """Request to upload a private document."""

    title: str
    content: str
    file_type: str = "text"
    access_level: AccessLevel = AccessLevel.PRIVATE
    source_classification: SourceClassification = SourceClassification.USER_UPLOADED
    metadata: dict = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    """Response for a single document."""

    doc_id: str
    owner_id: str
    title: str
    file_type: str
    access_level: str
    source_classification: str
    content_hash: str
    ingested_at: str
    metadata: dict


class SearchRequest(BaseModel):
    """Request to search private documents."""

    query: str
    top_k: int = 5


class SearchResponseItem(BaseModel):
    """Single search result item."""

    doc_id: str
    title: str
    content: str
    score: float
    metadata: dict


@router.post("/documents", response_model=DocumentResponse)
async def upload_document(request: DocumentUploadRequest, x_user_id: str = Header(...)):
    """Upload a new private document."""
    try:
        doc = PrivateDocument(
            title=request.title,
            content=request.content,
            file_type=request.file_type,
            access_level=request.access_level,
            source_classification=request.source_classification,
            metadata=request.metadata,
        )
        ingested = _store.ingest_document(doc, owner_id=x_user_id)
        return DocumentResponse(
            doc_id=ingested.doc_id,
            owner_id=ingested.owner_id,
            title=ingested.title,
            file_type=ingested.file_type,
            access_level=ingested.access_level.value,
            source_classification=ingested.source_classification.value,
            content_hash=ingested.content_hash,
            ingested_at=ingested.ingested_at.isoformat(),
            metadata=ingested.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("upload_document_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    x_user_id: str = Header(...),
    file_type: str | None = None,
    access_level: str | None = None,
):
    """List documents belonging to the authenticated user."""
    try:
        filters: dict = {}
        if file_type:
            filters["file_type"] = file_type
        if access_level:
            filters["access_level"] = access_level
        docs = _store.list_documents(owner_id=x_user_id, filters=filters if filters else None)
        return [
            DocumentResponse(
                doc_id=d.doc_id,
                owner_id=d.owner_id,
                title=d.title,
                file_type=d.file_type,
                access_level=d.access_level.value,
                source_classification=d.source_classification.value,
                content_hash=d.content_hash,
                ingested_at=d.ingested_at.isoformat(),
                metadata=d.metadata,
            )
            for d in docs
        ]
    except Exception as e:
        logger.error("list_documents_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, x_user_id: str = Header(...)):
    """Get a specific document by ID."""
    try:
        doc = _store.get_document(doc_id, owner_id=x_user_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse(
            doc_id=doc.doc_id,
            owner_id=doc.owner_id,
            title=doc.title,
            file_type=doc.file_type,
            access_level=doc.access_level.value,
            source_classification=doc.source_classification.value,
            content_hash=doc.content_hash,
            ingested_at=doc.ingested_at.isoformat(),
            metadata=doc.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_document_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, x_user_id: str = Header(...)):
    """Delete a document."""
    try:
        deleted = _store.delete_document(doc_id, owner_id=x_user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        return {"status": "deleted", "doc_id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_document_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/search", response_model=list[SearchResponseItem])
async def search_documents(request: SearchRequest, x_user_id: str = Header(...)):
    """Search private documents using hybrid search."""
    try:
        results = _engine.hybrid_search(
            query=request.query, owner_id=x_user_id, top_k=request.top_k
        )
        return [
            SearchResponseItem(
                doc_id=r.doc_id,
                title=r.title,
                content=r.content,
                score=r.score,
                metadata=r.metadata,
            )
            for r in results
        ]
    except Exception as e:
        logger.error("search_documents_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")
