import logging
import threading
import time
import uuid
from importlib.resources import files

from .generation import select_extractive, select_llm, suspicious
from .ingestion import chunk_documents, parse_file
from .retrieval import Retriever, tokens
from .schemas import Answer, Citation


class EvidenceService:
    def __init__(self, store, settings):
        self.store = store
        self.settings = settings
        self.lock = threading.RLock()
        self._index = None

    def add_file(self, name, payload):
        if len(payload) > self.settings.max_upload_bytes:
            raise ValueError("File exceeds the 2 MB upload limit")
        title, pages = parse_file(name, payload, self.settings.max_document_chars)
        with self.lock:
            ident, created = self.store.add(title, pages, self.settings.max_documents,
                                            self.settings.max_corpus_chars)
            if created:
                self._index = None
        return {"id": ident, "title": title, "created": created, "pages": len(pages)}

    def load_demo(self):
        source = files("evidencedesk").joinpath("demo")
        return [self.add_file(p.name, p.read_bytes()) for p in sorted(source.iterdir(), key=lambda p: p.name)
                if p.name.endswith(".md")]

    def delete(self, ident):
        with self.lock:
            deleted = self.store.delete(ident)
            if deleted:
                self._index = None
            return deleted

    def retriever(self):
        with self.lock:
            if self._index is None:
                self._index = Retriever(chunk_documents(self.store.documents()),
                                        self.settings.embedding_model)
            return self._index

    def ask(self, request):
        start = time.perf_counter()
        warnings = []
        selected = []
        backend = "not-run"
        generator = "extractive"
        if suspicious(request.question):
            status = "blocked"
            message = "This request contains an instruction-override pattern. Ask a document question."
        else:
            retriever = self.retriever()
            backend = retriever.backend
            hits = retriever.search(request.question, request.top_k, request.mode)
            safe = [h for h in hits if not suspicious(h.chunk.text)
                    and h.similarity >= self.settings.min_similarity]
            if len(safe) < len(hits):
                warnings.append("Some retrieved passages were excluded by relevance or instruction checks.")
            evidence_candidates = select_extractive(request.question, safe, self.settings.min_token_coverage)
            if safe and not evidence_candidates:
                warnings.append("No candidate sentence passed the conservative question-token coverage gate.")
                safe = []
            if safe and request.use_llm:
                if self.settings.llm_model:
                    generator = "llm-verified-quotes"
                    try:
                        selected = select_llm(request.question, safe, self.settings)
                        query_tokens = set(tokens(request.question))
                        selected = [(h, q) for h, q in selected
                                    if len(query_tokens & set(tokens(q))) / max(len(query_tokens), 1)
                                    >= self.settings.min_token_coverage]
                    except Exception as exc:
                        # Invalid JSON, fabricated quotes, unavailable model: fail closed.
                        logging.getLogger(__name__).warning("Model evidence selection rejected (%s)", type(exc).__name__)
                        warnings.append("Model output was unavailable or invalid; no model answer was accepted.")
                else:
                    warnings.append("No LLM is configured; using extractive retrieval demo.")
                    selected = evidence_candidates
            elif safe:
                selected = evidence_candidates
            status = "answered" if selected else "abstained"
            message = "\n\n".join(f"{quote} [{i}]" for i, (_, quote) in enumerate(selected, 1))
            if not selected:
                message = "I could not find sufficient evidence in the indexed documents."
        citations = [Citation(chunk_id=h.chunk.id, document_id=h.chunk.document_id,
                              title=h.chunk.title, page=h.chunk.page, quote=q,
                              score=round(h.score, 6)) for h, q in selected]
        answer = Answer(request_id=uuid.uuid4().hex, status=status, answer=message,
                        citations=citations, retrieval_backend=backend,
                        generation_backend=generator,
                        latency_ms=round((time.perf_counter() - start) * 1000, 2), warnings=warnings)
        self.store.trace(answer, request.question)
        return answer
