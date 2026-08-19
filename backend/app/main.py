from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, ALLOWED_ORIGINS, settings
from app.routes.career import router as career_router
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router
from app.routes.jobs import router as jobs_router
from app.services.gemini_service import validate_gemini_connection

app = FastAPI(
    title=APP_NAME,
    version=settings.app_version,
    description="CareerPilot AI backend for resume analysis, document RAG, and career guidance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(health_router, prefix="/api", tags=["api-health"])
app.include_router(documents_router, prefix="/documents", tags=["documents"])
app.include_router(documents_router, prefix="/api/documents", tags=["api-documents"])
app.include_router(career_router, prefix="/career", tags=["career"])
app.include_router(career_router, prefix="/api/career", tags=["api-career"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["api-jobs"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(chat_router, prefix="/api/chat", tags=["api-chat"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CareerPilot AI API is running"}


@app.on_event("startup")
async def startup_event() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env or set the environment variable before starting the app."
        )
    validate_gemini_connection()
