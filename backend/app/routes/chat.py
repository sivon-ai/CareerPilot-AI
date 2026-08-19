from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Send a message to the career assistant agent."""
    if not request.message.strip():
        return {"reply": "Please enter a message."}

    reply = answer_question(request.message)
    return {"reply": reply}
