from __future__ import annotations

import pytest

from app.tools.agent_tools import calculate_job_match


def test_required_skill_match_uses_deterministic_calculation() -> None:
    result = calculate_job_match(
        ["Python", "FastAPI", "RAG", "LangChain", "FAISS"],
        ["Python", "FastAPI", "RAG", "FAISS"],
    )

    assert result["match_percentage"] == 80
    assert result["matched_skills"] == ["FastAPI", "FAISS", "Python", "RAG"]
    assert result["missing_skills"] == ["LangChain"]


def test_no_required_skills_returns_insufficient_data() -> None:
    result = calculate_job_match([], ["Python", "FastAPI"])

    assert result["match_percentage"] is None
    assert "insufficient" in result["reason"].lower()


def test_duplicate_skill_names_are_normalized() -> None:
    result = calculate_job_match(["Python", "python", "REST API", "REST APIs"], ["python", "rest api"])

    assert result["matched_skills"] == ["Python", "REST APIs"]
    assert result["missing_skills"] == []


def test_preferred_skills_do_not_change_required_match_score() -> None:
    required = ["Python", "FastAPI", "RAG", "LangChain", "FAISS"]
    candidate = ["Python", "FastAPI", "RAG", "FAISS"]

    result = calculate_job_match(required, candidate)

    assert result["match_percentage"] == 80
    assert "LangChain" in result["missing_skills"]


def test_job_match_service_rejects_missing_resume_and_job() -> None:
    from app.services.job_service import validate_match_request

    with pytest.raises(ValueError, match="resume"):
        validate_match_request(None, "job-123")

    with pytest.raises(ValueError, match="job"):
        validate_match_request("resume-123", None)
