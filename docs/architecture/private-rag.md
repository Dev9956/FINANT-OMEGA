# Private RAG — Architecture

## Overview

Private RAG provides tenant-isolated document storage and hybrid search for confidential financial documents. Each user's documents are strictly isolated — no cross-tenant access is possible. Supports document ingestion, keyword search, vector search (placeholder), and hybrid search with result merging.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /rag/documents   GET /rag/search           │
│  GET /rag/documents/{id}   DELETE /rag/...       │
├──────────────────────────────────────────────────┤
│           PrivateSearchEngine                     │
│  hybrid_search · vector_search · keyword_search   │
│  merge_results                                    │
├──────────────────────────────────────────────────┤
│           PrivateDocumentStore                    │
│  ingest · get · list · delete · search            │
│  verify_access · get_document_hash                │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  PrivateDocument · PrivateDocumentChunk           │
│  TenantContext · SearchResult                     │
│  AccessLevel · SourceClassification               │
└──────────────────────────────────────────────────┘
```

## Key Components

### PrivateDocumentStore (`core/data/private_rag/store.py`)

- **`ingest_document(doc, owner_id)`** — Ingests document with owner enforcement, SHA-256 content hashing
- **`get_document(doc_id, owner_id)`** — Returns document only if owner matches
- **`list_documents(owner_id, filters)`** — Lists owner's documents with optional filters (file_type, access_level, source_classification)
- **`delete_document(doc_id, owner_id)`** — Owner-only deletion
- **`search(query, owner_id, top_k)`** — Keyword search scoped to owner's documents
- **`verify_access(doc_id, owner_id)`** — Access verification
- **`get_document_hash(doc_id)`** — Returns SHA-256 content hash

### PrivateSearchEngine (`core/data/private_rag/search.py`)

- **`hybrid_search(query, owner_id, top_k)`** — Combines vector and keyword results
- **`vector_search(query, owner_id, top_k)`** — Placeholder using keyword fallback (to be replaced with embedding-based search)
- **`keyword_search(query, owner_id, top_k)`** — Delegates to store's keyword search
- **`merge_results(vector_results, keyword_results, top_k)`** — Deduplicates by doc_id, keeps highest score

### Tenant Isolation Model

```
User A (owner_id="user_a")
  ├── doc_1 (owner: user_a) ✓ accessible
  ├── doc_2 (owner: user_a) ✓ accessible
  └── doc_3 (owner: user_b) ✗ inaccessible

User B (owner_id="user_b")
  ├── doc_3 (owner: user_b) ✓ accessible
  └── doc_1 (owner: user_a) ✗ inaccessible
```

Every operation checks `owner_id` before returning data. The store never returns documents belonging to other users.

## Data Models

```
PrivateDocument
  ├── doc_id: str (UUID)
  ├── owner_id: str
  ├── title: str
  ├── content: str
  ├── content_hash: str (SHA-256)
  ├── file_type: str
  ├── access_level: AccessLevel (PRIVATE/SHARED/PUBLIC)
  ├── source_classification: SourceClassification
  ├── metadata: dict
  └── ingested_at: datetime

SearchResult
  ├── doc_id: str
  ├── chunk_id: str | None
  ├── title: str
  ├── content: str (truncated to 500 chars)
  ├── score: float
  └── metadata: dict
```

## Security Model

1. **Owner enforcement** — All operations require `owner_id`; mismatched owners get `None`/empty results
2. **Content hashing** — SHA-256 hash stored for integrity verification
3. **No cross-tenant queries** — Search is scoped to `owner_id` filter
4. **Access levels** — PRIVATE/SHARED/PUBLIC classification (SHARED/PUBLIC not yet implemented for cross-user access)
5. **Source classification** — USER_UPLOADED, USER_CREATED, LICENSED for provenance tracking

## Data Flow

```
Document Upload
  │
  ▼
PrivateDocumentStore.ingest_document(doc, owner_id)
  ├─ enforce owner assignment
  ├─ compute SHA-256 content hash
  └─ store in memory

Search Request
  │
  ▼
PrivateSearchEngine.hybrid_search(query, owner_id)
  ├─ vector_search() → scored results
  ├─ keyword_search() → scored results
  └─ merge_results() → deduplicated, ranked
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/rag/documents` | Ingest a document |
| GET | `/api/v1/rag/documents` | List user's documents |
| GET | `/api/v1/rag/documents/{doc_id}` | Get document by ID |
| DELETE | `/api/v1/rag/documents/{doc_id}` | Delete document |
| GET | `/api/v1/rag/search` | Search documents |

## Design Decisions

1. **Owner-based isolation** — Simplest multi-tenant model; no complex ACL needed
2. **In-memory store** — Fast iteration; migration path to PostgreSQL/Redis documented
3. **Hybrid search** — Combines keyword (exact match) with vector (semantic) for better recall
4. **Content hashing** — Enables deduplication and integrity verification
5. **Placeholder vector search** — Keyword fallback allows testing; real embeddings pluggable

## Known Limitations

- In-memory only — no persistence across restarts
- Vector search is placeholder (keyword-based fallback)
- No document chunking or embedding generation
- SHARED/PUBLIC access levels not implemented for cross-user sharing
- No document versioning
- Search is O(n) over all documents (no indexing)
