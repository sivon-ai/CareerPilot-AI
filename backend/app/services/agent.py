from __future__ import annotations

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.services.rag import query_documents


def _format_retrieval_context(question: str) -> str:
    """Fetch the most relevant indexed passages and return them as prompt context."""
    try:
        results = query_documents(question, k=3)
    except Exception:
        return ""

    chunks = results.get("results", []) if isinstance(results, dict) else []
    if not chunks:
        return ""

    formatted = []
    for item in chunks:
        text = item.get("page_content", "") if isinstance(item, dict) else ""
        if text:
            formatted.append(text)
    return "\n\n".join(formatted)


def answer_question(question: str) -> str:
    """Return a helpful assistant answer grounded in uploaded document context when available."""
    if not GEMINI_API_KEY:
        return (
            "Gemini is not configured yet. Add GEMINI_API_KEY to backend/.env and restart the app "
            "to enable the AI assistant."
        )

    try:
        from google import genai

        context = _format_retrieval_context(question)
        prompt_parts = [
            "You are CareerPilot-AI, a helpful career assistant.",
            "Use the retrieved context below when it helps answer the user's question.",
        ]

        if context:
            prompt_parts.append(f"Relevant context:\n{context}")

        prompt_parts.append(f"Question: {question}")

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_parts,
        )
        return response.text or "No response generated."
    except Exception as exc:  # pragma: no cover - API wrapper
        message = str(exc).lower()
        if "quota" in message or "resource_exhausted" in message or "429" in message:
            return (
                "The AI assistant is temporarily rate-limited by Gemini right now. "
                "Please try again in a few moments or switch to a paid/quota-enabled key."
            )
        return "Unable to generate a response right now. Please try again in a moment."
