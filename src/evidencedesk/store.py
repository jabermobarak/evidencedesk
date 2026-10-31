"""SQLite source of truth; one short-lived connection per operation."""

import hashlib
import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    pages TEXT NOT NULL, chars INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS traces (
                    id TEXT PRIMARY KEY, query_hash TEXT NOT NULL,
                    status TEXT NOT NULL, latency_ms REAL NOT NULL,
                    citations INTEGER NOT NULL, backend TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def documents(self):
        with self.connect() as db:
            rows = db.execute("SELECT id, title, pages, chars FROM documents ORDER BY id").fetchall()
        return [{"id": r[0], "title": r[1], "pages": json.loads(r[2]), "chars": r[3]} for r in rows]

    def add(self, title, pages, max_documents=100, max_chars=1_000_000):
        content = json.dumps(pages, ensure_ascii=False)
        ident = hashlib.sha256(content.encode()).hexdigest()[:20]
        chars = sum(len(p) for p in pages)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM documents WHERE id=?", (ident,)).fetchone():
                return ident, False
            count, size = db.execute("SELECT COUNT(*), COALESCE(SUM(chars),0) FROM documents").fetchone()
            if count >= max_documents or size + chars > max_chars:
                raise ValueError("Corpus limit reached; delete a document before adding more")
            db.execute("INSERT INTO documents(id,title,pages,chars) VALUES (?,?,?,?)",
                       (ident, title, content, chars))
        return ident, True

    def delete(self, ident):
        with self.connect() as db:
            return db.execute("DELETE FROM documents WHERE id=?", (ident,)).rowcount > 0

    def trace(self, answer, question):
        # Raw questions, model prompts, and API credentials are deliberately not persisted.
        with self.connect() as db:
            db.execute("INSERT INTO traces(id,query_hash,status,latency_ms,citations,backend) VALUES (?,?,?,?,?,?)",
                       (answer.request_id, hashlib.sha256(question.encode()).hexdigest(),
                        answer.status, answer.latency_ms, len(answer.citations),
                        answer.retrieval_backend))
            # Bounded local demo telemetry.
            db.execute("DELETE FROM traces WHERE rowid NOT IN (SELECT rowid FROM traces ORDER BY rowid DESC LIMIT 10000)")

    def metrics(self):
        with self.connect() as db:
            total, latency = db.execute("SELECT COUNT(*), AVG(latency_ms) FROM traces").fetchone()
            statuses = dict(db.execute("SELECT status, COUNT(*) FROM traces GROUP BY status"))
        return {"requests": total, "mean_latency_ms": round(latency or 0, 2), "statuses": statuses}
