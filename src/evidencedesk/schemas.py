from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=1500)
    top_k: int = Field(default=4, ge=1, le=10)
    mode: Literal["hybrid", "bm25", "vector"] = "hybrid"
    use_llm: bool = False

    @field_validator("question")
    @classmethod
    def strip_question(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter a question of at least 3 characters")
        return value


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    page: int
    quote: str
    score: float


class Answer(BaseModel):
    request_id: str
    status: Literal["answered", "abstained", "blocked"]
    answer: str
    citations: list[Citation]
    retrieval_backend: str
    generation_backend: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
