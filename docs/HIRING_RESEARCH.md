# Why this project fits AI engineering applications

Research date: 31 October 2026. This is a targeted sample of current job pages, not a labor-market census or a promise of eligibility. Several sampled roles are senior; the skills are useful signals for a junior portfolio, not a claim that this project supplies their required experience.

| Employer / listing | Skills explicitly requested | Project evidence |
| --- | --- | --- |
| [Ростелеком — MLE](https://job.rt.ru/vacancy/9363) | Python, asynchronous/network applications, LLM/RAG, Docker, CI/CD, FastAPI, SQL | Python API, document retrieval, SQLite, Docker, CI |
| [MeJuvante — LLM / GenAI Engineer](https://mejuvante.ai/de/careers/llm-genai-engineer) | Backend APIs; chunking, embeddings, vector databases, reranking; agents; Docker/Kubernetes; CI/CD; prompt injection and access control | Chunking, optional embeddings, rank fusion, constrained LLM adapter, token auth, tests; no claim of Kubernetes, agents, or external vector database |
| [opta data — AI Engineer](https://jobs.optadata.de/jobportal/optadata/viewAusschreibung/2026-149.html) | LLM applications, RAG, APIs, Python/Java, vector databases, evaluation/monitoring; Docker/CI advantageous | Evidence validation, ablations, traces, API integration, packaging; no LangChain/Java/MCP implementation |
| [alpas — Senior AI Engineer](https://alpas-gmbh.jobs.personio.com/job/2566758) | LangGraph agents, Python/FastAPI, RAG, evaluation, CI/CD, cost and inference efficiency | Evaluation and backend skills; agent orchestration and cloud are outside scope |

The Ростелеком page is client-rendered; the indexed employer-page text supplied the requirements when the rendered HTML exposed only the page shell. Listings can close or change.

## Choice

EvidenceDesk demonstrates a complete document workflow with tests and measurable failure cases. That complements Jaber's medical vision-language research with backend, retrieval, packaging, and quality-engineering evidence. It is intentionally independent of private thesis artifacts and uses no patient data.

The central portfolio signal is being able to explain the decisions and failures. Adding every fashionable framework would not replace that. Future work with a real larger corpus could add Qdrant/pgvector, a cross-encoder reranker, per-tenant access filtering, or an agent only after measuring why it is needed.

## Documentation checked for implementation

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/): TestClient-based API tests.
- [Sentence Transformers encode API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html): normalized embedding encoding.
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility): chat-completions-compatible endpoint.

No salary, placement guarantee, or statistically representative demand percentages are claimed.
