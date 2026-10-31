"""BM25 + TF-IDF (offline) or learned embeddings, fused with reciprocal ranks."""

import math
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from .ingestion import Chunk


def tokens(text):
    return [t for t in re.findall(r"[^\W_]+", text.lower()) if t not in ENGLISH_STOP_WORDS]


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float  # Ranking score, never presented as a probability.
    similarity: float


class Retriever:
    def __init__(self, chunks, embedding_model="", encoder=None):
        self.chunks = chunks
        self.backend = "bm25+tfidf"
        self.encoder = encoder
        self.vectorizer = None
        self.matrix = None
        self.counts = [Counter(tokens(c.text)) for c in chunks]
        self.lengths = np.array([sum(c.values()) for c in self.counts], dtype=float)
        self.avg_length = float(self.lengths.mean()) if len(chunks) else 1.0
        self.df = Counter(t for c in self.counts for t in c)
        if not chunks:
            return
        texts = [c.text for c in chunks]
        if embedding_model and encoder is None:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(embedding_model, trust_remote_code=False)
        if self.encoder is not None:
            self.matrix = np.asarray(self.encoder.encode(texts, normalize_embeddings=True))
            self.backend = "bm25+sentence-transformer"
        else:
            # Character features keep short technical identifiers and non-English text searchable.
            self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=30000)
            try:
                self.matrix = self.vectorizer.fit_transform(texts)
            except ValueError:
                self.vectorizer = None

    def _scores(self, question):
        n = len(self.chunks)
        bm25 = np.zeros(n)
        for term in set(tokens(question)):
            idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
            for i, count in enumerate(self.counts):
                tf = count[term]
                denom = tf + 1.5 * (0.25 + 0.75 * self.lengths[i] / max(self.avg_length, 1))
                bm25[i] += idf * tf * 2.5 / denom
        vector = np.zeros(n)
        if self.encoder is not None:
            q = np.asarray(self.encoder.encode([question], normalize_embeddings=True))[0]
            vector = np.asarray(self.matrix @ q).ravel()
        elif self.vectorizer is not None:
            q = self.vectorizer.transform([question])
            vector = (self.matrix @ q.T).toarray().ravel()
        return bm25, vector

    def search(self, question, top_k=4, mode="hybrid"):
        if mode not in {"hybrid", "bm25", "vector"}:
            raise ValueError("Unknown retrieval mode")
        if not self.chunks:
            return []
        bm25, vector = self._scores(question)
        if mode == "bm25":
            scores = bm25
        elif mode == "vector":
            scores = vector
        else:
            scores = np.zeros(len(self.chunks))
            for values in (bm25, vector):
                order = np.argsort(-values, kind="stable")
                for rank, idx in enumerate(order, 1):
                    if values[idx] > 0:
                        scores[idx] += 1 / (60 + rank)
        order = np.argsort(-scores, kind="stable")
        return [Hit(self.chunks[i], float(scores[i]), float(vector[i]))
                for i in order[:top_k] if scores[i] > 0]
