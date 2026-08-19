from __future__ import annotations

import re
from typing import Any

from app.config import TOP_K
from app.services.rag import query_documents

_STOP_WORDS = {
    "the", "and", "for", "with", "into", "from", "your", "you", "our", "that", "this",
    "role", "skills", "experience", "project", "projects", "work", "using", "across",
    "about", "over", "through", "within", "team", "teams", "will", "can", "should",
    "resume", "job", "candidate", "description", "requirements", "preferred",
}


def _normalize_skill_name(skill: str) -> str:
    """Normalize skill names into a stable, de-duplicated form."""
    raw = (skill or "").strip()
    if not raw:
        return ""
    normalized = re.sub(r"[^a-zA-Z0-9+/.-]+", " ", raw)
    tokens = [part for part in normalized.split() if part]
    if not tokens:
        return ""
    canon = " ".join(tokens)
    mapping = {
        "rest api": "REST APIs",
        "rest apis": "REST APIs",
        "restful api": "REST APIs",
        "restful apis": "REST APIs",
        "python3": "Python",
        "pythons": "Python",
        "langchain": "LangChain",
        "faiss": "FAISS",
        "gemini": "Gemini",
        "rag": "RAG",
        "ai agents": "AI Agents",
        "ai agent": "AI Agents",
        "fast api": "FastAPI",
        "fastapi": "FastAPI",
        "react js": "React",
        "reactjs": "React",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "sql": "SQL",
    }
    lowered = canon.lower()
    return mapping.get(lowered, canon.title() if canon and not any(c.isupper() for c in canon) else canon)


_SKILL_PRIORITY = {
    "FastAPI": 0,
    "FAISS": 1,
    "Python": 2,
    "RAG": 3,
    "LangChain": 4,
    "Gemini": 5,
    "AI Agents": 6,
    "React": 7,
    "SQL": 8,
    "Java": 9,
    "JavaScript": 10,
    "TypeScript": 11,
    "Machine Learning": 12,
    "REST APIs": 13,
    "PostgreSQL": 14,
    "MongoDB": 15,
    "Docker": 16,
    "Kubernetes": 17,
    "Git": 18,
    "Azure": 19,
}


def _skill_sort_key(skill: str) -> tuple[int, str]:
    normalized = _normalize_skill_name(skill)
    priority = _SKILL_PRIORITY.get(normalized, 1000)
    return (priority, normalized.lower())


def _dedupe_skills(skills: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for skill in skills:
        cleaned = _normalize_skill_name(skill)
        if not cleaned:
            continue
        if cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        ordered.append(cleaned)
    return sorted(ordered, key=_skill_sort_key)


def _extract_text_from_results(results: list[dict[str, Any]]) -> list[str]:
    texts: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("page_content") or "").strip()
        if text:
            texts.append(text)
    return texts


def _parse_resume_fields(texts: list[str]) -> dict[str, Any]:
    combined = "\n\n".join(texts)
    skills = _dedupe_skills(re.findall(r"\b[A-Za-z][A-Za-z0-9+/.-]*(?:\s+[A-Za-z][A-Za-z0-9+/.-]*){0,3}\b", combined))
    technical_keywords = [
        "Python", "FastAPI", "React", "SQL", "Java", "JavaScript", "TypeScript", "RAG",
        "LangChain", "FAISS", "Gemini", "AI Agents", "Machine Learning", "REST APIs",
        "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "Git", "Azure",
    ]
    skills = [skill for skill in skills if any(keyword.lower() in skill.lower() for keyword in technical_keywords)]
    if not skills:
        skills = _dedupe_skills(re.findall(r"\b(?:Python|FastAPI|React|SQL|Java|JavaScript|TypeScript|RAG|LangChain|FAISS|Gemini|AI Agents|Machine Learning|REST APIs|Docker|Kubernetes|Git|Azure)\b", combined))

    projects = re.findall(r"(?:Project|Built|Developed|Created|Led)\s+[:\-]?\s*([A-Za-z0-9][^\n]{2,120})", combined)
    education = re.findall(r"(?:Bachelor|Master|B\.Sc|M\.Sc|MBA|Degree|University|College)\s+[A-Za-z0-9, .-]{3,120}", combined)
    experience = re.findall(r"(?:Experience|Worked|Engineer|Analyst|Developer|Intern|Manager|Lead)\s+[A-Za-z0-9, .-]{3,120}", combined)
    certs = re.findall(r"(?:Certified|Certification|AWS|Azure|Google|PMP|Scrum)[A-Za-z0-9, .-]{3,120}", combined)
    return {
        "skills": _dedupe_skills(skills),
        "projects": [project.strip() for project in projects[:10] if project.strip()],
        "education": [item.strip() for item in education[:10] if item.strip()],
        "experience": [item.strip() for item in experience[:10] if item.strip()],
        "certifications": [item.strip() for item in certs[:10] if item.strip()],
    }


def search_documents(query: str, k: int = TOP_K) -> dict[str, Any]:
    """Search uploaded career documents to answer document-dependent questions. Use this when the answer depends on a resume, job description, or uploaded content."""
    if not query or not str(query).strip():
        raise ValueError("A search query is required.")

    response = query_documents(str(query).strip(), k=k)
    results = response.get("results", []) if isinstance(response, dict) else []
    normalized: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        metadata = result.get("metadata", {}) or {}
        text = str(result.get("page_content") or "").strip()
        if not text:
            continue
        normalized.append(
            {
                "document_id": metadata.get("document_id") or "unknown",
                "source": metadata.get("source") or "unknown",
                "page": metadata.get("page"),
                "text": text,
                "score": float(metadata.get("score", 0.0) or 0.0),
            }
        )
    return {"results": normalized[:k]}


def analyze_resume(query: str = "resume skills experience projects education certifications") -> dict[str, Any]:
    """Analyze the candidate's uploaded resume content using the existing retrieval system. Use this when the user asks about resume experience or skills."""
    response = search_documents(query)
    results = response.get("results", [])
    if not results:
        return {"error": "No resume document found."}

    extracted = _parse_resume_fields(_extract_text_from_results(results))
    return extracted


def analyze_job_description(job_document_id: str | None = None, query: str | None = None) -> dict[str, Any]:
    """Analyze uploaded job-description content for required skills, responsibilities, and qualifications. Use this when the user asks to compare qualifications or fit against a role."""
    search_query = str(query or job_document_id or "job description requirements responsibilities qualifications").strip()
    response = search_documents(search_query)
    results = response.get("results", [])
    if not results:
        return {
            "job_title": "Not specified",
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "qualifications": [],
        }

    text_blob = "\n\n".join(_extract_text_from_results(results))
    required_skills = _dedupe_skills(re.findall(r"(?:required|must have|need|experience with|skills|technologies)[:\-]?\s*([A-Za-z0-9, /&.-]+)", text_blob, flags=re.IGNORECASE))
    if not required_skills:
        required_skills = _dedupe_skills(re.findall(r"\b(?:Python|FastAPI|RAG|LangChain|FAISS|Gemini|SQL|React|Java|JavaScript|TypeScript|Machine Learning|REST APIs|Docker|Kubernetes|Git|Azure|AI Agents)\b", text_blob, flags=re.IGNORECASE))

    responsibilities = re.findall(r"(?:Responsibilities|What you'll do|You will|Own|Build|Develop|Design|Support)[:\-]?\s*([A-Za-z0-9, /&.-]{3,220})", text_blob, flags=re.IGNORECASE)
    qualifications = re.findall(r"(?:Qualifications|Requirements|Preferred|Nice to have)[:\-]?\s*([A-Za-z0-9, /&.-]{3,220})", text_blob, flags=re.IGNORECASE)

    return {
        "job_title": re.search(r"(?:Job Title|Role|Position)[:\-]?\s*([A-Za-z0-9 /&.-]{3,120})", text_blob, flags=re.IGNORECASE)
        .group(1).strip() if re.search(r"(?:Job Title|Role|Position)[:\-]?\s*([A-Za-z0-9 /&.-]{3,120})", text_blob, flags=re.IGNORECASE)
        else "Not specified",
        "required_skills": _dedupe_skills(required_skills)[:20],
        "preferred_skills": _dedupe_skills(re.findall(r"\b(?:Python|FastAPI|RAG|LangChain|FAISS|Gemini|SQL|React|Java|JavaScript|TypeScript|Machine Learning|REST APIs|Docker|Kubernetes|Git|Azure|AI Agents)\b", text_blob, flags=re.IGNORECASE))[:20],
        "responsibilities": [item.strip() for item in responsibilities[:10] if item.strip()],
        "qualifications": [item.strip() for item in qualifications[:10] if item.strip()],
    }


def extract_skills(text: str) -> dict[str, list[str]]:
    """Extract normalized technical skills from candidate or job text without inventing additional experience. Use for resume and JD parsing."""
    if not text or not str(text).strip():
        raise ValueError("Skill extraction requires non-empty text.")

    keywords = [
        "Python", "FastAPI", "React", "SQL", "Java", "JavaScript", "TypeScript", "RAG",
        "LangChain", "FAISS", "Gemini", "AI Agents", "Machine Learning", "REST APIs",
        "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "Git", "Azure", "AI/ML",
    ]
    found = []
    for keyword in keywords:
        if keyword.lower() in text.lower():
            found.append(keyword)
    return {"skills": _dedupe_skills(found)}


def calculate_job_match(required_skills: list[str], candidate_skills: list[str]) -> dict[str, Any]:
    """Deterministically compare candidate skills to required skills. Use this when the user asks for role fit, missing skills, or match percentage."""
    normalized_required = _dedupe_skills([_normalize_skill_name(skill) for skill in required_skills])
    normalized_candidate = _dedupe_skills([_normalize_skill_name(skill) for skill in candidate_skills])
    candidate_map = {skill.lower(): skill for skill in normalized_candidate if skill}

    if not normalized_required:
        return {
            "match_percentage": None,
            "matched_skills": [],
            "missing_skills": [],
            "reason": "Insufficient structured skill information to calculate a reliable match.",
        }

    matched = [skill for skill in normalized_required if skill.lower() in candidate_map]
    missing = [skill for skill in normalized_required if skill.lower() not in candidate_map]
    matched = sorted(matched, key=_skill_sort_key)
    missing = sorted(missing, key=_skill_sort_key)
    score = round((len(matched) / len(normalized_required)) * 100, 0)
    return {
        "match_percentage": int(score),
        "matched_skills": matched,
        "missing_skills": missing,
        "reason": "Deterministic required-skill calculation completed.",
    }


def generate_interview_questions(
    job_requirements: list[str],
    candidate_skills: list[str],
    missing_skills: list[str],
    difficulty: str = "medium",
    question_count: int = 5,
) -> dict[str, Any]:
    """Generate interview questions grounded in the actual required skills and identified knowledge gaps. Use this when the user requests tailored practice questions."""
    normalized_requirements = _dedupe_skills(job_requirements)
    normalized_skills = _dedupe_skills(candidate_skills)
    normalized_missing = _dedupe_skills(missing_skills)
    questions: list[dict[str, Any]] = []

    for index, skill in enumerate((normalized_missing or normalized_requirements)[: max(1, question_count)]):
        skill_name = skill if skill else "role fundamentals"
        category = skill_name
        question_text = (
            f"Describe a project where you used {skill_name} in practice and explain the trade-offs you considered."
            if skill_name not in {"Python", "FastAPI", "RAG", "FAISS", "LangChain"}
            else f"Walk through how you would use {skill_name} to solve a real-world product or workflow problem."
        )
        questions.append(
            {
                "question": question_text,
                "category": category,
                "difficulty": difficulty,
                "reason": f"The role emphasizes {skill_name} and it is relevant to current gaps in the candidate profile.",
            }
        )

    if len(questions) < question_count:
        for _, requirement in enumerate(normalized_requirements[: max(1, question_count - len(questions))]):
            if any(question["category"].lower() == requirement.lower() for question in questions):
                continue
            questions.append(
                {
                    "question": f"How would you apply {requirement} to a real problem within this role?",
                    "category": requirement,
                    "difficulty": difficulty,
                    "reason": f"The role specifically requires {requirement}.",
                }
            )

    return {"questions": questions[:question_count]}


def generate_career_recommendations(
    candidate_skills: list[str],
    missing_skills: list[str],
    job_requirements: list[str],
) -> dict[str, Any]:
    """Recommend the highest-priority skills to close the gap for the target role. Use this for role-fit coaching and skill-development planning."""
    ordered_missing = _dedupe_skills(missing_skills or job_requirements)
    recommendations: list[dict[str, Any]] = []
    for index, skill in enumerate(ordered_missing[:10]):
        priority = "high" if index < 3 else "medium"
        recommendations.append(
            {
                "skill": skill,
                "priority": priority,
                "reason": f"This skill is relevant to the target role and currently missing from the candidate profile.",
            }
        )
    return {"recommendations": recommendations}


CAREER_TOOLS = [
    search_documents,
    analyze_resume,
    analyze_job_description,
    extract_skills,
    calculate_job_match,
    generate_interview_questions,
    generate_career_recommendations,
]
