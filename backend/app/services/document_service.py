from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_FILE_SIZE_BYTES, METADATA_DIR, UPLOAD_DIR
from app.services.rag import index_uploaded_chunks
from app.utils.file_utils import build_unique_storage_path, ensure_valid_pdf
from app.utils.text_utils import clean_text

logger = logging.getLogger(__name__)


class DocumentProcessingError(ValueError):
    """Raised when a PDF cannot be processed."""


def validate_upload(file_name: str, file_size: int, content_type: str | None) -> None:
    """Validate file metadata before saving and processing."""
    if not file_name:
        raise ValueError("A file is required.")

    ensure_valid_pdf(file_name, content_type)

    if file_size <= 0:
        raise ValueError("Uploaded file is empty.")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Uploaded file exceeds maximum size of {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB."
        )


def extract_pdf_text(file_path: Path) -> list[dict[str, object]]:
    """Extract text pages from a PDF file as structured records."""
    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  # pragma: no cover - parsing failure path
        raise DocumentProcessingError(f"Invalid PDF file: {exc}") from exc

    extracted_pages: list[dict[str, object]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        cleaned = clean_text(page_text)
        if not cleaned:
            continue
        extracted_pages.append(
            {
                "page": page_number,
                "text": cleaned,
                "source": file_path.name,
            }
        )

    if not extracted_pages:
        raise DocumentProcessingError(
            "PDF contains no extractable text. OCR is not supported in the current MVP."
        )

    return extracted_pages


def infer_document_type(file_name: str) -> str:
    """Infer whether a document is a resume or a job description from its name."""
    lowered = (file_name or "").lower()
    if any(token in lowered for token in ["resume", "cv", "curriculum", "profile"]):
        return "resume"
    if any(token in lowered for token in ["job", "jd", "description", "internship", "role", "opening"]):
        return "job_description"
    return "other"


def persist_document_metadata(document_id: str, file_name: str, pages: int, chunks: list[dict[str, object]]) -> dict[str, object]:
    """Persist lightweight metadata for the uploaded document without creating a separate database."""
    metadata_dir = METADATA_DIR
    metadata_dir.mkdir(parents=True, exist_ok=True)
    document_type = infer_document_type(file_name)
    payload = {
        "document_id": document_id,
        "filename": file_name,
        "pages": pages,
        "chunks": len(chunks),
        "status": "indexed",
        "document_type": document_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = metadata_dir / f"{document_id}.json"
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_document_chunks(file_name: str, file_bytes: bytes, content_type: str | None) -> tuple[str, Path, list[dict[str, object]], int]:
    """Store a PDF locally, extract text, and split it into chunk dictionaries."""
    validate_upload(file_name, len(file_bytes), content_type)

    target_dir = UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_path, document_id = build_unique_storage_path(target_dir, file_name)

    with saved_path.open("wb") as destination:
        destination.write(file_bytes)

    extracted_pages = extract_pdf_text(saved_path)

    chunks: list[dict[str, object]] = []
    for page_data in extracted_pages:
        text = str(page_data["text"])
        page_num = int(page_data["page"])
        for chunk_index, chunk in enumerate(split_text_into_chunks(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)):
            chunks.append(
                {
                    "document_id": document_id,
                    "chunk_id": f"{document_id}-{page_num}-{chunk_index}",
                    "source": file_name,
                    "page": page_num,
                    "text": chunk,
                }
            )

    index_result = index_uploaded_chunks(chunks)
    persist_document_metadata(document_id, file_name, len(extracted_pages), chunks)
    logger.info(
        "Saved document %s with %s pages and %s chunks. FAISS index at %s",
        document_id,
        len(extracted_pages),
        len(chunks),
        index_result.get("path"),
    )
    return document_id, saved_path, chunks, len(extracted_pages)


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks while keeping chunk boundaries readable."""
    if not text:
        return []

    text = clean_text(text)
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end == len(text):
            break
        start = max(0, end - chunk_overlap)

    return [chunk for chunk in chunks if chunk]
