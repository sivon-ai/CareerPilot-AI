from __future__ import annotations

import re
from typing import Any


class CareerTools:
    """Simple utility tools for career planning workflows."""

    @staticmethod
    def _normalize_tokens(text: str) -> set[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        stop_words = {
            "the", "and", "for", "with", "into", "from", "your", "you", "our", "that", "this",
            "role", "skills", "experience", "project", "projects", "work", "using", "across",
            "about", "over", "through", "within", "team", "teams", "will", "can", "should",
        }
        tokens = {token for token in re.split(r"\s+", text.strip()) if token and token not in stop_words}
        return tokens

    def summarize_skill_gap(self, skills: list[str], target_role: str) -> dict[str, Any]:
        missing = [skill for skill in skills if skill.lower() not in {"python", "sql", "communication", "project management"}]
        return {
            "target_role": target_role,
            "missing_skills": missing,
            "recommendation": "Focus on the highest-impact skills first and build a learning roadmap around them.",
        }

    def career_plan(self, current_role: str, target_role: str) -> dict[str, Any]:
        return {
            "current_role": current_role,
            "target_role": target_role,
            "steps": [
                "Audit current strengths and gaps",
                "Build a skill roadmap",
                "Create portfolio proof for target role",
                "Apply strategically and track results",
            ],
        }

    def match_resume_to_jobs(self, resume_text: str, jobs: list[dict[str, Any]]) -> dict[str, Any]:
        resume_tokens = self._normalize_tokens(resume_text)
        ranked: list[dict[str, Any]] = []

        for job in jobs:
            title = str(job.get("title", "Untitled role"))
            requirements = str(job.get("requirements", ""))
            job_tokens = self._normalize_tokens(f"{title} {requirements}")
            overlap = sorted(resume_tokens & job_tokens)
            if not overlap and not resume_tokens:
                score = 0.0
            else:
                score = round((len(overlap) / max(len(job_tokens), 1)) * 100, 2)

            ranked.append(
                {
                    "title": title,
                    "score": score,
                    "match_count": len(overlap),
                    "matched_skills": overlap,
                    "missing_skills": sorted(job_tokens - resume_tokens),
                }
            )

        ranked.sort(key=lambda item: (-item["score"], -item["match_count"], item["title"]))
        return {"count": len(ranked), "matches": ranked}
