# Deep Research Engine — Architecture

## Overview

The Deep Research Engine orchestrates multi-step financial research by decomposing questions into sub-questions, executing research tasks in parallel via a DAG, collecting evidence, detecting conflicts, and synthesizing findings with confidence scoring.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
│  POST /research/deep    GET /research/{id}                │
│  GET /research/{id}/tasks   GET /research/{id}/evidence   │
├──────────────────────────────────────────────────────────┤
│                  Research Planner                         │
│  question → domains → sub-questions → tasks               │
├──────────────────────────────────────────────────────────┤
│                   Task Graph (DAG)                        │
│  topological sort → ready_tasks → parallel execution      │
├──────────────────────────────────────────────────────────┤
│                  Research Executor                        │
│  tool dispatch → retry → evidence collection              │
├──────────────────────────────────────────────────────────┤
│               Conflict Resolver                           │
│  detect → classify → suggest → resolve                    │
├──────────────────────────────────────────────────────────┤
│               Research Synthesizer                        │
│  consensus → disagreement → confidence → limitations      │
├──────────────────────────────────────────────────────────┤
│               Research Evaluator                          │
│  completeness × evidence quality × consistency            │
├──────────────────────────────────────────────────────────┤
│             Budget & Stopping Control                     │
│  tokens · time · tasks · convergence                      │
└──────────────────────────────────────────────────────────┘
```

## Key Components

### ResearchPlanner (`core/research/deep_research/planner.py`)

- **`analyze_question(question)`** — Detects financial domains (company, earnings, valuation, sector, macro, risk, technical, portfolio) via keyword matching, extracts entity symbols, and generates domain-specific sub-questions from templates.
- **`create_task_graph(sub_questions, config)`** — Creates `ResearchTask` instances limited by `config.max_tasks`. All sub-tasks depend on the root task (first task).
- **`plan(question, config)`** — Full pipeline: analyze → create tasks.

### TaskGraph (`core/research/deep_research/task_graph.py`)

- DAG with cycle detection (DFS-based `CircularDependencyError`)
- **`topological_sort()`** — Returns tasks in dependency order
- **`ready_tasks()`** — Returns PENDING tasks whose dependencies are all COMPLETED
- **`complete_task(task_id, result)`** / **`fail_task(task_id, error)`** — State transitions
- **`is_complete()`** — True when all tasks are COMPLETED, FAILED, or SKIPPED

### ResearchExecutor (`core/research/desearch/executor.py`)

- Routes tasks to tools based on question keywords (price→market_data, earnings→earnings_data, valuation→fundamentals, etc.)
- Exponential backoff retry (up to 3 attempts, max 10s delay)
- **`execute_parallel(tasks, max_workers=4)`** — ThreadPoolExecutor-based parallel execution
- Wraps tool results as `EvidenceItem` with confidence scores

### ConflictResolver (`core/research/deep_research/conflict_resolution.py`)

- Detects conflicts between supporting and contradicting evidence for the same claim
- Severity based on confidence difference between opposing evidence
- Classifies as critical (≥0.7), moderate (≥0.4), or minor
- Auto-resolves by comparing average confidence; marks as IRREDUCIBLE when confidence difference <0.1

### ResearchSynthesizer (`core/research/deep_research/synthesis.py`)

- Groups evidence by claim, separates consensus from disagreement
- Computes overall confidence with conflict penalty (−0.05 per unresolved conflict, max −0.3)
- Generates limitations (low confidence, limited diversity, unresolved conflicts, shallow depth)
- Produces methodology summary from evidence source types

### ResearchEvaluator (`core/research/desearch/evaluation.py`)

- **Completeness** — task completion ratio × 0.5 + evidence score × 0.3 + synthesis bonus × 0.2 − failure penalty
- **Evidence Quality** — average confidence + source diversity bonus (max +0.2)
- **Consistency** — 1.0 − contradiction ratio − conflict penalty
- **Overall** — average of completeness, quality, consistency

### ResearchBudget (`core/research/deep_research/research_budget.py`)

- Tracks tokens used, API calls, elapsed time, task count
- `enforce_budget()` returns False when any limit is exceeded
- Usage reports with utilization percentages

### StoppingCriteria (`core/research/deep_research/stopping.py`)

- Evaluates: max_tasks_reached, max_sources_reached, max_time_reached, confidence_threshold_met, no_new_evidence (3 consecutive unchanged hashes), all_tasks_complete

## Data Models

| Model | Purpose |
|-------|---------|
| `ResearchConfig` | Depth presets (shallow/standard/deep), max_tasks, max_sources, timeout, budget_tokens |
| `ResearchTask` | Task with status, dependencies, evidence_ids, result/error |
| `EvidenceItem` | Source type/id, content, confidence, supports/contradicts claim |
| `ConflictItem` | Two opposing claims, severity, resolution status |
| `ResearchSynthesis` | Conclusion, confidence, claims, limitations, methodology |
| `ResearchRun` | Full run: tasks + evidence + conflicts + synthesis |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/research/deep` | Start deep research run |
| GET | `/api/v1/research/{research_id}` | Get research status |
| GET | `/api/v1/research/{research_id}/tasks` | Get task details |
| GET | `/api/v1/research/{research_id}/evidence` | Get collected evidence |

## Data Flow

```
Question
  │
  ▼
ResearchPlanner.analyze_question()
  → detected domains + entities
  → domain-specific sub-questions
  │
  ▼
ResearchPlanner.create_task_graph()
  → list[ResearchTask] with dependencies
  │
  ▼
TaskGraph (cycle validation + topological sort)
  │
  ▼
ResearchExecutor.execute_parallel()
  → tool dispatch per task
  → retry with backoff
  → EvidenceItem collection
  │
  ▼
ConflictResolver.detect_conflicts()
  → list[ConflictItem]
  │
  ▼
ResearchSynthesizer.synthesize()
  → ResearchSynthesis with confidence
  │
  ▼
ResearchEvaluator.get_evaluation_report()
  → completeness × quality × consistency
```

## Design Decisions

1. **Keyword-based domain detection** — Deterministic, no LLM dependency for planning phase
2. **DAG-based task execution** — Enables parallel execution while respecting dependencies
3. **Evidence as first-class objects** — Every claim traceable to source with confidence
4. **Automatic conflict resolution** — Confidence-weighted resolution with irreducible flag for manual review
5. **Budget enforcement** — Prevents runaway research with token/time/task limits

## Known Limitations

- In-memory storage only (no persistence across restarts)
- Tool dispatch is keyword-based, not semantic — may misroute ambiguous questions
- Conflict resolution uses simple confidence averaging, not Bayesian reasoning
- No incremental synthesis — runs are atomic
- Parallel execution limited to thread pool (GIL-bound for CPU tasks)
