from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import Document, User

router = APIRouter(tags=["protected"])


@router.get("/me/documents")
def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    documents = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    return {
        "documents": [
            {
                "document_id": document.id,
                "filename": document.filename,
                "document_type": document.document_type,
                "status": document.status,
            }
            for document in documents
        ]
    }


@router.get("/documents/{document_id}")
def get_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document or document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return {
        "document_id": document.id,
        "filename": document.filename,
        "document_type": document.document_type,
        "pages": document.pages,
        "chunks": document.chunks,
        "status": document.status,
    }
