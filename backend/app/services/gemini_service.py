from __future__ import annotations

import logging

from google import genai

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


def get_gemini_client() -> genai.Client:
    """Return the configured Gemini client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=GEMINI_API_KEY)


def validate_gemini_connection() -> bool:
    """Validate that the configured Gemini API key and model are usable.

    A temporary quota exhaustion should not crash the app at startup; the AI features can
    fail gracefully later when the user asks for a chat response.
    """
    try:
        client = get_gemini_client()
        client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Connection check",
        )
        logger.info("Gemini connection validated for model %s", GEMINI_MODEL)
        return True
    except Exception as exc:  # pragma: no cover - startup validation path
        logger.warning("Gemini validation failed; app will continue in degraded mode: %s", exc)
        return False
