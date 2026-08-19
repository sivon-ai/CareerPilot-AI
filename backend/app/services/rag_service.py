from __future__ import annotations

from typing import Any

from app.config import GEMINI_API_KEY, GEMINI_MODEL, TOP_K
from app.services.embeddings import get_embeddings
from app.services.rag import INDEX_PATH
from langchain_community.vectorstores import FAISS


def generate_query_embedding(query: str) -> list[float]:
    """Generate an embedding for the user's question."""
    normalized = (query or "").strip()
    if not normalized:
        raise ValueError("A question is required.")

    client = get_embeddings()
    return client.embed_query(normalized)


def search_similar_chunks(embedding: list[float], k: int = TOP_K) -> list[Any]:
    """Fetch the most relevant indexed passages from the local FAISS store."""
    if not INDEX_PATH.exists():
        return []

    vector_store = FAISS.load_local(
        str(INDEX_PATH),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )
    return vector_store.similarity_search_by_vector(embedding, k=k)


def _normalize_sources(matches: list[Any]) -> list[dict[str, Any]]:
    """Convert retrieval results to a simple list of source metadata."""
    sources: list[dict[str, Any]] = []
    for item in matches:
        metadata = getattr(item, "metadata", {}) or {}
        source = metadata.get("source") or "unknown"
        sources.append(
            {
                "source": source,
                "page": metadata.get("page"),
                "document_id": metadata.get("document_id"),
                "chunk_id": metadata.get("chunk_id"),
            }
        )
    return sources


def generate_answer(question: str, context: str) -> str:
    """Ask Gemini for a grounded answer using the retrieved context."""
    if not GEMINI_API_KEY:
        return "Gemini is not configured yet. Add GEMINI_API_KEY to backend/.env and restart the app."

    try:
        from google import genai

        prompt_parts = [
            "You are CareerPilot-AI, a helpful career assistant.",
            "Answer the user's question using the retrieved context when available.",
            f"Context:\n{context}",
            f"Question: {question}",
        ]

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


def answer_question(question: str) -> dict[str, Any]:
    """Return a grounded answer plus source metadata for the frontend chat panel."""
    normalized = (question or "").strip()
    if not normalized:
        raise ValueError("A question is required.")

    embedding = generate_query_embedding(normalized)
    matches = search_similar_chunks(embedding, k=TOP_K)

    context_parts = []
    for item in matches:
        text = getattr(item, "page_content", "") or ""
        if text:
            context_parts.append(text)

    context = "\n\n".join(context_parts)
    answer = generate_answer(normalized, context)
    return {
        "answer": answer,
        "sources": _normalize_sources(matches),
        "context": context,
    }
