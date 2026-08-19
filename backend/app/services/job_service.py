from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.models.requests import JobMatchRequest
from app.models.responses import JobMatchRecommendation, JobMatchResponse, SkillGapItem
from app.services.rag import query_documents
from app.tools.agent_tools import analyze_job_description, analyze_resume, calculate_job_match, extract_skills, generate_career_recommendations

logger = logging.getLogger(__name__)


def _read_document_text(document_id: str | None) -> str:
    if not document_id:
        raise ValueError("The required document ID is missing.")

    try:
        result = query_documents(document_id, k=5)
    except Exception:
        result = {"results": []}

    chunks = result.get("results", []) if isinstance(result, dict) else []
    parts: list[str] = []
    for item in chunks:
        if not isinstance(item, dict):
            continue
        text = str(item.get("page_content") or "").strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _normalize_document_type(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"resume", "job_description", "job description", "job-desc", "jobdesc"}:
        return "resume" if value == "resume" else "job_description"
    return "other"


def validate_match_request(resume_document_id: str | None, job_document_id: str | None) -> tuple[str, str]:
    if not resume_document_id or not str(resume_document_id).strip():
        raise ValueError("RESUME_NOT_FOUND: Please select a resume.")
    if not job_document_id or not str(job_document_id).strip():
        raise ValueError("JOB_DESCRIPTION_NOT_FOUND: Please select a job description.")
    if str(resume_document_id).strip() == str(job_document_id).strip():
        raise ValueError("INVALID_DOCUMENT_PAIR: The same document cannot be used for both resume and job description.")
    return str(resume_document_id).strip(), str(job_document_id).strip()


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        clean = str(item or "").strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(clean)
    return ordered


def _extract_skill_list(source_text: str) -> list[str]:
    text = source_text or ""
    match_tokens = [
        "Python", "FastAPI", "RAG", "LangChain", "FAISS", "Gemini", "AI Agents", "REST APIs",
        "React", "SQL", "Java", "JavaScript", "TypeScript", "Machine Learning", "Docker", "Kubernetes",
        "Git", "Azure", "PostgreSQL", "MongoDB",
    ]
    found: list[str] = []
    for token in match_tokens:
        if token.lower() in text.lower():
            found.append(token)
    return _dedupe_preserve_order(found)


def evaluate_job_match(request: JobMatchRequest) -> JobMatchResponse:
    resume_id, job_id = validate_match_request(request.resume_document_id, request.job_document_id)

    logger.info("Starting job match analysis for resume=%s job=%s", resume_id, job_id)

    resume_text = _read_document_text(resume_id)
    job_text = _read_document_text(job_id)

    resume_analysis = analyze_resume(query=resume_text or "resume skills experience projects education certifications")
    job_analysis = analyze_job_description(job_document_id=job_id, query=job_text or "job description requirements responsibilities qualifications")

    required_skills = _dedupe_preserve_order(job_analysis.get("required_skills", []) or [])
    preferred_skills = _dedupe_preserve_order(job_analysis.get("preferred_skills", []) or [])
    candidate_skills = _dedupe_preserve_order(resume_analysis.get("skills", []) or [])

    if not required_skills:
        fallback_job_skills = _extract_skill_list(job_text)
        required_skills = _dedupe_preserve_order(fallback_job_skills)

    required_match = calculate_job_match(required_skills, candidate_skills)
    match_percentage = required_match.get("match_percentage")
    matched_skills = required_match.get("matched_skills", [])
    missing_skills = required_match.get("missing_skills", [])

    if required_skills:
        if match_percentage is None:
            match_percentage = 0
    else:
        match_percentage = None

    preferred_match = calculate_job_match(preferred_skills, candidate_skills)
    matched_preferred_skills = preferred_match.get("matched_skills", [])
    missing_preferred_skills = preferred_match.get("missing_skills", [])

    strengths: list[str] = []
    if matched_skills:
        strengths.append(f"Your resume demonstrates relevant experience with: {', '.join(matched_skills[:4])}.")
    if any(skill in candidate_skills for skill in ["Python", "FastAPI", "RAG"]):
        strengths.append("Your background aligns with the role's core AI/backend tooling and workflow requirements.")

    skill_gaps: list[SkillGapItem] = []
    for skill in missing_skills:
        skill_gaps.append(
            SkillGapItem(
                skill=skill,
                importance="required",
                priority="high" if skill in required_skills else "medium",
                reason="This skill is explicitly required by the target role and not clearly demonstrated in the uploaded resume.",
            )
        )
    for skill in missing_preferred_skills:
        skill_gaps.append(
            SkillGapItem(
                skill=skill,
                importance="preferred",
                priority="medium",
                reason="This skill is listed as preferred by the job description and not demonstrated in the uploaded resume.",
            )
        )

    recs = generate_career_recommendations(candidate_skills, missing_skills + missing_preferred_skills, required_skills + preferred_skills)
    recommendations = [
        JobMatchRecommendation(
            skill=str(item.get("skill") or "skill"),
            priority=str(item.get("priority") or "medium"),
            reason=str(item.get("reason") or "Focus on this capability to improve your role fit."),
        )
        for item in recs.get("recommendations", [])
    ]

    sources = [
        {"source": job_id, "document_id": job_id, "page": 1},
        {"source": resume_id, "document_id": resume_id, "page": 1},
    ]

    if not required_skills:
        reason = "Not enough structured skill information to calculate a reliable match."
        return JobMatchResponse(
            match_percentage=None,
            required_skill_count=0,
            matched_required_skill_count=0,
            matched_skills=[],
            missing_skills=[],
            preferred_skills=preferred_skills,
            matched_preferred_skills=matched_preferred_skills,
            missing_preferred_skills=missing_preferred_skills,
            strengths=strengths,
            skill_gaps=skill_gaps,
            recommendations=recommendations,
            sources=sources,
        )

    response = JobMatchResponse(
        match_percentage=match_percentage,
        required_skill_count=len(required_skills),
        matched_required_skill_count=len(matched_skills),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        preferred_skills=preferred_skills,
        matched_preferred_skills=matched_preferred_skills,
        missing_preferred_skills=missing_preferred_skills,
        strengths=strengths,
        skill_gaps=skill_gaps,
        recommendations=recommendations,
        sources=sources,
    )
    logger.info("Completed job match analysis: result=%s", response.model_dump())
    return response
