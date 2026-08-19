from __future__ import annotations

from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import EMBEDDING_MODEL, GEMINI_API_KEY


def get_embeddings() -> Any:
    """Return configured embedding client for Gemini models."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured. Add it to backend/.env")
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )
