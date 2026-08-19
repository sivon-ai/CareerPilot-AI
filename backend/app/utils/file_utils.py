from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import uuid


def sanitize_filename(filename: str) -> str:
    """Normalize a user-supplied filename for safe local storage."""
    safe_name = Path(filename).name
    safe_name = safe_name.replace(" ", "_")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", safe_name)
    return safe_name or f"document_{uuid.uuid4().hex}"


def build_unique_storage_path(target_dir: Path, original_filename: str) -> tuple[Path, str]:
    """Return a safe storage path and a unique document ID for the uploaded file."""
    unique_id = uuid.uuid4().hex
    safe_name = sanitize_filename(original_filename)
    stored_name = f"{unique_id}_{safe_name}"
    return target_dir / stored_name, unique_id


def ensure_valid_pdf(file_name: str, content_type: str | None) -> None:
    """Validate a PDF filename and MIME type."""
    if not file_name.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported in this MVP.")

    if content_type and content_type.lower() not in {"application/pdf", "application/octet-stream"}:
        raise ValueError("Uploaded file must be a valid PDF.")
