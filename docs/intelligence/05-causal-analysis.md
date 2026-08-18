# Causal Analysis Engine

## Overview
Builds and evaluates causal hypothesis chains from financial data. Models cause-effect relationships as directed graphs with confidence levels, alternative explanations, and testable predictions.

## Architecture
- **CausalEngine** — manages causal graphs and hypotheses
- **CausalGraph** — container for nodes, edges, and hypotheses
- **CausalNode** — a financial/economic/macro factor with label, value, category
- **CausalEdge** — directed relationship (causes, influences, correlated, temporal, inverse) with lag and magnitude
- **CausalHypothesis** — chain of nodes/edges with alternative explanations and testable predictions

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/causal/graphs` | Create a new causal graph |
| POST | `/api/v1/intelligence/causal/graphs/{graph_id}/nodes` | Add a node to the graph |
| POST | `/api/v1/intelligence/causal/graphs/{graph_id}/chain` | Build a causal chain (cause → effect) |
| GET | `/api/v1/intelligence/causal/hypotheses/{hypothesis_id}` | Get a hypothesis |
| POST | `/api/v1/intelligence/causal/hypotheses/{hypothesis_id}/evaluate` | Evaluate with evidence |
| GET | `/api/v1/intelligence/causal/graphs` | List all graphs |
| GET | `/api/v1/intelligence/causal/hypotheses` | List all hypotheses |

## Data Models
- **CausalRelationship**: `causes`, `influences`, `correlated`, `temporal`, `inverse`
- **CausalConfidence**: `high` (≥0.75), `moderate` (≥0.5), `low` (≥0.25), `speculative`
- **CausalNode**: label, description, current_value, unit, category
- **CausalEdge**: source/target, relationship, lag_periods, magnitude, evidence, assumptions
- **CausalHypothesis**: nodes, edges, alternative_explanations, testable_predictions

## Design Decisions
- Graph-based modeling allows complex multi-step causal chains
- Each hypothesis includes alternative explanations to force consideration of confounders
- Testable predictions derived automatically from chain structure
- Evidence evaluation uses support_ratio (for / total)

## Known Limitations
- No statistical causality testing (Granger, instrumental variables)
- Manual graph construction — no automated discovery
- No temporal data integration for lag validation
- In-memory storage only

## Test Coverage
- Tested via `tests/unit/test_causal.py`
- Covers: graph creation, node/edge addition, chain building, hypothesis evaluation
