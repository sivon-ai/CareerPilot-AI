from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Message cannot be empty.")
        return value.strip()


@router.post("")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Send a message to the career assistant agent."""
    from app.services.agent_service import route_chat_message

    try:
        result = route_chat_message(request.message, session_id=request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - API guard
        raise HTTPException(status_code=500, detail=f"Agent request failed: {exc}") from exc

    payload = {
        "answer": result.get("answer", ""),
        "reply": result.get("answer", ""),
        "sources": result.get("sources", []),
        "tool_calls": result.get("tool_calls", []),
        "session_id": result.get("session_id") or request.session_id or "session-agent",
    }
    return payload
