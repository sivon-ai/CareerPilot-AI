from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import METADATA_DIR
from app.models.responses import DocumentUploadResponse
from app.services.document_service import build_document_chunks
from app.services.rag import query_documents

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload a PDF, save it locally, and prepare it for indexing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required.")

    raw = await file.read()

    try:
        document_id, saved_path, chunks, pages = build_document_chunks(
            file_name=file.filename,
            file_bytes=raw,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to process uploaded PDF %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {exc}") from exc

    return DocumentUploadResponse(
        document_id=document_id,
        filename=saved_path.name,
        pages=pages,
        chunks=len(chunks),
        status="indexed",
        document_type="resume" if "resume" in (file.filename or "").lower() or "cv" in (file.filename or "").lower() else "job_description" if any(token in (file.filename or "").lower() for token in ["job", "jd", "description", "opening", "role"]) else "other",
    )


@router.post("/search")
async def search_documents(request: SearchRequest) -> dict[str, Any]:
    """Search the local FAISS index for the highest-similarity document chunks."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="A search query is required.")

    try:
        return query_documents(request.query, k=5)
    except Exception as exc:
        logger.exception("Document search failed for query %s", request.query)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.get("/")
async def list_documents() -> dict[str, Any]:
    """Return uploaded document metadata stored in the lightweight metadata directory."""
    documents: list[dict[str, Any]] = []
    if METADATA_DIR.exists():
        for metadata_path in sorted(METADATA_DIR.glob("*.json")):
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    documents.append(payload)
            except Exception:
                continue
    return {"documents": documents}


@router.get("/{document_id}")
async def get_document(document_id: str) -> dict[str, Any]:
    """Return metadata about a single uploaded document."""
    metadata_path = METADATA_DIR / f"{document_id}.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return payload


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict[str, Any]:
    """Delete a document placeholder."""
    return {"document_id": document_id, "status": "deleted"}


@router.post("/reindex")
async def reindex_documents() -> dict[str, Any]:
    """Rebuild the vector index."""
    return {"status": "not_implemented"}
