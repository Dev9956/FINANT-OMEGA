# FININT OMEGA — Research Foundation

## Purpose

This directory contains research notes, literature reviews, and design decisions grounded in academic and industry research.

## Structure

```
docs/research/
├── README.md
├── literature/          # Paper summaries and implementation lessons
├── systems/             # Analysis of existing financial platforms
├── datasets/            # Benchmark data and licensing
└── decisions/           # Research-to-architecture mappings
```

## Key Research Areas

1. **Finance LLMs** — BloombergGPT, FinBen, Financial LLM Survey
2. **Financial QA** — FinQA, DocFinQA, FinTextQA (numerical reasoning)
3. **Sentiment & NLP** — FinBERT, domain-specific NLP
4. **RAG Architecture** — Hybrid retrieval, reranking, citation
5. **Quantitative Finance** — Factor models, risk, backtesting
6. **Evaluation** — FinResearchBench, evidence verification

## Implementation Pattern

Every major feature follows:

```
Research → Design Decision → ADR → Implementation → Test → Benchmark
```

## Key Papers

| Paper | Focus | Implementation Lesson |
|-------|-------|-----------------------|
| BloombergGPT | Finance LLMs | Use strong models + RAG + tools, not training |
| FinQA | Numerical reasoning | LLM cannot be trusted for arithmetic |
| DocFinQA | Long documents | Parse → structure → retrieve → rerank |
| FinTextQA | Long-form QA | Embedding + keyword + metadata retrieval |
| FinBen | Broad benchmark | Create FinResearchBench |
| FinLLM Survey | Landscape | Include guardrails, evaluation, privacy |
| FinBERT | Sentiment | Domain NLP models, not sole decision driver |
