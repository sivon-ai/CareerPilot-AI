from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple service health response."""
    return {"status": "healthy", "service": "careerpilot-ai"}
