from __future__ import annotations

import pytest

from app.services.interview_service import InterviewService, normalize_score


@pytest.fixture
def interview_service() -> InterviewService:
    return InterviewService()


def test_start_interview_with_valid_documents(interview_service: InterviewService) -> None:
    session = interview_service.start_interview(
        resume_document_id="resume-1",
        job_document_id="job-1",
        interview_type="mixed",
        difficulty="medium",
        question_count=5,
        resume_context="Built a FastAPI + FAISS RAG application for document search.",
        job_context="Role requires RAG, LLM APIs, vector databases, prompt engineering.",
        skill_gaps=["RAG", "LLM APIs", "Prompt Engineering"],
    )

    assert session["session_id"]
    assert session["status"] == "started"
    assert session["question_count"] == 5
    assert session["current_question"]["text"]


def test_missing_resume_is_rejected(interview_service: InterviewService) -> None:
    with pytest.raises(ValueError, match="resume"):
        interview_service.start_interview(
            resume_document_id="",
            job_document_id="job-1",
            interview_type="mixed",
            difficulty="medium",
            question_count=5,
        )


def test_submit_answer_generates_structured_evaluation(interview_service: InterviewService) -> None:
    session = interview_service.start_interview(
        resume_document_id="resume-1",
        job_document_id="job-1",
        interview_type="mixed",
        difficulty="medium",
        question_count=2,
        resume_context="Built a FastAPI + FAISS RAG application for document search.",
        job_context="Role requires RAG, LLM APIs, vector databases, prompt engineering.",
        skill_gaps=["RAG", "LLM APIs"],
    )

    question = session["current_question"]
    result = interview_service.submit_answer(
        session_id=session["session_id"],
        question_id=question["id"],
        answer="I built a retrieval pipeline using FastAPI plus FAISS. We chunked documents, embedded them, and retrieved the most relevant chunks to ground generation.",
    )

    assert result["evaluation"]["overall_score"] >= 0
    assert result["evaluation"]["overall_score"] <= 10
    assert result["evaluation"]["strengths"]
    assert result["next_question"] is not None


def test_no_duplicate_questions_are_generated(interview_service: InterviewService) -> None:
    questions = interview_service.generate_questions(
        resume_context="Built a FastAPI + FAISS RAG app",
        job_context="Role requires RAG and vector search.",
        skill_gaps=["RAG", "FAISS"],
        interview_type="mixed",
        difficulty="medium",
        question_count=5,
        previous_questions=[],
    )

    texts = [question["text"] for question in questions]
    assert len(set(texts)) == len(texts)


def test_final_report_aggregates_answer_scores(interview_service: InterviewService) -> None:
    session = interview_service.start_interview(
        resume_document_id="resume-1",
        job_document_id="job-1",
        interview_type="mixed",
        difficulty="medium",
        question_count=4,
        resume_context="Built a FastAPI + FAISS RAG application.",
        job_context="Role requires RAG, LLM APIs, vector databases.",
        skill_gaps=["RAG", "LLM APIs"],
    )

    for idx in range(4):
        question = interview_service.get_current_question(session["session_id"])
        score = 8.0 if idx % 2 == 0 else 9.0
        interview_service.submit_answer(
            session_id=session["session_id"],
            question_id=question["id"],
            answer="This answer covers the relevant concepts.",
            override_score=score,
        )

    report = interview_service.get_report(session["session_id"])
    assert report["overall_score"] == 85
    assert report["questions_answered"] == 4
    assert report["category_scores"]


def test_normalize_score_clamps_invalid_values() -> None:
    assert normalize_score(12) == 10
    assert normalize_score(-5) == 0
    assert normalize_score(8.2) == 8.2
