"""Reproducible small-corpus benchmark. No model-judged or fabricated metrics."""

import json
import platform
import statistics
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from .config import Settings
from .schemas import Question
from .service import EvidenceService
from .store import Store


def evaluate(output="reports/benchmark.json", settings=None):
    cases = json.loads(files("evidencedesk").joinpath("demo/questions.json").read_text())
    base = settings or Settings()
    with tempfile.TemporaryDirectory() as temp:
        service = EvidenceService(Store(str(Path(temp) / "eval.sqlite3")),
                                  replace(base, database=str(Path(temp) / "eval.sqlite3")))
        service.load_demo()
        retriever = service.retriever()  # Build before measuring warm query latency.
        modes = {}
        for mode in ("bm25", "vector", "hybrid"):
            rows = []
            for case in cases:
                hits = retriever.search(case["question"], top_k=4, mode=mode)
                relevant_ranks = [i for i, h in enumerate(hits, 1) if h.chunk.title == case.get("document")]
                answer = service.ask(Question(question=case["question"], mode=mode))
                expected = case["expected"]
                if expected == "answered":
                    outcome = answer.status == "answered" and any(
                        case["contains"].lower() in c.quote.lower()
                        and c.title == case["document"] for c in answer.citations
                    )
                else:
                    outcome = answer.status == expected
                rows.append({"id": case["id"], "question": case["question"],
                             "expected": expected, "actual": answer.status,
                             "passed": outcome,
                             "document_hit_at_4": bool(relevant_ranks) if expected == "answered" else None,
                             "reciprocal_rank": 1 / relevant_ranks[0] if relevant_ranks else 0,
                             "latency_ms": answer.latency_ms,
                             "answer": answer.answer,
                             "citation_titles": [c.title for c in answer.citations]})
            positive = [r for r in rows if r["expected"] == "answered"]
            negative = [r for r in rows if r["expected"] == "abstained"]
            blocked = [r for r in rows if r["expected"] == "blocked"]
            latency = sorted(r["latency_ms"] for r in rows)
            modes[mode] = {
                "document_hit_rate_at_4": sum(r["document_hit_at_4"] for r in positive) / len(positive),
                "document_mrr_at_4": statistics.mean(r["reciprocal_rank"] for r in positive),
                "answer_evidence_match_rate": sum(r["passed"] for r in positive) / len(positive),
                "unanswerable_refusal_rate": sum(r["passed"] for r in negative) / len(negative),
                "instruction_pattern_block_rate": sum(r["passed"] for r in blocked) / len(blocked),
                "mean_latency_ms": statistics.mean(latency),
                "p95_latency_ms": latency[max(0, int(len(latency) * .95 + .999) - 1)],
                "rows": rows,
            }
        report = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "python": platform.python_version(),
            "versions": {p: version(p) for p in ("evidencedesk", "numpy", "scikit-learn")},
            "backend": retriever.backend, "llm_evaluated": False,
            "cases": len(cases), "answerable": len(positive), "unanswerable": len(negative),
            "instruction_patterns": len(blocked), "top_k": 4,
            "threshold": base.min_similarity, "modes": modes,
            "min_token_coverage": base.min_token_coverage,
            "limitations": ["Small, hand-authored fictional English corpus; not a public benchmark.",
                            "Document-level retrieval labels, not exhaustively annotated chunk relevance.",
                            "Evidence match is a case-insensitive expected-substring check, not semantic answer correctness.",
                            "Warm single-process CPU timings exclude network, model calls, ingestion and index construction.",
                            "No statistical significance or real-world generalization claim.",
                            "Pattern tests do not establish prompt-injection robustness."]}
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    markdown = ["# Measured demo benchmark", "", f"Cases: {len(cases)}. Backend: `{report['backend']}`. LLM evaluated: no.", "",
                "| Retrieval | Doc hit@4 | Doc MRR@4 | Evidence match | Refusal | Pattern block | Warm p95 (ms) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for mode, metrics in modes.items():
        markdown.append(f"| {mode} | {metrics['document_hit_rate_at_4']:.1%} | {metrics['document_mrr_at_4']:.3f} | {metrics['answer_evidence_match_rate']:.1%} | {metrics['unanswerable_refusal_rate']:.1%} | {metrics['instruction_pattern_block_rate']:.1%} | {metrics['p95_latency_ms']:.2f} |")
    markdown.extend(["", "## Interpretation", "", *[f"- {x}" for x in report["limitations"]], "",
                     "The offline vector baseline is character TF-IDF. It is not a learned semantic embedding model.",
                     "Hybrid search is an engineering option; these results do not imply it beats every baseline.",
                     "Inspect per-question failures in the JSON before quoting these results."])
    path.with_suffix(".md").write_text("\n".join(markdown) + "\n")
    return {k: v for k, v in report.items() if k != "modes"} | {
        "modes": {name: {k: v for k, v in m.items() if k != "rows"} for name, m in modes.items()}}
