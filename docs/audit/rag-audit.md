# RAG Audit

## Executive Summary

The RAG layer has **complete architectural components** but **non-functional execution** due to mock embeddings. The chunking, retrieval, reranking, and citation modules are well-structured but produce semantically meaningless results.

---

## 1. Document Parsing

### Status: BASIC
- Supports TEXT, FILE, URL, MOCK source types
- FILE parser: reads arbitrary files (path traversal vulnerability)
- URL parser: accepts pre-fetched content, no actual HTTP
- No PDF parsing
- No HTML parsing
- No Excel/CSV parsing
- No table extraction
- No OCR

### Critical Gap
- **Cannot read SEC filings** (10-K, 10-Q, 8-K)
- **Cannot read earnings call transcripts**
- **Cannot read research reports**

---

## 2. Chunking

### Status: FUNCTIONAL
- Fixed-size chunking with overlap
- Sentence-based chunking with overlap
- Produces typed Chunk objects

### Gaps
- No semantic chunking (paragraph/section boundaries)
- No token-aware chunking (character count, not token count)
- No metadata enrichment (page numbers, section headers)

---

## 3. Embeddings

### Status: MOCK
- Hash-based pseudo-embeddings using MD5 + trigonometric functions
- Deterministic but semantically meaningless
- Cosine similarity implemented correctly but useless

### Critical Gap
- "Apple the company" and "apple the fruit" get similar embeddings
- Retrieved context is random, not relevant

---

## 4. Retrieval

### Status: ARCHITECTURE ONLY
- HybridRetriever combines vector (60%) + keyword (40%)
- Architecture is sound
- Useless with mock embeddings

### Gaps
- No vector database (in-memory only)
- No BM25 or TF-IDF
- No persistent index
- O(n) scan on every search
- No incremental indexing

---

## 5. Reranking

### Status: BASIC
- Boosts by query-term hits
- Penalizes by text length
- No cross-encoder model
- No freshness boosting
- No entity-aware reranking

---

## 6. Citations

### Status: FUNCTIONAL BUT NOT AUTO-GENERATED
- CitationManager tracks citations
- Supports adding, linking, formatting
- Never automatically called
- No persistence

---

## 7. Test Scenarios

### One-Document Questions
- **Status**: Would work architecturally
- **Gap**: Mock embeddings return random results

### Multi-Document Questions
- **Status**: HybridRetriever supports multiple documents
- **Gap**: Results not semantically relevant

### Conflicting Documents
- **Status**: Conflict resolution in deep_research module
- **Gap**: Not wired to RAG layer

### Exact Numerical Values
- **Status**: Keyword matching would find exact numbers
- **Gap**: No structured data extraction

---

## 8. Recommendations

### Immediate (P0)
1. Replace MockEmbedder with real embedding model
2. Add vector database (Chroma, Qdrant, or pgvector)
3. Fix path traversal vulnerability in parser

### Short-term (P1)
4. Add PDF parsing (PyPDF2/pdfplumber)
5. Add HTML parsing (BeautifulSoup)
6. Implement semantic chunking
7. Add token-aware chunking

### Medium-term (P2)
8. Add cross-encoder reranking
9. Implement incremental indexing
10. Add metadata enrichment to chunks
11. Implement citation auto-generation
