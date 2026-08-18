# Advanced Change Detection — Architecture

## Overview

The Change Detection system detects and classifies changes between data snapshots across multiple dimensions: numerical, textual, structural, sentiment, guidance, and risk. Each change is severity-classified and can be compared across time periods with significance scoring.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /change-detection/compare                  │
├──────────────────────────────────────────────────┤
│              PeriodComparator                     │
│  compare_periods · compute_significance           │
│  generate_summary                                 │
├──────────────────────────────────────────────────┤
│              ChangeDetector                       │
│  detect_numerical · detect_textual                │
│  detect_structural · detect_sentiment             │
│  detect_guidance · detect_risk                    │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  DetectedChange · ComparisonResult                │
│  ChangeType · ChangeSeverity                      │
└──────────────────────────────────────────────────┘
```

## Key Components

### ChangeDetector (`core/intelligence/change_detection/detector.py`)

#### Change Types

| Type | Method | Description |
|------|--------|-------------|
| `NUMERICAL` | `detect_numerical_changes(a, b, thresholds)` | Percentage-based field comparison with configurable thresholds (default 5%) |
| `TEXTUAL` | `detect_textual_changes(text_a, text_b)` | Word-level Jaccard similarity; severity based on similarity ratio |
| `STRUCTURAL` | `detect_structural_changes(schema_a, schema_b)` | Detects added/removed fields between dicts |
| `SENTIMENT` | `detect_sentiment_changes(sent_a, sent_b)` | Detects shifts ≥0.05 in sentiment scores |
| `GUIDANCE` | `detect_guidance_changes(guid_a, guid_b)` | Detects forward guidance changes with severity by magnitude |
| `RISK` | `detect_risk_changes(risks_a, risks_b)` | Detects added/removed risk factors |

#### Severity Classification

| Severity | Numerical | Textual Similarity | Sentiment Shift |
|----------|-----------|-------------------|-----------------|
| TRIVIAL | <2% | ≥95% | <0.1 |
| MINOR | ≥2% | ≥80% | ≥0.1 |
| MODERATE | ≥5% | ≥50% | ≥0.2 |
| MAJOR | ≥10% | <50% | ≥0.3 |
| CRITICAL | ≥20% | — | ≥0.5 |

### PeriodComparator (`core/intelligence/change_detection/comparator.py`)

- **`compare_periods(data_a, period_a, data_b, period_b, entity)`** — Runs all detectors on matching data types, computes significance, generates summary
- **`compute_significance(changes)`** — Weighted average: TRIVIAL=0.1, MINOR=0.3, MODERATE=0.5, MAJOR=0.8, CRITICAL=1.0, multiplied by confidence
- **`generate_summary(result)`** — Human-readable summary with change counts and significance percentage

## Data Models

```
DetectedChange
  ├── change_type: ChangeType
  ├── severity: ChangeSeverity
  ├── field: str
  ├── old_value / new_value: object
  ├── change_pct: float
  ├── evidence: str
  ├── confidence: float
  └── timestamp: datetime

ComparisonResult
  ├── entity_a / entity_b: str
  ├── period_a / period_b: str
  ├── changes: list[DetectedChange]
  ├── overall_significance: float
  └── summary: str
```

## Data Flow

```
Period A Data + Period B Data
  │
  ▼
PeriodComparator.compare_periods()
  │
  ├─ extract numerical fields → detect_numerical_changes()
  ├─ extract text fields → detect_textual_changes()
  ├─ extract sentiment dict → detect_sentiment_changes()
  ├─ extract guidance dict → detect_guidance_changes()
  ├─ extract risk list → detect_risk_changes()
  │
  ▼
list[DetectedChange]
  │
  ▼
compute_significance(changes)
  → overall_significance: float
  │
  ▼
generate_summary(result)
  → "Comparing Q1 vs Q2: 5 changes (2 moderate, 1 major). Significance: 65%."
```

## Design Decisions

1. **Multi-dimensional detection** — Separate detectors for each change type enable independent tuning
2. **Configurable thresholds** — Numerical thresholds per field allow domain-specific sensitivity
3. **Severity-weighted significance** — Higher-severity changes contribute more to overall significance
4. **Evidence strings** — Each change includes human-readable evidence for audit trails
5. **Confidence scoring** — Changes include confidence based on magnitude

## Known Limitations

- No semantic understanding of textual changes (word-level only)
- Sentiment detection relies on pre-computed sentiment scores
- No time-series analysis (point-in-time comparison only)
- Significance scoring is linear; no non-linear weighting
- No cross-entity correlation (single entity comparison)
