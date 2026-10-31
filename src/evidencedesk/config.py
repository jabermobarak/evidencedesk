"""Server-side configuration. No credentials are accepted from document content."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database: str = "data/evidencedesk.sqlite3"
    api_token: str = ""
    allow_colab_embed: bool = False
    embedding_model: str = ""
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = ""
    llm_api_key: str = ""
    min_similarity: float = 0.12
    min_token_coverage: float = 0.55
    max_upload_bytes: int = 2_000_000
    max_document_chars: int = 120_000
    max_corpus_chars: int = 1_000_000
    max_documents: int = 100

    @classmethod
    def from_env(cls):
        return cls(
            database=os.getenv("ED_DATABASE", cls.database),
            api_token=os.getenv("ED_API_TOKEN", ""),
            allow_colab_embed=os.getenv("ED_ALLOW_COLAB_EMBED", "").lower() == "true",
            embedding_model=os.getenv("ED_EMBEDDING_MODEL", ""),
            llm_base_url=os.getenv("ED_LLM_BASE_URL", cls.llm_base_url),
            llm_model=os.getenv("ED_LLM_MODEL", ""),
            llm_api_key=os.getenv("ED_LLM_API_KEY", ""),
            min_similarity=float(os.getenv("ED_MIN_SIMILARITY", "0.12")),
            min_token_coverage=float(os.getenv("ED_MIN_TOKEN_COVERAGE", "0.55")),
        )
