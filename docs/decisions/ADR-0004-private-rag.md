# ADR-0004: Private RAG

## Status

Accepted

## Date

2026-08-16

## Context

FININT OMEGA needs a Retrieval-Augmented Generation system for confidential financial documents that:
1. Provides strict tenant isolation (no cross-user access)
2. Supports document ingestion with provenance tracking
3. Enables hybrid search (keyword + vector)
4. Validates access on every operation
5. Tracks document integrity via content hashing

The system must handle earnings transcripts, research notes, filings, and other sensitive documents without leaking across tenants.

## Decision

Implement a **tenant-isolated private RAG** with:

1. **PrivateDocumentStore** — In-memory store with owner_id enforcement on every operation
2. **PrivateSearchEngine** — Hybrid search combining keyword and vector (placeholder) results
3. **Owner-based isolation** — Simplest multi-tenant model; `owner_id` checked on ingest, get, list, delete, search
4. **Content hashing** — SHA-256 hash stored on ingest for integrity verification
5. **Access levels** — PRIVATE/SHARED/PUBLIC classification (SHARED/PUBLIC reserved for future)
6. **Source classification** — USER_UPLOADED/USER_CREATED/LICENSED for provenance

### Security Model

- Every API operation requires `owner_id` parameter
- Store filters all queries by `owner_id`
- Cross-tenant access returns `None` or empty results
- Content hash enables tamper detection

## Consequences

### Positive

- **Simplicity** — Owner-based isolation is easy to reason about and audit
- **Security** — No complex ACL; every operation owner-checked
- **Integrity** — SHA-256 hashing detects document tampering
- **Provenance** — Source classification tracks document origin
- **Extensibility** — Vector search placeholder allows future embedding integration

### Negative

- **In-memory only** — No persistence across restarts
- **No real vector search** — Keyword fallback until embeddings implemented
- **No document chunking** — Large documents not split for embedding
- **No cross-user sharing** — SHARED/PUBLIC levels defined but not implemented
- **O(n) search** — No indexing; performance degrades with document count

### Mitigations

- Future: Migrate to PostgreSQL/Redis for persistence
- Future: Integrate sentence-transformers for real vector search
- Future: Implement document chunking and embedding pipeline
- Future: Implement SHARED/PUBLIC access with ACL
- Future: Add inverted index for keyword search

## Related

- See `docs/architecture/private-rag.md` for detailed architecture
- See `core/data/private_rag/` for implementation
- See `apps/api/routes/private_rag.py` for API endpoints
