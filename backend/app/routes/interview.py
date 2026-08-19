from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.interview_service import InterviewService

router = APIRouter()
service = InterviewService()


class StartInterviewRequest(BaseModel):
    resume_document_id: str = Field(..., min_length=1)
    job_document_id: str = Field(..., min_length=1)
    interview_type: str = "mixed"
    difficulty: str = "medium"
    question_count: int = 10


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1, max_length=5000)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Please enter an answer before submitting.")
        return value.strip()


@router.post("/start")
async def start_interview(request: StartInterviewRequest) -> dict[str, Any]:
    try:
        session = service.start_interview(
            resume_document_id=request.resume_document_id,
            job_document_id=request.job_document_id,
            interview_type=request.interview_type,
            difficulty=request.difficulty,
            question_count=request.question_count,
        )
        return {
            "session_id": session["session_id"],
            "question_number": 1,
            "total_questions": session["question_count"],
            "question": session["current_question"],
            "status": session["status"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"Unable to start the interview: {exc}") from exc


@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, request: SubmitAnswerRequest) -> dict[str, Any]:
    try:
        return service.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            answer=request.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"We couldn't evaluate this answer. Please try again.") from exc


@router.get("/{session_id}/report")
async def get_report(session_id: str) -> dict[str, Any]:
    try:
        return service.get_report(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"Unable to load the interview report: {exc}") from exc
