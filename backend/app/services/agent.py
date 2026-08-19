from __future__ import annotations

from typing import Any

from app.config import MODEL_NAME, OPENAI_API_KEY


def answer_question(question: str) -> str:
    """Return a simple assistant answer using the configured model when available."""
    if not OPENAI_API_KEY:
        return (
            "OpenAI is not configured yet. Add OPENAI_API_KEY to backend/.env and restart the app "
            "to enable the AI assistant."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are CareerPilot-AI, a helpful career assistant."},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content or "No response generated."
    except Exception as exc:  # pragma: no cover - API wrapper
        return f"Unable to generate a response right now: {exc}"
