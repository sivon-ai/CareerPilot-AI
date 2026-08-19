from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import APP_NAME, ALLOWED_ORIGINS, settings
from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.career import router as career_router
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router
from app.routes.interview import router as interview_router
from app.routes.jobs import router as jobs_router
from app.services.gemini_service import validate_gemini_connection

logger = logging.getLogger("careerpilot")
logging.basicConfig(level=getattr(logging, settings.environment.upper() == "PRODUCTION" and "INFO" or "DEBUG"), format="%(asctime)s %(levelname)s request_id=%(request_id)s %(message)s")


class RateLimitMiddleware:
    def __init__(self, app: FastAPI, *, limits: dict[str, int]) -> None:
        self.app = app
        self.limits = limits
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path
        if path in {"/health", "/ready"}:
            await self.app(scope, receive, send)
            return

        limit = {
            "/chat": settings.rate_limit_chat,
            "/api/chat": settings.rate_limit_chat,
            "/documents/upload": settings.rate_limit_upload,
            "/api/documents/upload": settings.rate_limit_upload,
            "/jobs/match": settings.rate_limit_match,
            "/api/jobs/match": settings.rate_limit_match,
            "/interview/start": settings.rate_limit_match,
            "/api/interview/start": settings.rate_limit_match,
        }.get(path, 0)

        if limit > 0:
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window = self.requests[client_ip]
            window.append(now)
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) > limit:
                payload = {"error": {"code": "RATE_LIMITED", "message": "Too many requests. Please wait a moment before trying again."}}
                response = JSONResponse(status_code=429, content=payload)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


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

app.add_middleware(RateLimitMiddleware, limits={})


@app.middleware("http")
async def _app_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:  # pragma: no cover - handled after
        logger.exception("Unhandled server error for %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info("method=%s path=%s status=%s duration_ms=%s request_id=%s", request.method, request.url.path, response.status_code, duration_ms, request_id)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": jsonable_encoder(exc.errors())}},
    )


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "The requested resource was not found."}})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}})


app.include_router(auth_router)
app.include_router(health_router, tags=["health"])
app.include_router(health_router, prefix="/api", tags=["api-health"])
app.include_router(documents_router, prefix="/documents", tags=["documents"])
app.include_router(documents_router, prefix="/api/documents", tags=["api-documents"])
app.include_router(career_router, prefix="/career", tags=["career"])
app.include_router(career_router, prefix="/api/career", tags=["api-career"])
app.include_router(interview_router, prefix="/interview", tags=["interview"])
app.include_router(interview_router, prefix="/api/interview", tags=["api-interview"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["api-jobs"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(chat_router, prefix="/api/chat", tags=["api-chat"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CareerPilot AI API is running"}


@app.get("/ready")
async def ready() -> dict[str, Any]:
    return {"status": "ready", "database": "ok"}


@app.on_event("startup")
async def startup_event() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - startup safety guard
        logger.warning("Database initialization skipped or failed: %s", exc)

    if settings.gemini_api_key:
        validate_gemini_connection()
