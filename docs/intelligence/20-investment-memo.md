# Investment Memo Engine

## Overview
Generates structured investment memos with 12 sections: executive summary, thesis, bull/base/bear cases, valuation, financial quality, risks, contradicting evidence, scenario analysis, "what would change my mind", and evidence limitations. Supports markdown rendering.

## Architecture
- **MemoEngine** — generates and renders investment memos
- **InvestmentMemo** — container with optional MemoSection fields
- **MemoSection** — title, content, evidence list, confidence
- Auto-generated executive summary and "what would change my mind" from inputs
- Markdown renderer produces formatted output

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/memo/generate` | Generate a memo |
| GET | `/api/v1/intelligence/memo/{memo_id}` | Get memo |
| GET | `/api/v1/intelligence/memo/{memo_id}/render?format=markdown` | Render memo as markdown |

## Data Models
- **MemoSection**: title, content, evidence[], confidence
- **InvestmentMemo**: entity, title, 12 optional sections, confidence, created_at

## Design Decisions
- All sections optional — memo can be built incrementally
- "What would change my mind" auto-derived from risks
- Executive summary truncated to 200 chars for conciseness
- Evidence attached to sections for traceability
- Markdown rendering for human-readable output

## Known Limitations
- No PDF/HTML export
- No template customization
- No collaborative editing
- No version control for memos

## Test Coverage
- Tested via `tests/unit/test_memo.py`
- Covers: memo generation, section population, markdown rendering
