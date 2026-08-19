from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    id: str
    text: str
    category: str = "Mixed"
    difficulty: str = "medium"
    skill: str | None = None
    source: str | None = None
    question_type: str = "conceptual"
    source_type: str = "general"

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class InterviewEvaluation(BaseModel):
    overall_score: float = 0.0
    correctness: float = 0.0
    relevance: float = 0.0
    depth: float = 0.0
    clarity: float = 0.0
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class InterviewSessionState(BaseModel):
    session_id: str
    resume_document_id: str
    job_document_id: str
    interview_type: str = "mixed"
    difficulty: str = "medium"
    question_count: int = 10
    current_question: InterviewQuestion | None = None
    questions: list[InterviewQuestion] = Field(default_factory=list)
    answers: list[dict[str, Any]] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    started_at: str
    completed_at: str | None = None
    status: str = "started"
