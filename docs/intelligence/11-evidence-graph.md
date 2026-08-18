# Evidence Graph

## Overview
Graph-based evidence tracking system that models relationships between claims, evidence, sources, and conclusions. Supports supporting/contradicting/derived relationships with confidence propagation.

## Architecture
- **EvidenceGraph** — adjacency-list graph with forward and reverse indexes
- Node types: claim, evidence, source, calculation, document, conclusion, data_point
- Edge relationships: supports, contradicts, derived_from, sourced_from, calculated_by, references, strengthens, weakens
- Confidence propagation: computed from supporting vs contradicting evidence weights

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/evidence-graph/nodes` | Add a node |
| POST | `/api/v1/intelligence/evidence-graph/edges` | Add an edge |
| GET | `/api/v1/intelligence/evidence-graph/nodes/{node_id}` | Get a node |
| GET | `/api/v1/intelligence/evidence-graph/nodes/{node_id}/supporting` | Get supporting evidence |
| GET | `/api/v1/intelligence/evidence-graph/nodes/{node_id}/contradicting` | Get contradicting evidence |
| GET | `/api/v1/intelligence/evidence-graph/nodes/{node_id}/chain` | Get full evidence chain for conclusion |
| GET | `/api/v1/intelligence/evidence-graph/nodes/{node_id}/confidence` | Compute node confidence |
| GET | `/api/v1/intelligence/evidence-graph/search?q=` | Search nodes by content |
| GET | `/api/v1/intelligence/evidence-graph/stats` | Graph statistics |

## Data Models
- **EvidenceNodeType**: `claim`, `evidence`, `source`, `calculation`, `document`, `conclusion`, `data_point`
- **GraphRelationship**: `supports`, `contradicts`, `derived_from`, `sourced_from`, `calculated_by`, `references`, `strengthens`, `weakens`
- **EvidenceNode**: node_type, label, content, confidence, source_id, metadata
- **EvidenceEdge**: source/target, relationship, weight, confidence, description

## Design Decisions
- Bidirectional adjacency lists enable efficient forward/backward traversal
- Confidence = support_score / (support_score + contra_score) — simple ratio
- Conclusion nodes can trace full evidence chain including sources
- Text search via case-insensitive substring matching

## Known Limitations
- No graph persistence — in-memory only
- No cycle detection
- No graph visualization export
- Search is linear scan — not indexed

## Test Coverage
- Tested via `tests/unit/test_evidence_graph.py`
- Covers: node/edge addition, supporting/contradicting retrieval, confidence computation, evidence chains
