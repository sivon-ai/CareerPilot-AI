from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunks: int
    status: str = "indexed"
    document_type: str = "other"


class StoredDocumentResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunks: int
    saved_path: str
    document_type: str = "other"


class SkillGapItem(BaseModel):
    skill: str
    importance: str = "preferred"
    priority: str = "medium"
    reason: str


class JobMatchRecommendation(BaseModel):
    skill: str
    priority: str = "medium"
    reason: str


class JobMatchResponse(BaseModel):
    match_percentage: int | None = None
    required_skill_count: int = 0
    matched_required_skill_count: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    skill_gaps: list[SkillGapItem] = Field(default_factory=list)
    recommendations: list[JobMatchRecommendation] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
