# Research Memory

## Overview
Provides persistent research context by storing and retrieving past research findings, hypotheses, and evidence. Acts as the long-term memory for the autonomous research loop and other intelligence features.

## Architecture
- Part of the `core.research` module
- Stores research findings with timestamps and source tracking
- Supports query-based retrieval of relevant past research
- Integrates with the Evidence Graph for structured evidence storage

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| — | — | Accessed via research and evidence graph APIs |

## Data Models
- Research findings stored as evidence items with provenance
- Query interface via Evidence Graph search functionality

## Design Decisions
- Leverages Evidence Graph as the underlying storage mechanism
- Provenance tracking ensures research traceability
- Query-by-content for retrieval

## Known Limitations
- No dedicated memory-specific API
- No semantic search (only keyword-based)
- No automatic memory consolidation or summarization
- No forgetting mechanism for stale research

## Test Coverage
- Indirectly tested via evidence graph and research loop tests
