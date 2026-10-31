# Measured demo benchmark

Cases: 40. Backend: `bm25+sentence-transformer`. LLM evaluated: no.

| Retrieval | Doc hit@4 | Doc MRR@4 | Evidence match | Refusal | Pattern block | Warm p95 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 100.0% | 1.000 | 92.9% | 100.0% | 100.0% | 21.88 |
| vector | 100.0% | 0.982 | 92.9% | 100.0% | 100.0% | 12.69 |
| hybrid | 100.0% | 1.000 | 92.9% | 100.0% | 100.0% | 20.98 |

## Interpretation

- Small, hand-authored fictional English corpus; not a public benchmark.
- Document-level retrieval labels, not exhaustively annotated chunk relevance.
- Evidence match is a case-insensitive expected-substring check, not semantic answer correctness.
- Warm single-process CPU timings exclude network, model calls, ingestion and index construction.
- No statistical significance or real-world generalization claim.
- Pattern tests do not establish prompt-injection robustness.

The offline vector baseline is character TF-IDF. It is not a learned semantic embedding model.
Hybrid search is an engineering option; these results do not imply it beats every baseline.
Inspect per-question failures in the JSON before quoting these results.
