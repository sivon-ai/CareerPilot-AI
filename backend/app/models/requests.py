from __future__ import annotations

from pydantic import BaseModel, Field


class JobMatchRequest(BaseModel):
    resume_document_id: str = Field(..., min_length=1)
    job_document_id: str = Field(..., min_length=1)
