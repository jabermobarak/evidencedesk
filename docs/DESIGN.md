# Design decisions

## 1. Evidence selection instead of unrestricted generation

The LLM may select exact source quotes, but cannot add accepted free-text claims. Each returned chunk ID must belong to the current retrieval result and each quote must be a substring of that chunk. This makes provenance testable and catches fabricated citations. It gives up fluent synthesis and cannot prove relevance or completeness.

The default no-model path ranks sentences by question-token overlap after retrieval. A similarity threshold gates obviously unrelated text, then a token coverage threshold of 0.55 requires a candidate sentence to contain a majority of the non-stopword question tokens. That path is a transparent classical NLP baseline and sacrifices paraphrase recall. The same candidate gate runs before an optional LLM call, and accepted model quotes must also pass token coverage. The optional LLM may select evidence or abstain, but cannot override this conservative gate. It makes a real network call and fails closed on invalid output.

The model sees short source aliases such as `S1`; these are mapped back to stable chunk IDs before validation. Two small prompt examples demonstrate evidence selection and abstention. The optional Transformers development adapter stops when a complete JSON object is generated and canonicalizes that first object, tolerating a Markdown JSON fence or trailing generation text. The core adapter still validates the object schema, source ID, and exact quotation. Remote providers must supply valid JSON directly. This is output parsing, not grammar-constrained decoding.

## 2. Hybrid retrieval and explicit baselines

BM25 uses term frequency, document frequency and length normalization. The second branch defaults to L2-normalized character TF-IDF vectors, which help with technical identifiers and partial spelling matches without a model download. Sentence Transformers can replace that branch with learned dense vectors.

Reciprocal rank fusion adds `1 / (60 + rank)` from each positive-scoring branch. It avoids treating the unrelated BM25 and cosine scales as directly comparable. A fused score is a ranking value, not confidence. The refusal threshold uses vector similarity, not the fused score. Even BM25-only answer mode retains the same similarity gate so answerability is held constant across retrieval ablations; the raw retrieval metric uses BM25 alone in that mode.

Dense vectors use exact in-memory dot products. At this bounded corpus size, an external vector service adds operations without a demonstrated benefit. Benchmark a larger workload before adding approximate nearest-neighbor search. No learned reranker or agent framework is included.

## 3. Page-aware chunks and storage

PDFs are parsed page by page. Markdown headings are omitted from retrieval passages so they do not get fused into answer sentences. Text is whitespace-normalized before chunking. Each chunk carries a stable document ID, one-based source page, and chunk index. Markdown and TXT are one logical page. Chunk size is 650 characters with 100 characters of overlap; long chunks split near a word boundary. IDs are content-derived, so repeated uploads deduplicate even if renamed. The first stored filename is retained.

SQLite persists original page text and bounded metadata-only traces. The current process caches the retrieval index. Writes take a process lock and invalidate it; an in-flight request may finish against the snapshot it already acquired. One application worker is supported. Multi-process invalidation is a documented extension rather than a hidden assumption.

## 4. Evaluation scope

The sample is four fictional policies with 40 hand-authored questions. `evaluate` rebuilds a fresh temporary corpus for each invocation, uses the same questions for three retrieval modes, and saves per-case outputs, dependency versions, and limitations. The token-coverage gate was added after inspecting the first run on these cases. This is development-set tuning, not an independent held-out test. Both the initial baseline and final results are retained; no held-out generalization claim is made.

Document hit@4 is the fraction of answerable questions whose labeled source document occurs in the first four retrieved chunks. Document MRR@4 gives reciprocal rank to the first chunk from that document. Evidence match requires at least one quote from the labeled document containing the expected substring; it is weaker than full answer correctness. Unsupported questions contribute only to refusal rate; instruction patterns are reported separately. Timing excludes index construction and model calls.

## 5. Security and operational boundary

Documents and questions are untrusted. The frontend renders their strings with `textContent`. SQL uses bound parameters. Uploaded filenames never choose a filesystem path. There are limits on bytes, extracted text, pages, corpus characters, document count, and retained trace rows. These are resource limits for a local demonstration, not a hardened hostile-upload sandbox. Framework multipart handling can spool data before the application-level size check; an exposed server needs ingress limits too.

The LLM receives only the question and selected snippets; the endpoint and credential come from server environment variables. The server does not execute document instructions or expose tools to the model. The regex filter catches a few literal override patterns. Neither this nor exact quoting establishes general prompt-injection resistance. A malicious source can state a false policy without using a suspicious pattern.

Default API binding is loopback. Optional constant-time bearer comparison protects `/api/*`; it is a single-workspace credential, not per-user RBAC. TLS, tenant isolation, encrypted storage, parser sandboxing, rate limits, and shared tracing are future work before a shared deployment.
