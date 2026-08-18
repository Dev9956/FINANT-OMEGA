"""FININT OMEGA — Unit tests for Private RAG."""

import pytest

from core.data.private_rag.models import (
    AccessLevel,
    PrivateDocument,
    SourceClassification,
    TenantContext,
)
from core.data.private_rag.search import PrivateSearchEngine
from core.data.private_rag.store import PrivateDocumentStore


class TestPrivateDocumentStore:
    """Test document ingestion with tenant isolation."""

    def setup_method(self):
        self.store = PrivateDocumentStore()

    def test_ingest_document(self):
        doc = PrivateDocument(title="Test", content="Hello world")
        result = self.store.ingest_document(doc, owner_id="user1")
        assert result.doc_id
        assert result.owner_id == "user1"
        assert result.title == "Test"
        assert result.content_hash

    def test_get_document(self):
        doc = PrivateDocument(title="Test", content="Content")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        retrieved = self.store.get_document(ingested.doc_id, owner_id="user1")
        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_get_document_wrong_owner(self):
        doc = PrivateDocument(title="Test", content="Content")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        retrieved = self.store.get_document(ingested.doc_id, owner_id="user2")
        assert retrieved is None

    def test_list_documents(self):
        self.store.ingest_document(PrivateDocument(title="A", content="a"), "user1")
        self.store.ingest_document(PrivateDocument(title="B", content="b"), "user1")
        self.store.ingest_document(PrivateDocument(title="C", content="c"), "user2")
        docs = self.store.list_documents("user1")
        assert len(docs) == 2

    def test_delete_document(self):
        doc = PrivateDocument(title="Del", content="x")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        assert self.store.delete_document(ingested.doc_id, "user1") is True
        assert self.store.get_document(ingested.doc_id, "user1") is None

    def test_delete_wrong_owner(self):
        doc = PrivateDocument(title="Del", content="x")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        assert self.store.delete_document(ingested.doc_id, "user2") is False

    def test_search_returns_only_owners_docs(self):
        self.store.ingest_document(
            PrivateDocument(title="Finance Report", content="revenue growth"), "user1"
        )
        self.store.ingest_document(
            PrivateDocument(title="Finance Report", content="revenue growth"), "user2"
        )
        results = self.store.search("revenue", "user1")
        assert len(results) == 1
        assert results[0].doc_id

    def test_document_hash_integrity(self):
        doc = PrivateDocument(title="Hash", content="integrity check")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        hash_val = self.store.get_document_hash(ingested.doc_id)
        assert hash_val
        assert len(hash_val) == 64  # SHA-256 hex length

    def test_verify_access(self):
        doc = PrivateDocument(title="Access", content="test")
        ingested = self.store.ingest_document(doc, owner_id="user1")
        assert self.store.verify_access(ingested.doc_id, "user1") is True
        assert self.store.verify_access(ingested.doc_id, "user2") is False

    def test_verify_access_nonexistent(self):
        assert self.store.verify_access("nonexistent", "user1") is False


class TestPrivateSearchEngine:
    """Test search engine with tenant isolation."""

    def setup_method(self):
        self.store = PrivateDocumentStore()
        self.engine = PrivateSearchEngine(self.store)

    def test_keyword_search(self):
        self.store.ingest_document(
            PrivateDocument(title="Alpha", content="beta gamma"), "user1"
        )
        results = self.engine.keyword_search("beta", "user1")
        assert len(results) == 1

    def test_hybrid_search_merges_results(self):
        self.store.ingest_document(
            PrivateDocument(title="Finance", content="revenue"), "user1"
        )
        results = self.engine.hybrid_search("finance", "user1")
        assert len(results) >= 1

    def test_merge_results_deduplicates(self):
        from core.data.private_rag.models import SearchResult

        r1 = SearchResult(doc_id="d1", title="T", content="C", score=1.0)
        r2 = SearchResult(doc_id="d1", title="T", content="C", score=0.5)
        merged = self.engine.merge_results([r1, r2], [], top_k=5)
        assert len(merged) == 1

    def test_cross_tenant_isolation_in_search(self):
        self.store.ingest_document(
            PrivateDocument(title="Secret", content="confidential"), "user1"
        )
        self.store.ingest_document(
            PrivateDocument(title="Secret", content="confidential"), "user2"
        )
        results = self.engine.keyword_search("confidential", "user1")
        assert len(results) == 1
        results = self.engine.keyword_search("confidential", "user2")
        assert len(results) == 1


class TestAccessLevel:
    """Test access level enum."""

    def test_access_levels(self):
        assert AccessLevel.PRIVATE.value == "private"
        assert AccessLevel.SHARED.value == "shared"
        assert AccessLevel.PUBLIC.value == "public"

    def test_source_classifications(self):
        assert SourceClassification.USER_UPLOADED.value == "user_uploaded"
        assert SourceClassification.USER_CREATED.value == "user_created"
        assert SourceClassification.LICENSED.value == "licensed"


class TestTenantContext:
    """Test tenant context model."""

    def test_create_context(self):
        ctx = TenantContext(user_id="u1", tenant_id="t1")
        assert ctx.user_id == "u1"
        assert ctx.access_level == AccessLevel.PRIVATE
