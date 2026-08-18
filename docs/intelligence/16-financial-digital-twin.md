# Financial Digital Twin

## Overview
Creates dynamic digital representations of companies/assets that maintain state snapshots and support scenario application. Tracks financials, market data, valuation, and risk across time.

## Architecture
- **DigitalTwinEngine** — manages twins, snapshots, and scenarios
- **DigitalTwin** — entity container with snapshot history and scenario history
- **TwinSnapshot** — point-in-time state with financials, market, valuation, risk dictionaries
- **TwinScenario** — named scenario with percentage changes applied to latest snapshot

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/digital-twin` | Create a digital twin |
| GET | `/api/v1/intelligence/digital-twin/{twin_id}` | Get twin with history |
| POST | `/api/v1/intelligence/digital-twin/{twin_id}/snapshot` | Add/update snapshot |
| POST | `/api/v1/intelligence/digital-twin/{twin_id}/scenario` | Apply scenario |
| GET | `/api/v1/intelligence/digital-twin` | List all twins |

## Data Models
- **TwinSnapshot**: financials, market, valuation, risk (all dict[str, float]), thesis, timestamp
- **TwinScenario**: name, changes (percentage), affected_metrics, assumptions, confidence
- **DigitalTwin**: entity, name, snapshots[], scenarios[], created_at, updated_at

## Design Decisions
- Snapshot-based history for time-series tracking
- Scenario application modifies latest snapshot values by percentage
- Flexible dictionaries allow any financial metrics
- Twin lookup by entity name for convenience

## Known Limitations
- No real-time data feeds
- No automatic snapshot generation
- No scenario comparison or backtesting
- No cross-twin correlation analysis

## Test Coverage
- Tested via `tests/unit/test_digital_twin.py`
- Covers: twin creation, snapshot updates, scenario application, listing
