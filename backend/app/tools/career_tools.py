from __future__ import annotations

from typing import Any


class CareerTools:
    """Simple utility tools for career planning workflows."""

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
