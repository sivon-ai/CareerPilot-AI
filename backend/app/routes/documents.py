from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.rag import build_document_index, query_documents

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a document to the knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required.")

    try:
        result = build_document_index(file.file, file.filename)
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "chunks": result.get("chunks", 0),
        }
    except Exception as exc:  # pragma: no cover - simple API wrapper
        raise HTTPException(status_code=500, detail=f"Failed to process document: {exc}") from exc


@router.get("/search")
def search_documents(query: str) -> dict[str, Any]:
    """Search uploaded documents for relevant snippets."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        return query_documents(query)
    except Exception as exc:  # pragma: no cover - simple API wrapper
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc
