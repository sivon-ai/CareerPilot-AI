from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.models.interview import InterviewEvaluation, InterviewQuestion, InterviewSessionState

logger = logging.getLogger(__name__)


def normalize_score(value: float | int | None, *, minimum: float = 0.0, maximum: float = 10.0) -> float:
    """Clamp a score to the valid interview range while preserving numeric fidelity."""
    if value is None:
        return minimum
    numeric = float(value)
    if numeric < minimum:
        return minimum
    if numeric > maximum:
        return maximum
    return numeric


class InterviewService:
    """Manage interview sessions, question generation, answer evaluation, and final reports."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_question(
        self,
        *,
        index: int,
        question_text: str,
        interview_type: str,
        difficulty: str,
        skill: str | None = None,
        source: str | None = None,
        source_type: str = "general",
        question_type: str = "conceptual",
    ) -> InterviewQuestion:
        category_label = "Mixed" if interview_type.lower() == "mixed" else interview_type.replace("_", " ").title()
        return InterviewQuestion(
            id=f"q{index + 1}",
            text=question_text,
            category=category_label,
            difficulty=difficulty,
            skill=skill,
            source=source,
            question_type=question_type,
            source_type=source_type,
        )

    def start_interview(
        self,
        *,
        resume_document_id: str,
        job_document_id: str,
        interview_type: str,
        difficulty: str,
        question_count: int,
        resume_context: str | None = None,
        job_context: str | None = None,
        skill_gaps: list[str] | None = None,
    ) -> dict[str, Any]:
        if not resume_document_id or not str(resume_document_id).strip():
            raise ValueError("No resume selected.")
        if not job_document_id or not str(job_document_id).strip():
            raise ValueError("No job description selected.")

        normalized_type = (interview_type or "mixed").strip().lower() or "mixed"
        normalized_difficulty = (difficulty or "medium").strip().lower() or "medium"
        count = max(1, int(question_count or 10))

        session_id = str(uuid.uuid4())
        question = self.generate_questions(
            resume_context=resume_context or "",
            job_context=job_context or "",
            skill_gaps=skill_gaps or [],
            interview_type=normalized_type,
            difficulty=normalized_difficulty,
            question_count=1,
            previous_questions=[],
        )[0]

        session = {
            "session_id": session_id,
            "resume_document_id": str(resume_document_id).strip(),
            "job_document_id": str(job_document_id).strip(),
            "interview_type": normalized_type,
            "difficulty": normalized_difficulty,
            "question_count": count,
            "current_question": question.model_dump(),
            "questions": [question.model_dump()],
            "answers": [],
            "evaluations": [],
            "scores": [],
            "started_at": self._timestamp(),
            "completed_at": None,
            "status": "started",
            "history": [],
        }
        self.sessions[session_id] = session
        return session

    def generate_questions(
        self,
        *,
        resume_context: str,
        job_context: str,
        skill_gaps: list[str],
        interview_type: str,
        difficulty: str,
        question_count: int,
        previous_questions: list[str],
    ) -> list[InterviewQuestion]:
        preferred_skills = skill_gaps or ["RAG", "AI Agents", "FastAPI", "SQL"]
        base_questions = [
            ("Explain how your RAG pipeline retrieves the most relevant document chunks and why you selected FAISS.", "AI/GenAI", "RAG", "resume", "project-based"),
            ("Walk through the architecture of the FastAPI backend in your project and the trade-offs you considered.", "Technical", "FastAPI", "resume", "project-based"),
            ("How would you diagnose a retrieval system that returns semantically similar but irrelevant chunks?", "AI/GenAI", "RAG", "skill_gap", "scenario-based"),
            ("Tell me about a technical challenge you solved in a team project and how you measured success.", "Behavioral", "Problem solving", "resume", "behavioral"),
            ("What are the trade-offs between keyword search and embedding-based retrieval for a production search system?", "AI/GenAI", "RAG", "job_description", "conceptual"),
            ("Describe how you would explain a complex AI feature to a non-technical stakeholder without losing technical accuracy.", "Behavioral", "Communication", "resume", "behavioral"),
        ]

        available = []
        for question_text, category, skill, source_type, question_type in base_questions:
            if question_text in previous_questions:
                continue
            if interview_type == "technical" and category not in {"Technical", "AI/GenAI"}:
                continue
            if interview_type == "ai_genai" and category not in {"AI/GenAI", "Technical"}:
                continue
            if interview_type == "behavioral" and category not in {"Behavioral"}:
                continue
            if interview_type == "resume_based" and source_type != "resume":
                continue
            if interview_type == "mixed":
                available.append((question_text, category, skill, source_type, question_type))
            else:
                available.append((question_text, category, skill, source_type, question_type))

        if not available:
            available = [
                ("How would you describe a system that combines retrieval and generation in a production workflow?", "AI/GenAI", "RAG", "job_description", "conceptual"),
                ("What project or work example best demonstrates your technical depth?", "Resume-based", "Project delivery", "resume", "resume-based"),
            ]

        dedupe = set()
        generated: list[InterviewQuestion] = []
        for index, (question_text, category, skill, source_type, question_type) in enumerate(available):
            normalized_text = question_text.strip()
            if normalized_text in dedupe:
                continue
            dedupe.add(normalized_text)
            generated.append(
                self._build_question(
                    index=index,
                    question_text=normalized_text,
                    interview_type=interview_type,
                    difficulty=difficulty,
                    skill=skill or (preferred_skills[0] if preferred_skills else None),
                    source=source_type,
                    source_type=source_type,
                    question_type=question_type,
                )
            )
            if len(generated) >= max(1, int(question_count or 1)):
                break

        if len(generated) < max(1, int(question_count or 1)):
            for offset in range(1, 20):
                fallback_text = f"Explain how you would apply {preferred_skills[(offset - 1) % len(preferred_skills)]} in a realistic production scenario."
                if fallback_text in dedupe:
                    continue
                dedupe.add(fallback_text)
                generated.append(
                    self._build_question(
                        index=len(generated),
                        question_text=fallback_text,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        skill=preferred_skills[(offset - 1) % len(preferred_skills)],
                        source="skill_gap",
                        source_type="skill_gap",
                        question_type="scenario-based",
                    )
                )
                if len(generated) >= max(1, int(question_count or 1)):
                    break

        return generated

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("This interview session is no longer available.")
        return session

    def get_current_question(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session["status"] == "completed":
            return {"id": None, "text": "Interview complete", "category": session["interview_type"], "difficulty": session["difficulty"]}
        return session["current_question"]

    def submit_answer(
        self,
        *,
        session_id: str,
        question_id: str,
        answer: str,
        override_score: float | None = None,
    ) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not answer or not str(answer).strip():
            raise ValueError("Please enter an answer before submitting.")

        if len(answer) > 5000:
            raise ValueError("Your answer is too long. Please keep it under 5,000 characters.")

        question = session["current_question"]
        question_id_current = str(question.get("id") if isinstance(question, dict) else question.id)
        if str(question_id).strip() != str(question_id_current).strip():
            raise ValueError("This question is no longer active for this interview.")

        if any(existing.get("question_id") == str(question_id) for existing in session["answers"]):
            raise ValueError("This answer has already been submitted for this question.")

        candidate_answer = str(answer).strip()
        evaluation = self._evaluate_answer(session, question, candidate_answer, override_score)
        session["answers"].append({
            "question_id": str(question_id),
            "answer": candidate_answer,
            "timestamp": self._timestamp(),
        })
        session["evaluations"].append({
            "question_id": str(question_id),
            "evaluation": evaluation,
            "timestamp": self._timestamp(),
        })
        session["scores"].append(float(evaluation["overall_score"]))

        total_questions = int(session["question_count"])
        answered = len(session["answers"])

        if answered >= total_questions:
            session["status"] = "completed"
            session["completed_at"] = self._timestamp()
            session["current_question"] = None
            next_question = None
            completed = True
        else:
            next_question = self._generate_next_question(session, question)
            session["current_question"] = next_question.model_dump()
            session["questions"].append(next_question.model_dump())
            completed = False

        return {
            "evaluation": evaluation,
            "next_question": next_question.model_dump() if next_question else None,
            "completed": completed,
            "question_number": min(answered + 1, total_questions),
            "total_questions": total_questions,
        }

    def _generate_next_question(self, session: dict[str, Any], last_question: dict[str, Any]) -> InterviewQuestion | None:
        previous_texts = [item.get("text") for item in session["questions"] if isinstance(item, dict)]
        if len(previous_texts) >= int(session["question_count"]):
            return None
        candidate = self.generate_questions(
            resume_context="",
            job_context="",
            skill_gaps=["RAG", "FAISS", "FastAPI", "LLM APIs"],
            interview_type=session["interview_type"],
            difficulty=session["difficulty"],
            question_count=1,
            previous_questions=previous_texts,
        )[0]
        candidate.id = f"q{len(session['questions']) + 1}"
        return candidate

    def _evaluate_answer(
        self,
        session: dict[str, Any],
        question: dict[str, Any],
        answer: str,
        override_score: float | None,
    ) -> dict[str, Any]:
        if override_score is not None:
            score = normalize_score(override_score)
            correctness = score
            relevance = score
            depth = score
            clarity = score
            strengths = ["Answer was clear and relevant to the question."]
            weaknesses = ["Consider adding a deeper example or trade-off discussion."]
            improvements = ["Add a concrete example from your project work."]
            overall = round((correctness + relevance + depth + clarity) / 4, 1)
        else:
            content = answer.lower()
            correctness = 8.0 if "rag" in content or "fastapi" in content or "faiss" in content else 6.0
            relevance = 9.0 if "retrieval" in content or "api" in content or "project" in content else 7.0
            depth = 7.0 if "trade" in content or "architecture" in content or "reason" in content else 5.0
            clarity = 8.0 if any(token in content for token in ["because", "we", "used", "i", "this"]) else 6.0
            strengths = [
                "Answer includes role-relevant technical context.",
                "The response connects project experience to the interview question.",
            ]
            weaknesses = [
                "Add more concrete trade-offs or measurement details.",
                "Explain how the design changes under production constraints.",
            ]
            improvements = [
                "Describe the system design choices in more detail.",
                "Provide a concrete example of a failure mode and how you would troubleshoot it.",
            ]
            overall = round((correctness + relevance + depth + clarity) / 4, 1)

        overall = round(float(overall), 1)
        return {
            "overall_score": overall,
            "correctness": round(float(normalize_score(correctness)), 1),
            "relevance": round(float(normalize_score(relevance)), 1),
            "depth": round(float(normalize_score(depth)), 1),
            "clarity": round(float(normalize_score(clarity)), 1),
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3],
            "improvements": improvements[:3],
        }

    def get_report(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        evaluations = [item.get("evaluation", {}) for item in session["evaluations"]]
        if not evaluations:
            raise ValueError("No interview answers have been submitted yet.")

        category_scores = defaultdict(list)
        for item in evaluations:
            category_scores["technical"].append(float(item.get("overall_score", 0)))
            category_scores["ai_genai"].append(float(item.get("overall_score", 0)))
            category_scores["behavioral"].append(float(item.get("overall_score", 0)))
            category_scores["resume"].append(float(item.get("overall_score", 0)))

        normalized_category_scores = {
            key: round(sum(values) / max(len(values), 1), 1) * 10 for key, values in category_scores.items()
        }
        overall_score = round(sum(session["scores"]) / max(len(session["scores"]), 1), 1) * 10
        report = {
            "session_id": session_id,
            "overall_score": int(round(overall_score)),
            "questions_answered": len(session["answers"]),
            "category_scores": normalized_category_scores,
            "strengths": [
                "Strong technical grounding in the selected domain.",
                "Clear explanation of project experience and trade-offs.",
            ],
            "weaknesses": [
                "Continue improving retrieval-evaluation explanations.",
                "Add more explicit production trade-offs.",
            ],
            "recommendations": [
                "Practice explaining RAG architecture without notes.",
                "Review retrieval evaluation metrics and failure modes.",
            ],
            "question_results": [
                {
                    "question_id": result["question_id"],
                    "score": float(result["evaluation"]["overall_score"]),
                    "feedback": result["evaluation"]["weaknesses"],
                }
                for result in session["evaluations"]
            ],
        }
        return report
