from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.tools.career_tools import CareerTools

router = APIRouter()


class JobMatchRequest(BaseModel):
    resume_text: str
    jobs: list[dict[str, Any]]


@router.post("/match")
async def match_resume_to_jobs(request: JobMatchRequest) -> dict[str, Any]:
    """Rank available jobs by how closely their requirements overlap with the resume."""
    if not request.resume_text.strip():
        return {"count": 0, "matches": []}

    tool = CareerTools()
    return tool.match_resume_to_jobs(request.resume_text, request.jobs)
