from typing import Literal

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """One knowledge chunk returned by Chroma."""

    content: str
    source: str
    chunk_number: int
    distance: float


class KnowledgeAnswer(BaseModel):
    """Structured final response produced by the decision agent."""

    answer: str
    decision: str
    confidence: Literal["high", "medium", "low"]
    sources: list[str] = Field(default_factory=list)
    needs_clarification: bool = False