from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.requests import JobMatchRequest
from app.models.responses import JobMatchResponse
from app.services.job_service import evaluate_job_match

router = APIRouter()


@router.post("/match", response_model=JobMatchResponse)
async def match_jobs(request: JobMatchRequest) -> JobMatchResponse:
    """Analyze a resume and a job description and produce a structured job-fit score."""
    try:
        return evaluate_job_match(request)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("RESUME_NOT_FOUND"):
            raise HTTPException(status_code=400, detail=message) from exc
        if message.startswith("JOB_DESCRIPTION_NOT_FOUND"):
            raise HTTPException(status_code=400, detail=message) from exc
        if message.startswith("INVALID_DOCUMENT_PAIR"):
            raise HTTPException(status_code=400, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"Job analysis failed: {exc}") from exc
