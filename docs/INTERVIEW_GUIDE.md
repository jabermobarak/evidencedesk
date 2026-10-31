# Explain and demonstrate the project

## A two-minute demonstration

1. Start the app and load the sample workspace. Explain that the policies are fictional and the default mode needs no API key.
2. Ask “How quickly must a critical incident be acknowledged?” Show the quote, source filename, page, and request trace.
3. Ask “What is the office Wi-Fi password?” Show the refusal. Then inspect the benchmark's harder unsupported cases; explain any false answers honestly.
4. Switch retrieval modes. Open the benchmark table and explain why a small demo cannot establish that hybrid is universally better.
5. Open `/docs` and the test suite. Explain model-output validation, index invalidation after upload/delete, and the optional learned-embedding path.

## Questions you should be able to answer

| Question | What to explain |
| --- | --- |
| Why not just prompt an LLM with the entire file? | Context cost, retrieval control, measurable evidence selection, source provenance; small files may not need retrieval. |
| Is the default model a neural network? | No. BM25 and TF-IDF are classical NLP. Learned embeddings and a real LLM are optional and explicitly identified. |
| What is BM25? | Keyword retrieval with inverse document frequency, term-frequency saturation, and document-length normalization. |
| Why reciprocal rank fusion? | It combines positions rather than incompatible score scales; the constant limits dominance of the first few ranks. |
| What does a citation prove? | The displayed quote exists in a retrieved chunk. It does not prove the source is correct or the quote answers the question. |
| What fails? | Related unsupported questions, vague paraphrases, conflicting source documents, tables and OCR; inspect real failure rows. |
| How do you evaluate it? | Separate document retrieval, expected-evidence matching, unsupported refusal, literal attack-pattern blocking, and latency. |
| How would you scale it? | Measure first; move embeddings to a shared index, add document versioning and access-filtered retrieval, background ingestion, worker limits. |
| Did you train a model? | No. This project integrates retrieval and optional pretrained models. It does not claim training or fine-tuning. |
| Was AI used? | Yes, for implementation assistance. Demonstrate your understanding through code walkthroughs, measurements, and modifications. |

## A practical learning exercise

Add one fictional policy and five questions, run the evaluation, inspect an incorrect result, and propose one measurable fix. This is stronger interview preparation than memorizing library names. Do not claim ownership of decisions you cannot explain yet.

## CV bullet after you reproduce the project

Built an evidence-first document QA application with Python, FastAPI, SQLite, hybrid BM25/vector retrieval, verified source quotations, an optional LLM adapter, Docker packaging, and a reproducible evaluation harness.

Add numeric results only with the metric name, corpus size, and evaluation scope. Do not relabel evidence-substring matching as “LLM accuracy” or warm local timing as production latency.

## Repository and sharing

The source repository is https://github.com/jabermobarak/evidencedesk.
It includes the application, evaluation reports, automated tests, GitHub Actions, Docker configuration, and the self-contained Colab notebook.

To work on a local copy:

```bash
git clone https://github.com/jabermobarak/evidencedesk.git
cd evidencedesk
python -m pip install -e '.[dev]'
python -m evidencedesk.cli demo
python -m evidencedesk.cli serve
```

Before sharing it in job applications, reproduce the demonstration, review the failure cases, and confirm the latest GitHub Actions run passes. Pin the repository on your GitHub profile when you are ready.

Suggested topics: `python`, `rag`, `information-retrieval`, `fastapi`, `llm`, `evaluation`, `docker`, `nlp`.
