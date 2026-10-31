# Validation record

Date: 31 October 2026. The record distinguishes executed checks from supplied configurations.

## Executed

- Python 3.12: 40 behavior/integration tests passed. Tests cover ingestion, PDF extraction, upload rejection, authentication, Colab framing configuration, persistence, deletion/index invalidation, telemetry privacy, retrieval, model HTTP adapter contracts, JSON framing, pre-model evidence gating, and fail-closed model output.
- Ruff lint passed.
- Desktop Chromium (1440 × 1100) and mobile viewport (390 × 844): page load, sample ingestion, cited answer, related unsupported-question refusal, upload, deletion. No JavaScript page errors or horizontal overflow. See `reports/browser-check.json` and the screenshots.
- Offline TF-IDF + BM25 development benchmark: see `reports/benchmark.json` and `.md` for measured results.
- Real pretrained `sentence-transformers/all-MiniLM-L6-v2` inference: benchmark executed on CPU, including BM25, learned-vector, and hybrid ablations. See `reports/semantic-benchmark.json` and `.md`.
- All nine code cells of the default notebook were replayed from a fresh local directory, including dependency installation, tests, real MiniLM inference, both benchmark runs, API startup, and export. See `reports/notebook-check.json`. This was not execution inside a hosted Colab runtime; the actual Colab port-proxy display remains an environment-specific check.
- The notebook was also replayed with the optional local-Qwen switch enabled, including real model download/loading, HTTP serving, and a model-assisted question. All nine code cells completed. See `reports/notebook-with-llm-check.json`.
- A Python wheel was built and inspected for required static files, demo data, and the local model adapter.

## Live local LLM check

Real `Qwen/Qwen2.5-1.5B-Instruct` inference was exercised on CPU through the local HTTP adapter. The two-question smoke-test record is in `reports/live-model-smoke.json`. This is not a full LLM quality benchmark.

The first live model check showed a valid but irrelevant quote for an unsupported expense-penalty question. That output is preserved in `reports/llm-before-coverage-gate.json`. The final service applies the same conservative sentence-coverage gate before model calls and to returned quotes; the LLM cannot bypass it. This reduces unsupported answers on the authored cases while preserving the known paraphrase-recall limitation. It is another development-set improvement, not independent validation.

## Scope of measurements

The answerable evidence-substring match rate is 26/28 after the coverage gate; unsupported-question refusal is 8/8. The two false refusals concern the buddy program and equipment ownership. The initial gate-free baseline answered 28/28 but refused only 3/8 unsupported questions; it is retained as `reports/initial_baseline.*`.

These are results on the same 40-question development set used to inspect and improve the gate. They are not an independent benchmark or an unrestricted LLM correctness measure. The initial report predates omission of Markdown headings as well as the coverage gate, so the two snapshots are a development comparison rather than a controlled single-variable experiment. Retrieval was already easy on the four small policies; hybrid does not show a material accuracy advantage here.

## Not established by these checks

- Docker/Compose is configured but was not built: Docker is unavailable in this execution environment.
- The GitHub Actions matrix is supplied, but has not run on GitHub. Local testing used Python 3.12; the configured 3.11 CI leg remains to be observed.
- Public cloud deployment, concurrent load, malicious-PDF containment, multi-tenant access control, and multilingual quality were not tested.
- Source-quote validation and four literal override-pattern cases do not establish factual reliability or general prompt-injection resistance.

Dependency ranges in `pyproject.toml` allow minor updates. `requirements-tested.txt` records the core versions used in the local checks; optional model-library versions appear in `requirements-semantic-tested.txt`.
